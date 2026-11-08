package kim.biryeong.destiny.test;

import kim.biryeong.destiny.activity.strike.StrikeInstances;
import kim.biryeong.destiny.strike.devils.DevilsTemplateGenerator;
import kim.biryeong.destiny.strike.exodus.ExodusMaps;
import kim.biryeong.destiny.strike.exodus.ExodusPlan;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.core.BlockPos;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;

import java.util.List;
import java.util.UUID;

/** The one connected Exodus map generates through the real Fantasy lifecycle, and its walk is physically passable. */
public final class ExodusNbtGameTests {
    private static void check(GameTestHelper h, boolean condition, String text) { h.assertTrue(condition, Component.literal(text)); }

    @GameTest(structure = "destiny-test:floor", maxTicks = 3000, environment = "destiny-test:w90_isolated")
    public void exodusMapGeneratesAndTheRouteAndGatesAreWhereThePlanSaysTheyAre(GameTestHelper h) {
        var server = h.getLevel().getServer();
        var preload = ExodusMaps.maps().preloadAsync(server);
        var instances = new StrikeInstances(server, "exodus_crash", 1, 1, 3,
                () -> new DevilsTemplateGenerator(server, ExodusMaps.maps().nbtTemplates()));
        var instance = new StrikeInstances.Instance[1];
        var build = new kim.biryeong.destiny.campaign.RisingServices.ZoneBuild[1];
        long deadline = System.nanoTime() + java.util.concurrent.TimeUnit.SECONDS.toNanos(120);
        long[] nextPoll = {System.nanoTime()};
        boolean[] done = {false};
        TestCleanup.register(h, () -> {
            if (build[0] != null) build[0].cancel();
            if (instance[0] != null) instances.close(instance[0]);
        });
        h.onEachTick(() -> {
            if (done[0]) return;
            long remaining = nextPoll[0] - System.nanoTime();
            while (remaining > 0) { java.util.concurrent.locks.LockSupport.parkNanos(remaining); remaining = nextPoll[0] - System.nanoTime(); }
            nextPoll[0] = System.nanoTime() + java.util.concurrent.TimeUnit.MILLISECONDS.toNanos(50);
            check(h, System.nanoTime() < deadline, "Exodus fixture exceeded 120 seconds; preload=" + preload.isDone()
                    + ", build=" + (build[0] == null ? "none" : build[0].progress()));
            if (!preload.isDone()) return;
            preload.join();
            if (instance[0] == null) {
                instance[0] = instances.prepare(List.of(UUID.randomUUID())).orElseThrow();
                build[0] = ExodusMaps.begin(instance[0].level(), ExodusPlan.Zone.WORLD);
            }
            if (!build[0].step(2_000_000)) return;
            var level = instance[0].level();
            var plan = ExodusPlan.data();
            int checked = 0;
            for (int i = 0; i < plan.route().size(); i += 12) {
                var at = ExodusMaps.world(plan.route().get(i));
                if (!level.hasChunkAt(BlockPos.containing(at))) continue;
                var feet = BlockPos.containing(at);
                check(h, !level.getBlockState(feet.below()).getCollisionShape(level, feet.below()).isEmpty(), "route floor " + i + " at " + feet);
                check(h, level.noCollision(new net.minecraft.world.phys.AABB(at.x - .3, at.y + 1.0, at.z - .3, at.x + .3, at.y + 1.8, at.z + .3)),
                        "route headroom " + i + " at " + feet);
                checked++;
            }
            check(h, checked >= 3, "Start area route cells were not sampled: " + checked);
            for (var seat : List.of("WORLD.IN", "WORLD.IN.0", "WORLD.IN.1", "WORLD.IN.2")) {
                var p = ExodusMaps.anchor(seat).pos();
                var feet = BlockPos.containing(p);
                check(h, !level.getBlockState(feet.below()).getCollisionShape(level, feet.below()).isEmpty(), seat + " floor");
                check(h, level.noCollision(new net.minecraft.world.phys.AABB(p.x - .3, p.y + 1.0, p.z - .3, p.x + .3, p.y + 1.8, p.z + .3)), seat + " clear");
            }
            done[0] = true;
            h.succeed();
        });
    }
}
