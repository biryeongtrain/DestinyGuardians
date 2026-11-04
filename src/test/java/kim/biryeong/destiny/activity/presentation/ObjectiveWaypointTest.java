package kim.biryeong.destiny.activity.presentation;

import net.minecraft.world.phys.Vec3;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;

class ObjectiveWaypointTest {
    @Test void farTargetsAreClampedAndKeepScreenSize() {
        Vec3 eye = new Vec3(0, 0, 0);
        double[] far = ObjectiveWaypoint.place(eye, new Vec3(0, 0, 100));
        double[] farther = ObjectiveWaypoint.place(eye, new Vec3(0, 0, 400));
        assertEquals(ObjectiveWaypoint.CLAMP, far[2], 1e-9);
        assertEquals(far[3], farther[3], 1e-9, "same on-screen size beyond the clamp");
        double[] near = ObjectiveWaypoint.place(eye, new Vec3(0, 0, 8));
        assertEquals(8, near[2], 1e-9);
        assertEquals(far[3] * 8 / ObjectiveWaypoint.CLAMP, near[3], 1e-9, "scale grows with distance up close");
    }

    @Test void labelIsWholeMetres() {
        assertEquals("42m", ObjectiveWaypoint.label(41.6));
        assertEquals("0m", ObjectiveWaypoint.label(-1));
    }
}
