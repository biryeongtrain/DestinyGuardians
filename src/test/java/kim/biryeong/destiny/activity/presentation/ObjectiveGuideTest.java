package kim.biryeong.destiny.activity.presentation;

import kim.biryeong.destiny.activity.presentation.ObjectiveGuide.Mode;
import net.minecraft.world.phys.Vec3;
import org.junit.jupiter.api.Test;

import java.util.ArrayList;
import java.util.List;

import static org.junit.jupiter.api.Assertions.*;

class ObjectiveGuideTest {
    @Test void travelShowsMarkerSoonAndSoftTrail() {
        assertFalse(ObjectiveGuide.decide(Mode.TRAVEL, 10, 10, 30)[0]);
        var s = ObjectiveGuide.decide(Mode.TRAVEL, 60, 60, 60);
        assertTrue(s[0]); assertTrue(s[1]); assertFalse(s[2]);
    }

    @Test void combatStaysCleanUntilLost() {
        var s = ObjectiveGuide.decide(Mode.COMBAT, 400, 400, 60);
        assertFalse(s[0]); assertFalse(s[1]);
        var lost = ObjectiveGuide.decide(Mode.COMBAT, 600, ObjectiveGuide.LOST, 600);
        assertTrue(lost[0]); assertTrue(lost[1]); assertTrue(lost[2]);
    }

    @Test void trailFollowsRouteAndFallsBackToStraightLine() {
        var route = GuideRoute.of(List.of(new Vec3(0, 60, 0), new Vec3(10, 60, 0), new Vec3(10, 60, 10)));
        var jumps = new ArrayList<Vec3>();
        var path = GuideTrail.path(route, new Vec3(-1, 60, 0), new Vec3(10, 60, 10), jumps);
        assertEquals(new Vec3(10, 60, 10), path.getLast());
        var straight = GuideTrail.path(null, Vec3.ZERO, new Vec3(0, 0, 40), null);
        assertEquals(GuideTrail.STRAIGHT, straight.getLast().z, 1e-9);
    }
}
