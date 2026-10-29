package kim.biryeong.destiny.test;

import kim.biryeong.destiny.sound.DestinySounds;
import kim.biryeong.destiny.weapon.WeaponCatalog;
import kim.biryeong.destiny.weapon.WeaponItems;
import kim.biryeong.destiny.weapon.WeaponLoadout;
import kim.biryeong.destiny.weapon.WeaponMagazine;
import kim.biryeong.destiny.weapon.WeaponProfile;
import kim.biryeong.destiny.weapon.WeaponRuntime;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.core.Holder;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.game.ClientboundSoundPacket;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.gamerules.GameRules;
import net.minecraft.world.phys.Vec3;

import java.util.List;

/** Paid production emissions through W92's native framed PLAY encoder/client decode.
 * Not an authenticated client, client-side random-variant selection, or acoustic proof.
 */
public final class WeaponAudioVariantsW98GameTests {
    private static final List<String> NAMED = List.of(
            "seventh_seraph_officer_revolver", "steelfeather_repeater", "the_recluse");

    private static void check(GameTestHelper h, boolean yes, String why) {
        h.assertTrue(yes, Component.literal(why));
    }

    private static void deck(GameTestHelper h) {
        check(h, !h.getLevel().getGameRules().get(GameRules.SPAWN_MOBS),
                "Registered W90 isolation is active before fixture setup");
        for (int x = 0; x < 48; x++) for (int z = 0; z < 32; z++)
            h.setBlock(x, 3, z, Blocks.STONE);
    }

    private static void bounded(GameTestHelper h, ServerPlayer player) {
        var o = h.absoluteVec(Vec3.ZERO);
        var b = player.getBoundingBox();
        check(h, player.level() == h.getLevel()
                        && b.minX > o.x && b.maxX < o.x + 48
                        && b.minY > o.y && b.maxY < o.y + 12
                        && b.minZ > o.z && b.maxZ < o.z + 32,
                "Entire owned actor AABB remains inside the W90 48x12x32 fixture");
    }

    private static InventoryWireW92 wire(GameTestHelper h, Vec3 relative, boolean listener) {
        // W92 registers its idempotent close before channel construction. Register level removal
        // before addNewPlayer, so LIFO cleanup removes membership before releasing that channel.
        var w = new InventoryWireW92(h, relative);
        var p = w.player;
        TestCleanup.register(h, () -> {
            if (h.getLevel().players().contains(p))
                h.getLevel().removePlayerImmediately(p, Entity.RemovalReason.DISCARDED);
        });
        p.setAttached(WeaponLoadout.ENABLED, false);
        bounded(h, p);
        h.onEachTick(() -> bounded(h, p));
        if (listener) h.getLevel().addNewPlayer(p);
        w.discard();
        return w;
    }

    private static ItemStack equip(GameTestHelper h, InventoryWireW92 w, String id) {
        var entry = WeaponCatalog.find(id).orElseThrow();
        var profile = WeaponProfile.forEntry(entry);
        check(h, profile.mode() == WeaponProfile.Mode.HITSCAN && profile.chargeTicks() == 0
                        && profile.burst() == 1 && profile.pellets() == 1 && profile.magazine() >= 3,
                "Fixture uses an immediate, single paid hitscan emission: " + id);
        var gun = WeaponItems.create(entry);
        WeaponItems.save(gun, new WeaponMagazine(profile, 3, 0));
        w.player.getInventory().setItem(0, gun);
        w.player.getInventory().setSelectedSlot(0);
        WeaponRuntime.tickPlayer(w.player);
        state(h, gun, 3);
        w.discard();
        return gun;
    }

    private static WeaponMagazine ammo(ItemStack gun) {
        return WeaponItems.magazine(gun, WeaponProfile.forEntry(WeaponItems.entry(gun).orElseThrow()));
    }

    private static void state(GameTestHelper h, ItemStack gun, int loaded) {
        var a = ammo(gun);
        check(h, a.rounds() == loaded && a.reserve() == 0 && a.overflow() == 0,
                "Exact item-owned ammunition is " + loaded + "/0 with zero overflow");
    }

    private static List<ClientboundSoundPacket> firePackets(InventoryWireW92 w,
                                                            ClientboundSoundPacket origin) {
        // Capture() reads framed native bytes and decodes outside server PacketContext. Match the
        // source's wire-quantized origin, as in W33, to exclude adjacent parallel fixtures only.
        return w.capture().stream().filter(ClientboundSoundPacket.class::isInstance)
                .map(ClientboundSoundPacket.class::cast)
                .filter(p -> p.getSound().value().location().getNamespace().equals("destiny")
                        && p.getSound().value().location().getPath().startsWith("weapon.")
                        && (p.getSound().value().location().getPath().endsWith(".fire")
                            || p.getSound().value().location().getPath().endsWith(".honed_fire"))
                        && p.getX() == origin.getX() && p.getY() == origin.getY() && p.getZ() == origin.getZ())
                .toList();
    }

    private static ClientboundSoundPacket origin(ServerPlayer p, String key) {
        // Only the expected quantized origin comes from this packet factory; observed packets
        // must come from real paid Runtime dispatch and W92's complete native PLAY pipeline.
        return DestinySounds.packet(key, p.getEyePosition(), SoundSource.PLAYERS, .8f, 0L);
    }

    private static ClientboundSoundPacket one(GameTestHelper h, List<ClientboundSoundPacket> packets,
                                             String key) {
        check(h, packets.size() == 1, "Exactly one source fire packet, not named plus family/variant: " + key);
        var packet = packets.getFirst();
        check(h, packet.getSound().kind() == Holder.Kind.DIRECT
                        && packet.getSound().value().location().toString().equals("destiny:" + key)
                        && packet.getSource() == SoundSource.PLAYERS
                        && packet.getVolume() == .8f && packet.getPitch() == 1f
                        && packet.getSound().value().fixedRange().equals(java.util.Optional.of(32f)),
                "Client-decoded inline exact event/source/volume/pitch/fixed32 range: " + key);
        return packet;
    }

