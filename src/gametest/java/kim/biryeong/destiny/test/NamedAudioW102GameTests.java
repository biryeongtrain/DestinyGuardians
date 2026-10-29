package kim.biryeong.destiny.test;

import kim.biryeong.destiny.sound.DestinySounds;
import kim.biryeong.destiny.weapon.*;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.core.Holder;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.Packet;
import net.minecraft.network.protocol.game.*;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.Display;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.gamerules.GameRules;
import net.minecraft.world.phys.Vec3;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;

/** Production payments -> W92 native framed PLAY bytes -> client-context decode.
 * No authenticated socket, audio playback/hearing, or pulse-sample identity claim.
 */
public final class NamedAudioW102GameTests {
    private static final String STRUCTURE = "destiny-test:w78_floor";
    private static final String ENVIRONMENT = "destiny-test:w90_isolated";
    private static final List<String> FULL = List.of("blast_furnace", "chattering_bone", "aishas_embrace", "retrofit_escapade");
    private static final Map<String, Integer> BASE_TICKS = Map.of(
            "blast_furnace", 43, "chattering_bone", 34, "aishas_embrace", 46, "retrofit_escapade", 90);

    private static void check(GameTestHelper h, boolean yes, String message) {
        h.assertTrue(yes, Component.literal(message));
    }

    private static void deck(GameTestHelper h) {
        check(h, !h.getLevel().getGameRules().get(GameRules.SPAWN_MOBS), "W90 isolation is active");
        for (int x = 0; x < 48; x++) for (int z = 0; z < 32; z++) h.setBlock(x, 3, z, Blocks.STONE);
    }

    private static InventoryWireW92 wire(GameTestHelper h, Vec3 relative, boolean receivesPositionalSounds) {
        var w = new InventoryWireW92(h, relative);
        TestCleanup.register(h, () -> {
            if (h.getLevel().players().contains(w.player))
                h.getLevel().removePlayerImmediately(w.player, Entity.RemovalReason.DISCARDED);
        });
        w.player.setAttached(WeaponLoadout.ENABLED, false);
        Runnable bounded = () -> {
            var origin = h.absoluteVec(Vec3.ZERO); var box = w.player.getBoundingBox();
            check(h, w.player.level() == h.getLevel()
                            && box.minX > origin.x && box.maxX < origin.x + 48
                            && box.minY > origin.y && box.maxY < origin.y + 12
                            && box.minZ > origin.z && box.maxZ < origin.z + 32,
                    "Entire owned actor AABB stays inside W90's 48x12x32 fixture");
        };
        bounded.run(); h.onEachTick(bounded);
        if (receivesPositionalSounds) h.getLevel().addNewPlayer(w.player);
        w.discard();
        return w;
    }

    private static ItemStack equip(InventoryWireW92 w, String id, int rounds, int reserve) {
        var entry = WeaponCatalog.find(id).orElseThrow();
        var gun = WeaponItems.create(entry);
        WeaponItems.save(gun, new WeaponMagazine(WeaponProfile.forEntry(entry), rounds, reserve));
        w.player.getInventory().setItem(0, gun); w.player.getInventory().setSelectedSlot(0);
        WeaponRuntime.tickPlayer(w.player); w.discard();
        return gun;
    }

    private static WeaponProfile profile(ItemStack gun) { return WeaponProfile.forEntry(WeaponItems.entry(gun).orElseThrow()); }
    private static WeaponMagazine ammo(ItemStack gun) { return WeaponItems.magazine(gun, profile(gun)); }
    private static long now(GameTestHelper h) { return h.getLevel().getServer().getTickCount(); }
    private static <T> List<T> packets(List<Packet<?>> queued, Class<T> type) {
        return queued.stream().filter(type::isInstance).map(type::cast).toList();
    }
    private static long removed(List<Packet<?>> queued, int id) {
        return packets(queued, ClientboundRemoveEntitiesPacket.class).stream().filter(p -> p.entityIds().contains(id)).count();
    }
    private static void noGlobalStop(GameTestHelper h, List<Packet<?>> queued) {
        check(h, packets(queued, ClientboundStopSoundPacket.class).isEmpty(), "No event-global stop can silence another owner");
    }
    private static void silentRefusal(GameTestHelper h, List<Packet<?>> queued) {
        check(h, packets(queued, ClientboundSoundEntityPacket.class).isEmpty()
                        && packets(queued, ClientboundSoundPacket.class).isEmpty()
                        && packets(queued, ClientboundAddEntityPacket.class).isEmpty()
                        && packets(queued, ClientboundRemoveEntitiesPacket.class).isEmpty(),
                "Refused action creates no audio, emitter, or retirement packet");
        noGlobalStop(h, queued);
    }

