package kim.biryeong.destiny.camera;

import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;

class CameraMathTest {
    private static final double EPS = 1e-9;
    private static final float INPUT_EPS = 1e-6f;

    private static void point(double x, double y, double z, CameraMath.Point actual) {
        assertEquals(x, actual.x(), EPS);
        assertEquals(y, actual.y(), EPS);
        assertEquals(z, actual.z(), EPS);
    }

    private static void vector(float strafe, float forward, CameraMath.InputVector actual) {
        assertEquals(strafe, actual.strafe(), INPUT_EPS);
        assertEquals(forward, actual.forward(), INPUT_EPS);
    }

    @Test void fourHeadingsUseEyeRelativeRearAndRightShoulder() {
        point(9.55, 64.25, 17, CameraMath.desired(10, 64, 20, 0, 0));
        point(13, 64.25, 19.55, CameraMath.desired(10, 64, 20, 90, 0));
        point(10.45, 64.25, 23, CameraMath.desired(10, 64, 20, 180, 0));
        point(7, 64.25, 20.45, CameraMath.desired(10, 64, 20, 270, 0));
    }

    @Test void positivePitchLooksDownSoRearCameraMovesUp() {
        double rear = 3 / Math.sqrt(2);
        point(-0.45, rear + 0.25, -rear, CameraMath.desired(0, 0, 0, 0, 45));
        point(-0.45, -rear + 0.25, -rear, CameraMath.desired(0, 0, 0, 0, -45));
    }

    @Test void verticalPitchKeepsYawBasedShoulderAndClampsAtNinety() {
        point(-0.45, 3.25, 0, CameraMath.desired(0, 0, 0, 0, 90));
        point(-0.45, -2.75, 0, CameraMath.desired(0, 0, 0, 0, -90));
        point(0, 3.25, -0.45, CameraMath.desired(0, 0, 0, 90, 120));
        point(0, -2.75, -0.45, CameraMath.desired(0, 0, 0, 90, -120));
        point(-0.45, 3.25, 0, CameraMath.desired(0, 0, 0, 0, Float.MAX_VALUE));
        point(-0.45, -2.75, 0, CameraMath.desired(0, 0, 0, 0, -Float.MAX_VALUE));
    }

    @Test void fullLookRearDistanceAndShoulderStayConstantAtAllPitches() {
        for (float yaw : new float[]{0, 37, 90, 180, 270}) {
            for (float pitch : new float[]{-90, -45, 0, 45, 90}) {
                var p = CameraMath.desired(10, 64, -20, yaw, pitch);
                double y = Math.toRadians(yaw), a = Math.toRadians(pitch);
                double xOffset = p.x() - 10, yOffset = p.y() - 64 - 0.25, zOffset = p.z() + 20;
                double alongLook = xOffset * -Math.sin(y) * Math.cos(a)
                        + yOffset * -Math.sin(a) + zOffset * Math.cos(y) * Math.cos(a);
                double alongRight = xOffset * -Math.cos(y) + zOffset * -Math.sin(y);
                assertEquals(-3, alongLook, EPS, "Rear distance uses the complete unit look vector");
                assertEquals(0.45, alongRight, EPS, "Shoulder does not depend on pitch");
                assertEquals(Math.hypot(3, 0.45),
                        Math.sqrt(xOffset * xOffset + yOffset * yOffset + zOffset * zOffset), EPS);
            }
        }
    }

    @Test void yawWrapsAndFiniteExtremeYawRemainsBounded() {
        point(-0.45, 0.25, -3, CameraMath.desired(0, 0, 0, 720, 0));
        point(-3, 0.25, 0.45, CameraMath.desired(0, 0, 0, -90, 0));
        for (float yaw : new float[]{Float.MAX_VALUE, -Float.MAX_VALUE}) {
            var p = CameraMath.desired(0, 0, 0, yaw, 25);
            assertTrue(Double.isFinite(p.x()) && Double.isFinite(p.y()) && Double.isFinite(p.z()));
            assertTrue(Math.abs(p.x()) <= 3.45 && Math.abs(p.z()) <= 3.45);
        }
    }

