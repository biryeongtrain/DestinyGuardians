package kim.biryeong.destiny.weapon;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class KillClipCycleTest {
    private static final int WINDOW = 72;
    private static final int DURATION = 100;

    @Test void reloadWithoutAKillNeverCreatesDamageTime() {
        var cycle = new KillClipCycle();
        for (long tick : new long[]{0, 1, 72, 100, 100000}) {
            assertFalse(cycle.reloaded(tick, WINDOW, DURATION));
            assertEquals(0, cycle.remaining(tick, DURATION));
        }
    }

    @Test void killAloneIsPendingAndLatestKillDeterminesTheWindow() {
        var cycle = new KillClipCycle();
        cycle.killed(10);
        assertEquals(0, cycle.remaining(10, DURATION));
        assertEquals(0, cycle.remaining(81, DURATION));
        cycle.killed(80);
        assertTrue(cycle.reloaded(152, WINDOW, DURATION));
        assertEquals(DURATION, cycle.remaining(152, DURATION));
    }

    @Test void killWindowIncludesItsEndpointButNotTheFollowingTick() {
        for (int delay : new int[]{0, WINDOW - 1, WINDOW, WINDOW + 1}) {
            var cycle = new KillClipCycle();
            cycle.killed(10);
            assertEquals(delay <= WINDOW, cycle.reloaded(10 + delay, WINDOW, DURATION), "delay=" + delay);
            assertEquals(delay <= WINDOW ? DURATION : 0, cycle.remaining(10 + delay, DURATION));
        }
    }

    @Test void damageWindowHasExactlyOneHundredTicksAndReadsDoNotRefreshIt() {
        var cycle = new KillClipCycle(); cycle.killed(0);
        assertTrue(cycle.reloaded(20, WINDOW, DURATION));
        assertEquals(0, cycle.remaining(19, DURATION));
        assertEquals(100, cycle.remaining(20, DURATION));
        assertEquals(100, cycle.remaining(20, DURATION));
        assertEquals(1, cycle.remaining(119, DURATION));
        assertEquals(0, cycle.remaining(120, DURATION));
        assertEquals(0, cycle.remaining(121, DURATION));
    }

    @Test void successfulReloadConsumesKillSoDuplicateReloadsAndShellsCannotRefresh() {
        var cycle = new KillClipCycle(); cycle.killed(0);
        assertTrue(cycle.reloaded(16, WINDOW, DURATION));
        assertFalse(cycle.reloaded(16, WINDOW, DURATION));
        assertFalse(cycle.reloaded(32, WINDOW, DURATION));
        assertFalse(cycle.reloaded(48, WINDOW, DURATION));
        assertEquals(68, cycle.remaining(48, DURATION));
        assertFalse(cycle.reloaded(116, WINDOW, DURATION));
        assertEquals(0, cycle.remaining(116, DURATION));
    }

    @Test void freshKillAndReloadRefreshActiveBuffAndCanStartAnotherAfterExpiry() {
        var cycle = new KillClipCycle(); cycle.killed(0);
        assertTrue(cycle.reloaded(10, WINDOW, DURATION));
        cycle.killed(60);
        assertEquals(50, cycle.remaining(60, DURATION));
        assertTrue(cycle.reloaded(70, WINDOW, DURATION));
        assertEquals(100, cycle.remaining(70, DURATION));
        assertEquals(60, cycle.remaining(110, DURATION));
        assertEquals(0, cycle.remaining(170, DURATION));
        cycle.killed(180);
        assertTrue(cycle.reloaded(181, WINDOW, DURATION));
        assertEquals(100, cycle.remaining(181, DURATION));
    }

    @Test void expiredOrFutureKillCannotActivateOrEraseAnExistingBuff() {
        var cycle = new KillClipCycle(); cycle.killed(10);
        assertFalse(cycle.reloaded(9, WINDOW, DURATION));
        assertTrue(cycle.reloaded(10, WINDOW, DURATION));
        cycle.killed(11);
        assertFalse(cycle.reloaded(84, WINDOW, DURATION));
        assertEquals(26, cycle.remaining(84, DURATION));
        assertFalse(cycle.reloaded(1000, WINDOW, DURATION));
        assertEquals(0, cycle.remaining(1000, DURATION));
    }

    @Test void invalidTimingNegativeKillsAndOverflowNeverManufactureABuff() {
        var cycle = new KillClipCycle();
        for (int bad : new int[]{Integer.MIN_VALUE, -1, 0, 1201, Integer.MAX_VALUE}) {
            assertThrows(IllegalArgumentException.class, () -> cycle.reloaded(0, bad, DURATION));
            assertThrows(IllegalArgumentException.class, () -> cycle.reloaded(0, WINDOW, bad));
            assertEquals(0, cycle.remaining(0, bad));
        }
        cycle.killed(-1);
        assertFalse(cycle.reloaded(0, WINDOW, DURATION));
        assertEquals(0, cycle.remaining(-1, DURATION));
        cycle.killed(Long.MAX_VALUE - 10);
        assertFalse(cycle.reloaded(Long.MAX_VALUE - 1, WINDOW, DURATION));
        assertEquals(0, cycle.remaining(Long.MAX_VALUE - 1, DURATION));
        cycle.killed(Long.MAX_VALUE - DURATION);
        assertTrue(cycle.reloaded(Long.MAX_VALUE - DURATION, WINDOW, DURATION));
        assertEquals(DURATION, cycle.remaining(Long.MAX_VALUE - DURATION, DURATION));
        assertEquals(1, cycle.remaining(Long.MAX_VALUE - 1, DURATION));
        assertEquals(0, cycle.remaining(Long.MAX_VALUE, DURATION));
    }
}
