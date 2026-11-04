package kim.biryeong.destiny.weapon;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class FeedingFrenzyCycleTest {
    @Test void inactiveReadsDoNotCreateCredit() {
        var c = new FeedingFrenzyCycle();
        for (long t : new long[]{0, 1, 100, Long.MAX_VALUE}) {
            assertEquals(0, c.stacks(t, 100));
            assertEquals(0, c.remaining(t, 100));
        }
        assertTrue(c.killed(1000, 100));
        assertEquals(1, c.stacks(1000, 100));
    }
    @Test void eachKillAddsOneStackAndCapsAtFive() {
        var c = new FeedingFrenzyCycle();
        for (int i = 1; i <= 20; i++) {
            assertTrue(c.killed(i, 100));
            assertEquals(Math.min(i, 5), c.stacks(i, 100));
            assertEquals(100, c.remaining(i, 100));
        }
    }
    @Test void simultaneousDistinctFinalBlowsCanBuildStacks() {
        var c = new FeedingFrenzyCycle();
        assertTrue(c.killed(20, 80));
        assertTrue(c.killed(20, 80));
        assertEquals(2, c.stacks(20, 80));
    }
    @Test void allStacksExpireTogetherAtExactBoundary() {
        var c = new FeedingFrenzyCycle();
        for (int i = 0; i < 5; i++) c.killed(10, 100);
        assertEquals(5, c.stacks(109, 100));
        assertEquals(1, c.remaining(109, 100));
        assertEquals(0, c.stacks(110, 100));
        assertEquals(0, c.remaining(110, 100));
        assertEquals(0, c.stacks(10000, 100));
    }
    @Test void killBeforeExpiryRefreshesTheWholeChain() {
        var c = new FeedingFrenzyCycle();
        c.killed(20, 100); c.killed(119, 100);
        assertEquals(2, c.stacks(120, 100));
        assertEquals(99, c.remaining(120, 100));
        assertEquals(2, c.stacks(218, 100));
        assertEquals(0, c.stacks(219, 100));
    }
    @Test void killAtOrAfterExpiryRestartsAtOne() {
        for (long tick : new long[]{110, 111, 1000000}) {
            var c = new FeedingFrenzyCycle();
            c.killed(10, 100); c.killed(10, 100);
            c.killed(tick, 100);
            assertEquals(1, c.stacks(tick, 100));
            assertEquals(100, c.remaining(tick, 100));
        }
    }
    @Test void readOrderDoesNotConsumeOrRefreshTheWindow() {
        var c = new FeedingFrenzyCycle();
        c.killed(100, 60); c.killed(120, 60);
        assertEquals(0, c.stacks(180, 60));
        assertEquals(2, c.stacks(125, 60));
        for (int i = 0; i < 1000; i++) assertEquals(55, c.remaining(125, 60));
        assertEquals(1, c.remaining(179, 60));
    }
    @Test void invalidClockDoesNotCorruptAnExistingChain() {
        var c = new FeedingFrenzyCycle();
        c.killed(100, 60);
        assertFalse(c.killed(-1, 60));
        assertFalse(c.killed(99, 60));
        assertFalse(c.killed(Long.MAX_VALUE, 60));
        assertEquals(0, c.stacks(99, 60));
        assertEquals(1, c.stacks(100, 60));
        assertEquals(60, c.remaining(100, 60));
    }
    @Test void maximumSafeDeadlineCannotOverflow() {
        var c = new FeedingFrenzyCycle();
        assertTrue(c.killed(Long.MAX_VALUE - 100, 100));
        assertEquals(1, c.stacks(Long.MAX_VALUE - 1, 100));
        assertEquals(1, c.remaining(Long.MAX_VALUE - 1, 100));
        assertEquals(0, c.stacks(Long.MAX_VALUE, 100));
        assertFalse(c.killed(Long.MAX_VALUE - 99, 100));
    }
    @Test void durationsAreStrictlyBoundedForReadsAndWrites() {
        var c = new FeedingFrenzyCycle();
        for (int t : new int[]{Integer.MIN_VALUE, -1, 0, 1201, Integer.MAX_VALUE}) {
            assertThrows(IllegalArgumentException.class, () -> c.killed(0, t));
            assertThrows(IllegalArgumentException.class, () -> c.stacks(0, t));
            assertThrows(IllegalArgumentException.class, () -> c.remaining(0, t));
        }
        assertTrue(c.killed(0, 1));
        assertEquals(1, c.stacks(0, 1));
        assertTrue(c.killed(1, 1200));
        assertEquals(1, c.stacks(1, 1200));
    }
    @Test void clearRetiresCreditWithoutResurrection() {
        var c = new FeedingFrenzyCycle();
        c.killed(100, 60); c.clear();
        assertEquals(0, c.stacks(100, 60));
        assertEquals(0, c.remaining(159, 60));
        c.killed(160, 60);
        assertEquals(1, c.stacks(160, 60));
    }
    @Test void sessionsAreIndependent() {
        var a = new FeedingFrenzyCycle(); var b = new FeedingFrenzyCycle();
        a.killed(0, 60); a.killed(0, 60);
        assertEquals(0, b.stacks(0, 60));
        b.killed(10, 60); a.clear();
        assertEquals(1, b.stacks(20, 60));
        assertEquals(50, b.remaining(20, 60));
    }
}
