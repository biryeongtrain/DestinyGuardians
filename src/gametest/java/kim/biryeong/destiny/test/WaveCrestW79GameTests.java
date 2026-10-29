package kim.biryeong.destiny.test;

import io.netty.channel.embedded.EmbeddedChannel;
import kim.biryeong.destiny.combat.Combat;
import kim.biryeong.destiny.fx.WaveCrestVfx;
import kim.biryeong.destiny.guardian.Element;
import kim.biryeong.destiny.hud.CombatHud;
import kim.biryeong.destiny.weapon.*;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.Connection;
import net.minecraft.network.RegistryFriendlyByteBuf;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.BundlePacket;
import net.minecraft.network.protocol.Packet;
import net.minecraft.network.protocol.PacketFlow;
import net.minecraft.network.protocol.game.ClientboundAddEntityPacket;
import net.minecraft.network.protocol.game.ClientboundRemoveEntitiesPacket;
import net.minecraft.network.protocol.game.GameProtocols;
import net.minecraft.network.protocol.game.ServerboundPlayerLoadedPacket;
import net.minecraft.server.network.CommonListenerCookie;
import net.minecraft.server.network.ServerGamePacketListenerImpl;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.monster.zombie.Husk;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.level.GameType;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.UUID;
import java.util.stream.StreamSupport;

/** Paid-shot cases use production beginUse/releaseUse and real END_SERVER_TICK progression.
 * Direct VFX cases are explicitly named focusedVfx: they do not claim paid-shot coverage.
 * W78's private raised-floor fixture is copied here; no inherited tests or entrypoints are edited.
 * Display-required cases reuse an existing empty environment to separate the default W78 batch.
 * No global clears, reflection, synthetic server clocks, or manual projectile advancement.
 */
public final class WaveCrestW79GameTests {
    private static final String FLOOR = "destiny-test:w78_floor";
    // This existing empty all_of environment separates these cases from default W78 tests.
    // The concurrently running paid display cases below reserve at most 102 elements in total.
    private static final String VISUAL_ENV = "destiny-test:w90_w77_global";
    private static final String WHISPER = "deafening_whisper";
    private static final String HYPO = "dimensional_hypotrochoid";
    private static final float HP = 1000, EPS = .004f;
    // x=3, eye height ~1.62, downward 35 degrees: ballistic floor contact is near x=5.3.
    // All positive wave witnesses start after x=7: none intercepts the initial grenade.
    private static final double IMPACT_X = 5.3;

    private static void check(GameTestHelper h, boolean ok, String message) {
        h.assertTrue(ok, Component.literal(message));
    }

    private static void hp(GameTestHelper h, LivingEntity target, float expected, String message) {
        check(h, Math.abs(target.getHealth() - expected) < EPS,
                message + ": expected HP " + expected + ", got " + target.getHealth());
    }

    private static void bounded(GameTestHelper h, LivingEntity entity) {
        var origin = h.absoluteVec(Vec3.ZERO);
        var b = entity.getBoundingBox();
        check(h, b.minX > origin.x && b.maxX < origin.x + 48
                        && b.minY > origin.y && b.maxY < origin.y + 12
                        && b.minZ > origin.z && b.maxZ < origin.z + 32,
                "Whole W79 entity AABB remains strictly inside the dedicated 48x12x32 structure");
    }

    private static WeaponProfile profile(ItemStack stack) {
        return WeaponProfile.forEntry(WeaponItems.entry(stack).orElseThrow());
    }

    private static WeaponMagazine ammo(ItemStack stack) {
        return WeaponItems.magazine(stack, profile(stack));
    }

    private static void deck(GameTestHelper h) {
        // The structure supplies the full 48x12x32 test bounds. Materialize the raised
        // gameplay deck explicitly before any wall/slab/gap edits, independent of SNBT conversion.
        // No players or mobs exist yet, so an assertion here cannot leak an entity fixture.
        for (int x = 0; x < 48; x++) for (int z = 0; z < 32; z++) {
            h.setBlock(x, 3, z, Blocks.STONE);
            var position = h.absolutePos(new BlockPos(x, 3, z));
            var state = h.getLevel().getBlockState(position);
            check(h, state.is(Blocks.STONE),
                    "Explicit W79 deck setup must place stone at local (" + x + ",3," + z
                            + "); actual=" + state + ", absolute=" + position);
        }
    }

    private static ServerPlayer player(GameTestHelper h, double z) {
        deck(h);
        var p = TestPlayers.hunter(h, Element.VOID, new Vec3(3, 4, z), -90, 35,
                "W79_" + UUID.randomUUID().toString().substring(0, 8));
        TestCleanup.register(h, () -> {
            // These embedded players are intentionally not world/player-list registered.
            p.setServerLevel(h.getLevel());
            WeaponRuntime.cleanup(p);
            CombatHud.remove(p);
            TestPlayers.remove(p);
        });
        p.setAttached(WeaponLoadout.ENABLED, true);
        p.setOnGround(true);
        bounded(h, p);
        h.onEachTick(() -> bounded(h, p));
        return p;
    }

    private static ItemStack equip(GameTestHelper h, ServerPlayer p, String id, int rounds, int reserve) {
        var entry = WeaponCatalog.find(id).orElseThrow();
        var f = WeaponProfile.forEntry(entry);
        check(h, f.mode() == WeaponProfile.Mode.PROJECTILE && f.chargeTicks() == 0
                        && f.burst() == 1 && f.pellets() == 1 && !f.infiniteReserve(),
                id + " is an immediate finite-ammunition projectile fixture");
        var stack = WeaponItems.create(entry);
        WeaponItems.save(stack, new WeaponMagazine(f, rounds < 0 ? f.magazine() : rounds, reserve));
        int slot = WeaponCharacteristics.of(entry).slot().hotbar();
        p.getInventory().setItem(slot, stack);
        p.getInventory().setSelectedSlot(slot);
        kim.biryeong.destiny.weapon.WeaponAccuracy.setAirborneBonus(stack, 100);
        WeaponRuntime.tickPlayer(p); // Bind once; projectile progression only uses the real server event.
        TestPlayers.drain(p);
        return stack;
    }

