package kim.biryeong.destiny.test;

import kim.biryeong.destiny.fx.BowTrailFx;
import kim.biryeong.destiny.fx.Fx;
import kim.biryeong.destiny.weapon.*;
import kim.biryeong.minigamelib.cinematic.CameraViews;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.core.particles.DustParticleOptions;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.game.ClientboundLevelParticlesPacket;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.gamerules.GameRules;
import net.minecraft.world.phys.Vec3;

import java.util.ArrayList;
import java.util.List;

/** Actual PLAY bytes through unchanged W92, then context-free client decode.
 * Registered recipients, original Fx oracle, real input/server clock; not native visual acceptance.
 */
public final class BowTrailW95GameTests {
    private static final String FLOOR = "destiny-test:w78_floor";
    private static final String ISOLATED = "destiny-test:w90_isolated";
    private static final int RGB = 0xFFE2A8;
    private static final float SIZE = .7f;
    private static final double RADIUS_SQUARED = 1.5625; // Independent provisional contract, not product constant.

    private static void check(GameTestHelper h, boolean yes, String why) {
        h.assertTrue(yes, Component.literal(why));
    }

    /** Compare every transported particle field, not DustParticleOptions object identity. */
    private record Sample(Vec3 point, float red, float green, float blue, float size,
                          boolean limiter, boolean always, int count,
                          float dx, float dy, float dz, float sx, float sy, float sz,
                          ClientboundLevelParticlesPacket.RandomizationType randomization) { }

    private static List<Sample> particles(InventoryWireW92 wire) {
        var result = new ArrayList<Sample>();
        for (var packet : wire.capture()) {
            if (!(packet instanceof ClientboundLevelParticlesPacket p)) continue;
            if (!(p.particle() instanceof DustParticleOptions dust))
                throw new IllegalStateException("Unexpected non-dust particle in isolated trail capture: " + p.particle());
            var c = dust.getColor();
            result.add(new Sample(new Vec3(p.x(), p.y(), p.z()), c.x(), c.y(), c.z(), dust.getScale(),
                    p.overrideLimiter(), p.alwaysShow(), p.count(), p.xDist(), p.yDist(), p.zDist(),
                    p.xMaxSpeed(), p.yMaxSpeed(), p.zMaxSpeed(), p.randomizationType()));
        }
        return List.copyOf(result);
    }

    private static void fields(GameTestHelper h, List<Sample> samples, int rgb, float size) {
        var expected = Fx.dust(rgb, size).getColor();
        for (var p : samples) {
            check(h, p.red == expected.x() && p.green == expected.y() && p.blue == expected.z()
                            && p.size == size && !p.limiter && !p.always && p.count == 1
                            && p.dx == 0 && p.dy == 0 && p.dz == 0 && p.sx == 0 && p.sy == 0 && p.sz == 0
                            && p.randomization == ClientboundLevelParticlesPacket.RandomizationType.DEFAULT,
                    "Decoded dust keeps exact RGB/size, false/false, count1, zero spread/speed, DEFAULT randomization");
        }
    }

    private static List<Sample> visible(List<Sample> baseline, Vec3 eye) {
        return baseline.stream().filter(p -> p.point.distanceToSqr(eye) >= RADIUS_SQUARED).toList();
    }

    private static final class Scene {
        final GameTestHelper h;
        final long start;
        final List<InventoryWireW92> wires = new ArrayList<>();

        Scene(GameTestHelper h) {
            this.h = h;
            start = h.getLevel().getServer().getTickCount();
            check(h, !h.getLevel().getGameRules().get(GameRules.SPAWN_MOBS), "Isolated W90 spawning preflight");
            for (int x = 0; x < 48; x++) for (int z = 0; z < 32; z++) h.setBlock(x, 3, z, Blocks.STONE);
            h.onEachTick(() -> {
                var origin = h.absoluteVec(Vec3.ZERO);
                for (var w : wires) {
                    var b = w.player.getBoundingBox();
                    check(h, w.player.level() == h.getLevel() && b.minX > origin.x && b.maxX < origin.x + 48
                                    && b.minY > origin.y && b.maxY < origin.y + 12
                                    && b.minZ > origin.z && b.maxZ < origin.z + 32,
                            "Entire registered recipient stays inside owned W90 fixture");
                }
            });
        }

