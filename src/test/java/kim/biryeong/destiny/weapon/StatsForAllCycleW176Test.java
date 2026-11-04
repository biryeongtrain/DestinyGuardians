package kim.biryeong.destiny.weapon;

import static org.junit.jupiter.api.Assertions.*;
import org.junit.jupiter.api.Test;
import java.util.*;

class StatsForAllCycleW176Test {
    private static final UUID A = new UUID(1, 1), B = new UUID(2, 2), C = new UUID(3, 3), D = new UUID(4, 4);
    private static StatsForAllCycle active(long tick) {
        var cycle = new StatsForAllCycle();
        assertTrue(cycle.confirmed(tick, A));
        assertTrue(cycle.confirmed(tick, B));
        assertTrue(cycle.confirmed(tick, C));
        return cycle;
    }
    @Test void defaultsMatchProfileAndThreeDistinctSameTickActivate() {
        assertEquals(60, StatsForAllProfile.hitWindowTicks());
        assertEquals(200, StatsForAllProfile.durationTicks());
        var c = new StatsForAllCycle();
        assertEquals(0, c.progress(0)); assertEquals(0, c.remaining(0));
        assertTrue(c.confirmed(0, A)); assertEquals(1, c.progress(0));
        assertTrue(c.confirmed(0, B)); assertEquals(2, c.progress(0));
        assertTrue(c.confirmed(0, C)); assertEquals(0, c.progress(0));
        assertEquals(200, c.remaining(0)); assertEquals(1, c.remaining(199)); assertEquals(0, c.remaining(200));
    }
    @Test void newDistinctTargetRenewsWindowRatherThanFixedFirstHitDeadline() {
        var c = new StatsForAllCycle();
        assertTrue(c.confirmed(0, A)); assertTrue(c.confirmed(59, B));
        assertEquals(2, c.progress(117)); assertTrue(c.confirmed(118, C));
        assertEquals(200, c.remaining(118)); assertEquals(1, c.remaining(317)); assertEquals(0, c.remaining(318));
    }
    @Test void exactCollectionDeadlineIsExpiredAndTargetCanReenter() {
        var c = new StatsForAllCycle();
        assertTrue(c.confirmed(10, A)); assertEquals(1, c.progress(69)); assertEquals(0, c.progress(70));
        assertTrue(c.confirmed(70, A)); assertEquals(1, c.progress(70));
        assertTrue(c.confirmed(129, B));
        assertTrue(c.confirmed(189, C)); assertEquals(1, c.progress(189)); assertEquals(0, c.remaining(189));
    }
    @Test void duplicateUuidValueNeverExtendsDeadlineOrCountsTwice() {
        var c = new StatsForAllCycle();
        assertTrue(c.confirmed(0, A)); assertFalse(c.confirmed(59, new UUID(1, 1)));
        assertEquals(1, c.progress(59)); assertEquals(0, c.progress(60));
        assertTrue(c.confirmed(60, B)); assertEquals(1, c.progress(60));
        assertTrue(c.confirmed(61, C)); assertEquals(2, c.progress(61));
    }
    @Test void activeCannotRefreshOrCollectAnyTargetsAndExpiryStartsFresh() {
        var c = active(100);
        for (int i = 101; i < 300; i++) {
            assertFalse(c.confirmed(i, List.of(A, B, C, D).get(i % 4)));
            assertEquals(300-i, c.remaining(i)); assertEquals(0, c.progress(i));
        }
        assertEquals(0, c.remaining(300)); assertTrue(c.confirmed(300, D));
        assertEquals(1, c.progress(300)); assertEquals(0, c.remaining(300));
        assertTrue(c.confirmed(301, A)); assertTrue(c.confirmed(302, B)); assertEquals(200, c.remaining(302));
    }
    @Test void futureAndBackwardQueriesArePureAndCannotEraseCollectionOrBuff() {
        var c = new StatsForAllCycle();
        c.confirmed(20, A); c.confirmed(21, B);
        for (long tick : new long[]{-1, 0, 19, 1000, Long.MAX_VALUE, Long.MIN_VALUE}) {
            assertEquals(0, c.progress(tick)); assertEquals(0, c.remaining(tick));
        }
        assertEquals(2, c.progress(21)); assertTrue(c.confirmed(22, C));
        assertEquals(0, c.remaining(Long.MAX_VALUE)); assertEquals(200, c.remaining(22));
        assertEquals(1, c.remaining(221)); assertEquals(200, c.remaining(22));
    }
    @Test void invalidNullBackwardAndOverflowEventsNeverMutateClockOrState() {
        var c = new StatsForAllCycle(); c.confirmed(100, A); c.confirmed(110, B);
        assertFalse(c.confirmed(109, C)); assertFalse(c.confirmed(-1, C));
        assertFalse(c.confirmed(Long.MAX_VALUE, C)); assertFalse(c.confirmed(Long.MIN_VALUE, C));
        assertFalse(c.confirmed(150, null));
        assertEquals(2, c.progress(110)); assertTrue(c.confirmed(111, C)); assertEquals(200, c.remaining(111));
        assertFalse(c.confirmed(Long.MAX_VALUE, A)); assertEquals(200, c.remaining(111));
    }
    @Test void validIgnoredEventsAdvanceClockButReadQueriesDoNot() {
        var c = active(100);
        assertFalse(c.confirmed(150, D));
        assertEquals(0, c.remaining(149)); assertEquals(150, c.remaining(150));
        assertEquals(0, c.remaining(500)); assertEquals(150, c.remaining(150));
        assertFalse(c.confirmed(149, D));
        var collecting = new StatsForAllCycle(); collecting.confirmed(10, A);
        assertFalse(collecting.confirmed(20, A)); assertFalse(collecting.confirmed(19, B));
        assertEquals(1, collecting.progress(20));
    }
    @Test void overflowBoundaryAcceptsLastSafeTickAndCanExpireAtLongMax() {
        long last = Long.MAX_VALUE-200;
        var c = active(last);
        assertEquals(200, c.remaining(last)); assertEquals(1, c.remaining(Long.MAX_VALUE-1));
        assertEquals(0, c.remaining(Long.MAX_VALUE)); assertFalse(c.confirmed(last+1, D));
        assertEquals(200, c.remaining(last));
    }
    @Test void allAdjacentGapPairsObeyRenewalWithDuplicateNoise() {
        for (int gap1 = 0; gap1 <= 61; gap1++) for (int gap2 = 0; gap2 <= 61; gap2++) {
            var c = new StatsForAllCycle();
            long second = 10+gap1, third = second+gap2;
            c.confirmed(10, A); c.confirmed(second, B);
            assertFalse(c.confirmed(second, new UUID(2, 2)));
            c.confirmed(third, C);
            boolean expected = gap1 < 60 && gap2 < 60;
            assertEquals(expected ? 200 : 0, c.remaining(third), gap1+"/"+gap2);
        }
    }
    @Test void localStowReloadPersistenceMeansRetainingInstanceWithoutPausing() {
        // No fake proof of Destiny behavior: master retains this pure object across these local actions.
        var c = active(10);
        assertEquals(180, c.remaining(30)); assertEquals(80, c.remaining(130));
        assertEquals(0, c.remaining(210)); assertEquals(200, c.remaining(10));
        var partial = new StatsForAllCycle(); partial.confirmed(10, A);
        assertTrue(partial.confirmed(69, B)); assertTrue(partial.confirmed(128, C));
    }
    @Test void customSafeBoundsAreCheckedAndCycleHasNoDamageMultiplier() {
        for (int n : new int[]{Integer.MIN_VALUE, -1, 0, 1201, Integer.MAX_VALUE}) {
            assertThrows(IllegalArgumentException.class, () -> new StatsForAllCycle(n, 200));
            assertThrows(IllegalArgumentException.class, () -> new StatsForAllCycle(60, n));
        }
        var c = new StatsForAllCycle(1, 1); c.confirmed(0, A); c.confirmed(0, B); c.confirmed(0, C);
        assertEquals(1, c.remaining(0)); assertEquals(0, c.remaining(1));
        assertDoesNotThrow(() -> new StatsForAllCycle(1200, 1200));
        assertTrue(Arrays.stream(StatsForAllCycle.class.getDeclaredMethods()).noneMatch(m -> m.getName().equals("multiplier")));
    }
}