    private static Husk target(GameTestHelper h, double x, double y, double z) {
        var target = h.spawn(EntityTypes.HUSK, new Vec3(x, y, z));
        TestCleanup.register(h, target::discard);
        target.setNoAi(true);
        target.setNoGravity(true);
        target.setPersistenceRequired();
        target.getAttribute(Attributes.MAX_HEALTH).setBaseValue(HP);
        target.getAttribute(Attributes.ARMOR).setBaseValue(0);
        target.getAttribute(Attributes.KNOCKBACK_RESISTANCE).setBaseValue(1);
        target.setHealth(HP);
        bounded(h, target);
        h.onEachTick(() -> bounded(h, target));
        return target;
    }

    /** W241 exact-impact fixture: earn ADS on real ticks, with explicit per-stack AE.
     * No RNG replacement, production tuning change, or synthetic server clock. */
    private static void exactAim(GameTestHelper h, java.util.List<ServerPlayer> owners, Runnable action) {
        for (var p : owners) {
            var gun = p.getMainHandItem();
            check(h, kim.biryeong.destiny.weapon.WeaponAccuracy.airborne(WeaponItems.entry(gun).orElseThrow(), gun) == 100, "Fixture explicitly equips AE100");
            WeaponRuntime.tickPlayer(p);
            if (!WeaponAiming.requested(p)) check(h, WeaponAiming.toggle(p), "Real ADS toggle accepted");
        }
        // GameTestInfo executes sequences after iterating its fastutil callback map.
        // The final action may register follow-up deadlines, so it must run here.
        var sequence = h.startSequence();
        for (int tick = 1; tick <= 40; tick++) {
            final int age = tick;
            sequence.thenExecuteAfter(1, () -> {
                for (var p : owners) {
                    WeaponRuntime.tickPlayer(p);
                    // Initial handling can consume ADS. A later actual click earns it after ready.
                    if (!WeaponAiming.requested(p) && age % 4 == 0) WeaponAiming.toggle(p);
                }
                if (age == 40) {
                    for (var p : owners) check(h, WeaponAiming.progress(p) == 1
                                    && WeaponAiming.coneDegrees(p) == 0,
                            "Fully earned ADS and AE100 give an exact ray before any paid shot");
                    action.run();
                }
            });
        }
    }

    private static void shot(GameTestHelper h, ServerPlayer p) {
        var stack = p.getMainHandItem();
        int rounds = ammo(stack).rounds(), reserve = ammo(stack).reserve();
        p.setYRot(-90); p.setYHeadRot(-90); p.setXRot(35);
        WeaponAiming.tick(p);
        floorPath(h, p);
        check(h, WeaponRuntime.beginUse(p), "Production beginUse accepts the real paid grenade shot");
        check(h, ammo(stack).rounds() == rounds - 1 && ammo(stack).reserve() == reserve,
                "Acceptance spends exactly one loaded round and no reserve before automatic reload");
        WeaponRuntime.releaseUse(p, stack);
        check(h, WeaponRuntime.activeProjectiles(p) == 1,
                "Accepted shot has one owned in-flight projectile before any real server tick");
    }

    /** Independent fixture preflight only: it never creates/advances a runtime projectile.
     * Check the actual world collision shapes and hostile boxes along each free-flight segment.
     */
    private static void floorPath(GameTestHelper h, ServerPlayer p) {
        var f = profile(p.getMainHandItem());
        var from = p.getEyePosition();
        var initialEye = from;
        var origin = h.absoluteVec(Vec3.ZERO);
        var velocity = p.getLookAngle().normalize().scale(f.speed());
        for (int tick = 0; tick < 8; tick++) {
            var to = from.add(velocity);
            var block = h.getLevel().clip(new ClipContext(from, to,
                    ClipContext.Block.COLLIDER, ClipContext.Fluid.NONE, p));
            var end = block.getType() == HitResult.Type.MISS ? to : block.getLocation();
            for (var target : h.getLevel().getEntitiesOfClass(LivingEntity.class,
                    new AABB(from, end).inflate(.3), e -> Combat.isEnemy(p, e) && !p.isAlliedTo(e))) {
                var box = target.getBoundingBox().inflate(.08);
                check(h, !box.contains(from) && box.clip(from, end).isEmpty(),
                        "No hostile witness intercepts the initial paid ballistic flight to the floor");
            }
            if (block.getType() == HitResult.Type.BLOCK) {
                var local = block.getLocation().subtract(origin);
                check(h, block.getDirection() == Direction.UP
                                && local.x > 5 && local.x < 5.6 && Math.abs(local.y - 4) < .001,
                        "First ballistic collider is the explicit deck's upper face near x=5.3, y=4"
                                + "; flightTick=" + tick + ", local=" + local
                                + ", from=" + from + ", fromLocal=" + from.subtract(origin)
                                + ", velocity=" + velocity + ", toLocal=" + to.subtract(origin)
                                + ", face=" + block.getDirection() + ", inside=" + block.isInside()
                                + ", hitBlock=" + block.getBlockPos()
                                + ", hitState=" + h.getLevel().getBlockState(block.getBlockPos())
                                + ", origin=" + origin + ", playerLocal=" + p.position().subtract(origin)
                                + ", initialEyeLocal=" + initialEye.subtract(origin)
                                + ", eyeHeight=" + p.getEyeHeight() + ", pose=" + p.getPose()
                                + ", yaw=" + p.getYRot() + ", pitch=" + p.getXRot());
                return;
            }
            from = to;
            velocity = velocity.add(0, -f.gravity(), 0);
        }
        check(h, false, "Bounded downward fixture must reach the floor within eight free-flight ticks");
    }

