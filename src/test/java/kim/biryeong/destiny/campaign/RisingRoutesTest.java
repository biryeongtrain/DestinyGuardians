package kim.biryeong.destiny.campaign;

import kim.biryeong.destiny.activity.presentation.GuideRoute;

import kim.biryeong.destiny.campaign.RisingServices.Zone;
import net.minecraft.world.phys.Vec3;
import org.junit.jupiter.api.Test;

import java.io.StringReader;
import java.util.List;

import static org.junit.jupiter.api.Assertions.*;

class RisingRoutesTest {
    static final String JSON = """
            {"schema":1,"zones":{
              "gateway":{"waypoints":[
                {"pos":[0,64,0],"jump":false,"objective":"spawn.player"},
                {"pos":[0,64,4],"jump":false},{"pos":[0,65,8],"jump":true},{"pos":[0,66,12],"jump":false},
                {"pos":[4,66,12],"jump":false},{"pos":[8,66,12],"jump":false},{"pos":[12,66,12],"jump":false},
                {"pos":[16,66,12],"jump":false,"objective":"exit.breach"}]},
              "breach":{"waypoints":[{"pos":[1,2,3]}]},
              "divide":{"waypoints":[{"pos":[0,0,0]},{"pos":["x",0,0]}]}
            }}""";

    static GuideRoute gateway() { return RisingRoutes.parse(new StringReader(JSON)).get(Zone.GATEWAY); }

    @Test void parsesZonesSkipsUnusableAndOffsetsToWorld() {
        var routes = RisingRoutes.parse(new StringReader(JSON));
        assertEquals(java.util.Set.of(Zone.GATEWAY), routes.keySet(), "one-point and broken routes are dropped");
        var r = routes.get(Zone.GATEWAY);
        assertEquals(8, r.points().size());
        assertTrue(r.points().get(2).jump());
        assertEquals("exit.breach", r.points().get(7).objective());
        var world = r.offset(new Vec3(2048, 64, 2048));
        assertEquals(new Vec3(2048, 128, 2052), world.points().get(1).pos());
    }

    @Test void bundledLoaderNeverThrows() {
        var routes = RisingRoutes.bundled();
        routes.values().forEach(r -> assertTrue(r.usable()));
    }

    @Test void nearestWeightsHeightSoStackedFloorsDoNotSnap() {
        var r = new GuideRoute(List.of(
                new GuideRoute.Point(new Vec3(0, 60, 0), false, null),
                new GuideRoute.Point(new Vec3(3, 70, 0), false, null)));
        // Horizontally closer to the upper point, but standing on the lower floor.
        assertEquals(0, r.nearest(new Vec3(2.5, 60, 0)));
        assertEquals(1, r.nearest(new Vec3(2.5, 70, 0)));
    }

    @Test void sectionFollowsRouteAroundCornerAndIsCapped() {
        var r = gateway();
        Vec3 target = new Vec3(16, 66, 12);
        // Player at the start: straight line would cut across; the section turns the corner instead.
        var s = r.section(new Vec3(0, 64, 0.5), target, 5, 100);
        // The player already stepped past waypoint 0, so the trail starts at waypoint 1.
        assertEquals(List.of(new Vec3(0, 64, 4), new Vec3(0, 65, 8), new Vec3(0, 66, 12),
                new Vec3(4, 66, 12), new Vec3(8, 66, 12), new Vec3(12, 66, 12)), s.stream().map(GuideRoute.Point::pos).toList());
        assertTrue(s.get(1).jump(), "jump flag survives into the section");
        // Length cap stops early.
        var shortS = r.section(new Vec3(0, 64, 0.5), target, 5, 7);
        assertEquals(new Vec3(0, 65, 8), shortS.getLast().pos());
        // Never runs past the objective's waypoint.
        var end = r.section(new Vec3(9, 66, 12), target, 5, 100);
        assertEquals(target, end.getLast().pos());
    }

    @Test void sectionDropsWaypointAlreadyPassedAndWalksBackwards() {
        var r = gateway();
        // Between waypoint 1 (z=4) and 2 (z=8), nearer 1 but already past it.
        var ahead = r.section(new Vec3(0, 64, 5.5), new Vec3(16, 66, 12), 3, 100);
        assertEquals(new Vec3(0, 65, 8), ahead.getFirst().pos());
        // Target behind: walk the route in reverse.
        var back = r.section(new Vec3(12, 66, 12), new Vec3(0, 64, 0), 3, 100);
        assertEquals(new Vec3(12, 66, 12), back.getFirst().pos());
        assertEquals(new Vec3(0, 66, 12), back.getLast().pos());
        // Already at the target's waypoint, or no target: nothing to draw.
        assertTrue(r.section(new Vec3(16, 66, 12), new Vec3(16.5, 66, 12), 3, 100).isEmpty());
        assertTrue(r.section(new Vec3(0, 64, 0), null, 3, 100).isEmpty());
    }

    @Test void softGuideOnlyForPlacesToWalkTo() {
        assertTrue(RisingObjectives.softGuide(RisingMission.Hint.MOVE));
        assertTrue(RisingObjectives.softGuide(RisingMission.Hint.GRAB));
        assertFalse(RisingObjectives.softGuide(RisingMission.Hint.FIGHT));
        assertFalse(RisingObjectives.softGuide(RisingMission.Hint.FIRE));
        assertTrue(RisingObjectives.WEAK_HINT < 20 * 20 && RisingObjectives.STRONG_HINT < 20 * 45);
    }

    @org.junit.jupiter.api.Test void compactArrayFormatParsesAndBundledRoutesLoad() {
        var routes = RisingRoutes.parse(new java.io.StringReader(
                "{\"zones\":{\"gateway\":[[1,2,3,0],[4,2,3,1],[\"bad\"],[7,2,3,0]]}}"));
        var r = routes.get(kim.biryeong.destiny.campaign.RisingServices.Zone.GATEWAY);
        org.junit.jupiter.api.Assertions.assertNotNull(r);
        org.junit.jupiter.api.Assertions.assertEquals(3, r.points().size());
        org.junit.jupiter.api.Assertions.assertTrue(r.points().get(1).jump());
        var bundled = RisingRoutes.bundled();
        org.junit.jupiter.api.Assertions.assertEquals(4, bundled.size(), "all four zones ship a usable route");
    }
}