        InventoryWireW92 player(Vec3 relative) {
            var w = new InventoryWireW92(h, relative);
            // W92 registered channel closure before its setup. This later callback executes first,
            // while the channel is live; every teardown stage runs even if a prior stage fails.
            TestCleanup.register(h, () -> {
                try { CameraViews.stop(w.player); }
                finally {
                    try { w.player.setCamera(w.player); }
                    finally {
                        try { h.getLevel().removePlayerImmediately(w.player, Entity.RemovalReason.DISCARDED); }
                        finally { w.player.discard(); }
                    }
                }
            });
            h.getLevel().addNewPlayer(w.player);
            check(h, h.getLevel().players().contains(w.player)
                            && h.getLevel().getEntity(w.player.getUUID()) == w.player,
                    "Real level.addNewPlayer registered exact wire recipient before particle/camera calls");
            wires.add(w);
            w.player.setAttached(WeaponLoadout.ENABLED, false);
            w.discard();
            return w;
        }

        void discard() { for (var w : wires) w.discard(); }

        void at(int tick, Runnable action) {
            check(h, h.getLevel().getServer().getTickCount() == start, "Register every deadline up front");
            h.runAfterDelay(tick, () -> {
                check(h, h.getLevel().getServer().getTickCount() - start == tick, "Actual server clock " + tick);
                action.run();
            });
        }
    }

    private record Pair(List<Sample> owner, List<Sample> observer) { }

    private static Pair original(Scene s, InventoryWireW92 owner, InventoryWireW92 observer,
                                 Vec3 from, Vec3 to, double step, int rgb, float size) {
        s.discard();
        Fx.line(s.h.getLevel(), from, to, rgb, step, size);
        return new Pair(particles(owner), particles(observer));
    }

    private static Pair filtered(Scene s, InventoryWireW92 owner, InventoryWireW92 observer,
                                 Vec3 from, Vec3 to, double step, int rgb, float size) {
        s.discard();
        BowTrailFx.line(owner.player, s.h.getLevel(), from, to, rgb, step, size);
        return new Pair(particles(owner), particles(observer));
    }

    @GameTest(structure = FLOOR, maxTicks = 10, environment = ISOLATED)
    public void originalLatticeAndEveryEncodedFieldSurviveZeroShortDiagonalAndNonmultipleLines(GameTestHelper h) {
        var s = new Scene(h);
        var owner = s.player(new Vec3(4, 4, 8)); var observer = s.player(new Vec3(10, 4, 8));
        var from = owner.player.getEyePosition().add(0, 0, 4);
        var deltas = List.of(Vec3.ZERO, new Vec3(.00001, 0, 0), new Vec3(.1, 0, 0),
                new Vec3(1, 0, 0), new Vec3(1.5, 0, 0), new Vec3(.6, .8, 0));
        int[] counts = {0, 0, 1, 3, 5, 3};
        for (int i = 0; i < deltas.size(); i++) {
            var to = from.add(deltas.get(i));
            var before = original(s, owner, observer, from, to, .35, 0x1234AB, 1.125f);
            var after = filtered(s, owner, observer, from, to, .35, 0x1234AB, 1.125f);
            check(h, before.owner.size() == counts[i] && before.owner.equals(before.observer)
                            && after.owner.equals(before.owner) && after.observer.equals(before.observer),
                    "Actual encoded original/helper lattice parity case " + i);
            fields(h, after.owner, 0x1234AB, 1.125f);
            if (!after.owner.isEmpty()) {
                check(h, after.owner.getFirst().point.equals(from), "Original d=0 is retained, never restarted");
                // This isolated level may be translated millions of blocks from origin.
                // Use its actual representable endpoint delta, not the pre-translation literal.
                var representedDelta = to.subtract(from);
                var direction = representedDelta.scale(1.0 / representedDelta.length());
                double lastDistance = 0;
                for (int j = 1; j < counts[i]; j++) lastDistance += .35;
                var last = from.add(direction.scale(lastDistance));
                check(h, after.owner.getLast().point.distanceToSqr(last) < 1e-24,
                        "Original nonmultiple last lattice point; no forced endpoint");
            }
        }
        // Binary-exact endpoint control avoids making .35 accumulation an endpoint oracle.
        var end = from.add(1.5, 0, 0);
        var baseline = original(s, owner, observer, from, end, .5, RGB, SIZE);
        var actual = filtered(s, owner, observer, from, end, .5, RGB, SIZE);
        check(h, actual.observer.equals(baseline.observer) && actual.owner.equals(baseline.owner)
                        && actual.owner.size() == 4 && actual.owner.getLast().point.equals(end),
                "An exact lattice endpoint is retained exactly once");
        h.succeed();
    }