    private record Fixture(GameTestHelper h, ServerPlayer owner, ItemStack gun,
                           WaveFrameProfile.Profile wave, double z) {
        int finish() { return (int) Math.ceil(wave.length() / wave.speed()) + 16; }
        float damage() { return profile(gun).damage() * wave.waveMultiplier(); }
        Husk target(double x, double y) { return WaveCrestW79GameTests.target(h, x, y, z); }
        void hitOnce(LivingEntity target, String message) { hp(h, target, HP - damage(), message); }
    }

    private static Fixture fixture(GameTestHelper h, String id, double z) {
        var p = player(h, z);
        var gun = equip(h, p, id, -1, 3);
        var wave = WaveFrameProfile.of(WeaponItems.entry(gun).orElseThrow()).orElseThrow();
        check(h, wave.length() > 6 && IMPACT_X + wave.length() < 47
                        && z - wave.width() / 2 > 1 && z + wave.width() / 2 < 31,
                "Complete wave travel and width fit strictly inside the bounded floor");
        return new Fixture(h, p, gun, wave, z);
    }


    private static List<WaveCrestVfx.Snapshot> owned(ServerPlayer owner) {
        return WaveCrestVfx.snapshots().stream().filter(s -> s.owner().equals(owner.getUUID())).toList();
    }

    private static WaveCrestVfx.Snapshot one(GameTestHelper h, ServerPlayer owner, int elements) {
        var snapshots = owned(owner);
        check(h, snapshots.size() == 1, "Exactly one shot-owned crest holder: " + snapshots);
        var s = snapshots.getFirst();
        check(h, s.elements() == elements && s.positions().size() == elements
                        && WaveCrestVfx.activeElements(owner) == elements,
                "Exactly one display and observed live tip per live lane: " + s);
        return s;
    }

    private static void gone(GameTestHelper h, ServerPlayer owner) {
        check(h, owned(owner).isEmpty() && WaveCrestVfx.activeElements(owner) == 0,
                "Owner has no surviving crest holder or reserved elements");
    }

    private static void flatten(Packet<?> packet, List<Packet<?>> result) {
        if (packet instanceof BundlePacket<?> bundle) {
            for (var child : bundle.subPackets()) flatten(child, result);
        } else result.add(packet);
    }

    private static List<Packet<?>> outbound(ServerPlayer owner) {
        var result = new ArrayList<Packet<?>>();
        for (var packet : TestPlayers.outbound(owner)) flatten(packet, result);
        return result;
    }

    /** Observes only this fixture's owner, allowing unrelated sessions to exist concurrently. */
    private static final class CrestObservation {
        boolean seen, advanced, partial;
        double firstX = Double.NaN;
        final Set<Integer> itemDisplays = new HashSet<>();
        CrestObservation(Fixture f) {
            f.h.onEachTick(() -> {
                for (var packet : outbound(f.owner)) {
                    if (packet instanceof ClientboundAddEntityPacket add && add.getType() == EntityTypes.ITEM_DISPLAY)
                        itemDisplays.add(add.getId());
                }
                var snapshots = owned(f.owner);
                if (snapshots.isEmpty()) return;
                check(f.h, snapshots.size() == 1, "Only this paid shot's one holder belongs to its owner");
                var s = snapshots.getFirst();
                // Constructor reservations may not have tips until the first production update.
                if (s.positions().isEmpty()) return;
                int lanes = (int) Math.ceil(f.wave.width() / .5);
                check(f.h, s.elements() > 0 && s.elements() <= lanes && s.positions().size() == s.elements()
                                && WaveCrestVfx.activeElements(f.owner) == s.elements()
                                && s.stasis() == isStasis(f.gun),
                        "Snapshot describes this owner's live lanes and the correct Void/Stasis palette");
                check(f.h, s.viewers().contains(f.owner.getUUID()), "Nearby embedded owner watches its ground crest");
                check(f.h, WeaponRuntime.activeProjectiles(f.owner) == 1,
                        "Observed display belongs to a still-live paid projectile");
                var origin = f.h.absoluteVec(Vec3.ZERO);
                double x = s.positions().getFirst().x;
                for (var tip : s.positions()) {
                    double localZ = tip.z - origin.z;
                    double lane = (localZ - f.z + f.wave.width() / 2) / (f.wave.width() / lanes) - .5;
                    check(f.h, Double.isFinite(tip.x) && Double.isFinite(tip.y) && Double.isFinite(tip.z)
                                    && Math.abs(tip.x - x) < .001
                                    && tip.x > origin.x + 5 && tip.x <= origin.x + 5.6 + f.wave.length()
                                    && Math.abs(tip.y - origin.y - 4.04) < .001
                                    && lane >= -.001 && lane <= lanes - 1 + .001
                                    && Math.abs(lane - Math.rint(lane)) < .001,
                            "Each observation is a real supported lane tip, not an origin/trail/foreign-owner position: " + tip);
                }
                if (!seen) firstX = x;
                else if (x > firstX + .1) advanced = true;
                seen = true;
                partial |= s.elements() < lanes;
            });
        }
    }

    private static boolean isStasis(ItemStack gun) {
        return WeaponItems.entry(gun).orElseThrow().id().equals(HYPO);
    }

