package kim.biryeong.destiny.test;

import kim.biryeong.destiny.guardian.Element;
import kim.biryeong.destiny.guardian.Guardians;
import kim.biryeong.destiny.hud.CombatHud;
import kim.biryeong.minigamelib.displayhud.DisplayHud;
import kim.biryeong.minigamelib.displayhud.ItemDisplayHud;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.BundlePacket;
import net.minecraft.network.protocol.Packet;
import net.minecraft.network.protocol.game.ClientboundAddEntityPacket;
import net.minecraft.network.protocol.game.ClientboundRemoveEntitiesPacket;
import net.minecraft.network.protocol.game.ClientboundSetEntityDataPacket;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.server.players.PlayerList;
import net.minecraft.util.Brightness;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.phys.Vec3;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

/** W76 server HUD state and actual outgoing metadata; client occlusion is checked by Vision separately. */
public final class HudOffhandW76GameTests {
    private static final String FLOOR = "destiny-test:floor";
    private static final String GLOBAL = "destiny-test:w90_w76_global";

    private static void check(GameTestHelper h, boolean ok, String message) {
        h.assertTrue(ok, Component.literal(message));
    }

    /** Lookup-only registration lets DisplayHud resolve viewers without world-ticking the embedded owner. */
    @SuppressWarnings("unchecked")
    private static Map<UUID, ServerPlayer> playerLookup(GameTestHelper h) {
        try {
            var field = PlayerList.class.getDeclaredField("playersByUUID");
            field.setAccessible(true);
            return (Map<UUID, ServerPlayer>) field.get(h.getLevel().getServer().getPlayerList());
        } catch (ReflectiveOperationException failure) {
            throw new AssertionError("W76 embedded viewer lookup fixture", failure);
        }
    }

    private static final class Owner implements AutoCloseable {
        private final ServerPlayer player;
        private final Map<UUID, ServerPlayer> lookup;
        private boolean closed;

        private Owner(GameTestHelper h) {
            lookup = playerLookup(h);
            player = TestPlayers.hunter(h, Element.ARC, new Vec3(2.5, 1, 2.5), 0, 0);
            TestCleanup.register(h, this::close);
            check(h, lookup.putIfAbsent(player.getUUID(), player) == null, "Unique embedded HUD owner");
            Guardians.data(player).setSuperEnergy(0.5f);
            player.getAttribute(Attributes.MAX_ABSORPTION).setBaseValue(20);
            player.setAbsorptionAmount(4);
            TestPlayers.drain(player);
        }

        @Override
        public void close() {
            if (closed) return;
            closed = true;
            try {
                CombatHud.remove(player);
            } finally {
                try { TestPlayers.remove(player); }
                finally { lookup.remove(player.getUUID(), player); }
            }
        }
    }

    private static Map<String, DisplayHud> left(GameTestHelper h, ServerPlayer player) {
        var result = new HashMap<String, DisplayHud>();
        DisplayHud.getHuds(player).forEach((id, hud) -> {
            if (hud.getAlignment() == DisplayHud.HudAlignment.LEFT) result.put(id, hud);
        });
        check(h, result.containsKey(CombatHud.ABILITIES_ID)
                        && result.containsKey(CombatHud.ABILITIES_ID + "_icon")
                        && result.containsKey(CombatHud.ABILITIES_ID + "_charge")
                        && result.containsKey(CombatHud.SUPER_ID)
                        && result.containsKey("destiny:hud_super_diamond"),
                "Exercise actual ability tiles, glyphs, charge bars and super cluster");
        return result;
    }

    private static Brightness brightness(boolean aboveHand) {
        return aboveHand
                ? new Brightness(DisplayHud.ABOVE_HAND_BLOCK_LIGHT, DisplayHud.ABOVE_HAND_SKY_LIGHT)
                : new Brightness(15, 15);
    }

    private static void flags(GameTestHelper h, ServerPlayer player, boolean aboveHand) {
        for (var entry : left(h, player).entrySet()) {
            var hud = entry.getValue();
            check(h, hud.isAboveHand() == aboveHand, entry.getKey() + " actual above-hand flag");
            check(h, brightness(aboveHand).equals(hud.getDisplay().getBrightnessOverride()),
                    entry.getKey() + " actual display brightness marker");
        }
        for (String id : List.of(CombatHud.HEALTH_ID + "_track", CombatHud.HEALTH_ID, CombatHud.ABSORPTION_ID)) {
            var hud = DisplayHud.getHud(player, id);
            check(h, hud != null && hud.getAlignment() == DisplayHud.HudAlignment.CENTER
                            && !hud.isAboveHand() && brightness(false).equals(hud.getDisplay().getBrightnessOverride()),
                    id + " remains ordinary center-aligned vitals");
        }
    }

    private static void flatten(Packet<?> packet, List<Packet<?>> result) {
        if (packet instanceof BundlePacket<?> bundle) {
            for (var child : bundle.subPackets()) flatten(child, result);
        } else result.add(packet);
    }

    private static List<Packet<?>> outbound(ServerPlayer player) {
        var result = new ArrayList<Packet<?>>();
        for (var packet : TestPlayers.outbound(player)) flatten(packet, result);
        return result;
    }

