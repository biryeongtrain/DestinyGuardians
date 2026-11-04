package kim.biryeong.destiny.weapon;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class KillingTallyCycleW194Test {
    @Test void preOwnKillSnapshotCapsLiveStacksButNeverBoostsItsOwnSplash() {
        var c = new KillingTallyCycle();
        var shot = c.capture(10);
        for (int i = 0; i < 5; i++) assertTrue(c.killed(10, shot, new Object(), true));
        assertEquals(3, c.stacks(10));
        assertEquals(0, c.capturedStacks(10, shot));
        assertEquals(3, c.capturedStacks(10, c.capture(10)));
        c.update(1_000_000, true);
        assertEquals(3, c.stacks(1_000_000)); // no timer
    }

    @Test void stowAndAcceptedReloadResetLiveButPreservePaidDamageAndCannotRebankOldShots() {
        for (boolean reload : new boolean[]{false, true}) {
            var c = new KillingTallyCycle();
            c.killed(1, c.capture(1), new Object(), true);
            var paid = c.capture(2);
            if (reload) c.reloadStarted(2); else c.stowing(2);
            assertEquals(0, c.stacks(2));
            assertEquals(1, c.capturedStacks(2, paid));
            assertTrue(c.killed(3, paid, new Object(), true));
            assertEquals(0, c.stacks(3));
            var fresh = c.capture(3);
            assertTrue(c.killed(3, fresh, new Object(), true));
            assertEquals(1, c.stacks(3));
        }
    }

    @Test void directSplashDuplicateLedgerIsIdentityBoundedAndNeverEvicts() {
        var c = new KillingTallyCycle();
        var paid = c.capture(10);
        var corpse = new Object();
        assertTrue(c.killed(10, paid, corpse, false));
        assertFalse(c.killed(11, paid, corpse, true));
        assertEquals(0, c.stacks(11));
        for (int i = 1; i < KillingTallyCycle.MAX_CORPSES_PER_EMISSION; i++)
            assertTrue(c.killed(11, paid, new Object(), true));
        assertFalse(c.killed(12, paid, new Object(), true));
        assertFalse(c.killed(12, paid, corpse, true));
        // New emissions have a separate bound, not a weapon-lifetime kill ceiling.
        assertTrue(c.killed(12, c.capture(12), new Object(), true));
    }

    @Test void probesArePureAndForeignClearedOrRollbackEpochsCannotCredit() {
        var c = new KillingTallyCycle();
        c.killed(10, c.capture(10), new Object(), true);
        var paid = c.capture(11);
        assertEquals(1, c.stacks(Long.MAX_VALUE));
        assertEquals(0, c.stacks(-1));
        assertEquals(1, c.stacks(11));
        assertEquals(0, new KillingTallyCycle().capturedStacks(11, paid));
        assertFalse(new KillingTallyCycle().killed(11, paid, new Object(), true));
        c.clear();
        assertEquals(0, c.capturedStacks(11, paid));
        assertFalse(c.killed(12, paid, new Object(), true));
        var next = c.capture(12);
        c.update(11, true);
        assertFalse(c.killed(13, next, new Object(), true));
        assertNull(c.capture(-1));
    }

    @Test void invalidCallbacksDoNotSpendCreditAndPollingStowAlsoResets() {
        var c = new KillingTallyCycle();
        var paid = c.capture(10);
        var corpse = new Object();
        assertFalse(c.killed(9, paid, corpse, true));
        assertFalse(c.killed(10, null, corpse, true));
        assertFalse(c.killed(10, paid, null, true));
        assertTrue(c.killed(10, paid, corpse, true));
        c.update(11, false);
        c.update(12, true);
        assertEquals(0, c.stacks(12));
        assertTrue(c.killed(12, paid, new Object(), true));
        assertEquals(0, c.stacks(12));
    }
}