    private static void paidExpiry(GameTestHelper h, String id) {
        var f = fixture(h, id, 16);
        var far = f.target(IMPACT_X + f.wave.length() * .8, 4);
        var seen = new CrestObservation(f);
        exactAim(h, java.util.List.of(f.owner), () -> {
            shot(h, f.owner);
            h.runAfterDelay(f.finish(), () -> {
                check(h, seen.seen && seen.advanced && !seen.partial && !seen.itemDisplays.isEmpty(),
                        "Real paid ground wave creates item-display packets and advances every unobstructed lane");
                f.hitOnce(far, "Display integration preserves paid wave damage exactly once");
                gone(h, f.owner);
                check(h, WeaponRuntime.activeProjectiles(f.owner) == 0, "Natural expiry also releases the shot");
                h.succeed();
            });
        });
    }

    @GameTest(structure = FLOOR, environment = VISUAL_ENV, maxTicks = 205)
    public void voidPaidShotShowsLiveGroundCrestAndNaturalExpiryClosesIt(GameTestHelper h) { paidExpiry(h, WHISPER); }

    @GameTest(structure = FLOOR, environment = VISUAL_ENV, maxTicks = 205)
    public void stasisPaidShotShowsLiveGroundCrestAndNaturalExpiryClosesIt(GameTestHelper h) { paidExpiry(h, HYPO); }

    private static void barrier(GameTestHelper h, boolean gap, boolean partial) {
        var f = fixture(h, HYPO, 16);
        var before = f.target(7.3, 4);
        var safe = target(h, 11.5, 4, partial ? 17.75 : 16);
        var open = partial ? target(h, 11.5, 4, 14.25) : null;
        // Partial barrier removes the three lanes at z=17.25/17.75/18.25; seven remain alive.
        for (int z = partial ? 17 : 10; z <= 22; z++) {
            if (gap) for (int y = 0; y <= 3; y++) h.setBlock(9, y, z, Blocks.AIR);
            else for (int y = 4; y <= 9; y++) h.setBlock(9, y, z, Blocks.STONE);
        }
        var seen = new CrestObservation(f);
        final boolean[] stopped = {false};
        h.onEachTick(() -> {
            for (var s : owned(f.owner)) for (var tip : s.positions()) {
                var local = tip.subtract(h.absoluteVec(Vec3.ZERO));
                if (local.x >= 9) {
                    check(h, partial && local.z < 17,
                            "Stopped wall/gap lanes never leave displays on or beyond the obstruction");
                    stopped[0] = true;
                    one(h, f.owner, 7);
                }
            }
        });
        exactAim(h, java.util.List.of(f.owner), () -> {
            shot(h, f.owner);
            h.runAfterDelay(f.finish(), () -> {
                check(h, seen.seen && seen.advanced, "Barrier case observed the real paid ground display before stopping");
                f.hitOnce(before, "Wave damages near witness before obstruction");
                hp(h, safe, HP, "Blocked lanes preserve the far witness");
                if (partial) {
                    check(h, seen.partial && stopped[0], "Only blocked lanes close; seven supported lanes keep moving");
                    f.hitOnce(open, "Unblocked lanes keep their paid gameplay damage");
                }
                gone(h, f.owner);
                check(h, WeaponRuntime.activeProjectiles(f.owner) == 0, "Stopped or expired wave removes its shot");
                h.succeed();
            });
        });
    }

    @GameTest(structure = FLOOR, environment = VISUAL_ENV, maxTicks = 205)
    public void paidWallStopsAllLaneDisplays(GameTestHelper h) { barrier(h, false, false); }

    @GameTest(structure = FLOOR, environment = VISUAL_ENV, maxTicks = 205)
    public void paidGapStopsAllLaneDisplays(GameTestHelper h) { barrier(h, true, false); }

    @GameTest(structure = FLOOR, environment = VISUAL_ENV, maxTicks = 205)
    public void paidPartialWallClosesOnlyStoppedLaneDisplays(GameTestHelper h) { barrier(h, false, true); }

    @GameTest(structure = FLOOR, environment = VISUAL_ENV, maxTicks = 205)
    public void paidPartialGapClosesOnlyStoppedLaneDisplays(GameTestHelper h) { barrier(h, true, true); }

    private static void lateralBarrier(GameTestHelper h, boolean gap) {
        var f = fixture(h, HYPO, 16);
        for (int x = 4; x <= 22; x++) {
            if (gap) for (int y = 0; y <= 3; y++) h.setBlock(x, y, 17, Blocks.AIR);
            else for (int y = 4; y <= 9; y++) h.setBlock(x, y, 17, Blocks.STONE);
        }
        var reachable = target(h, 11, 4, 15.5);
        var shielded = target(h, 11, 4, 18.4);
        var seen = new CrestObservation(f);
        h.onEachTick(() -> {
            for (var s : owned(f.owner)) for (var tip : s.positions())
                check(h, tip.z < h.absoluteVec(Vec3.ZERO).z + 17,
                        "Parallel wall/gap cannot seed a visual on an unreachable outer lane");
        });
        exactAim(h, java.util.List.of(f.owner), () -> {
            shot(h, f.owner);
            h.runAfterDelay(f.finish(), () -> {
                check(h, seen.seen && seen.partial && seen.advanced, "Reachable subset has a real advancing paid crest");
                f.hitOnce(reachable, "Reachable side retains wave damage");
                hp(h, shielded, HP, "No damage across the parallel obstruction");
                gone(h, f.owner);
                h.succeed();
            });
        });
    }

    @GameTest(structure = FLOOR, environment = VISUAL_ENV, maxTicks = 205)
    public void paidParallelWallNeverShowsUnreachableLaneDisplays(GameTestHelper h) { lateralBarrier(h, false); }

    @GameTest(structure = FLOOR, environment = VISUAL_ENV, maxTicks = 205)
    public void paidParallelGapNeverShowsUnreachableLaneDisplays(GameTestHelper h) { lateralBarrier(h, true); }