    private static void inline(GameTestHelper h, ClientboundSoundEntityPacket p, String key) {
        check(h, p.getSound().kind() == Holder.Kind.DIRECT
                        && p.getSound().value().location().toString().equals("destiny:" + key)
                        && p.getSound().value().fixedRange().equals(java.util.Optional.of(32f))
                        && p.getSource() == SoundSource.PLAYERS && p.getVolume() == .8f && p.getPitch() == 1f,
                "Native PLAY client decode preserves exact inline event, fixed32 range, player channel, volume and pitch");
    }

    private static ClientboundSoundEntityPacket started(GameTestHelper h, InventoryWireW92 w,
                                                         String id, int ticks, List<Packet<?>> queued) {
        var sounds = packets(queued, ClientboundSoundEntityPacket.class);
        check(h, sounds.size() == 1, "One timed sound for accepted " + id);
        var sound = sounds.getFirst(); inline(h, sound, "weapon.reload_w102." + id + "." + ticks);
        var spawns = packets(queued, ClientboundAddEntityPacket.class).stream().filter(p -> p.getId() == sound.getId()).toList();
        check(h, spawns.size() == 1 && spawns.getFirst().getType() == EntityTypes.ITEM_DISPLAY
                        && queued.indexOf(spawns.getFirst()) < queued.indexOf(sound), "Client-only item-display spawn precedes its sound");
        var spawn = spawns.getFirst();
        check(h, spawn.getId() != w.player.getId() && w.player.level().getEntity(spawn.getId()) == null
                        && new Vec3(spawn.getX(), spawn.getY(), spawn.getZ()).distanceToSqr(w.player.getEyePosition()) < 1e-10,
                "Emitter is private, absent from the world, and starts at the owner's eye");
        var display = new Display.ItemDisplay(EntityTypes.ITEM_DISPLAY, w.player.level());
        for (var metadata : packets(queued, ClientboundSetEntityDataPacket.class))
            if (metadata.id() == sound.getId()) display.getEntityData().assignValues(metadata.packedItems());
        check(h, display.getItemStack().isEmpty(), "Default plus decoded metadata leaves emitter visually empty");
        check(h, packets(queued, ClientboundSoundPacket.class).isEmpty(), "Accepted timed reload adds no positional fallback");
        noGlobalStop(h, queued);
        return sound;
    }

    private record ReloadCase(InventoryWireW92 wire, ItemStack gun, String id, int ticks, int credit,
                              int loaded, int reserve, long total, long at, int emitter, List<Packet<?>> later) {}

    private static void collect(ReloadCase c) {
        WeaponRuntime.tickPlayer(c.wire.player); c.later.addAll(c.wire.capture());
    }

