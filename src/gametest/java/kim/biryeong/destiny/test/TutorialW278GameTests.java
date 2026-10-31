package kim.biryeong.destiny.test;

import kim.biryeong.destiny.tutorial.Tutorial;
import kim.biryeong.destiny.tutorial.TutorialCourse;
import kim.biryeong.destiny.world.TowerSpawnWorld;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.core.BlockPos;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.phys.Vec3;

/** W278 tutorial lane: every checkpoint is a safe arrival, gates close/open, the ledge needs help, the portal is reachable. */
public final class TutorialW278GameTests {
    private static void check(GameTestHelper h, boolean v, String m) { h.assertTrue(v, Component.literal(m)); }

    @GameTest(structure = "destiny-test:floor", maxTicks = 40, environment = "destiny-test:w90_isolated")
    public void laneGeometryAndGates(GameTestHelper h) {
        var server = h.getLevel().getServer();
        TutorialCourse course = Tutorial.testCourse(server);
        TestCleanup.register(h, () -> Tutorial.releaseTestCourse(course));
        var level = course.level();
        check(h, Tutorial.isTutorialLevel(level), "Course lives in the dedicated tutorial world");
        for (Vec3 rel : new Vec3[]{TutorialCourse.SPAWN, TutorialCourse.CLASS_ENTRY, TutorialCourse.LIGHT_ENTRY,
                TutorialCourse.RANGE_ENTRY, TutorialCourse.RUN_ENTRY, TutorialCourse.RUN_RETRY,
                TutorialCourse.ARENA_ENTRY, TutorialCourse.FINALE_ENTRY, TutorialCourse.PORTAL})
            check(h, TowerSpawnWorld.isSafeArrival(level, course.world(rel)), "Safe checkpoint " + rel);
        for (var c : TutorialCourse.CLASSES) check(h, TowerSpawnWorld.isSafeArrival(level, course.world(c.center())), "Class pad " + c.name());
        for (var c : TutorialCourse.SUBCLASSES) check(h, TowerSpawnWorld.isSafeArrival(level, course.world(c.center())), "Light pad " + c.name());
        for (var gate : TutorialCourse.Gate.values()) {
            BlockPos pos = BlockPos.containing(course.gateCenter(gate));
            check(h, level.getBlockState(pos).is(Blocks.TINTED_GLASS), gate + " starts closed");
            course.open(gate);
            check(h, level.getBlockState(pos).isAir(), gate + " opens");
            course.close(gate);
        }
        check(h, level.getBlockState(BlockPos.containing(course.world(new Vec3(.5, -1, 128.5)))).isAir(), "Chasm is open");
        check(h, TowerSpawnWorld.isSafeArrival(level, course.world(TutorialCourse.FAR_SIDE)), "Far side is standable");
        check(h, course.acrossChasm(course.world(TutorialCourse.FAR_SIDE)), "Far side is detected");
        check(h, TowerSpawnWorld.isSafeArrival(level, course.world(new Vec3(.5, 0, 140.5))), "One-block step back up to the arena");
        Vec3 bridge = course.world(new Vec3(.5, -1, 128.5));
        course.fallbackBridge(true);
        check(h, TowerSpawnWorld.isSafeArrival(level, bridge), "Fallback bridge carries the player");
        course.fallbackBridge(false);
        check(h, !TowerSpawnWorld.isSafeArrival(level, bridge), "Fallback bridge retracts");
        check(h, level.getBlockState(BlockPos.containing(course.world(new Vec3(.5, -1, 118.5)))).isAir(), "Sprint gap is open");
        check(h, course.inPortal(course.world(TutorialCourse.PORTAL)), "Portal trigger covers the portal");
        check(h, !level.getBlockState(BlockPos.containing(course.world(new Vec3(.5, .5, 191.5)))).isAir(), "Portal back wall is sealed");
        h.succeed();
    }
}