    @GameTest(structure = FLOOR, maxTicks = 10, environment = ISOLATED)
    public void crossingAndEntirelyNearSegmentsFilterOnlyStrictOwnerInteriorWithoutResampling(GameTestHelper h) {
        var s = new Scene(h);
        var owner = s.player(new Vec3(8, 4, 8)); var observer = s.player(new Vec3(12, 4, 8));
        var eye = owner.player.getEyePosition();
        var from = eye.add(-2, 0, 0); var to = eye.add(2, 0, 0);
        var baseline = original(s, owner, observer, from, to, .25, RGB, SIZE);
        var actual = filtered(s, owner, observer, from, to, .25, RGB, SIZE);
        check(h, baseline.owner.equals(baseline.observer) && baseline.owner.size() == 17
                        && actual.observer.equals(baseline.observer)
                        && actual.owner.equals(visible(baseline.owner, eye)) && actual.owner.size() == 8,
                "Crossing line preserves all 17 observer samples and only eight original owner exterior samples");
        check(h, actual.owner.stream().anyMatch(p -> p.point.equals(eye.add(-1.25, 0, 0)))
                        && actual.owner.stream().anyMatch(p -> p.point.equals(eye.add(1.25, 0, 0))),
                "Both exact 1.25m boundary samples remain on encoded wire");
        var nearBaseline = original(s, owner, observer, eye, eye.add(.5, 0, 0), .25, RGB, SIZE);
        var near = filtered(s, owner, observer, eye, eye.add(.5, 0, 0), .25, RGB, SIZE);
        check(h, nearBaseline.owner.size() == 3 && near.owner.isEmpty()
                        && near.observer.equals(nearBaseline.observer),
                "Whole short interior segment disappears only for owner, including d=0");
        fields(h, actual.owner, RGB, SIZE); fields(h, actual.observer, RGB, SIZE);
        h.succeed();
    }

    @GameTest(structure = FLOOR, maxTicks = 10, environment = ISOLATED)
    public void foreignNativeAndSameLevelCinematicCamerasKeepOriginalOwnerPacketParity(GameTestHelper h) {
        var s = new Scene(h);
        var owner = s.player(new Vec3(8, 4, 8)); var observer = s.player(new Vec3(10, 4, 8));
        owner.player.setCamera(observer.player);
        check(h, owner.player.getCamera() == observer.player && CameraViews.get(owner.player) == null,
                "Actual native foreign entity camera, not fabricated visibility state");
        var eye = owner.player.getEyePosition();
        var baseline = original(s, owner, observer, eye, eye.add(.5, 0, 0), .25, RGB, SIZE);
        var actual = filtered(s, owner, observer, eye, eye.add(.5, 0, 0), .25, RGB, SIZE);
        check(h, baseline.owner.size() == 3 && actual.owner.equals(baseline.owner)
                        && actual.observer.equals(baseline.observer), "Foreign native camera must not apply self-eye exclusion");
        owner.player.setCamera(owner.player);
        eye = owner.player.getEyePosition();
        CameraViews.open(owner.player, h.getLevel(), eye.add(0, 0, 2), 0, 0);
        check(h, owner.player.getCamera() == owner.player && CameraViews.get(owner.player) != null,
                "Actual cinematic session with native self camera independently disables exclusion");
        baseline = original(s, owner, observer, eye, eye.add(.5, 0, 0), .25, RGB, SIZE);
        actual = filtered(s, owner, observer, eye, eye.add(.5, 0, 0), .25, RGB, SIZE);
        check(h, baseline.owner.size() == 3 && actual.owner.equals(baseline.owner)
                        && actual.observer.equals(baseline.observer),
                "Targeted send retains existing CameraViews routing and every original particle field");
        CameraViews.stop(owner.player);
        var self = filtered(s, owner, observer, eye, eye.add(.5, 0, 0), .25, RGB, SIZE);
        check(h, self.owner.isEmpty() && self.observer.size() == 3,
                "Stopping actual cinematic restores owner-only filtering immediately");
        h.succeed();
    }