    @GameTest(structure = FLOOR, environment = VISUAL_ENV, maxTicks = 205)
    public void paidCleanupClosesOnlyItsOwnersCrestAndCannotRevive(GameTestHelper h) {
        var a = fixture(h, WHISPER, 8);
        var b = fixture(h, HYPO, 24);
        var first = a.target(7.6, 4);
        var safe = a.target(IMPACT_X + a.wave.length() * .85, 4);
        var kept = b.target(IMPACT_X + b.wave.length() * .85, 4);
        var seenA = new CrestObservation(a);
        var seenB = new CrestObservation(b);
        final boolean[] cleaned = {false};
        h.onEachTick(() -> {
            if (cleaned[0] || first.getHealth() == HP) return;
            one(h, a.owner, 6); one(h, b.owner, 10);
            var before = owned(b.owner);
            WeaponRuntime.cleanup(a.owner); WeaponRuntime.cleanup(a.owner);
            gone(h, a.owner);
            check(h, owned(b.owner).equals(before) && WeaponRuntime.activeProjectiles(b.owner) == 1,
                    "Idempotent shot cleanup preserves the other owner's exact holder and tips");
            cleaned[0] = true;
        });
        exactAim(h, java.util.List.of(a.owner, b.owner), () -> {
            shot(h, a.owner); shot(h, b.owner);
            h.runAfterDelay(Math.max(a.finish(), b.finish()), () -> {
                check(h, cleaned[0] && seenA.seen && seenB.seen, "Cleanup occurred after both paid shots showed crests");
                hp(h, safe, HP, "Cleaned paid wave cannot resume at a later tick");
                b.hitOnce(kept, "Other owner's wave still reaches its far witness");
                gone(h, a.owner); gone(h, b.owner);
                h.succeed();
            });
        });
    }

    @GameTest(structure = FLOOR, environment = VISUAL_ENV, maxTicks = 205)
    public void paidLevelMismatchClosesShotAndCrestPermanently(GameTestHelper h) {
        var f = fixture(h, HYPO, 16);
        var first = f.target(7.6, 4);
        var far = f.target(IMPACT_X + f.wave.length() * .85, 4);
        var other = StreamSupport.stream(h.getLevel().getServer().getAllLevels().spliterator(), false)
                .filter(level -> level != h.getLevel()).findFirst().orElseThrow();
        var seen = new CrestObservation(f);
        final int[] changed = {-1};
        final boolean[] returned = {false};
        h.onEachTick(() -> {
            if (changed[0] < 0 && first.getHealth() < HP) {
                one(h, f.owner, 10);
                check(h, far.getHealth() == HP, "Level change occurs before the far witness is hit");
                f.owner.setServerLevel(other);
                changed[0] = h.getLevel().getServer().getTickCount();
            } else if (!returned[0] && changed[0] >= 0
                    && h.getLevel().getServer().getTickCount() >= changed[0] + 2) {
                gone(h, f.owner);
                check(h, WeaponRuntime.activeProjectiles(f.owner) == 0, "Real server tick discards mismatched shot");
                f.owner.setServerLevel(h.getLevel());
                returned[0] = true;
            }
        });
        exactAim(h, java.util.List.of(f.owner), () -> {
            shot(h, f.owner);
            h.runAfterDelay(f.finish(), () -> {
                check(h, seen.seen && returned[0], "Observed a real paid crest before persistent level mismatch");
                hp(h, far, HP, "Returning to the original level cannot revive shot or display");
                gone(h, f.owner);
                h.succeed();
            });
        });
    }

    /** Focused VFX owner; deliberately unregistered, and may move outside the paid-floor bounds. */
    private static ServerPlayer visualOwner(GameTestHelper h) {
        var p = TestPlayers.hunter(h, Element.VOID, new Vec3(3, 4, 16), -90, 0,
                "W79_" + UUID.randomUUID().toString().substring(0, 8));
        TestCleanup.register(h, () -> {
            p.setServerLevel(h.getLevel());
            WeaponRuntime.cleanup(p); CombatHud.remove(p); TestPlayers.remove(p);
        });
        return p;
    }

    private static WaveCrestVfx reserve(GameTestHelper h, ServerPlayer owner, int lanes) {
        var v = new WaveCrestVfx(owner, owner.position(), new Vec3(1, 0, 0), false, .5, lanes);
        TestCleanup.register(h, v::close);
        return v;
    }

    private static Vec3[] tips(ServerPlayer owner, int lanes) {
        var tips = new Vec3[lanes];
        for (int i = 0; i < lanes; i++) tips[i] = owner.position().add(1, 0, (i - lanes / 2.0) * .5);
        return tips;
    }

