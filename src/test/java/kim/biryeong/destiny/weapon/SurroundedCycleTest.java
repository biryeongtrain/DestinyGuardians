package kim.biryeong.destiny.weapon;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class SurroundedCycleTest {
    @Test void exactlyThreeEnemiesStartsBuffWithoutAHitOrKill() {
        var cycle = new SurroundedCycle();
        cycle.update(0, 0); assertFalse(cycle.active(0));
        cycle.update(1, 2); assertFalse(cycle.active(1));
        cycle.update(2, 3); assertTrue(cycle.active(2));
        cycle.update(3, Integer.MAX_VALUE); assertTrue(cycle.active(3));
    }

    @Test void radiusIsInclusiveFifteenMetreFootPointSphereInAllThreeAxes() {
        assertTrue(SurroundedCycle.withinRadius(0, 0, 0));
        assertTrue(SurroundedCycle.withinRadius(15, 0, 0));
        assertTrue(SurroundedCycle.withinRadius(0, -15, 0));
        assertTrue(SurroundedCycle.withinRadius(0, 0, 15));
        assertTrue(SurroundedCycle.withinRadius(9, 12, 0));
        assertTrue(SurroundedCycle.withinRadius(-9, 0, -12));
        assertTrue(SurroundedCycle.withinRadius(5, 10, 10));
        assertFalse(SurroundedCycle.withinRadius(15, .001, 0));
        assertFalse(SurroundedCycle.withinRadius(Math.nextUp(15d), 0, 0));
        assertFalse(SurroundedCycle.withinRadius(10, 10, 10)); // Inside cube, outside sphere.
        assertTrue(SurroundedCycle.withinRadius(9, 0, 0)); // Obsolete 8 m must not survive.
    }

    @Test void nonfiniteAndOverflowingCoordinatesNeverCount() {
        for (double invalid : new double[]{Double.NaN, Double.POSITIVE_INFINITY, Double.NEGATIVE_INFINITY, Double.MAX_VALUE}) {
            assertFalse(SurroundedCycle.withinRadius(invalid, 0, 0));
            assertFalse(SurroundedCycle.withinRadius(0, invalid, 0));
            assertFalse(SurroundedCycle.withinRadius(0, 0, invalid));
        }
    }

    @Test void onlyThreePointsInsideSphereReachThresholdIncludingExactBoundary() {
        var cycle = new SurroundedCycle();
        double[][] points = {{0, 0, 1}, {9, 0, 0}, {9, 12, 0}, {10, 10, 10}, {15.0001, 0, 0}};
        int count = 0;
        for (var point : points)
            if (SurroundedCycle.withinRadius(point[0], point[1], point[2])) count++;
        assertEquals(3, count);
        cycle.update(0, count); assertTrue(cycle.active(0));
        points[2][1] = Math.nextUp(12d);
        count = 0;
        for (var point : points)
            if (SurroundedCycle.withinRadius(point[0], point[1], point[2])) count++;
        assertEquals(2, count);
        cycle.update(1, count); assertEquals(30, cycle.remaining(1));
    }

    @Test void lingerStartsAtGenuineThresholdLossAndLastsExactlyThirtyTicks() {
        var cycle = new SurroundedCycle();
        cycle.update(100, 3);
        cycle.update(101, 2);
        for (int elapsed = 0; elapsed < 30; elapsed++) {
            cycle.update(101 + elapsed, 2);
            assertTrue(cycle.active(101 + elapsed));
            assertEquals(30 - elapsed, cycle.remaining(101 + elapsed));
        }
        assertFalse(cycle.active(131));
        assertEquals(0, cycle.remaining(131));
        cycle.update(132, 2); assertFalse(cycle.active(132));
    }

    @Test void aSparseObservationDoesNotMeasureLingerFromLastGoodSample() {
        var cycle = new SurroundedCycle();
        cycle.update(10, 3);
        cycle.update(100, 0);
        assertEquals(30, cycle.remaining(100));
        assertEquals(1, cycle.remaining(129));
        assertFalse(cycle.active(130));
    }

    @Test void neverMetThresholdCannotAcquireLingerFromRepeatedFailures() {
        var cycle = new SurroundedCycle();
        for (int tick = 0; tick < 100; tick++) {
            cycle.update(tick, tick % 3);
            assertEquals(0, cycle.remaining(tick));
        }
    }

    @Test void reentryCancelsOldLingerAndNextLossGetsItsOwnFullThirtyTicks() {
        var cycle = new SurroundedCycle();
        cycle.update(0, 3); cycle.update(1, 2);
        cycle.update(29, 3);
        assertTrue(cycle.active(31));
        cycle.update(40, 2);
        assertEquals(30, cycle.remaining(40));
        assertEquals(1, cycle.remaining(69));
        assertFalse(cycle.active(70));
        cycle.update(100, 3); assertTrue(cycle.active(100));
    }

    @Test void pureReadsNeitherStartNorRefreshOrConsumeLinger() {
        var cycle = new SurroundedCycle();
        assertFalse(cycle.active(0));
        cycle.update(10, 3); cycle.update(11, 0);
        for (int i = 0; i < 20; i++) assertEquals(20, cycle.remaining(21));
        assertFalse(cycle.active(41));
        assertEquals(20, cycle.remaining(21)); // Reading a future tick did not mutate state.
        assertFalse(cycle.active(10));
        assertEquals(30, cycle.remaining(11));
    }

    @Test void heldThresholdHasNoDeadlineUntilLost() {
        var cycle = new SurroundedCycle();
        cycle.update(0, 3);
        cycle.update(1_000_000, 3);
        assertEquals(30, cycle.remaining(1_000_000));
        cycle.update(1_000_001, 0);
        assertEquals(30, cycle.remaining(1_000_001));
    }

    @Test void stowingRevokesImmediatelyAndReturningBelowThresholdDoesNotRevive() {
        var cycle = new SurroundedCycle();
        cycle.update(0, 3);
        cycle.update(1, false, 3);
        assertFalse(cycle.active(1));
        cycle.update(2, true, 2);
        assertFalse(cycle.active(2));
        cycle.update(3, true, 3);
        assertTrue(cycle.active(3));
        cycle.update(4, true, 2);
        cycle.update(5, false, 2);
        assertFalse(cycle.active(5));
    }

    @Test void clearErasesThresholdAndLingerAndNeverStartsFreshLinger() {
        var cycle = new SurroundedCycle();
        cycle.update(10, 3); cycle.clear();
        assertFalse(cycle.active(10));
        cycle.update(11, 0); assertFalse(cycle.active(11));
        cycle.update(12, 3); cycle.update(13, 0); cycle.clear();
        assertEquals(0, cycle.remaining(13));
        cycle.clear(); assertFalse(cycle.active(Long.MAX_VALUE));
    }

    @Test void negativeAndBackwardObservationsFailClosed() {
        var cycle = new SurroundedCycle();
        cycle.update(100, 3);
        assertFalse(cycle.active(99));
        cycle.update(99, 3); assertFalse(cycle.active(100));
        cycle.update(101, 2); assertFalse(cycle.active(101));
        cycle.update(102, 3); cycle.update(-1, 3);
        assertFalse(cycle.active(102));
        cycle.update(103, 3); cycle.update(104, -1);
        assertFalse(cycle.active(104));
    }

    @Test void timeNearLongMaximumCannotOverflowIntoExpiredOrImmortalLinger() {
        var cycle = new SurroundedCycle();
        cycle.update(Long.MAX_VALUE - 31, 3);
        cycle.update(Long.MAX_VALUE - 30, 0);
        assertEquals(30, cycle.remaining(Long.MAX_VALUE - 30));
        assertEquals(1, cycle.remaining(Long.MAX_VALUE - 1));
        assertFalse(cycle.active(Long.MAX_VALUE));
        cycle.clear();
        cycle.update(Long.MAX_VALUE - 1, 3); cycle.update(Long.MAX_VALUE, 0);
        assertEquals(30, cycle.remaining(Long.MAX_VALUE));
        cycle.update(Long.MIN_VALUE, 0); assertFalse(cycle.active(0));
        cycle.update(0, 3); cycle.update(1, 0);
        assertFalse(cycle.active(Long.MAX_VALUE));
    }

    @Test void separateWeaponCyclesCannotBorrowEachOthersThresholdOrLinger() {
        var first = new SurroundedCycle(); var second = new SurroundedCycle();
        first.update(0, 3); second.update(0, 2);
        assertTrue(first.active(0)); assertFalse(second.active(0));
        first.update(1, false, 0); second.update(1, 2);
        assertFalse(first.active(1)); assertFalse(second.active(1));
    }

    @Test void paidEmissionKeepsSwordAndGunSnapshotsAfterStowWhileLiveBuffDisappears() {
        var cycle = new SurroundedCycle();
        cycle.update(10, 3);
        var swordEmission = cycle.capture(10, 1.35f);
        var gunEmission = cycle.capture(10, 1.4f);
        cycle.update(11, false, 3);
        assertFalse(cycle.active(11)); assertEquals(0, cycle.remaining(11));
        assertEquals(1.35f, swordEmission.multiplier());
        assertEquals(1.4f, gunEmission.multiplier());
        cycle.update(12, true, 2);
        assertEquals(1, cycle.capture(12, 1.35f).multiplier());
        assertEquals(1.35f, swordEmission.multiplier());
        var differentWeapon = new SurroundedCycle();
        differentWeapon.update(12, 2);
        assertEquals(1, differentWeapon.capture(12, 1.4f).multiplier());
    }

    @Test void proximityAndLingerChangesCannotUpgradeOrExpireAnAlreadyPaidEmission() {
        var cycle = new SurroundedCycle();
        cycle.update(0, 2);
        var unbuffed = cycle.capture(0, 1.4f);
        cycle.update(1, 3);
        var buffed = cycle.capture(1, 1.4f);
        assertEquals(1, unbuffed.multiplier());
        cycle.update(2, 2);
        var duringLinger = cycle.capture(31, 1.4f);
        assertEquals(1.4f, duringLinger.multiplier());
        assertEquals(1, cycle.capture(32, 1.4f).multiplier());
        cycle.clear();
        assertEquals(1.4f, buffed.multiplier());
        assertEquals(1.4f, duringLinger.multiplier());
        assertEquals(1, unbuffed.multiplier());
    }

    @Test void snapshotReadsStayPureAndRejectUnsupportedDamageFactors() {
        var cycle = new SurroundedCycle();
        cycle.update(0, 3); cycle.update(1, 2);
        for (int i = 0; i < 10; i++) assertEquals(1.4f, cycle.capture(20, 1.4f).multiplier());
        assertEquals(11, cycle.remaining(20));
        assertFalse(cycle.active(31));
        for (float invalid : new float[]{Float.NaN, Float.POSITIVE_INFINITY, 0, 1, 1.5f})
            assertThrows(IllegalArgumentException.class, () -> cycle.capture(20, invalid));
    }
}
