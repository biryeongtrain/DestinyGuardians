package kim.biryeong.destiny.inventory;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class WeaponScreenControlsW227Test {
    @Test void yawWrapDoesNotTeleportCursorAcrossScreen() {
        var c = new WeaponScreenControls(); c.point(960, 540); c.baseline(179, 0);
        assertTrue(c.rotate(-179, 0)); assertEquals(990, c.x()); assertEquals(540, c.y());
        c.rotate(179, 0); assertEquals(960, c.x());
    }
    @Test void badRotationCannotPoisonFutureInput() {
        var c = new WeaponScreenControls(); c.point(500, 300); c.baseline(0, 0);
        assertFalse(c.rotate(Float.NaN, 0)); assertFalse(c.rotate(0, Float.POSITIVE_INFINITY));
        c.rotate(1, 1); assertEquals(515, c.x()); assertEquals(315, c.y());
    }
    @Test void cursorClampsAndKeyboardPointingDoesNotResetMouseBaseline() {
        var c = new WeaponScreenControls(); c.baseline(0, 0); c.point(9000, -9000);
        assertEquals(1896, c.x()); assertEquals(24, c.y());
        c.point(600, 400); c.rotate(-1, 2); assertEquals(585, c.x()); assertEquals(430, c.y());
    }
}