    @GameTest(structure = FLOOR, environment = GLOBAL, maxTicks = 20)
    public void initialOffhandCobblestoneMarksLeftSpritesButLeavesCenterVitalsOrdinary(GameTestHelper h) {
        try (var owner = new Owner(h)) {
            var player = owner.player;
            player.setItemInHand(InteractionHand.OFF_HAND, new ItemStack(Items.COBBLESTONE));
            CombatHud.update(player);
            flags(h, player, true);
            var packets = outbound(player);
            for (var hud : left(h, player).values()) {
                check(h, packets.stream().anyMatch(packet -> packet instanceof ClientboundAddEntityPacket add
                                && add.getId() == hud.getEntityId()), "Initial left HUD entity actually spawned");
                var first = packets.stream().filter(packet -> packet instanceof ClientboundSetEntityDataPacket data
                                && data.id() == hud.getEntityId())
                        .map(ClientboundSetEntityDataPacket.class::cast).findFirst().orElseThrow();
                check(h, first.packedItems().stream().anyMatch(value -> Integer.valueOf(brightness(true).pack()).equals(value.value())),
                        "First spawn metadata already contains above-hand marker");
            }
        }
        h.succeed();
    }

    @GameTest(structure = FLOOR, environment = GLOBAL, maxTicks = 20)
    public void emptyOffhandEmptyTransitionsInvalidateCacheAndUpdateTheSameEntities(GameTestHelper h) {
        try (var owner = new Owner(h)) {
            var player = owner.player;
            CombatHud.update(player);
            flags(h, player, false);
            var original = Map.copyOf(DisplayHud.getHuds(player));
            var left = left(h, player);
            var states = new HashMap<String, Object>();
            left.forEach((id, hud) -> states.put(id, hud.getExtraData("state")));
            TestPlayers.drain(player);
            for (boolean occupied : List.of(true, false)) {
                player.setItemInHand(InteractionHand.OFF_HAND,
                        occupied ? new ItemStack(Items.COBBLESTONE) : ItemStack.EMPTY);
                CombatHud.update(player);
                flags(h, player, occupied);
                var packets = outbound(player);
                check(h, DisplayHud.getHuds(player).keySet().equals(original.keySet()), "Offhand changes no HUD node membership");
                for (var entry : original.entrySet()) {
                    var hud = entry.getValue();
                    check(h, DisplayHud.getHud(player, entry.getKey()) == hud, "Transition reuses exact HUD object and entity ID");
                    check(h, packets.stream().noneMatch(packet ->
                                    packet instanceof ClientboundAddEntityPacket add && add.getId() == hud.getEntityId()
                                    || packet instanceof ClientboundRemoveEntitiesPacket remove && remove.entityIds().contains(hud.getEntityId())),
                            "No existing HUD entity respawn or removal on transition");
                    var updates = packets.stream().filter(packet -> packet instanceof ClientboundSetEntityDataPacket data
                                    && data.id() == hud.getEntityId()).map(ClientboundSetEntityDataPacket.class::cast).toList();
                    if (left.containsKey(entry.getKey())) {
                        check(h, states.get(entry.getKey()).equals(hud.getExtraData("state")) != occupied,
                                "Offhand state participates in the sprite cache and restores the empty-hand key");
                        check(h, updates.size() == 1 && updates.getFirst().packedItems().stream()
                                        .anyMatch(value -> Integer.valueOf(brightness(occupied).pack()).equals(value.value())),
                                "Exactly one real metadata update carries each changed left HUD marker");
                    } else check(h, updates.isEmpty(), "Ordinary center HUD sends no offhand-only update");
                }
            }
        }
        h.succeed();
    }

    @GameTest(structure = FLOOR, environment = GLOBAL, maxTicks = 20)
    public void stableEmptyAndOccupiedOffhandsKeepCachedItemsAndEmitNoRepeatedUpdates(GameTestHelper h) {
        try (var owner = new Owner(h)) {
            var player = owner.player;
            // A main-hand block alone must not opt the lower-left HUD into the above-hand pass.
            player.setItemInHand(InteractionHand.MAIN_HAND, new ItemStack(Items.COBBLESTONE));
            for (boolean occupied : List.of(false, true, false)) {
                player.setItemInHand(InteractionHand.OFF_HAND,
                        occupied ? new ItemStack(Items.COBBLESTONE) : ItemStack.EMPTY);
                CombatHud.update(player);
                flags(h, player, occupied);
                var original = Map.copyOf(DisplayHud.getHuds(player));
                var items = new HashMap<String, ItemStack>();
                original.forEach((id, hud) -> items.put(id, ((ItemDisplayHud) hud).getItemDisplay().getItemStack()));
                TestPlayers.drain(player);
                for (int i = 0; i < 32; i++) CombatHud.update(player);
                check(h, outbound(player).isEmpty(), "32 stable updates emit no outgoing metadata, spawn or mount traffic");
                for (var entry : original.entrySet()) {
                    var hud = DisplayHud.getHud(player, entry.getKey());
                    check(h, hud == entry.getValue()
                                    && ((ItemDisplayHud) hud).getItemDisplay().getItemStack() == items.get(entry.getKey()),
                            "Stable cache keeps exact HUD and native item objects");
                }
                flags(h, player, occupied);
            }
            player.setItemInHand(InteractionHand.OFF_HAND, new ItemStack(Items.COBBLESTONE));
            CombatHud.update(player);
            check(h, DisplayHud.getVisibleHudIds(player).length == DisplayHud.getHuds(player).size() + 1,
                    "Occupied offhand has exactly one private above-hand trigger");
            CombatHud.remove(player);
            check(h, DisplayHud.getHuds(player).isEmpty() && DisplayHud.getVisibleHudIds(player).length == 0,
                    "Own HUD teardown also removes the private above-hand trigger");
        }
        h.succeed();
    }
}