    @GameTest(structure = FLOOR, environment = VISUAL_ENV, maxTicks = 65)
    public void focusedVfxUpdatesDoNotMutateTipsAndClosedLanesNeverResurrect(GameTestHelper h) {
        var p = visualOwner(h);
        TestPlayers.drain(p);
        var v = reserve(h, p, 3);
        var tips = tips(p, 3);
        var before = tips.clone();
        v.update(tips, 0, 10);
        check(h, Arrays.equals(before, tips), "First update preserves the gameplay-owned tip array");
        check(h, one(h, p, 3).positions().equals(Arrays.asList(before)), "Snapshot copies exact live positions");
        var ids = outbound(p).stream().filter(packet -> packet instanceof ClientboundAddEntityPacket add
                        && add.getType() == EntityTypes.ITEM_DISPLAY)
                .map(packet -> ((ClientboundAddEntityPacket) packet).getId()).toList();
        check(h, ids.size() == 3, "Three lanes create exactly three virtual item displays");
        tips[1] = null;
        before = tips.clone();
        v.update(tips, 1, 9);
        check(h, Arrays.equals(before, tips), "Stopped-lane update preserves the null in the caller's array");
        check(h, one(h, p, 2).positions().equals(List.of(tips[0], tips[2])), "Only surviving live tips remain visible");
        var removals = new HashSet<Integer>();
        for (var packet : outbound(p)) if (packet instanceof ClientboundRemoveEntitiesPacket remove)
            removals.addAll(remove.entityIds());
        check(h, removals.size() == 1 && ids.containsAll(removals), "One dead lane sends exactly its own despawn");
        tips[1] = p.position().add(10, 0, 0);
        v.update(tips, 2, 8);
        one(h, p, 2);
        check(h, !owned(p).getFirst().positions().contains(tips[1]), "A stopped lane cannot be resurrected");
        v.close(); v.close();
        for (var packet : outbound(p)) if (packet instanceof ClientboundRemoveEntitiesPacket remove)
            removals.addAll(remove.entityIds());
        check(h, removals.containsAll(ids), "Close despawns every remaining virtual item display");
        v.update(tips, 3, 7);
        gone(h, p);
        h.succeed();
    }

    @GameTest(structure = FLOOR, environment = VISUAL_ENV, maxTicks = 65)
    public void focusedVfxViewerUsesLiveTipDistanceAndFiveTickRefresh(GameTestHelper h) {
        var p = visualOwner(h);
        var nearby = visualOwner(h);
        var distant = visualOwner(h);
        var otherLevelViewer = visualOwner(h);
        var participants = List.of(nearby, distant, otherLevelViewer);
        var players = h.getLevel().getServer().getPlayerList().getPlayers();
        players.addAll(participants);
        TestCleanup.register(h, () -> players.removeAll(participants));
        var other = StreamSupport.stream(h.getLevel().getServer().getAllLevels().spliterator(), false)
                .filter(level -> level != h.getLevel()).findFirst().orElseThrow();
        var anchor = p.position();
        var v = reserve(h, p, 1);
        // Keep tips within 32 blocks of attachment, but place owner >48 from attachment.
        var live = anchor.add(20, 0, 0);
        var tips = new Vec3[]{live};
        p.setPos(live.add(48, 0, 0));
        nearby.setPos(live);
        distant.setPos(live.add(48.01, 0, 0));
        otherLevelViewer.setPos(live);
        otherLevelViewer.setServerLevel(other);
        v.update(tips, 0, 10);
        var first = one(h, p, 1);
        check(h, first.viewers().containsAll(List.of(p.getUUID(), nearby.getUUID())),
                "Owner's inclusive 48-block boundary and nearby viewer use live tips, not impact origin");
        check(h, !first.viewers().contains(distant.getUUID()) && !first.viewers().contains(otherLevelViewer.getUUID()),
                "Out-of-range and other-level viewers never join the holder");
        p.setPos(live.add(48.01, 0, 0));
        v.update(tips, 4, 9);
        check(h, one(h, p, 1).viewers().contains(p.getUUID()), "Viewer set is retained until the five-tick refresh");
        v.update(tips, 5, 8);
        check(h, !one(h, p, 1).viewers().contains(p.getUUID()), "Just outside 48 blocks leaves at refresh");
        p.setPos(live.add(47.99, 0, 0));
        nearby.setServerLevel(other);
        otherLevelViewer.setServerLevel(h.getLevel());
        v.update(tips, 10, 7);
        var refreshed = one(h, p, 1);
        check(h, refreshed.viewers().containsAll(List.of(p.getUUID(), otherLevelViewer.getUUID()))
                        && !refreshed.viewers().contains(nearby.getUUID()),
                "Refresh enrolls re-entry and removes a viewer that changed levels");
        v.close(); gone(h, p);
        players.removeAll(participants);
        h.succeed();
    }

    @GameTest(structure = FLOOR, environment = VISUAL_ENV, maxTicks = 205)
    public void focusedVfxOwnerCapRejectsWholeReservationAndCloseFreesOnlyOwnedBudget(GameTestHelper h) {
        h.startSequence().thenWaitUntil(() -> check(h,
                WaveCrestVfx.MAX_TOTAL_ELEMENTS - WaveCrestVfx.totalElements() >= 32,
                "Wait for owner-cap capacity without clearing or evicting foreign sessions"))
                .thenExecute(() -> ownerCap(h));
    }

    private static void ownerCap(GameTestHelper h) {
        var p = visualOwner(h);
        var baseline = WaveCrestVfx.totalElements();
        var a = reserve(h, p, 16);
        var b = reserve(h, p, 14);
        check(h, WaveCrestVfx.activeElements(p) == 30, "Owner reserves 30 elements");
        var foreign = WaveCrestVfx.snapshots().stream().filter(s -> !s.owner().equals(p.getUUID())).toList();
        var rejected = reserve(h, p, 3);
        rejected.update(tips(p, 3), 0, 10);
        check(h, WaveCrestVfx.activeElements(p) == 30 && WaveCrestVfx.totalElements() == baseline + 30,
                "Only two free owner slots reject an entire three-lane reservation without eviction");
        var tail = reserve(h, p, 2);
        check(h, WaveCrestVfx.activeElements(p) == WaveCrestVfx.MAX_OWNER_ELEMENTS, "Exact owner cap is accepted");
        a.close(); a.close();
        check(h, WaveCrestVfx.activeElements(p) == 16, "Idempotent close frees exactly its 16 slots");
        var replacement = reserve(h, p, 16);
        check(h, WaveCrestVfx.activeElements(p) == 32, "Released owner budget can be reused");
        check(h, WaveCrestVfx.snapshots().containsAll(foreign), "Owner budget operations preserve preexisting sessions");
        for (var v : List.of(a, b, rejected, tail, replacement)) v.close();
        gone(h, p);
        check(h, WaveCrestVfx.totalElements() == baseline, "Focused test restores only its own reservations");
        h.succeed();
    }

