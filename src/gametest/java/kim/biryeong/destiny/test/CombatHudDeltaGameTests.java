package kim.biryeong.destiny.test;

import io.netty.buffer.Unpooled;
import kim.biryeong.destiny.hud.CombatHud;
import kim.biryeong.minigamelib.displayhud.DisplayHud;
import kim.biryeong.minigamelib.displayhud.ItemDisplayHud;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.core.component.DataComponents;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.RegistryFriendlyByteBuf;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.BundlePacket;
import net.minecraft.network.protocol.Packet;
import net.minecraft.network.protocol.game.ClientboundSetEntityDataPacket;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.server.players.PlayerList;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.component.CustomModelData;
import net.minecraft.world.phys.Vec3;

import java.lang.reflect.Method;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.UUID;

/** Native metadata deltas, not a counter that assumes a setter sent a packet. */
public final class CombatHudDeltaGameTests {
    private static final int WHITE = 0xF1F3F5;
    private static final DisplayHud.HudAlignment CENTER = DisplayHud.HudAlignment.CENTER;
    private static final DisplayHud.HudAlignment LEFT = DisplayHud.HudAlignment.LEFT;

    private static void check(GameTestHelper h, boolean ok, String message) {
        h.assertTrue(ok, Component.literal(message));
    }

    @SuppressWarnings("unchecked")
    private static ServerPlayer player(GameTestHelper h) {
        var p = TestPlayers.create(h, new Vec3(2.5, 2, 6.5), 0, 0);
        try {
            // Real DisplayHud.update resolves viewers via PlayerList.getPlayer(UUID).
            // Register only this fixture identity; do not run a native login or unrelated player ticks.
            var field = PlayerList.class.getDeclaredField("playersByUUID");
            field.setAccessible(true);
            var owners = (Map<UUID, ServerPlayer>) field.get(h.getLevel().getServer().getPlayerList());
            check(h, owners.putIfAbsent(p.getUUID(), p) == null, "Independent HUD viewer UUID");
            TestCleanup.register(h, () -> {
                for (var id : List.copyOf(DisplayHud.getHuds(p).keySet())) DisplayHud.removeHud(p, id);
                owners.remove(p.getUUID(), p);
                TestPlayers.remove(p);
            });
            check(h, h.getLevel().getServer().getPlayerList().getPlayer(p.getUUID()) == p,
                    "Native HUD viewer lookup resolves the exact fixture connection");
            TestPlayers.drain(p);
            return p;
        } catch (ReflectiveOperationException e) { TestPlayers.remove(p); throw new AssertionError(e); }
    }

    private static Method method(String name, Class<?>... types) {
        try {
            var m = CombatHud.class.getDeclaredMethod(name, types);
            m.setAccessible(true);
            return m;
        } catch (ReflectiveOperationException e) { throw new AssertionError(e); }
    }

    private static void sprite(ServerPlayer p, String id, String image, float width, int color,
                               DisplayHud.HudAlignment alignment) {
        try {
            method("sprite", ServerPlayer.class, String.class, String.class, float.class, float.class,
                    float.class, float.class, float.class, int.class, DisplayHud.HudAlignment.class)
                    .invoke(null, p, id, image, 100f, 100f, width, 6f, 2f, color, alignment);
        } catch (ReflectiveOperationException e) { throw new AssertionError(e); }
    }

    private static void bar(ServerPlayer p, String id, float width) {
        try {
            method("bar", ServerPlayer.class, String.class, float.class, float.class, float.class,
                    float.class, float.class, int.class, DisplayHud.HudAlignment.class)
                    .invoke(null, p, id, 40f, 76f, width, 7f, 2f, WHITE, CENTER);
        } catch (ReflectiveOperationException e) { throw new AssertionError(e); }
    }

    private static void flatten(Packet<?> packet, List<Packet<?>> out) {
        if (packet instanceof BundlePacket<?> bundle) for (var child : bundle.subPackets()) flatten(child, out);
        else out.add(packet);
    }

    private static List<ClientboundSetEntityDataPacket> metadata(GameTestHelper h, ServerPlayer p, int id) {
        var all = new ArrayList<Packet<?>>();
        for (var packet : TestPlayers.outbound(p)) flatten(packet, all);
        var result = all.stream().filter(ClientboundSetEntityDataPacket.class::isInstance)
                .map(ClientboundSetEntityDataPacket.class::cast).filter(packet -> packet.id() == id).toList();
        for (var packet : result) {
            var bytes = new RegistryFriendlyByteBuf(Unpooled.buffer(), p.registryAccess());
            try {
                ClientboundSetEntityDataPacket.STREAM_CODEC.encode(bytes, packet);
                var decoded = ClientboundSetEntityDataPacket.STREAM_CODEC.decode(bytes);
                check(h, decoded.id() == id && decoded.packedItems().size() == packet.packedItems().size()
                        && bytes.readableBytes() == 0, "Native metadata codec consumes the complete owner HUD delta");
            } finally { bytes.release(); }
        }
        return result;
    }

    private static boolean containsItem(List<ClientboundSetEntityDataPacket> packets) {
        return packets.stream().flatMap(p -> p.packedItems().stream()).anyMatch(v -> v.value() instanceof ItemStack);
    }