    @Test void nonfiniteEyeCoordinatesAreRejectedOnEveryAxis() {
        for (double bad : new double[]{Double.NaN, Double.POSITIVE_INFINITY, Double.NEGATIVE_INFINITY}) {
            assertThrows(IllegalArgumentException.class, () -> CameraMath.desired(bad, 0, 0, 0, 0));
            assertThrows(IllegalArgumentException.class, () -> CameraMath.desired(0, bad, 0, 0, 0));
            assertThrows(IllegalArgumentException.class, () -> CameraMath.desired(0, 0, bad, 0, 0));
        }
    }

    @Test void nonfiniteAnglesAreRejectedBeforePitchClamping() {
        for (float bad : new float[]{Float.NaN, Float.POSITIVE_INFINITY, Float.NEGATIVE_INFINITY}) {
            assertThrows(IllegalArgumentException.class, () -> CameraMath.desired(0, 0, 0, bad, 0));
            assertThrows(IllegalArgumentException.class, () -> CameraMath.desired(0, 0, 0, 0, bad));
        }
    }

    @Test void cardinalInputUsesVanillaSignsAndIdleIsZero() {
        vector(0, 0, CameraMath.input(false, false, false, false, false));
        vector(0, 1, CameraMath.input(true, false, false, false, false));
        vector(0, -1, CameraMath.input(false, true, false, false, false));
        vector(1, 0, CameraMath.input(false, false, true, false, false));
        vector(-1, 0, CameraMath.input(false, false, false, true, false));
    }

    @Test void allFourDiagonalsAreNormalized() {
        float diagonal = (float) (1 / Math.sqrt(2));
        vector(diagonal, diagonal, CameraMath.input(true, false, true, false, false));
        vector(-diagonal, diagonal, CameraMath.input(true, false, false, true, false));
        vector(diagonal, -diagonal, CameraMath.input(false, true, true, false, false));
        vector(-diagonal, -diagonal, CameraMath.input(false, true, false, true, false));
    }

    @Test void oppositeKeysCancelBeforeNormalizingRemainingAxis() {
        vector(0, 0, CameraMath.input(true, true, true, true, false));
        vector(1, 0, CameraMath.input(true, true, true, false, false));
        vector(-1, 0, CameraMath.input(true, true, false, true, false));
        vector(0, 1, CameraMath.input(true, false, true, true, false));
        vector(0, -1, CameraMath.input(false, true, true, true, false));
    }

    @Test void crouchScalesCardinalAndDiagonalSpeedToPointThree() {
        vector(0, 0.3f, CameraMath.input(true, false, false, false, true));
        vector(-0.3f, 0, CameraMath.input(false, false, false, true, true));
        float diagonal = (float) (0.3 / Math.sqrt(2));
        vector(diagonal, diagonal, CameraMath.input(true, false, true, false, true));
        vector(0, 0, CameraMath.input(true, true, true, true, true));
    }

    @Test void everyKeyCombinationIsBoundedAndCrouchIsOnlyAScale() {
        for (int keys = 0; keys < 16; keys++) {
            boolean forward = (keys & 1) != 0, backward = (keys & 2) != 0;
            boolean left = (keys & 4) != 0, right = (keys & 8) != 0;
            var normal = CameraMath.input(forward, backward, left, right, false);
            var crouch = CameraMath.input(forward, backward, left, right, true);
            boolean idle = forward == backward && left == right;
            assertEquals(idle ? 0 : 1, Math.hypot(normal.strafe(), normal.forward()), INPUT_EPS);
            assertEquals(idle ? 0 : 0.3, Math.hypot(crouch.strafe(), crouch.forward()), INPUT_EPS);
            vector(normal.strafe() * 0.3f, normal.forward() * 0.3f, crouch);
        }
    }
}
