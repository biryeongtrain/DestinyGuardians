package kim.biryeong.destiny.test;

import kim.biryeong.destiny.ability.AbilityService;
import kim.biryeong.destiny.fx.HunterVfx;
import kim.biryeong.destiny.fx.HunterVfxAssets;
import kim.biryeong.destiny.fx.SuperVfx;
import kr.toxicity.model.api.BetterModel;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.Vec3;

import java.util.List;

/** Real BetterModel renderers and Polymer holders; no screenshot or multiplayer claims. */
public final class SuperVfxGameTests {
    private static final String FLOOR = "destiny-test:floor";
    private static final Vec3 ORIGIN = new Vec3(2.5, 1, 6.5);

    private static void check(GameTestHelper h, boolean condition, String message) {
        h.assertTrue(condition, Component.literal(message));
    }

    private ServerPlayer owner(GameTestHelper h) { return TestPlayers.create(h, ORIGIN, -90, 0); }

    private void delayed(GameTestHelper h, ServerPlayer p, int ticks, Runnable assertions) {
        h.runBeforeTestEnd(() -> TestPlayers.remove(p));
        h.runAfterDelay(ticks, () -> {
            try { assertions.run(); h.succeed(); }
            finally { TestPlayers.remove(p); }
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 1200)
    public void dedicatedUltimateRenderersHaveThreeAnimatedRenderBones(GameTestHelper h) {
        h.startSequence().thenWaitUntil(() -> {
            for (String name : HunterVfxAssets.SUPER_MODELS)
                check(h, BetterModel.model(name).isPresent(), "Waiting for ultimate model " + name);
        }).thenExecute(() -> {
            for (String name : HunterVfxAssets.SUPER_MODELS) {
                var renderer = BetterModel.model(name).orElseThrow();
                check(h, renderer.animation(name.contains("anchor") ? "loop" : "spawn").isPresent(), "Animation contract " + name);
                check(h, renderer.flatten().filter(g -> !g.getItemStack().isAir()).count() == 3,
                        "Exactly three render bones " + name);
            }
            ServerPlayer p = owner(h);
            try {
                check(h, HunterVfx.play(p, p.level(), p.position(), HunterVfx.Kind.ARC_SWEEP, 3, 12, 0, -90),
                        "Directional arc sweep starts a real tracker");
                check(h, !HunterVfx.play(p, p.level(), p.position(), HunterVfx.Kind.ARC_SWEEP, 3, 12, 0, Float.NaN),
                        "Nonfinite model yaw rejected");
                check(h, SuperVfx.anchor(p, p.position().add(2, 0, 0), 160), "Void anchor starts a real tracker");
                h.succeed();
            } finally { TestPlayers.remove(p); }
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 30)
    public void flameTrailExpiresOnNormalServerTicks(GameTestHelper h) {
        ServerPlayer p = owner(h);
        try {
            Vec3 from = p.position().add(0, 1, 0);
            float health = p.getHealth();
            Vec3 velocity = p.getDeltaMovement();
            check(h, SuperVfx.trail(p, from, from.add(5, 0, 0), 999), "Trail allocates a real Polymer holder");
            check(h, SuperVfx.activeCount(p) == 1, "One beam is retained");
            delayed(h, p, 11, () -> {
                check(h, SuperVfx.activeCount(p) == 0, "Even an overlong tracer expires after ten ticks");
                check(h, p.getHealth() == health && p.getDeltaMovement().equals(velocity), "Cosmetics do not change health/velocity");
            });
        } catch (RuntimeException | Error e) { TestPlayers.remove(p); throw e; }
    }

    @GameTest(structure = FLOOR, maxTicks = 30)
    public void movingTetherReusesDisplayAndDropsOutOfRadiusTarget(GameTestHelper h) {
        ServerPlayer p = owner(h);
        LivingEntity target = h.spawn(EntityTypes.HUSK, new Vec3(5.5, 1, 6.5));
        ((net.minecraft.world.entity.Mob) target).setNoAi(true);
        try {
            Vec3 anchor = p.position();
            check(h, SuperVfx.link(p, anchor, target, 7, 12), "Tether starts");
            target.setPos(target.position().add(0, 0, 1));
            check(h, SuperVfx.link(p, anchor, target, 7, 12), "Refresh succeeds for moved target");
            check(h, SuperVfx.activeCount(p) == 1, "Refreshing must reuse, not allocate another holder");
            target.setPos(anchor.add(20, 0, 0));
            delayed(h, p, 2, () -> check(h, SuperVfx.activeCount(p) == 0, "Moving outside radius removes link without refresh"));
        } catch (RuntimeException | Error e) { TestPlayers.remove(p); throw e; }
    }

    @GameTest(structure = FLOOR, maxTicks = 30)
    public void tetherVisualsAreCappedToThreeEnemiesAndExpireWithoutRefresh(GameTestHelper h) {
        ServerPlayer p = owner(h);
        try {
            List<LivingEntity> enemies = new java.util.ArrayList<>();
            for (int i = 0; i < 5; i++) {
                var mob = h.spawn(EntityTypes.HUSK, new Vec3(3.5 + i, 1, 6.5));
                mob.setNoAi(true);
                enemies.add(mob);
            }
            SuperVfx.tether(p, p.position(), 7, enemies);
            check(h, SuperVfx.activeCount(p) == 3, "Five gameplay targets create only three cosmetic links");
            delayed(h, p, 13, () -> check(h, SuperVfx.activeCount(p) == 0, "Links expire when anchor task no longer refreshes"));
        } catch (RuntimeException | Error e) { TestPlayers.remove(p); throw e; }
    }

    @GameTest(structure = FLOOR, maxTicks = 20)
    public void beamOwnerCapCleanupAndInvalidInputAreIsolated(GameTestHelper h) {
        ServerPlayer p = owner(h), other = owner(h);
        try {
            Vec3 from = p.position();
            for (int i = 0; i < 6; i++) check(h, SuperVfx.trail(p, from, from.add(3 + i, 1, 0), 10), "Valid tracer");
            check(h, SuperVfx.activeCount(p) == 4, "Per owner maximum four beams");
            check(h, SuperVfx.trail(other, from, from.add(3, 0, 0), 10), "Other owner tracer");
            check(h, !SuperVfx.trail(p, from, from.add(97, 0, 0), 10), "Reject unsupported long beam");
            check(h, !SuperVfx.trail(p, from, from, 10), "Reject zero-length beam");
            check(h, !SuperVfx.trail(p, new Vec3(Double.NaN, 0, 0), from, 10), "Reject nonfinite beam");
            check(h, !SuperVfx.trail(p, from, from.add(1, 0, 0), 0), "Reject nonpositive TTL");
            AbilityService.cleanup(p);
            check(h, SuperVfx.activeCount(p) == 0 && SuperVfx.activeCount(other) == 1,
                    "Cleanup must preserve the other owner");
            h.succeed();
        } finally { TestPlayers.remove(p); TestPlayers.remove(other); }
    }

    @GameTest(structure = FLOOR, maxTicks = 20)
    public void ownerDimensionChangeDropsBeamOnNextTick(GameTestHelper h) {
        ServerPlayer p = owner(h);
        try {
            check(h, SuperVfx.trail(p, p.position(), p.position().add(4, 0, 0), 10), "Starts before dimension change");
            var other = h.getLevel().getServer().getLevel(h.getLevel().dimension().equals(Level.NETHER) ? Level.OVERWORLD : Level.NETHER);
            check(h, other != null, "Second dimension");
            p.setServerLevel(other);
            delayed(h, p, 2, () -> check(h, SuperVfx.activeCount(p) == 0, "Dimension change removes beam"));
        } catch (RuntimeException | Error e) { TestPlayers.remove(p); throw e; }
    }
}