    @GameTest(structure="destiny-test:floor", environment="destiny-test:w90_isolated", maxTicks=30)
    public void geometryOnlyRecoveryRetainsFractionalWidthWithoutResendingItem(GameTestHelper h) {
        var p = player(h);
        bar(p, CombatHud.HEALTH_ID, 200);
        var hud = (ItemDisplayHud) DisplayHud.getHud(p, CombatHud.HEALTH_ID);
        int id = hud.getEntityId();
        TestPlayers.drain(p);
        bar(p, CombatHud.HEALTH_ID, 200.25f);
        var recovery = metadata(h, p, id);
        check(h, recovery.size() == 1 && !containsItem(recovery), "Recovery emits one geometry delta without an item payload");
        check(h, hud.getScale().x == 200.25f && hud.getInterpolationDuration() == 2,
                "Health retains fractional scale and two-tick healing interpolation");
        for (int i = 0; i < 20; i++) bar(p, CombatHud.HEALTH_ID, 200.25f);
        check(h, metadata(h, p, id).isEmpty(), "Unchanged repeated health projection emits zero metadata");
        bar(p, CombatHud.HEALTH_ID, 199.75f);
        var damage = metadata(h, p, id);
        check(h, damage.size() == 1 && !containsItem(damage) && hud.getInterpolationDuration() == 0,
                "Damage remains immediate and reuses the same item");
        String quantized = "destiny:scale_hud_quantized";
        bar(p, quantized, 10.26f); TestPlayers.drain(p);
        int quantizedId = DisplayHud.getHud(p, quantized).getEntityId();
        bar(p, quantized, 10.49f);
        check(h, metadata(h, p, quantizedId).isEmpty() && DisplayHud.getHud(p, quantized).getScale().x == 10.5f,
                "Ordinary bars keep the existing half-pixel quantization");
        h.succeed();
    }

    @GameTest(structure="destiny-test:floor", environment="destiny-test:w90_isolated", maxTicks=30)
    public void changedModelTintAndAboveHandStillReachTheNativeViewer(GameTestHelper h) {
        var p = player(h); String key = "destiny:scale_hud_item";
        sprite(p, key, "solid", 100, WHITE, LEFT);
        var hud = (ItemDisplayHud) DisplayHud.getHud(p, key); int id = hud.getEntityId(); TestPlayers.drain(p);
        sprite(p, key, "ammo_panel", 100, WHITE, LEFT);
        var model = metadata(h, p, id);
        check(h, model.size() == 1 && containsItem(model)
                        && Identifier.parse("destiny:gui/hud/ammo_panel").equals(hud.getItem().get(DataComponents.ITEM_MODEL)),
                "A changed model still sends one real item delta");
        sprite(p, key, "ammo_panel", 100, 0xFF0000, LEFT);
        var tint = metadata(h, p, id);
        check(h, tint.size() == 1 && containsItem(tint)
                        && hud.getItem().get(DataComponents.CUSTOM_MODEL_DATA).colors().equals(List.of(0xFF0000)),
                "Changed tint reaches the stack without respawning the HUD");
        p.setItemInHand(InteractionHand.OFF_HAND, new ItemStack(Items.STONE)); TestPlayers.drain(p);
        sprite(p, key, "ammo_panel", 100, 0xFF0000, LEFT);
        var hand = metadata(h, p, id);
        check(h, hand.size() == 1 && !containsItem(hand) && hud.isAboveHand(),
                "Offhand occupancy changes above-hand brightness without resending the item");
        h.succeed();
    }

    @GameTest(structure="destiny-test:floor", environment="destiny-test:w90_isolated", maxTicks=30)
    public void legacyStateMigratesSilentlyAndRemovedNodesDoNotRetainCachedItems(GameTestHelper h) {
        var p = player(h); String id = "destiny:scale_hud_legacy";
        var old = new ItemDisplayHud(); old.updateWhenDataChanged(false);
        var stack = new ItemStack(Items.PAPER);
        stack.set(DataComponents.ITEM_MODEL, Identifier.parse("destiny:gui/hud/solid"));
        stack.set(DataComponents.CUSTOM_MODEL_DATA, new CustomModelData(List.of(), List.of(), List.of(), List.of(WHITE)));
        old.setItem(stack); old.setScale(100.04f, 6, 1); old.setAlignment(CENTER); old.setLocation(100, 100, 2);
        old.setExtraData("state", "solid:" + WHITE + ":1000:6.0:100.0:100.0:2.0:CENTER:false");
        old.spawn(p, id); old.updateWhenDataChanged(true); TestPlayers.drain(p);
        sprite(p, id, "solid", 100.03f, WHITE, CENTER);
        check(h, metadata(h, p, old.getEntityId()).isEmpty(), "Matching legacy string migrates without an item or geometry delta");
        sprite(p, id, "solid", 100.03f, 0xFF0000, CENTER);
        check(h, containsItem(metadata(h, p, old.getEntityId())) && old.getScale().x == 100.03f,
                "A later changed state applies its actual width despite the legacy rounded cache key");
        DisplayHud.removeHud(p, id); TestPlayers.drain(p);
        sprite(p, id, "solid", 100.03f, 0xFF0000, CENTER);
        var fresh = DisplayHud.getHud(p, id);
        check(h, fresh != old && fresh.getEntityId() != old.getEntityId()
                        && containsItem(metadata(h, p, fresh.getEntityId())),
                "Removal ends cache ownership; a replacement sends its required item metadata");
        h.succeed();
    }
}
