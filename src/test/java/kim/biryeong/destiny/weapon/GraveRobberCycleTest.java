package kim.biryeong.destiny.weapon;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class GraveRobberCycleTest {
    @Test void poweredNonlethalHitActivatesWithoutAKill() {
        var cycle = new GraveRobberCycle();
        assertTrue(cycle.confirmed(0, true, false));
        assertEquals(60, cycle.remaining(0));
        assertFalse(cycle.confirmed(0, true, true));
    }

    @Test void poweredKillsAndUnpoweredMeleeKillsBothActivate() {
        assertTrue(new GraveRobberCycle().confirmed(0, true, true));
        assertTrue(new GraveRobberCycle().confirmed(0, false, true));
    }

    @Test void unpoweredNonlethalContactNeverSpendsTheOpportunity() {
        var cycle = new GraveRobberCycle();
        assertFalse(cycle.confirmed(0, false, false));
        assertEquals(0, cycle.remaining(0));
        assertTrue(cycle.confirmed(0, true, false));
    }

    @Test void exactSixtyTickBoundaryAndDeniedContactsNeverRefreshCooldown() {
        var cycle = new GraveRobberCycle();
        assertTrue(cycle.confirmed(10, true, false));
        for (int tick = 10; tick < 70; tick++) {
            assertFalse(cycle.confirmed(tick, false, true));
            assertEquals(70 - tick, cycle.remaining(tick));
        }
        assertEquals(0, cycle.remaining(70));
        assertTrue(cycle.confirmed(70, false, true));
        assertEquals(60, cycle.remaining(70));
    }

    @Test void clockIsSharedBySourcesAndIndependentBetweenOwners() {
        // The wrapper gives one instance to an owner, not one instance to each selected stack.
        var owner = new GraveRobberCycle();
        var otherOwner = new GraveRobberCycle();
        assertTrue(owner.confirmed(10, true, false)); // Source A
        assertFalse(owner.confirmed(11, false, true)); // Source B
        assertTrue(otherOwner.confirmed(11, false, true));
        assertTrue(owner.confirmed(70, true, false)); // Source B at original boundary
    }

    @Test void observationsDuringStowAndSelectionEditsDoNotErasePaidTime() {
        var cycle = new GraveRobberCycle();
        cycle.confirmed(0, true, false);
        assertTrue(cycle.update(20));
        assertEquals(40, cycle.remaining(20));
        assertTrue(cycle.update(59));
        assertFalse(cycle.confirmed(59, true, false));
        assertTrue(cycle.confirmed(60, true, false));
    }

    @Test void validNoTransferProcStillSpendsSixtyTicks() {
        var cycle = new GraveRobberCycle();
        assertTrue(cycle.confirmed(0, true, false));
        // No ammo/transfer flag can bypass the local activation clock for full or empty-reserve guns.
        assertFalse(cycle.confirmed(59, true, false));
        assertTrue(cycle.confirmed(60, true, false));
    }

    @Test void negativeTicksAndRegressionFailClosedWithoutClearingCooldown() {
        var cycle = new GraveRobberCycle();
        assertFalse(cycle.confirmed(-1, true, false));
        assertFalse(cycle.update(Long.MIN_VALUE));
        assertTrue(cycle.confirmed(100, true, false));
        assertTrue(cycle.update(120));
        assertFalse(cycle.update(119));
        assertFalse(cycle.confirmed(119, true, true));
        assertFalse(cycle.confirmed(-1, false, true));
        assertEquals(0, cycle.remaining(119));
        assertEquals(0, cycle.remaining(Long.MIN_VALUE));
        assertEquals(40, cycle.remaining(120));
        assertFalse(cycle.confirmed(159, true, false));
        assertTrue(cycle.confirmed(160, true, false));
    }

    @Test void queryIsPureAndCannotMoveAnObservedClockOrExpireState() {
        var cycle = new GraveRobberCycle();
        cycle.confirmed(10, true, false);
        for (int i = 0; i < 20; i++) assertEquals(30, cycle.remaining(40));
        assertEquals(0, cycle.remaining(Long.MAX_VALUE));
        assertEquals(60, cycle.remaining(10));
        assertFalse(cycle.confirmed(69, true, false));
        assertTrue(cycle.confirmed(70, true, false));
    }

    @Test void subtractionSupportsExactExpiryAtLongMaxWithoutDeadlineOverflow() {
        var cycle = new GraveRobberCycle();
        long start = Long.MAX_VALUE - 60;
        assertTrue(cycle.confirmed(start, true, false));
        assertEquals(60, cycle.remaining(start));
        assertEquals(1, cycle.remaining(Long.MAX_VALUE - 1));
        assertEquals(0, cycle.remaining(Long.MAX_VALUE));
        assertTrue(cycle.confirmed(Long.MAX_VALUE, true, false));
        assertEquals(60, cycle.remaining(Long.MAX_VALUE));
        assertFalse(cycle.confirmed(Long.MAX_VALUE, false, true));
    }

    @Test void nearLongMaxProcCannotWrapIntoEarlyReadiness() {
        var cycle = new GraveRobberCycle();
        assertTrue(cycle.confirmed(Long.MAX_VALUE - 10, true, false));
        assertEquals(50, cycle.remaining(Long.MAX_VALUE));
        assertFalse(cycle.confirmed(Long.MAX_VALUE, true, false));
        assertFalse(cycle.confirmed(Long.MIN_VALUE, true, false));
        assertEquals(50, cycle.remaining(Long.MAX_VALUE));
    }

    @Test void trueLifecycleClearResetsCooldownAndClockEpoch() {
        var cycle = new GraveRobberCycle();
        cycle.confirmed(100, true, false);
        cycle.clear();
        assertEquals(0, cycle.remaining(100));
        assertTrue(cycle.confirmed(0, false, true));
        assertEquals(60, cycle.remaining(0));
    }
}
