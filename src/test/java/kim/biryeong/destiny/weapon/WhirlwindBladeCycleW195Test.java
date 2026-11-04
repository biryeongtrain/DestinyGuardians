package kim.biryeong.destiny.weapon;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class WhirlwindBladeCycleW195Test {
    @Test void paidSnapshotPrecedesOwnHitAndEveryValidContactRefreshesDeadline() {
        var c = new WhirlwindBladeCycle(); var first = c.capture(10);
        assertTrue(c.confirmed(10, first, new Object(), 1, true));
        assertEquals(0, c.capturedStacks(10, first));
        var second = c.capture(11); int before = c.stacks(11);
        assertTrue(c.confirmed(11, second, new Object(), 1, true));
        assertEquals(before, c.capturedStacks(11, second));
        long end = 11L + WhirlwindBladeProfile.durationTicks();
        assertTrue(c.stacks(end - 1) > 0);
        assertEquals(0, c.stacks(end));
        // A future query cannot advance the authoritative clock or expire earlier state.
        assertTrue(c.stacks(11) > 0);
        assertTrue(c.confirmed(end, c.capture(end), new Object(), 1, true));
        assertTrue(c.remaining(end) > 0);
    }
    @Test void sharedCleaveDirectSplashTokenDeduplicatesSameTargetAndRejectsNoLoss() {
        var c = new WhirlwindBladeCycle(); var paid = c.capture(0); var target = new Object();
        assertFalse(c.confirmed(0, paid, target, 0, true));
        assertFalse(c.confirmed(0, paid, target, Float.NaN, true));
        assertTrue(c.confirmed(0, paid, target, 1, true));
        int before = c.stacks(0);
        assertFalse(c.confirmed(0, paid, target, 1, true));
        assertEquals(before, c.stacks(0));
        assertTrue(c.confirmed(0, paid, new Object(), 1, true));
        assertTrue(c.stacks(0) > before);
    }
    @Test void guardAndPreselectionStowResetLiveStateWithoutChangingPaidSnapshot() {
        var c = new WhirlwindBladeCycle();
        c.confirmed(0, c.capture(0), new Object(), 1, true);
        var old = c.capture(1); int frozen = c.capturedStacks(1, old);
        c.blocking(1);
        assertEquals(0, c.stacks(1));
        assertEquals(frozen, c.capturedStacks(1, old));
        assertFalse(c.confirmed(1, old, new Object(), 1, true));
        c.confirmed(1, c.capture(1), new Object(), 1, true);
        var outgoing = c.capture(1); c.stowing(1); c.update(1, true);
        assertEquals(0, c.stacks(1));
        assertFalse(c.confirmed(1, outgoing, new Object(), 1, true));
        assertTrue(c.confirmed(2, c.capture(2), new Object(), 1, true));
    }
    @Test void sameTickEditRebindForeignSourceAndRollbackRevokeOldAuthority() {
        var c = new WhirlwindBladeCycle(); var foreign = new WhirlwindBladeCycle();
        c.confirmed(10, c.capture(10), new Object(), 1, true);
        var old = c.capture(10); c.clear();
        assertEquals(0, c.capturedStacks(10, old));
        assertFalse(c.confirmed(10, old, new Object(), 1, true));
        assertFalse(c.confirmed(10, foreign.capture(10), new Object(), 1, true));
        assertTrue(c.confirmed(10, c.capture(10), new Object(), 1, true));
        var current = c.capture(11); c.update(10, true);
        assertFalse(c.confirmed(11, current, new Object(), 1, true));
    }
    @Test void boundedLedgerFailsClosedForEvictedContactsAndOverflowTargets() {
        var c = new WhirlwindBladeCycle(); var old = c.capture(0);
        for (int i = 0; i < 128; i++) c.capture(0);
        assertFalse(c.confirmed(0, old, new Object(), 1, true));
        var paid = c.capture(0);
        for (int i = 0; i < 256; i++) assertTrue(c.confirmed(0, paid, new Object(), 1, true));
        long before = c.remaining(0);
        assertFalse(c.confirmed(1, paid, new Object(), 1, true));
        assertEquals(before - 1, c.remaining(1));
    }
}
