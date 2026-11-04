package kim.biryeong.destiny.weapon;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class BackupPlanCycleW192Test {
    @Test void unseenAndInitialHeldWeaponsDoNotInventThreeSecondsOfStow() {
        var unseen = new BackupPlanCycle();
        assertFalse(unseen.selecting(1000));
        assertEquals(0, unseen.remaining(1000));
        var held = new BackupPlanCycle();
        held.update(1000, true);
        held.update(1060, true);
        assertFalse(held.selecting(1060));
        assertEquals(0, held.remaining(1060));
    }

    @Test void observedStowRequiresExactlySixtyTicksAndRepeatedUpdatesRetainItsOrigin() {
        var c = new BackupPlanCycle();
        c.update(10, false);
        c.update(40, false);
        assertFalse(c.selecting(69));
        c.stowing(70);
        c.update(129, false);
        assertTrue(c.selecting(130));
        assertEquals(40, c.remaining(130));
        assertEquals(1, c.remaining(169));
        assertEquals(0, c.remaining(170));
    }

    @Test void duplicateSelectingAndHeldHeartbeatsCannotRefreshTheBuff() {
        var c = armed();
        assertFalse(c.selecting(61));
        c.update(80, true);
        assertEquals(1, c.remaining(99));
        assertEquals(0, c.remaining(100));
        assertFalse(c.selecting(100));
    }

    @Test void sameTickAwayAndBackCancelsAndRestartsTheWholeStowRequirement() {
        var c = armed();
        c.stowing(70);
        assertEquals(0, c.remaining(70));
        assertFalse(c.selecting(70));
        c.stowing(71);
        c.stowing(80);
        assertFalse(c.selecting(130));
        c.stowing(131);
        assertTrue(c.selecting(191));
    }

    @Test void paidLfrEmissionRefreshesOnlyAnAlreadyActiveHeldWindow() {
        var c = armed();
        assertTrue(c.paidEmission(99, true));
        assertEquals(40, c.remaining(99));
        assertTrue(c.paidEmission(120, true));
        assertEquals(1, c.remaining(159));
        assertFalse(c.paidEmission(160, true));
        assertEquals(0, c.remaining(160));
        assertFalse(c.paidEmission(200, true));
    }

    @Test void fusionShotsAndStowedOrUnseenLfrShotsNeverRefresh() {
        var c = armed();
        assertFalse(c.paidEmission(99, false));
        assertEquals(0, c.remaining(100));
        c.stowing(100);
        assertFalse(c.paidEmission(110, true));
        assertTrue(c.selecting(160));
        c.stowing(161);
        assertFalse(c.paidEmission(162, true));
        assertFalse(new BackupPlanCycle().paidEmission(1000, true));
    }

    @Test void readOnlyQueriesAndAcceptedValuesCannotObserveOrRetimeTheCycle() {
        var c = armed();
        int acceptedRemaining = c.remaining(99);
        assertEquals(0, c.remaining(1000));
        assertEquals(1, c.remaining(99));
        assertEquals(0, c.remaining(59));
        assertEquals(1, acceptedRemaining);
        assertEquals(1, c.remaining(99));
    }

    @Test void sourceLifecycleClearRevokesActiveAndPreviouslyEarnedStowCredit() {
        var c = armed();
        c.clear();
        assertEquals(0, c.remaining(60));
        assertFalse(c.selecting(1000));
        c.stowing(1001);
        c.clear();
        assertFalse(c.selecting(2000));
        assertEquals(0, new BackupPlanCycle().remaining(2000));
    }

    @Test void observedInventoryTransitionsUseTheSameClockWithoutInitialProc() {
        var c = new BackupPlanCycle();
        c.update(0, true);
        c.update(1, false);
        c.update(61, true);
        assertEquals(40, c.remaining(61));
        c.update(62, false);
        assertEquals(0, c.remaining(62));
    }

    @Test void rewindsNegativeTimesAndOverflowFailClosedWithoutOldStowCredit() {
        var c = armed();
        c.update(59, true);
        assertEquals(0, c.remaining(60));
        assertFalse(c.selecting(61));
        c.stowing(62);
        assertFalse(c.selecting(-1));
        assertFalse(c.selecting(1000));
        c.stowing(1001);
        assertFalse(c.selecting(Long.MAX_VALUE));
        assertEquals(0, c.remaining(Long.MAX_VALUE));
        assertFalse(c.selecting(2000));
    }

    private static BackupPlanCycle armed() {
        var c = new BackupPlanCycle();
        c.update(0, false);
        assertTrue(c.selecting(60));
        return c;
    }
}
