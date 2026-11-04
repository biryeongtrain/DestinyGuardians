package kim.biryeong.destiny.weapon;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;
import static kim.biryeong.destiny.weapon.UnrelentingCycle.Rank.*;

class UnrelentingW200Test {
    @Test void chainUsesAdjacentKillWindowAndResetsAfterProcInsteadOfBankingOverflow() {
        var c = new UnrelentingCycle();
        assertFalse(c.killed(1, c.capture(1), new Object(), RANK_AND_FILE));
        assertFalse(c.killed(101, c.capture(101), new Object(), RANK_AND_FILE));
        assertTrue(c.killed(201, c.capture(201), new Object(), RANK_AND_FILE));
        assertEquals(0, c.progress(201));
        assertTrue(c.active(201));
        assertFalse(c.killed(202, c.capture(202), new Object(), RANK_AND_FILE));
        c.update(303);
        assertEquals(0, c.progress(303));
        assertFalse(c.killed(303, c.capture(303), new Object(), RANK_AND_FILE));
        assertFalse(c.killed(304, c.capture(304), new Object(), RANK_AND_FILE));
        assertTrue(c.killed(305, c.capture(305), new Object(), RANK_AND_FILE));
    }
    @Test void guardianAndMixedProgressCrossThresholdAndPowerfulProcsOnItsOwn() {
        var c = new UnrelentingCycle();
        assertFalse(c.killed(0, c.capture(0), new Object(), GUARDIAN));
        assertTrue(c.killed(1, c.capture(1), new Object(), RANK_AND_FILE));
        c.clear();
        assertTrue(c.killed(2, c.capture(2), new Object(), POWERFUL));
        c.clear();
        assertFalse(c.killed(3, c.capture(3), new Object(), GUARDIAN));
        assertTrue(c.killed(4, c.capture(4), new Object(), GUARDIAN));
    }
    @Test void duplicatesCannotGrantOrRefreshAndSaturatedLedgersFailClosedWithoutEviction() {
        var c = new UnrelentingCycle(); var e = c.capture(10); var corpse = new Object();
        assertTrue(c.killed(10, e, corpse, POWERFUL));
        c.damaged(1);
        assertFalse(c.killed(11, e, corpse, POWERFUL));
        assertFalse(c.killed(11, c.capture(11), corpse, POWERFUL));
        assertFalse(c.active(11));
        for (int i = 1; i < UnrelentingCycle.MAX_CORPSES; i++)
            assertTrue(c.killed(11, e, new Object(), POWERFUL));
        c.damaged(1);
        assertFalse(c.killed(12, e, new Object(), POWERFUL));
        assertFalse(c.active(12));
        c.update(112); // Current-window cross-emission ledger is bounded and expires.
        assertFalse(c.killed(112, e, corpse, POWERFUL)); // Original token never forgets.
        assertTrue(c.killed(112, c.capture(112), new Object(), POWERFUL));
    }
    @Test void tokenEpochAndIdentityCannotBeBorrowedAcrossSourcesEditsOrClockRollback() {
        var c = new UnrelentingCycle(); var other = new UnrelentingCycle(); var e = c.capture(5);
        assertFalse(other.killed(5, e, new Object(), POWERFUL));
        assertFalse(c.killed(4, e, new Object(), POWERFUL));
        assertFalse(c.killed(5, e, null, POWERFUL));
        assertFalse(c.killed(5, e, new Object(), null));
        c.clear(); var fresh = c.capture(5);
        assertFalse(c.killed(5, e, new Object(), POWERFUL));
        assertTrue(c.killed(5, fresh, new Object(), POWERFUL));
        c.update(4);
        assertFalse(c.active(5));
        assertFalse(c.killed(5, fresh, new Object(), POWERFUL));
        assertNull(c.capture(-1));
    }
    @Test void regenerationIsOncePerTickStopsAtFullAndNeverUsesKillWindowAsExpiry() {
        var c = new UnrelentingCycle(); c.killed(0, c.capture(0), new Object(), POWERFUL);
        assertEquals(0, c.regeneration(0, 1, 20));
        assertTrue(c.regeneration(1, 1, 20) > 0);
        assertEquals(0, c.regeneration(1, 1, 20));
        c.update(101); // Stow/update has no made-up five-second regeneration timeout.
        assertTrue(c.active(101));
        float grant = c.regeneration(102, 19.95f, 20);
        assertTrue(grant > 0 && 19.95f + grant <= 20);
        assertEquals(0, c.regeneration(103, 20, 20));
        assertFalse(c.active(103));
        assertEquals(0, c.regeneration(104, 5, 20)); // Full completion cannot restart itself.
    }
    @Test void onlyPositiveFiniteActualDamageInterruptsAndQueriesCannotHealOrAdvanceTime() {
        var c = new UnrelentingCycle(); c.killed(10, c.capture(10), new Object(), POWERFUL);
        c.damaged(0); c.damaged(-1); c.damaged(Float.NaN); c.damaged(Float.POSITIVE_INFINITY);
        assertTrue(c.active(10));
        assertTrue(c.active(Long.MAX_VALUE)); // Pure probe cannot move the writer clock.
        assertEquals(0, c.progress(Long.MAX_VALUE));
        assertFalse(c.active(-1));
        assertTrue(c.regeneration(11, 1, 20) > 0);
        c.damaged(.1f);
        assertFalse(c.active(11));
        assertEquals(0, c.regeneration(12, 1, 20));
        assertTrue(c.killed(13, c.capture(13), new Object(), POWERFUL));
        assertTrue(c.active(13));
    }
    @Test void nonFiniteOrDeadHealthCannotReceiveRegeneration() {
        var c = new UnrelentingCycle(); c.killed(0, c.capture(0), new Object(), POWERFUL);
        assertEquals(0, c.regeneration(1, Float.NaN, 20));
        assertFalse(c.active(1));
        c.killed(2, c.capture(2), new Object(), POWERFUL);
        assertEquals(0, c.regeneration(3, 0, 20));
        assertFalse(c.active(3));
    }
}
