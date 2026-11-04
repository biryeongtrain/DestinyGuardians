package kim.biryeong.destiny.weapon;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class EncoreCycleW192Test {
    @Test void paidCaptureDoesNotProcAndPrecisionGrantsTwoTotal() {
        var c = new EncoreCycle();
        var first = c.capture(10);
        assertEquals(0, c.stacks(10));
        assertEquals(0, c.remaining(10));
        assertFalse(c.killed(10, null, new Object(), true));
        assertTrue(c.killed(10, first, new Object(), false));
        assertEquals(1, c.stacks(10));
        assertTrue(c.killed(11, c.capture(11), new Object(), true));
        assertEquals(3, c.stacks(11));
        assertEquals(140, c.remaining(11));
    }

    @Test void capKillsRefreshAndExactDeadlineExpiresWhileIdleOrStowed() {
        var c = new EncoreCycle();
        assertTrue(c.killed(10, c.capture(10), new Object(), true));
        assertTrue(c.killed(11, c.capture(11), new Object(), true));
        assertEquals(4, c.stacks(11));
        assertTrue(c.killed(140, c.capture(140), new Object(), true));
        assertEquals(4, c.stacks(140));
        // No held/stowed flag exists: time advances without pausing or requiring another capture.
        c.update(279);
        assertEquals(4, c.stacks(279));
        assertEquals(1, c.remaining(279));
        assertEquals(0, c.stacks(280));
        assertEquals(0, c.remaining(280));
        assertTrue(c.killed(280, c.capture(280), new Object(), false));
        assertEquals(1, c.stacks(280));
    }

    @Test void duplicateDirectPayloadCallbacksDoNotStackOrRefreshButNewCorpsesCan() {
        var c = new EncoreCycle();
        var paid = c.capture(10);
        var corpse = new Object();
        assertTrue(c.killed(11, paid, corpse, false));
        assertFalse(c.killed(100, paid, corpse, true));
        assertEquals(1, c.stacks(100));
        assertEquals(51, c.remaining(100));
        assertTrue(c.killed(100, paid, new Object(), false));
        assertEquals(2, c.stacks(100));
        assertEquals(140, c.remaining(100));
    }

    @Test void perEmissionCorpseLedgerUsesIdentityAndFailsClosedAtItsBound() {
        var c = new EncoreCycle();
        var paid = c.capture(10);
        // Distinct objects with equal values must still count as distinct actual corpses.
        class EqualCorpse {
            @Override public boolean equals(Object o) { return o instanceof EqualCorpse; }
            @Override public int hashCode() { return 1; }
        }
        var first = new EqualCorpse();
        assertTrue(c.killed(10, paid, first, false));
        for (int i = 1; i < EncoreCycle.MAX_CORPSES_PER_EMISSION; i++)
            assertTrue(c.killed(10, paid, new EqualCorpse(), false));
        assertFalse(c.killed(100, paid, new EqualCorpse(), true));
        assertFalse(c.killed(100, paid, first, true));
        assertEquals(50, c.remaining(100));
        // A new paid emission has its own ledger, not a weapon-lifetime kill set.
        assertTrue(c.killed(100, c.capture(100), new EqualCorpse(), false));
        assertEquals(140, c.remaining(100));
    }

    @Test void pureQueriesCannotExpireOrRefreshStateAndExpiryDoesNotRevokeInflightPaidShot() {
        var c = new EncoreCycle();
        var inflight = c.capture(10);
        assertTrue(c.killed(10, c.capture(10), new Object(), true));
        assertEquals(0, c.stacks(-1));
        assertEquals(0, c.remaining(9));
        assertEquals(0, c.remaining(1000));
        assertEquals(2, c.stacks(149));
        assertEquals(1, c.remaining(149));
        c.update(150);
        assertTrue(c.killed(151, inflight, new Object(), false));
        assertEquals(1, c.stacks(151));
    }

    @Test void foreignSourcesAndInvalidatedEpochsFailAndRebindingRequiresNewToken() {
        var c = new EncoreCycle();
        var other = new EncoreCycle();
        var old = c.capture(20);
        assertFalse(other.killed(20, old, new Object(), true));
        assertTrue(c.killed(20, old, new Object(), true));
        c.clear();
        assertEquals(0, c.stacks(20));
        assertFalse(c.killed(21, old, new Object(), false));
        assertTrue(c.killed(22, c.capture(22), new Object(), false));
        var beforeRewind = c.capture(23);
        c.update(22);
        assertEquals(0, c.stacks(23));
        assertFalse(c.killed(24, beforeRewind, new Object(), true));
        assertTrue(c.killed(24, c.capture(24), new Object(), false));
    }

    @Test void negativeBackwardAndOverflowEventsCannotConsumeCorpseOrAlterDeadline() {
        var c = new EncoreCycle();
        assertNull(c.capture(-1));
        assertNull(c.capture(Long.MAX_VALUE));
        var token = c.capture(20);
        var corpse = new Object();
        assertFalse(c.killed(19, token, corpse, true));
        assertFalse(c.killed(Long.MAX_VALUE, token, corpse, true));
        assertFalse(c.killed(20, token, null, true));
        assertTrue(c.killed(20, token, corpse, true));
        assertEquals(2, c.stacks(20));
        assertEquals(140, c.remaining(20));
        var edge = new EncoreCycle();
        long last = Long.MAX_VALUE - EncoreCycle.DURATION_TICKS;
        assertTrue(edge.killed(last, edge.capture(last), new Object(), true));
        assertEquals(1, edge.remaining(Long.MAX_VALUE - 1));
        assertEquals(0, edge.remaining(Long.MAX_VALUE));
    }
}