    @GameTest(structure = FLOOR, maxTicks = 10, environment = ISOLATED)
    public void differentOwnerUnrelatedFxAndNativeRangeNeverBecomeGlobalSuppression(GameTestHelper h) {
        var s = new Scene(h);
        var a = s.player(new Vec3(4, 4, 8)); var b = s.player(new Vec3(4, 4, 8));
        var far = s.player(new Vec3(44, 4, 8));
        var eye = a.player.getEyePosition();
        var baseline = original(s, a, b, eye, eye.add(.5, 0, 0), .25, RGB, SIZE);
        check(h, particles(far).isEmpty(), "Original native false-force range excludes registered distant recipient");
        s.discard();
        BowTrailFx.line(b.player, h.getLevel(), eye, eye.add(.5, 0, 0), RGB, .25, SIZE);
        check(h, particles(a).equals(baseline.owner) && particles(b).isEmpty() && particles(far).isEmpty(),
                "Only exact owner b is filtered; co-located a remains an observer and far stays native-out-of-range");
        var self = filtered(s, a, b, eye, eye.add(.5, 0, 0), .25, RGB, SIZE);
        check(h, self.owner.isEmpty() && self.observer.equals(baseline.observer) && particles(far).isEmpty(),
                "Changing owner cannot latch suppression onto a prior recipient");
        var unrelated = original(s, a, b, eye, eye.add(.5, 0, 0), .25, RGB, SIZE);
        check(h, unrelated.equals(baseline), "Unrelated original Fx.line remains fully visible even inside eye radius");
        check(h, particles(far).isEmpty(), "Unrelated Fx preserves original native range too");
        h.succeed();
    }

    @GameTest(structure = FLOOR, maxTicks = 110, environment = ISOLATED)
    public void bitingWindsRealPaidShotFiltersWireButKeepsDamageAndNockClock(GameTestHelper h) {
        paidShot(h, "biting_winds");
    }

    @GameTest(structure = FLOOR, maxTicks = 110, environment = ISOLATED)
    public void whisperingSlabRealPaidShotFiltersWireButKeepsDamageAndNockClock(GameTestHelper h) {
        paidShot(h, "whispering_slab");
    }