    @GameTest(structure = FLOOR, environment = VISUAL_ENV, maxTicks = 65)
    public void focusedVfxGlobalCapAccountsForPreexistingReservationsWithoutEviction(GameTestHelper h) {
        var baseline = WaveCrestVfx.totalElements();
        var foreign = WaveCrestVfx.snapshots();
        var allocated = new ArrayList<WaveCrestVfx>();
        // Synchronous fill and release: no real tick can starve concurrent paid shots.
        while (WaveCrestVfx.totalElements() < WaveCrestVfx.MAX_TOTAL_ELEMENTS) {
            var p = visualOwner(h);
            int count = Math.min(WaveCrestVfx.MAX_OWNER_ELEMENTS,
                    WaveCrestVfx.MAX_TOTAL_ELEMENTS - WaveCrestVfx.totalElements());
            int previous = WaveCrestVfx.totalElements();
            allocated.add(reserve(h, p, count));
            check(h, WaveCrestVfx.totalElements() == previous + count, "Fill only available global capacity");
        }
        var deniedOwner = visualOwner(h);
        var denied = reserve(h, deniedOwner, 1);
        denied.update(tips(deniedOwner, 1), 0, 10);
        gone(h, deniedOwner);
        check(h, WaveCrestVfx.totalElements() == 128 && WaveCrestVfx.snapshots().containsAll(foreign),
                "Full global payload budget rejects without evicting any preexisting holder");
        if (!allocated.isEmpty()) {
            allocated.getLast().close();
            var reuse = reserve(h, deniedOwner, 1);
            check(h, WaveCrestVfx.activeElements(deniedOwner) == 1, "Closed holder frees global capacity immediately");
            reuse.close();
        }
        for (var v : allocated) v.close();
        denied.close();
        check(h, WaveCrestVfx.totalElements() == baseline && WaveCrestVfx.snapshots().containsAll(foreign),
                "Focused global-cap case restores its own allocations and preserves foreign sessions");
        h.succeed();
    }

    @GameTest(structure = FLOOR, environment = VISUAL_ENV, maxTicks = 65)
    public void focusedVfxInvalidOwnersCloseWithoutChangingHealthyOwnersOrGameplay(GameTestHelper h) {
        var healthy = visualOwner(h);
        var control = reserve(h, healthy, 2);
        control.update(tips(healthy, 2), 0, 10);
        var before = one(h, healthy, 2);
        float health = healthy.getHealth();
        var other = StreamSupport.stream(h.getLevel().getServer().getAllLevels().spliterator(), false)
                .filter(level -> level != h.getLevel()).findFirst().orElseThrow();
        for (String guard : List.of("dead", "removed", "disconnected", "spectator", "level")) {
            var invalid = visualOwner(h);
            var v = reserve(h, invalid, 1);
            var tips = tips(invalid, 1);
            v.update(tips, 0, 10);
            one(h, invalid, 1);
            switch (guard) {
                case "dead" -> invalid.setHealth(0);
                case "removed" -> invalid.discard();
                case "disconnected" -> invalid.disconnect();
                case "spectator" -> invalid.setGameMode(GameType.SPECTATOR);
                case "level" -> invalid.setServerLevel(other);
                default -> throw new AssertionError(guard);
            }
            var copy = tips.clone();
            v.update(tips, 5, 9);
            gone(h, invalid);
            check(h, Arrays.equals(copy, tips), "Invalid owner affects visuals only, never gameplay tips: " + guard);
            invalid.setServerLevel(h.getLevel());
            if (guard.equals("level")) {
                v.update(tips, 10, 8);
                gone(h, invalid);
            } else {
                var denied = reserve(h, invalid, 1);
                denied.update(tips, 0, 10);
                gone(h, invalid);
            }
            check(h, owned(healthy).equals(List.of(before)) && healthy.getHealth() == health,
                    "Invalid owner preserves healthy owner's holder, viewers, tips and HP: " + guard);
        }
        control.close(); gone(h, healthy);
        h.succeed();
    }


    @GameTest(structure = FLOOR, environment = VISUAL_ENV, maxTicks = 65)
    public void focusedVfxInvalidUpdatesCloseWithoutChangingGameplayTips(GameTestHelper h) {
        var p = visualOwner(h);
        for (String invalid : List.of("null", "length", "negativeAge", "expiredAge", "zeroLength", "nanLength", "stopped", "far", "nanTip")) {
            var v = reserve(h, p, 1);
            v.update(tips(p, 1), 0, 10);
            one(h, p, 1);
            Vec3[] input = switch (invalid) {
                case "null" -> null;
                case "length" -> new Vec3[0];
                case "stopped" -> new Vec3[]{null};
                case "far" -> new Vec3[]{p.position().add(33, 0, 0)};
                case "nanTip" -> new Vec3[]{new Vec3(Double.NaN, 0, 0)};
                default -> tips(p, 1);
            };
            var before = input == null ? null : input.clone();
            int age = invalid.equals("negativeAge") ? -1 : invalid.equals("expiredAge") ? 100 : 1;
            double remaining = invalid.equals("zeroLength") ? 0 : invalid.equals("nanLength") ? Double.NaN : 9;
            v.update(input, age, remaining);
            check(h, Arrays.equals(before, input), "Rejected visual update preserves caller-owned tips: " + invalid);
            gone(h, p);
            v.close();
        }
        h.succeed();
    }

