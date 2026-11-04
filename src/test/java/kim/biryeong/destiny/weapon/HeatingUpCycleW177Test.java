package kim.biryeong.destiny.weapon;

import org.junit.jupiter.api.Test;
import java.util.Random;
import static org.junit.jupiter.api.Assertions.*;

class HeatingUpCycleW177Test {
    @Test void startsNeutralAndInvalidEventsDoNotGrant() {
        var cycle = new HeatingUpCycle();
        for (long tick : new long[]{Long.MIN_VALUE, -1, 0, 110, Long.MAX_VALUE}) {
            assertEquals(0, cycle.stacks(tick));
            assertEquals(0, cycle.remaining(tick));
        }
        assertFalse(cycle.killed(-1));
        assertFalse(cycle.killed(Long.MIN_VALUE));
        assertFalse(cycle.killed(Long.MAX_VALUE));
        assertTrue(cycle.killed(0));
        assertEquals(1, cycle.stacks(0));
        assertEquals(110, cycle.remaining(0));
    }

    @Test void everyAcceptedKillRefreshesTheWholeWindowEvenAtCap() {
        var cycle = new HeatingUpCycle();
        assertTrue(cycle.killed(10));
        assertEquals(1, cycle.stacks(119));
        assertEquals(1, cycle.remaining(119));
        assertTrue(cycle.killed(119));
        assertEquals(2, cycle.stacks(119));
        assertEquals(110, cycle.remaining(119));
        assertTrue(cycle.killed(228));
        assertEquals(2, cycle.stacks(337));
        assertEquals(1, cycle.remaining(337));
        assertEquals(0, cycle.stacks(338));
        assertEquals(0, cycle.remaining(338));
    }

    @Test void expiryIsAllAtOnceAndKillAtExactDeadlineStartsAtOne() {
        var cycle = new HeatingUpCycle();
        cycle.killed(0); cycle.killed(1);
        assertEquals(2, cycle.stacks(110));
        assertEquals(0, cycle.stacks(111));
        assertTrue(cycle.killed(111));
        assertEquals(1, cycle.stacks(111));
        assertEquals(110, cycle.remaining(111));
        assertTrue(cycle.killed(1000));
        assertEquals(1, cycle.stacks(1000));
    }

    @Test void distinctFinalBlowsAtSameTickCanReachTwoButNeverExceedIt() {
        var cycle = new HeatingUpCycle();
        for (int n = 1; n <= 10; n++) {
            assertTrue(cycle.killed(50));
            assertEquals(Math.min(n, 2), cycle.stacks(50));
            assertEquals(110, cycle.remaining(50));
        }
        assertEquals(0, cycle.stacks(160));
    }

    @Test void queriesArePureIncludingExpiryFutureAndBackwardProbes() {
        var cycle = new HeatingUpCycle();
        cycle.killed(100);
        for (int n = 0; n < 10; n++) {
            assertEquals(0, cycle.stacks(99));
            assertEquals(0, cycle.remaining(-1));
            assertEquals(0, cycle.stacks(210));
            assertEquals(0, cycle.remaining(Long.MAX_VALUE));
            assertEquals(1, cycle.stacks(100));
            assertEquals(110, cycle.remaining(100));
        }
        assertTrue(cycle.killed(101)); // observations cannot advance the event clock
        assertEquals(2, cycle.stacks(101));
        assertEquals(110, cycle.remaining(101));
    }

    @Test void backwardAndOverflowKillsRejectWithoutChangingStateOrDeadline() {
        var cycle = new HeatingUpCycle();
        cycle.killed(100);
        for (long tick : new long[]{-1, Long.MIN_VALUE, 99, Long.MAX_VALUE, Long.MAX_VALUE - 109}) {
            assertFalse(cycle.killed(tick));
            assertEquals(1, cycle.stacks(100));
            assertEquals(110, cycle.remaining(100));
            assertEquals(1, cycle.remaining(209));
            assertEquals(0, cycle.stacks(210));
        }
        assertTrue(cycle.killed(100));
        assertEquals(2, cycle.stacks(100));
    }

    @Test void lastSafeDeadlineDoesNotWrapAndExpiresExactly() {
        var cycle = new HeatingUpCycle();
        long tick = Long.MAX_VALUE - 110;
        assertTrue(cycle.killed(tick));
        assertEquals(110, cycle.remaining(tick));
        assertFalse(cycle.killed(tick + 1));
        assertEquals(1, cycle.stacks(Long.MAX_VALUE - 1));
        assertEquals(1, cycle.remaining(Long.MAX_VALUE - 1));
        assertEquals(0, cycle.stacks(Long.MAX_VALUE));
        assertEquals(0, cycle.remaining(Long.MAX_VALUE));
        assertTrue(cycle.killed(tick));
        assertEquals(2, cycle.stacks(tick));
    }

    @Test void stowedIdleTimeKeepsStacksWithoutPausingOrRefreshing() {
        var cycle = new HeatingUpCycle();
        cycle.killed(20); cycle.killed(30);
        // There is no stow reset: master retains this source's cycle while the clock continues.
        assertEquals(2, cycle.stacks(80));
        assertEquals(60, cycle.remaining(80));
        assertEquals(2, cycle.stacks(139));
        assertEquals(0, cycle.stacks(140));
    }

    @Test void deterministicMixedScheduleMatchesIndependentDeadlineModel() {
        var cycle = new HeatingUpCycle();
        var random = new Random(177);
        long tick = 0, lastKill = -1, deadline = -1;
        int count = 0;
        for (int n = 0; n < 10000; n++) {
            tick += random.nextInt(160);
            if (random.nextBoolean()) {
                count = tick >= deadline ? 1 : Math.min(2, count + 1);
                assertTrue(cycle.killed(tick));
                lastKill = tick;
                deadline = tick + 110;
            }
            int expected = tick >= lastKill && tick < deadline ? count : 0;
            assertEquals(expected, cycle.stacks(tick));
            assertEquals(expected == 0 ? 0 : (int) (deadline - tick), cycle.remaining(tick));
            assertEquals(0, cycle.stacks(Long.MAX_VALUE));
            if (lastKill > 0) {
                assertFalse(cycle.killed(lastKill - 1));
                assertEquals(0, cycle.stacks(lastKill - 1));
            }
        }
    }
}
