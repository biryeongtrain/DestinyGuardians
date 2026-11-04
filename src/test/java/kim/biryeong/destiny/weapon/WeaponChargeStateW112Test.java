package kim.biryeong.destiny.weapon;

import org.junit.jupiter.api.Test;

import static kim.biryeong.destiny.weapon.WeaponChargeState.Phase.*;
import static org.junit.jupiter.api.Assertions.*;

/** Pure state contract only: no Minecraft, runtime shim, wall clock or HUD rendering. */
class WeaponChargeStateW112Test {
    @Test
    void idleHasOnlyTheCanonicalEmptyState() {
        var idle = WeaponChargeState.idle();
        assertEquals(new WeaponChargeState(IDLE, 0, 0, 0), idle);
        assertSame(idle, WeaponChargeState.idle());
        assertEquals(IDLE, idle.phase());
        assertEquals(0f, idle.progress());
        assertEquals(0, idle.emittedBolts());
        assertEquals(0, idle.totalBolts());
        assertThrows(IllegalArgumentException.class, () -> new WeaponChargeState(IDLE, .5f, 0, 0));
        assertThrows(IllegalArgumentException.class, () -> new WeaponChargeState(IDLE, 0, 1, 0));
        assertThrows(IllegalArgumentException.class, () -> new WeaponChargeState(IDLE, 0, 0, 1));
    }

    @Test
    void chargingUsesAcceptedDurationAndSaturatesWithoutLeavingCharging() {
        for (int total = 1; total <= 9; total++) {
            assertEquals(new WeaponChargeState(CHARGING, 0, 0, total), WeaponChargeState.charging(0, 40, total));
            assertEquals(new WeaponChargeState(CHARGING, .25f, 0, total), WeaponChargeState.charging(10, 40, total));
            assertEquals(new WeaponChargeState(CHARGING, .5f, 0, total), WeaponChargeState.charging(20, 40, total));
            assertEquals(new WeaponChargeState(CHARGING, 1, 0, total), WeaponChargeState.charging(40, 40, total));
            assertEquals(WeaponChargeState.charging(40, 40, total), WeaponChargeState.charging(41, 40, total));
        }
        assertEquals(.125f, WeaponChargeState.charging(1, 8, 1).progress());
        assertEquals(.5f, WeaponChargeState.charging(1, 2, 9).progress());
        assertEquals(1f, WeaponChargeState.charging(1, 1, 1).progress());
    }

    @Test
    void extremeElapsedAndDurationCannotOverflowOrBecomeNonfinite() {
        for (int duration : new int[]{1, 2, 40, Integer.MAX_VALUE}) {
            for (long elapsed : new long[]{0, 1, 2, 39, 40, Integer.MAX_VALUE, (long) Integer.MAX_VALUE + 1, Long.MAX_VALUE}) {
                var state = WeaponChargeState.charging(elapsed, duration, 9);
                assertTrue(Float.isFinite(state.progress()));
                assertTrue(state.progress() >= 0 && state.progress() <= 1);
                assertEquals((float) Math.min(1d, (double) elapsed / duration), state.progress(), 1e-7f);
                if (elapsed >= duration) assertEquals(1f, state.progress());
            }
        }
        assertTrue(WeaponChargeState.charging(1, Integer.MAX_VALUE, 9).progress() > 0);
    }

    @Test
    void chargeProgressIsMonotonicAndSnapshotsDoNotAdvanceThemselves() {
        var captured = WeaponChargeState.charging(7, 80, 9);
        for (int duration : new int[]{1, 3, 20, 80, 1000}) {
            float previous = 0;
            for (long elapsed = 0; elapsed <= duration + 1; elapsed++) {
                float current = WeaponChargeState.charging(elapsed, duration, 9).progress();
                assertTrue(current >= previous);
                previous = current;
            }
        }
        assertEquals(new WeaponChargeState(CHARGING, .0875f, 0, 9), captured);
    }

