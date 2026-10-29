package kim.biryeong.destiny.weapon;

import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

class WeaponNativeZoomW244Test {
    @Test void lowZoomInterpolatesFromHipToFullAds() {
        assertEquals(1, WeaponNativeZoom.movementScalar(.8, 1.25, 0));
        assertEquals(.82, WeaponNativeZoom.movementScalar(.8, 1.25, .5), 1e-12);
        assertEquals(.64, WeaponNativeZoom.movementScalar(.8, 1.25, 1), 1e-12);
    }

    @Test void highZoomKeepsBothTransitionDirectionsOnTheSameCurve() {
        assertEquals(1, WeaponNativeZoom.movementScalar(.8, 4, 0));
        assertEquals(.4, WeaponNativeZoom.movementScalar(.8, 4, .75), 1e-12);
        assertEquals(.8, WeaponNativeZoom.movementScalar(.8, 4, .25), 1e-12);
        assertEquals(.2, WeaponNativeZoom.movementScalar(.8, 4, 1), 1e-12);
    }

    @Test void finiteProgressIsClampedAndZoomBelowOneCannotIncreaseMovement() {
        assertEquals(1, WeaponNativeZoom.movementScalar(.8, 4, -2));
        assertEquals(.2, WeaponNativeZoom.movementScalar(.8, 4, 2), 1e-12);
        assertEquals(.8, WeaponNativeZoom.movementScalar(.8, .5, 1));
        assertEquals(.8, WeaponNativeZoom.movementScalar(.8, 0, 1));
        assertEquals(.8, WeaponNativeZoom.movementScalar(.8, -2, 1));
        assertEquals(1, WeaponNativeZoom.movementScalar(1, 1, .5));
    }

    @Test void rejectsBaseOutsideThePositiveUnitIntervalEvenAtHip() {
        assertThrows(IllegalArgumentException.class, () -> WeaponNativeZoom.movementScalar(0, 2, 0));
        assertThrows(IllegalArgumentException.class, () -> WeaponNativeZoom.movementScalar(-.1, 2, 0));
        assertThrows(IllegalArgumentException.class, () -> WeaponNativeZoom.movementScalar(1.01, 2, 0));
    }

    @Test void rejectsNonFiniteInputsBeforeClampingOrEndpointShortcuts() {
        for (double invalid : new double[]{Double.NaN, Double.POSITIVE_INFINITY, Double.NEGATIVE_INFINITY}) {
            assertThrows(IllegalArgumentException.class, () -> WeaponNativeZoom.movementScalar(invalid, 2, 0));
            assertThrows(IllegalArgumentException.class, () -> WeaponNativeZoom.movementScalar(.8, invalid, 0));
            assertThrows(IllegalArgumentException.class, () -> WeaponNativeZoom.movementScalar(.8, 2, invalid));
        }
    }

    @Test void extremeFiniteInputsKeepFullAdsPositiveWithoutCancellation() {
        assertEquals(Double.MIN_VALUE, WeaponNativeZoom.movementScalar(Double.MIN_VALUE, 1, 1));
        assertEquals(Double.MIN_VALUE, WeaponNativeZoom.movementScalar(Double.MIN_VALUE, Double.MAX_VALUE, 1));
        double nearFullAds = WeaponNativeZoom.movementScalar(.8, Double.MAX_VALUE, Math.nextDown(1.0));
        assertTrue(Double.isFinite(nearFullAds) && nearFullAds > 0 && nearFullAds <= 1);
    }
}