    @GameTest(structure = STRUCTURE, environment = ENVIRONMENT, maxTicks = 110)
    public void fourAcceptedFullMagazineReloadsKeepRealAmmoDeadlinesAndPrivateCancellation(GameTestHelper h) {
        deck(h);
        var listener = wire(h, new Vec3(10, 4, 16), true);
        var cases = new ArrayList<ReloadCase>();
        for (int i = 0; i < FULL.size(); i++) {
            String id = FULL.get(i);
            var w = wire(h, new Vec3(6, 4, 6 + i * 5), false);
            var entry = WeaponCatalog.find(id).orElseThrow(); var p = WeaponProfile.forEntry(entry);
            int ticks = BASE_TICKS.get(id), credit = id.equals("retrofit_escapade") ? 59 : ticks;
            check(h, !p.shellReload() && p.firstReloadTicks() == ticks, "Independent full-magazine base deadline: " + id);
            var plan = new WeaponReloadPolicy.Plan(ticks, p.reloadTicks(), 0);
            check(h, ReloadCreditProfile.ammoTicks(entry, plan) == credit, "Existing W65 credit remains distinct from audio recovery");
            var gun = equip(w, id, p.magazine() - 3, p.infiniteReserve() ? 0 : 7);
            var before = ammo(gun); listener.discard(); long at = now(h);
            check(h, WeaponRuntime.reload(w.player), "Production reload accepts " + id);
            var sound = started(h, w, id, ticks, w.capture());
            var heard = listener.capture(); var heardSound = packets(heard, ClientboundSoundEntityPacket.class);
            check(h, heardSound.size() == 1 && heardSound.getFirst().getId() == sound.getId()
                            && heardSound.getFirst().getSeed() == sound.getSeed(), "One accepted event reaches nearby recipient with same emitter/seed");
            inline(h, heardSound.getFirst(), "weapon.reload_w102." + id + "." + ticks);
            var c = new ReloadCase(w, gun, id, ticks, credit, before.rounds(), before.reserve(), before.total(), at,
                    sound.getId(), new ArrayList<>()); cases.add(c);
            check(h, ammo(gun).rounds() == c.loaded && ammo(gun).reserve() == c.reserve && WeaponRuntime.reloading(w.player),
                    "Audio start neither credits nor spends ammo");
            check(h, WeaponRuntime.ammunition(w.player).orElseThrow().reloadDuration() == ticks, "Runtime exposes actual unchanged duration");
            check(h, !WeaponRuntime.reload(w.player), "Duplicate live reload is refused");
            silentRefusal(h, w.capture()); silentRefusal(h, listener.capture());
            h.onEachTick(() -> collect(c));
            h.runAfterDelay(credit - 1, () -> {
                collect(c);
                check(h, now(h) - c.at == credit - 1 && ammo(gun).rounds() == c.loaded
                                && ammo(gun).reserve() == c.reserve && ammo(gun).overflow() == 0
                                && WeaponRuntime.reloading(w.player) && removed(c.later, c.emitter) == 0,
                        "Immediately before actual credit, ammo and emitter are unchanged: " + id);
            });
            h.runAfterDelay(credit, () -> {
                collect(c);
                check(h, now(h) - c.at == credit && ammo(gun).rounds() == p.magazine()
                                && ammo(gun).reserve() == c.reserve - (p.infiniteReserve() ? 0 : 3)
                                && ammo(gun).overflow() == 0
                                && (p.infiniteReserve() || ammo(gun).total() == c.total),
                        "Exact existing credit transfers only three missing rounds: " + id);
                if (credit < ticks) check(h, WeaponRuntime.reloading(w.player) && removed(c.later, c.emitter) == 0,
                        "Early paid ammo does not prematurely retire the 90-tick audio/recovery");
            });
            h.runAfterDelay(ticks - 1, () -> {
                collect(c);
                check(h, now(h) - c.at == ticks - 1 && WeaponRuntime.reloading(w.player)
                                && removed(c.later, c.emitter) == 0, "Emitter survives until the real recovery boundary: " + id);
            });
            h.runAfterDelay(ticks, () -> {
                collect(c);
                check(h, now(h) - c.at == ticks && !WeaponRuntime.reloading(w.player)
                                && removed(c.later, c.emitter) == 1, "Real recovery retires its emitter exactly once: " + id);
                check(h, packets(c.later, ClientboundSoundEntityPacket.class).isEmpty(), "No replay during ticks/completion");
                noGlobalStop(h, c.later);
            });
            // A separate initially full stack is a genuine refusal, without resetting live state.
            var full = wire(h, new Vec3(18, 4, 6 + i * 5), false);
            var fullGun = equip(full, id, p.magazine(), 0);
            check(h, !WeaponRuntime.reload(full.player) && ammo(fullGun).rounds() == p.magazine(), "Full magazine refusal: " + id);
            silentRefusal(h, full.capture()); silentRefusal(h, listener.capture());
        }
        var empty = wire(h, new Vec3(22, 4, 25), false);
        var emptyGun = equip(empty, "retrofit_escapade", 0, 0);
        check(h, !WeaponRuntime.reload(empty.player) && ammo(emptyGun).total() == 0, "No finite reserve means no accepted reload/audio");
        silentRefusal(h, empty.capture()); silentRefusal(h, listener.capture());

        // Same event/deadline as the first positive owner: only this owner's emitter may stop.
        var cancelled = wire(h, new Vec3(6, 4, 28), false);
        var cancelledGun = equip(cancelled, "blast_furnace", 5, 0);
        check(h, WeaponRuntime.reload(cancelled.player), "Second owner accepts same-key reload");
        var peer = started(h, cancelled, "blast_furnace", 43, cancelled.capture());
        listener.capture();
        check(h, peer.getId() != cases.getFirst().emitter, "Same-key sessions own distinct emitter IDs");
        WeaponRuntime.cancelUseForSkill(cancelled.player);
        var cancelledPackets = cancelled.capture(); var audience = listener.capture();
        check(h, removed(cancelledPackets, peer.getId()) == 1 && removed(audience, peer.getId()) == 1
                        && removed(audience, cases.getFirst().emitter) == 0 && WeaponRuntime.reloading(cases.getFirst().wire.player),
                "Skill cancellation retires only cancelled owner's emitter, including nearby recipient");
        noGlobalStop(h, cancelledPackets); noGlobalStop(h, audience);
        check(h, ammo(cancelledGun).rounds() == 5 && !WeaponRuntime.reloading(cancelled.player), "Cancellation before credit grants no ammo");

        // Long Arm must retain the actual two-cartridge incremental fallback, never full-source audio.
        var incremental = wire(h, new Vec3(26, 4, 16), false);
        var longArm = equip(incremental, "long_arm", 0, 0);
        check(h, profile(longArm).shellReload() && profile(longArm).roundsPerInsert() == 2
                        && WeaponRuntime.reload(incremental.player), "Canonical Long Arm accepts its real incremental reload");
        check(h, packets(incremental.capture(), ClientboundSoundEntityPacket.class).isEmpty(), "Long Arm creates no timed emitter sound");
        var fallback = listener.capture();
        var positional = packets(fallback, ClientboundSoundPacket.class);
        check(h, positional.size() == 1 && positional.getFirst().getSound().value().location().toString().equals("destiny:weapon.scout_rifle.reload")
                        && packets(fallback, ClientboundSoundEntityPacket.class).isEmpty()
                        && packets(fallback, ClientboundAddEntityPacket.class).isEmpty(), "Existing scout positional fallback remains incremental");
        h.runAfterDelay(20, () -> {
            WeaponRuntime.tickPlayer(incremental.player);
            check(h, ammo(longArm).rounds() == 2 && WeaponRuntime.reloading(incremental.player), "First Long Arm phase pays exactly two rounds at 20 ticks");
        });
        h.runAfterDelay(33, () -> {
            WeaponRuntime.tickPlayer(incremental.player);
            check(h, ammo(longArm).rounds() == 4 && WeaponRuntime.reloading(incremental.player), "Second Long Arm phase pays two more at 33 ticks");
            WeaponRuntime.cancelUseForSkill(incremental.player);
        });
        h.runAfterDelay(92, () -> {
            WeaponRuntime.tickPlayer(cancelled.player);
            check(h, ammo(cancelledGun).rounds() == 5 && !WeaponRuntime.reloading(cancelled.player), "No latent completion resurrects cancelled reload");
            silentRefusal(h, cancelled.capture());
            for (var c : cases) {
                collect(c);
                check(h, removed(c.later, c.emitter) == 1, "Repeated completion ticks do not retire emitter twice");
                noGlobalStop(h, c.later);
            }
            h.succeed();
        });
    }