    /** A normal embedded listener with a synchronous failure only for entity removal packets. */
    private static final class FaultingListener extends ServerGamePacketListenerImpl {
        boolean rejectRemovals;
        final List<Packet<?>> delivered = new ArrayList<>();
        FaultingListener(GameTestHelper h, Connection connection, ServerPlayer owner, CommonListenerCookie cookie) {
            super(h.getLevel().getServer(), connection, owner, cookie);
        }
        @Override public void send(Packet<?> packet) {
            var flat = new ArrayList<Packet<?>>();
            flatten(packet, flat);
            if (rejectRemovals && flat.stream().anyMatch(p -> p instanceof ClientboundRemoveEntitiesPacket))
                throw new IllegalStateException("W79 injected entity-removal send failure");
            super.send(packet);
            delivered.addAll(flat);
        }
    }

    @GameTest(structure = FLOOR, environment = VISUAL_ENV, maxTicks = 85)
    public void focusedVfxFailedLaneRemovalRetainsAllIdsAndBudgetUntilRealTickRetry(GameTestHelper h) {
        var p = visualOwner(h);
        var healthy = visualOwner(h);
        var original = p.connection;
        var network = new Connection(PacketFlow.SERVERBOUND);
        var channel = new EmbeddedChannel(network);
        var cookie = CommonListenerCookie.createInitial(p.getGameProfile(), false);
        var fault = new FaultingListener(h, network, p, cookie);
        network.setupInboundProtocol(GameProtocols.SERVERBOUND_TEMPLATE.bind(
                RegistryFriendlyByteBuf.decorator(h.getLevel().getServer().registryAccess()), fault), fault);
        p.connection = fault;
        fault.handleAcceptPlayerLoad(new ServerboundPlayerLoadedPacket());
        // Enroll just this temporary embedded viewer through the public list, not reflection or a full login.
        var players = h.getLevel().getServer().getPlayerList().getPlayers();
        players.add(healthy);
        var vfx = new ArrayList<WaveCrestVfx>();
        TestCleanup.register(h, () -> {
            fault.rejectRemovals = false;
            for (var v : vfx) v.close();
            players.remove(healthy);
            p.connection = original;
            channel.finishAndReleaseAll();
        });
        int pendingBefore = WaveCrestVfx.pendingCleanupCount();
        int totalBefore = WaveCrestVfx.totalElements();
        var v = reserve(h, p, 3);
        vfx.add(v);
        var input = tips(p, 3);
        v.update(input, 0, 10);
        check(h, one(h, p, 3).viewers().containsAll(List.of(p.getUUID(), healthy.getUUID())),
                "Faulting owner and independent healthy connection both receive the same crest");
        var ids = fault.delivered.stream().filter(packet -> packet instanceof ClientboundAddEntityPacket add
                        && add.getType() == EntityTypes.ITEM_DISPLAY)
                .map(packet -> ((ClientboundAddEntityPacket) packet).getId()).toList();
        check(h, ids.size() == 3, "Fault is armed only after all three lane IDs have spawned");
        TestPlayers.drain(healthy);
        fault.rejectRemovals = true;
        input[1] = null;
        var before = input.clone();
        v.update(input, 1, 9);
        check(h, Arrays.equals(before, input), "Transport failure cannot change authoritative gameplay tips");
        check(h, owned(p).isEmpty() && WaveCrestVfx.activeElements(p) == 3
                        && WaveCrestVfx.totalElements() == totalBefore + 3
                        && WaveCrestVfx.pendingCleanupCount() == pendingBefore + 1,
                "Failed send hides the closed holder but reserves every original lane ID, including the detached lane");
        var healthyRemoved = new HashSet<Integer>();
        for (var packet : outbound(healthy)) if (packet instanceof ClientboundRemoveEntitiesPacket remove)
            healthyRemoved.addAll(remove.entityIds());
        check(h, healthyRemoved.containsAll(ids), "One faulting viewer cannot strand ghost IDs on the healthy viewer");
        v.close();
        check(h, WaveCrestVfx.activeElements(p) == 3, "Repeated close while transport fails cannot free pending payload budget");
        fault.rejectRemovals = false;
        fault.delivered.clear();
        // Do not call close/update again: END_SERVER_TICK must perform the actual retry.
        h.runAfterDelay(2, () -> {
            var retried = new HashSet<Integer>();
            for (var packet : fault.delivered) if (packet instanceof ClientboundRemoveEntitiesPacket remove)
                retried.addAll(remove.entityIds());
            check(h, retried.containsAll(ids), "Recovered connection receives every original ID on real tick retry");
            gone(h, p);
            check(h, WaveCrestVfx.pendingCleanupCount() <= pendingBefore, "Successful retry releases this pending cleanup");
            h.succeed();
        });
    }

    @GameTest(structure = FLOOR, environment = "destiny-test:w90_allied_isolated", maxTicks = 205)
    public void paidShotStillDealsWaveDamageWhenFocusedVfxReservationsExhaustOwnerBudget(GameTestHelper h) {
        var f = fixture(h, WHISPER, 16);
        var far = f.target(IMPACT_X + f.wave.length() * .8, 4);
        var filler = reserve(h, f.owner, 32);
        check(h, WaveCrestVfx.activeElements(f.owner) == 32, "Focused reservation fills this owner's cosmetic budget");
        exactAim(h, java.util.List.of(f.owner), () -> {
            shot(h, f.owner);
            h.runAfterDelay(f.finish(), () -> {
                f.hitOnce(far, "Actual paid shot retains full ground-wave gameplay while optional display allocation is denied");
                check(h, owned(f.owner).size() == 1 && WaveCrestVfx.activeElements(f.owner) == 32
                                && WeaponRuntime.activeProjectiles(f.owner) == 0,
                        "Denied wave visual neither evicts focused filler nor leaks a shot/extra holder");
                filler.close(); gone(h, f.owner);
                h.succeed();
            });
        });
    }
}
