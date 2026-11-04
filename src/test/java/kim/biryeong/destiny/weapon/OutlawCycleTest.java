package kim.biryeong.destiny.weapon;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class OutlawCycleTest {
    private static final int DURATION = 120;

    @Test void freshCycleAndQueriesNeverCreateOutlawTime() {
        var cycle = new OutlawCycle();
        for (long tick : new long[]{0, 1, 119, 120, 100000, Long.MAX_VALUE}) {
            assertEquals(0, cycle.remaining(tick, DURATION));
            assertEquals(0, cycle.remaining(tick, DURATION));
        }
    }

    @Test void precisionFinalBlowHasExactlyOneHundredTwentyTicks() {
        var cycle = new OutlawCycle(); cycle.precisionKilled(40, DURATION);
        assertEquals(120, cycle.remaining(40, DURATION));
        assertEquals(119, cycle.remaining(41, DURATION));
        assertEquals(1, cycle.remaining(159, DURATION));
        assertEquals(0, cycle.remaining(160, DURATION));
        assertEquals(0, cycle.remaining(161, DURATION));
    }

    @Test void repeatedReadsNeitherConsumeNorRefreshTheWindow() {
        var cycle = new OutlawCycle(); cycle.precisionKilled(0, DURATION);
        for (int tick = 0; tick <= DURATION + 2; tick++) {
            for (int read = 0; read < 8; read++)
                assertEquals(Math.max(0, DURATION - tick), cycle.remaining(tick, DURATION));
        }
    }

    @Test void anotherPrecisionKillRefreshesFromThatTickInsteadOfAddingDuration() {
        var cycle = new OutlawCycle(); cycle.precisionKilled(10, DURATION);
        assertEquals(40, cycle.remaining(90, DURATION));
        cycle.precisionKilled(90, DURATION);
        assertEquals(120, cycle.remaining(90, DURATION));
        cycle.precisionKilled(90, DURATION);
        assertEquals(120, cycle.remaining(90, DURATION));
        assertEquals(1, cycle.remaining(209, DURATION));
        assertEquals(0, cycle.remaining(210, DURATION));
    }

    @Test void aFreshFinalBlowCanActivateAgainAfterThePreviousWindowExpired() {
        var cycle = new OutlawCycle(); cycle.precisionKilled(0, DURATION);
        assertEquals(0, cycle.remaining(500, DURATION));
        cycle.precisionKilled(500, DURATION);
        assertEquals(120, cycle.remaining(500, DURATION));
        assertEquals(1, cycle.remaining(619, DURATION));
        assertEquals(0, cycle.remaining(620, DURATION));
    }

    @Test void negativeOrPreKillQueriesAreInertAndDoNotDestroyValidTime() {
        var cycle = new OutlawCycle(); cycle.precisionKilled(100, DURATION);
        assertEquals(0, cycle.remaining(-1, DURATION));
        assertEquals(0, cycle.remaining(0, DURATION));
        assertEquals(0, cycle.remaining(99, DURATION));
        assertEquals(120, cycle.remaining(100, DURATION));
        assertEquals(60, cycle.remaining(160, DURATION));
    }

    @Test void invalidDurationsAreRejectedWithoutMutatingAnExistingWindow() {
        var cycle = new OutlawCycle(); cycle.precisionKilled(10, DURATION);
        for (int bad : new int[]{Integer.MIN_VALUE, -1, 0, 1201, Integer.MAX_VALUE}) {
            assertThrows(IllegalArgumentException.class, () -> cycle.precisionKilled(20, bad));
            assertEquals(0, cycle.remaining(20, bad));
            assertEquals(110, cycle.remaining(20, DURATION));
        }
        var minimum = new OutlawCycle(); minimum.precisionKilled(0, 1);
        assertEquals(1, minimum.remaining(0, 1));
        assertEquals(0, minimum.remaining(1, 1));
        var maximum = new OutlawCycle(); maximum.precisionKilled(0, 1200);
        assertEquals(1200, maximum.remaining(0, 1200));
        assertEquals(0, maximum.remaining(1200, 1200));
    }

    @Test void invalidKillTicksClearOldTimeAndOverflowBoundaryIsExact() {
        var cycle = new OutlawCycle();
        for (long bad : new long[]{Long.MIN_VALUE, -1, Long.MAX_VALUE - DURATION + 1, Long.MAX_VALUE}) {
            cycle.precisionKilled(10, DURATION);
            cycle.precisionKilled(bad, DURATION);
            assertEquals(0, cycle.remaining(10, DURATION));
            assertEquals(0, cycle.remaining(Math.max(0, bad), DURATION));
        }
        cycle.precisionKilled(Long.MAX_VALUE - DURATION, DURATION);
        assertEquals(DURATION, cycle.remaining(Long.MAX_VALUE - DURATION, DURATION));
        assertEquals(1, cycle.remaining(Long.MAX_VALUE - 1, DURATION));
        assertEquals(0, cycle.remaining(Long.MAX_VALUE, DURATION));
    }
}