    private static List<ClientboundSoundPacket> firePackets(List<Packet<?>> queued, ClientboundSoundPacket origin) {
        return packets(queued, ClientboundSoundPacket.class).stream().filter(p ->
                p.getSound().value().location().getNamespace().equals("destiny")
                        && p.getSound().value().location().getPath().startsWith("weapon.")
                        && p.getSound().value().location().getPath().endsWith(".fire")
                        && p.getX() == origin.getX() && p.getY() == origin.getY() && p.getZ() == origin.getZ()).toList();
    }
    private static void oneFire(GameTestHelper h, List<ClientboundSoundPacket> sounds, String id) {
        check(h, sounds.size() == 1, "One source fire event for paid trigger, without family duplicate: " + id);
        var p = sounds.getFirst();
        check(h, p.getSound().kind() == Holder.Kind.DIRECT
                        && p.getSound().value().location().toString().equals("destiny:weapon." + id + ".fire")
                        && p.getSource() == SoundSource.PLAYERS && p.getVolume() == .8f && p.getPitch() == 1f
                        && p.getSound().value().fixedRange().equals(java.util.Optional.of(32f)), "Client-decoded named fire identity and unshifted inline parameters");
    }

    @GameTest(structure = STRUCTURE, environment = ENVIRONMENT, maxTicks = 35)
    public void sixPaidNamedFireEventsPreservePulseFollowupPaymentsAndRealBowDrawRelease(GameTestHelper h) {
        deck(h);
        var ids = List.of("blast_furnace", "chattering_bone", "aishas_embrace", "long_arm", "retrofit_escapade", "whispering_slab");
        var observations = new ArrayList<List<ClientboundSoundPacket>>();
        for (int i = 0; i < ids.size(); i++) {
            String id = ids.get(i); boolean bow = id.equals("whispering_slab");
            var w = wire(h, new Vec3(6, 4, 5 + i * 4), true);
            var entry = WeaponCatalog.find(id).orElseThrow(); var p = WeaponProfile.forEntry(entry);
            int initial = bow ? 1 : p.burst() + 2;
            var gun = equip(w, id, initial, 0);
            var origin = DestinySounds.packet("weapon." + id + ".fire", w.player.getEyePosition(), SoundSource.PLAYERS, .8f, 0);
            var observed = new ArrayList<ClientboundSoundPacket>(); observations.add(observed);
            long at = now(h);
            if (bow) {
                WeaponCombatItem.INSTANCE.use(h.getLevel(), w.player, InteractionHand.MAIN_HAND);
                check(h, w.player.isUsingItem() && w.player.getUseItem() == gun,
                        "Production item use owns a real native draw session, maintained through tickPlayer");
                check(h, p.chargeTicks() == 12 && p.mode() == WeaponProfile.Mode.PROJECTILE, "Whispering Slab retains its real 12-tick bow draw");
                check(h, ammo(gun).rounds() == 1 && firePackets(w.capture(), origin).isEmpty(), "Draw start is unpaid and emits no fake instant fire");
                h.onEachTick(() -> {
                    WeaponRuntime.tickPlayer(w.player); observed.addAll(firePackets(w.capture(), origin));
                });
                h.runAfterDelay(11, () -> {
                    WeaponRuntime.tickPlayer(w.player); observed.addAll(firePackets(w.capture(), origin));
                    check(h, now(h) - at == 11 && ammo(gun).rounds() == 1 && observed.isEmpty(), "Held bow remains unpaid/silent immediately before full draw");
                });
                h.runAfterDelay(12, () -> {
                    check(h, now(h) - at == 12 && ammo(gun).rounds() == 1 && observed.isEmpty(), "Actual full draw elapsed before release");
                    w.player.releaseUsingItem();
                    // Start the shot-caused nock on this exact release tick, independent of
                    // GameTest callback/END_SERVER_TICK order. This is production tick work.
                    WeaponRuntime.tickPlayer(w.player);
                    var released = w.capture(); observed.addAll(firePackets(released, origin));
                    check(h, ammo(gun).rounds() == 0 && ammo(gun).reserve() == 0, "Real bow release pays exactly its arrow");
                    check(h, !w.player.isUsingItem() && WeaponRuntime.reloading(w.player)
                                    && WeaponRuntime.ammunition(w.player).orElseThrow().reloadRemaining() == 14,
                            "Released input starts its actual 14-tick nock at release, without a buffered next draw");
                    check(h, packets(released, ClientboundSoundEntityPacket.class).isEmpty(), "Bow release/nock starts no timed reload sound");
                    oneFire(h, observed, id);
                });
                h.runAfterDelay(14, () -> {
                    WeaponRuntime.tickPlayer(w.player); var nock = w.capture(); observed.addAll(firePackets(nock, origin));
                    check(h, WeaponRuntime.reloading(w.player) && ammo(gun).rounds() == 0, "Shot-caused nock remains a real later phase");
                    check(h, packets(nock, ClientboundSoundEntityPacket.class).isEmpty(), "Bow nock never starts full-source timed reload audio");
                    oneFire(h, observed, id);
                });
                h.runAfterDelay(25, () -> {
                    WeaponRuntime.tickPlayer(w.player); observed.addAll(firePackets(w.capture(), origin));
                    check(h, now(h) - at == 25 && ammo(gun).rounds() == 0 && WeaponRuntime.reloading(w.player),
                            "No free arrow one tick before real nock completion");
                    oneFire(h, observed, id);
                });
                h.runAfterDelay(26, () -> {
                    WeaponRuntime.tickPlayer(w.player); var finished = w.capture(); observed.addAll(firePackets(finished, origin));
                    check(h, now(h) - at == 26 && ammo(gun).rounds() == 1 && ammo(gun).reserve() == 0
                                    && !WeaponRuntime.reloading(w.player) && !w.player.isUsingItem(),
                            "Original nock deadline restores one arrow without another trigger/draw");
                    check(h, packets(finished, ClientboundSoundEntityPacket.class).isEmpty(), "Nock completion starts no full reload audio");
                    oneFire(h, observed, id);
                });
                continue;
            }
            check(h, WeaponRuntime.beginUse(w.player), "Production beginUse accepts " + id);
            WeaponRuntime.releaseUse(w.player, gun);
            observed.addAll(firePackets(w.capture(), origin)); oneFire(h, observed, id);
            check(h, ammo(gun).rounds() == initial - 1 && ammo(gun).reserve() == 0 && ammo(gun).overflow() == 0,
                    "Initial actual emission pays one cartridge: " + id);
            check(h, !WeaponRuntime.beginUse(w.player), "Released same-tick retry is refused: " + id);
            check(h, firePackets(w.capture(), origin).isEmpty() && ammo(gun).rounds() == initial - 1, "Refused retry cannot emit or spend");
            h.onEachTick(() -> {
                WeaponRuntime.tickPlayer(w.player); observed.addAll(firePackets(w.capture(), origin));
            });
            if (entry.family().equals("pulse_rifle")) {
                int burst = id.equals("blast_furnace") ? 4 : 3;
                check(h, p.burst() == burst && !p.sharedBurstAmmo()
                                && Math.abs(p.burstSpacingTicks() - 4.0 / 3) < 1e-9,
                        "Pulse retains independent original burst size and per-bullet payment");
                for (int t = 1; t <= 4; t++) {
                    int elapsed = t;
                    h.runAfterDelay(elapsed, () -> {
                        WeaponRuntime.tickPlayer(w.player); observed.addAll(firePackets(w.capture(), origin));
                        int paid = 1 + Math.min(burst - 1, (int) Math.floor((elapsed + 1e-7) / (4.0 / 3)));
                        check(h, now(h) - at == elapsed && ammo(gun).rounds() == initial - paid
                                        && ammo(gun).reserve() == 0 && ammo(gun).overflow() == 0,
                                "Actual delayed pulse bullets pay at original fractional-spacing deadlines: " + id + " tick " + elapsed);
                        oneFire(h, observed, id);
                    });
                }
            } else {
                h.runAfterDelay(4, () -> {
                    WeaponRuntime.tickPlayer(w.player); observed.addAll(firePackets(w.capture(), origin));
                    check(h, ammo(gun).rounds() == initial - 1, "Released scout/MG does not auto-emit extra triggers: " + id);
                    oneFire(h, observed, id);
                });
            }
        }
        h.runAfterDelay(28, () -> {
            for (int i = 0; i < ids.size(); i++) oneFire(h, observations.get(i), ids.get(i));
            h.succeed();
        });
    }
}