    @Test
    void invalidElapsedDurationAndChargingCountsAreRejected() {
        for (long elapsed : new long[]{-1, Long.MIN_VALUE})
            assertThrows(IllegalArgumentException.class, () -> WeaponChargeState.charging(elapsed, 40, 9));
        for (int duration : new int[]{0, -1, Integer.MIN_VALUE})
            assertThrows(IllegalArgumentException.class, () -> WeaponChargeState.charging(0, duration, 9));
        for (int total : new int[]{Integer.MIN_VALUE, -1, 0, 10, Integer.MAX_VALUE}) {
            assertThrows(IllegalArgumentException.class, () -> WeaponChargeState.charging(0, 40, total));
            assertThrows(IllegalArgumentException.class, () -> new WeaponChargeState(CHARGING, .5f, 0, total));
        }
        for (int emitted : new int[]{Integer.MIN_VALUE, -1, 1, 9, Integer.MAX_VALUE})
            assertThrows(IllegalArgumentException.class, () -> new WeaponChargeState(CHARGING, .5f, emitted, 9));
    }

    @Test
    void allPhasesRejectNonfiniteAndOutOfRangeProgressAndMissingPhase() {
        for (float progress : new float[]{Float.NaN, Float.POSITIVE_INFINITY, Float.NEGATIVE_INFINITY,
                -Float.MIN_VALUE, -1, Math.nextUp(1f), Float.MAX_VALUE}) {
            assertThrows(IllegalArgumentException.class, () -> new WeaponChargeState(IDLE, progress, 0, 0));
            assertThrows(IllegalArgumentException.class, () -> new WeaponChargeState(CHARGING, progress, 0, 9));
            assertThrows(IllegalArgumentException.class, () -> new WeaponChargeState(BURSTING, progress, 1, 9));
        }
        assertThrows(IllegalArgumentException.class, () -> new WeaponChargeState(null, 0, 0, 0));
        assertEquals(Float.MIN_VALUE, new WeaponChargeState(CHARGING, Float.MIN_VALUE, 0, 1).progress());
        assertEquals(Math.nextDown(1f), new WeaponChargeState(CHARGING, Math.nextDown(1f), 0, 9).progress());
    }

    @Test
    void everyUnfinishedBurstHasStrictlyDecreasingRemainingBoltsIncludingMaximumNine() {
        for (int total = 2; total <= 9; total++) {
            int previousRemaining = total;
            for (int emitted = 1; emitted < total; emitted++) {
                var state = WeaponChargeState.bursting(emitted, total);
                assertEquals(new WeaponChargeState(BURSTING, 1, emitted, total), state);
                assertEquals(1f, state.progress());
                int remaining = state.totalBolts() - state.emittedBolts();
                assertEquals(previousRemaining - 1, remaining);
                assertTrue(remaining > 0);
                previousRemaining = remaining;
            }
            assertEquals(1, previousRemaining);
        }
        assertEquals(8, WeaponChargeState.bursting(1, 9).totalBolts() - 1);
        assertEquals(8, WeaponChargeState.bursting(8, 9).emittedBolts());
    }

    @Test
    void burstCannotRepresentNoShotCompletedBurstOrSingleBoltShot() {
        for (int total : new int[]{Integer.MIN_VALUE, -1, 0, 1, 10, Integer.MAX_VALUE})
            assertThrows(IllegalArgumentException.class, () -> WeaponChargeState.bursting(1, total));
        for (int total = 2; total <= 9; total++) {
            int bolts = total;
            for (int emitted : new int[]{Integer.MIN_VALUE, -1, 0, total, total + 1, Integer.MAX_VALUE}) {
                assertThrows(IllegalArgumentException.class, () -> WeaponChargeState.bursting(emitted, bolts));
                assertThrows(IllegalArgumentException.class, () -> new WeaponChargeState(BURSTING, 1, emitted, bolts));
            }
        }
        for (float progress : new float[]{0, .5f, Math.nextDown(1f)})
            assertThrows(IllegalArgumentException.class, () -> new WeaponChargeState(BURSTING, progress, 1, 9));
    }
}