    private static void paid(GameTestHelper h, ServerPlayer p, ItemStack gun, int before) {
        check(h, WeaponRuntime.beginUse(p), "Production beginUse accepts a real paid emission");
        WeaponRuntime.releaseUse(p, gun); // No held-auto session can conceal a refused new press.
        state(h, gun, before - 1);
        check(h, !WeaponRuntime.reloading(p), "Loaded ammunition remains; no reload masks cadence");
    }

    @GameTest(structure = "destiny-test:w78_floor", environment = "destiny-test:w90_isolated", maxTicks = 40)
    public void paidNamedShotsEmitOneInlineEventAndRespectCadence(GameTestHelper h) {
        deck(h);
        int[] finished = {0};
        for (int i = 0; i < NAMED.size(); i++) {
            String id = NAMED.get(i), key = "weapon." + id + ".fire";
            var w = wire(h, new Vec3(6, 4, 8 + i * 8), true);
            var gun = equip(h, w, id);
            var expected = origin(w.player, key);
            var profile = WeaponProfile.forEntry(WeaponItems.entry(gun).orElseThrow());
            int boundary = (int) Math.ceil(profile.cadenceTicks());
            check(h, boundary >= 2 && boundary < 30, "Bounded nonzero recovery for " + id);
            long acceptedAt = h.getLevel().getServer().getTickCount();
            paid(h, w.player, gun, 3);
            one(h, firePackets(w, expected), key);
            check(h, !WeaponRuntime.beginUse(w.player), "Released same-tick retry is refused: " + id);
            state(h, gun, 2);
            check(h, firePackets(w, expected).isEmpty(), "Refused same-tick input is silent: " + id);
            h.runAfterDelay(boundary - 1, () -> {
                check(h, h.getLevel().getServer().getTickCount() - acceptedAt == boundary - 1,
                        "Measure actual server tick immediately before first cadence boundary");
                check(h, !WeaponRuntime.beginUse(w.player), "No emission before exact cadence: " + id);
                state(h, gun, 2);
                check(h, firePackets(w, expected).isEmpty(), "No deferred/rejected-input fire event: " + id);
            });
            h.runAfterDelay(boundary, () -> {
                check(h, h.getLevel().getServer().getTickCount() - acceptedAt == boundary,
                        "Measure actual server tick at first integer cadence boundary");
                // Do not discard the preceding window: a latent extra emission must fail count1.
                state(h, gun, 2);
                paid(h, w.player, gun, 2);
                one(h, firePackets(w, expected), key);
                check(h, !WeaponRuntime.beginUse(w.player), "Second released same-tick retry is refused");
                state(h, gun, 1);
                check(h, firePackets(w, expected).isEmpty(), "No duplicated source fire after second payment");
                if (++finished[0] == NAMED.size()) h.succeed();
            });
        }
    }

    @GameTest(structure = "destiny-test:w78_floor", environment = "destiny-test:w90_isolated", maxTicks = 20)
    public void paidShotRangeKeepsNamedAndFamilyEventsIsolated(GameTestHelper h) {
        deck(h);
        var near = wire(h, new Vec3(8, 4, 16), true);
        var edge = wire(h, new Vec3(38, 4, 16), true);
        var far = wire(h, new Vec3(38.25, 4, 16), true);
        // A same-family non-overridden catalog entry must retain its ordinary family event.
        check(h, !DestinySounds.has("weapon.austringer.fire"), "Austringer exercises real family fallback");
        for (String id : List.of("seventh_seraph_officer_revolver", "austringer")) {
            var shooter = wire(h, new Vec3(6, 4, 16), false);
            var gun = equip(h, shooter, id);
            check(h, WeaponItems.entry(gun).orElseThrow().family().equals("hand_cannon"),
                    "Both positive and fallback controls share the hand-cannon family");
            String key = id.equals("austringer") ? "weapon.hand_cannon.fire" : "weapon." + id + ".fire";
            var source = shooter.player.getEyePosition();
            near.player.setPos(source.add(2, 0, 0));
            edge.player.setPos(source.add(32, 0, 0));
            far.player.setPos(source.add(32.25, 0, 0));
            for (var w : List.of(near, edge, far)) bounded(h, w.player);
            check(h, edge.player.position().distanceToSqr(source) == 32 * 32
                            && far.player.position().distanceToSqr(source) > 32 * 32,
                    "Actual listener feet, not eye-height-offset approximations, bracket radius32");
            check(h, h.getLevel().players().contains(near.player)
                            && h.getLevel().players().contains(edge.player)
                            && h.getLevel().players().contains(far.player),
                    "All measured listeners participate in actual production level dispatch");
            var expected = origin(shooter.player, key);
            paid(h, shooter.player, gun, 3);
            var insidePacket = one(h, firePackets(near, expected), key);
            var boundaryPacket = one(h, firePackets(edge, expected), key);
            check(h, insidePacket.getSeed() == boundaryPacket.getSeed(),
                    "One accepted emission carries the same server seed to both actual recipients");
            check(h, firePackets(far, expected).isEmpty(), "Beyond32 receives no source event: " + key);
            check(h, !WeaponRuntime.beginUse(shooter.player), "Refused new press cannot bypass audience checks");
            state(h, gun, 2);
            for (var w : List.of(near, edge, far))
                check(h, firePackets(w, expected).isEmpty(), "Refused input reaches no measured listener");
        }
        h.succeed();
    }
}