    private static void paidShot(GameTestHelper h, String id) {
        var s = new Scene(h);
        var owner = s.player(new Vec3(4, 4, 16)); var observer = s.player(new Vec3(6, 4, 20));
        var p = owner.player;
        p.setYRot(-90); p.setYHeadRot(-90); p.setXRot(0);
        var entry = WeaponCatalog.find(id).orElseThrow(); var profile = WeaponProfile.forEntry(entry);
        var stack = WeaponItems.create(entry);
        p.setItemInHand(InteractionHand.MAIN_HAND, stack);
        WeaponRuntime.tickPlayer(p);
        var target = h.spawn(EntityTypes.HUSK, new Vec3(12, 4.7, 16));
        TestCleanup.register(h, target::discard);
        target.setNoAi(true); target.setNoGravity(true); target.setPersistenceRequired();
        target.getAttribute(Attributes.MAX_HEALTH).setBaseValue(1000);
        target.getAttribute(Attributes.ARMOR).setBaseValue(0);
        target.getAttribute(Attributes.KNOCKBACK_RESISTANCE).setBaseValue(1);
        target.setHealth(1000);
        WeaponCombatItem.INSTANCE.use(h.getLevel(), p, InteractionHand.MAIN_HAND);
        check(h, p.isUsingItem() && p.getUseItem() == stack && rounds(stack, profile) == 1,
                id + " production native hold begins without spending arrow");
        int shotTick = profile.chargeTicks() + 2;
        int deadline = shotTick + profile.firstReloadTicks();
        int end = deadline + 2;
        check(h, end < 110 && profile.firstReloadTicks() > 5, "Bounded real draw/impact/nock deadlines");
        Vec3[] launch = new Vec3[2];
        for (int t = 1; t <= end; t++) {
            int elapsed = t;
            s.at(t, () -> {
                WeaponRuntime.tickPlayer(p);
                if (elapsed == profile.chargeTicks() - 1)
                    check(h, WeaponRuntime.bowDrawState(p).phase() == WeaponBowWindow.Phase.DRAWING
                                    && rounds(stack, profile) == 1 && WeaponRuntime.activeProjectiles(p) == 0,
                            "No early projectile or ammo spend before accepted draw deadline");
                if (elapsed == shotTick) {
                    check(h, WeaponRuntime.bowDrawState(p).progress() == 1, "Actual server draw reached full charge");
                    launch[0] = p.getEyePosition();
                    // Sampling direction here used to consume a different random ray than the shot.
                    // Fixed input seed + independent disk math preserve nonzero hip spread.
                    p.getRandom().setSeed(0x95241L);
                    double u=p.getRandom().nextDouble(), v=p.getRandom().nextDouble();
                    var forward=p.getLookAngle().normalize();
                    var right=forward.cross(Vec3.Y_AXIS).normalize();var up=right.cross(forward);
                    double radius=Math.sqrt(u)*Math.tan(Math.toRadians(WeaponAiming.coneDegrees(p)));
                    var axis=forward.add(right.scale(radius*Math.cos(v*2*Math.PI)))
                            .add(up.scale(radius*Math.sin(v*2*Math.PI))).normalize();
                    launch[1] = launch[0].add(axis.scale(profile.speed()));
                    p.getRandom().setSeed(0x95241L);
                    s.discard();
                    p.releaseUsingItem();
                    check(h, rounds(stack, profile) == 0 && WeaponRuntime.activeProjectiles(p) == 1,
                            "Exactly one real paid projectile, not a fabricated Shot or visual-only trigger");
                    WeaponRuntime.tickPlayer(p);
                    check(h, WeaponRuntime.reloading(p), "Real paid shot starts original automatic nock at this server tick");
                }
                if (elapsed == shotTick + 1) {
                    var ownerTrail = particles(owner); var observerTrail = particles(observer);
                    var saved = stack.copy(); long clock = h.getLevel().getServer().getTickCount();
                    var expected = original(s, owner, observer, launch[0], launch[1], .35, RGB, SIZE);
                    check(h, expected.observer.size() == 9 && ownerTrail.size() == 5
                                    && observerTrail.equals(expected.observer)
                                    && expected.owner.equals(expected.observer)
                                    && ownerTrail.equals(visible(expected.owner, launch[0]))
                                    && ownerTrail.size() < observerTrail.size(),
                            id + " actual Runtime ordinary-bow first segment matches original Fx bytes for observer and owner subset");
                    fields(h, observerTrail, RGB, SIZE); fields(h, ownerTrail, RGB, SIZE);
                    check(h, ItemStack.matches(saved, stack) && rounds(stack, profile) == 0
                                    && h.getLevel().getServer().getTickCount() == clock && WeaponRuntime.reloading(p),
                            "Particle baseline/readback cannot mutate source components/ammo or advance authoritative clock");
                }
                if (elapsed == shotTick + 5) {
                    check(h, Math.abs((1000 - target.getHealth()) - profile.damage()) < .001
                                    && WeaponRuntime.activeProjectiles(p) == 0,
                            "Full paid bow still makes exactly original body damage and retires on actual collision");
                }
                if (elapsed == deadline - 1)
                    check(h, rounds(stack, profile) == 0 && WeaponRuntime.reloading(p), "No early nock ammunition");
                if (elapsed == deadline)
                    check(h, rounds(stack, profile) == 1 && !WeaponRuntime.reloading(p)
                                    && !p.isUsingItem(), "Original exact server nock deadline restores one idle arrow");
                if (elapsed == end) {
                    check(h, rounds(stack, profile) == 1 && WeaponRuntime.activeProjectiles(p) == 0
                                    && !p.isUsingItem(), "No latent draw, extra shot or duplicated ammunition");
                    h.succeed();
                    return; // Terminal cleanup may already have closed the wire channels.
                }
                if (elapsed != shotTick) s.discard();
            });
        }
    }

    private static int rounds(ItemStack stack, WeaponProfile profile) {
        return WeaponItems.magazine(stack, profile).rounds();
    }
}
