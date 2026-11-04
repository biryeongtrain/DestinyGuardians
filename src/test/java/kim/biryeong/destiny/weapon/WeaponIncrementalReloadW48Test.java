package kim.biryeong.destiny.weapon;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

/** Pure reload mechanics with synthetic profiles; catalog timing policy is tested separately. */
class WeaponIncrementalReloadW48Test {
    private static WeaponProfile profile(int capacity, int reserves, boolean infinite,
                                         boolean incremental, int firstTicks, int repeatTicks, int batch) {
        return new WeaponProfile(WeaponProfile.Mode.HITSCAN, 5, 10, capacity, reserves,
                repeatTicks, 40, 0, 1, 1, 0, 0, 0, 0, false, infinite,
                10, 1, false, incremental, firstTicks, batch);
    }

    private static WeaponProfile batchTwo(int capacity, int reserves) {
        return profile(capacity, reserves, false, true, 7, 3, 2);
    }

    private static void counts(WeaponMagazine ammo, int rounds, int reserve, long overflow, long total) {
        assertEquals(rounds, ammo.rounds());
        assertEquals(reserve, ammo.reserve());
        assertEquals(overflow, ammo.overflow());
        assertEquals(total, ammo.total());
    }

    @Test void expandedProfileRetainsIndependentFirstAndRepeatDurationsAndBatchSize() {
        var p = batchTwo(5, 10);
        assertTrue(p.shellReload());
        assertEquals(7, p.firstReloadTicks());
        assertEquals(3, p.reloadTicks());
        assertEquals(2, p.roundsPerInsert());
        assertEquals(1, profile(5, 10, false, true, 1, 3, 1).roundsPerInsert());
        assertEquals(3, profile(5, 10, false, true, 2, 3, 3).roundsPerInsert());
        assertEquals(0, profile(5, 10, false, false, 7, 3, 0).roundsPerInsert());
    }

    @Test void compatibilityConstructorKeepsEqualDeadlinesAndSingleShellOrWholeMagazine() {
        for (boolean shell : new boolean[]{false, true}) {
            var p = new WeaponProfile(WeaponProfile.Mode.HITSCAN, 5, 10, 5, 10,
                    3, 40, 0, 1, 1, 0, 0, 0, 0, false, false,
                    10, 1, false, shell);
            assertEquals(p.reloadTicks(), p.firstReloadTicks());
            assertEquals(shell ? 1 : 0, p.roundsPerInsert());
        }
    }

    @Test void nonpositiveFirstAndRepeatDurationsAreRejected() {
        for (int invalid : new int[]{0, -1, Integer.MIN_VALUE}) {
            assertThrows(IllegalArgumentException.class,
                    () -> profile(5, 10, false, true, invalid, 3, 2));
            assertThrows(IllegalArgumentException.class,
                    () -> profile(5, 10, false, true, 7, invalid, 2));
        }
    }

    @Test void batchMustBeBoundedAndAgreeWithIncrementalReloadFlag() {
        for (int invalid : new int[]{-1, 0, 4, Integer.MAX_VALUE}) {
            assertThrows(IllegalArgumentException.class,
                    () -> profile(5, 10, false, true, 7, 3, invalid));
        }
        for (int invalid : new int[]{-1, 1, 2, 3}) {
            assertThrows(IllegalArgumentException.class,
                    () -> profile(5, 10, false, false, 7, 3, invalid));
        }
    }

    @Test void reloadRoundsTransfersOnlyRequestedBatchAndConservesFiniteTotal() {
        var ammo = new WeaponMagazine(batchTwo(5, 10), 0, 8);
        assertEquals(2, ammo.reloadRounds(2));
        counts(ammo, 2, 6, 0, 8);
        assertEquals(1, ammo.reloadRounds(1));
        counts(ammo, 3, 5, 0, 8);
    }

    @Test void nonpositiveRoundLimitsNeverMoveOrPromoteOverflow() {
        var ammo = new WeaponMagazine(batchTwo(5, 10), 0, 10, 5);
        for (int limit : new int[]{0, -1, Integer.MIN_VALUE}) {
            assertEquals(0, ammo.reloadRounds(limit));
            counts(ammo, 0, 10, 5, 15);
        }
    }

    @Test void oddCapacityEndsWithOneRoundAndFullMagazineAcceptsNothing() {
        var ammo = new WeaponMagazine(batchTwo(5, 10), 0, 10);
        assertEquals(2, ammo.reloadRounds(2));
        assertEquals(2, ammo.reloadRounds(2));
        assertEquals(1, ammo.reloadRounds(2));
        counts(ammo, 5, 5, 0, 10);
        assertFalse(ammo.canReload());
        assertEquals(0, ammo.reloadRounds(Integer.MAX_VALUE));
        counts(ammo, 5, 5, 0, 10);
    }

    @Test void oddFiniteReserveEndsWithPartialBatchWithoutInventingAmmo() {
        var ammo = new WeaponMagazine(batchTwo(7, 10), 0, 3);
        assertEquals(2, ammo.reloadRounds(2));
        counts(ammo, 2, 1, 0, 3);
        assertEquals(1, ammo.reloadRounds(2));
        counts(ammo, 3, 0, 0, 3);
        assertFalse(ammo.canReload());
        assertEquals(0, ammo.reloadRounds(2));
        assertFalse(new WeaponMagazine(batchTwo(7, 10), 0, 0).canReload());
    }

    @Test void oversizedPositiveRoundLimitIsClampedToSpaceAndAvailableAmmo() {
        var roomLimited = new WeaponMagazine(batchTwo(5, 10), 4, 10);
        assertEquals(1, roomLimited.reloadRounds(Integer.MAX_VALUE));
        counts(roomLimited, 5, 9, 0, 14);
        var ammoLimited = new WeaponMagazine(batchTwo(5, 10), 0, 3);
        assertEquals(3, ammoLimited.reloadRounds(Integer.MAX_VALUE));
        counts(ammoLimited, 3, 0, 0, 3);
    }

    @Test void batchReloadPromotesW47OverflowWithoutLosingAmmoOrAllowingPickupBypass() {
        var ammo = new WeaponMagazine(batchTwo(5, 3), 0, 3, 5);
        assertEquals(2, ammo.reloadRounds(2));
        counts(ammo, 2, 3, 3, 8);
        assertEquals(0, ammo.addReserve(2));
        assertEquals(2, ammo.reloadRounds(2));
        counts(ammo, 4, 3, 1, 8);
        assertEquals(1, ammo.reloadRounds(2));
        counts(ammo, 5, 3, 0, 8);
        assertTrue(ammo.consume());
        counts(ammo, 4, 3, 0, 7);
        assertEquals(1, ammo.reloadRounds(2));
        counts(ammo, 5, 2, 0, 7);
    }

    @Test void zeroReserveCapacityStillAllowsPartialBatchesFromSavedOverflow() {
        var ammo = new WeaponMagazine(batchTwo(5, 0), 0, 0, 3);
        assertEquals(2, ammo.reloadRounds(2));
        counts(ammo, 2, 0, 1, 3);
        assertEquals(1, ammo.reloadRounds(2));
        counts(ammo, 3, 0, 0, 3);
        assertFalse(ammo.canReload());
        assertEquals(0, ammo.reloadRounds(2));
    }

    @Test void saturatedW47FiniteTotalSurvivesBatchTransferAndOnlyShotReducesIt() {
        var ammo = new WeaponMagazine(batchTwo(5, 3), 0, Long.MAX_VALUE, Long.MAX_VALUE);
        counts(ammo, 0, 3, Long.MAX_VALUE - 3, Long.MAX_VALUE);
        assertEquals(2, ammo.reloadRounds(2));
        counts(ammo, 2, 3, Long.MAX_VALUE - 5, Long.MAX_VALUE);
        assertEquals(0, ammo.addReserve(Integer.MAX_VALUE));
        assertTrue(ammo.consume());
        assertEquals(2, ammo.reloadRounds(2));
        counts(ammo, 3, 3, Long.MAX_VALUE - 7, Long.MAX_VALUE - 1);
    }

    @Test void infiniteReserveBatchRetiresSavedExcessBeforeSupplyingNewRounds() {
        var p = profile(5, 0, true, true, 7, 3, 2);
        var ammo = new WeaponMagazine(p, 0, Integer.MAX_VALUE, 3);
        counts(ammo, 0, 0, 3, 3);
        assertEquals(2, ammo.reloadRounds(2));
        counts(ammo, 2, 0, 1, 3);
        assertEquals(2, ammo.reloadRounds(2));
        counts(ammo, 4, 0, 0, 4);
        assertEquals(1, ammo.reloadRounds(2));
        counts(ammo, 5, 0, 0, 5);
        assertEquals(0, ammo.reloadRounds(2));
    }

    @Test void cycleUsesFirstDeadlineThenRepeatDeadlineForEachAtomicBatch() {
        var p = batchTwo(7, 10);
        var ammo = new WeaponMagazine(p, 0, 10);
        var cycle = new WeaponCycle();
        assertTrue(cycle.startReload(100, p, ammo));
        assertEquals(7, cycle.reloadPhaseTicks());
        assertEquals(7, cycle.reloadRemaining(100));
        assertFalse(cycle.ready(106));
        assertFalse(cycle.finishReload(106, ammo));
        counts(ammo, 0, 10, 0, 10);
        assertTrue(cycle.finishReload(107, ammo));
        counts(ammo, 2, 8, 0, 10);
        assertTrue(cycle.reloading());
        assertEquals(3, cycle.reloadPhaseTicks());
        assertEquals(3, cycle.reloadRemaining(107));
        assertFalse(cycle.finishReload(109, ammo));
        assertTrue(cycle.finishReload(110, ammo));
        counts(ammo, 4, 6, 0, 10);
        assertEquals(3, cycle.reloadRemaining(110));
    }

    @Test void cycleCompletesOddCapacityWithFinalSingleRoundAndClearsPhase() {
        var p = batchTwo(5, 10);
        var ammo = new WeaponMagazine(p, 0, 10);
        var cycle = new WeaponCycle();
        assertTrue(cycle.startReload(0, p, ammo));
        assertTrue(cycle.finishReload(7, ammo));
        assertTrue(cycle.finishReload(10, ammo));
        counts(ammo, 4, 6, 0, 10);
        assertFalse(cycle.finishReload(12, ammo));
        assertTrue(cycle.finishReload(13, ammo));
        counts(ammo, 5, 5, 0, 10);
        assertFalse(cycle.reloading());
        assertEquals(0, cycle.reloadPhaseTicks());
        assertEquals(0, cycle.reloadRemaining(13));
        assertTrue(cycle.ready(13));
        assertFalse(cycle.finishReload(1000, ammo));
    }

    @Test void cycleStopsOnOddReserveEvenWithMagazineSpaceRemaining() {
        var p = batchTwo(7, 10);
        var ammo = new WeaponMagazine(p, 0, 3);
        var cycle = new WeaponCycle();
        assertTrue(cycle.startReload(0, p, ammo));
        assertTrue(cycle.finishReload(7, ammo));
        counts(ammo, 2, 1, 0, 3);
        assertTrue(cycle.reloading());
        assertTrue(cycle.finishReload(10, ammo));
        counts(ammo, 3, 0, 0, 3);
        assertFalse(cycle.reloading());
        assertEquals(0, cycle.reloadPhaseTicks());
        assertFalse(cycle.startReload(11, p, ammo));
        assertFalse(cycle.finishReload(1000, ammo));
    }

    @Test void redundantReloadStartCannotResetFirstOrRepeatDeadline() {
        var p = batchTwo(7, 10);
        var ammo = new WeaponMagazine(p, 0, 10);
        var cycle = new WeaponCycle();
        assertTrue(cycle.startReload(0, p, ammo));
        assertFalse(cycle.startReload(6, p, ammo));
        assertEquals(1, cycle.reloadRemaining(6));
        assertTrue(cycle.finishReload(7, ammo));
        assertFalse(cycle.startReload(8, p, ammo));
        assertEquals(2, cycle.reloadRemaining(8));
        assertTrue(cycle.finishReload(10, ammo));
        counts(ammo, 4, 6, 0, 10);
    }

    @Test void cancellationBeforeFirstDeadlineMovesNoAmmoAndRestartUsesFullFirstDelay() {
        var p = batchTwo(5, 3);
        var ammo = new WeaponMagazine(p, 0, 3, 5);
        var cycle = new WeaponCycle();
        assertTrue(cycle.startReload(0, p, ammo));
        assertFalse(cycle.finishReload(6, ammo));
        cycle.cancelPending();
        assertFalse(cycle.reloading());
        assertEquals(0, cycle.reloadPhaseTicks());
        assertFalse(cycle.finishReload(1000, ammo));
        counts(ammo, 0, 3, 5, 8);
        assertTrue(cycle.startReload(1000, p, ammo));
        assertEquals(7, cycle.reloadPhaseTicks());
        assertFalse(cycle.finishReload(1006, ammo));
        assertTrue(cycle.finishReload(1007, ammo));
        counts(ammo, 2, 3, 3, 8);
    }

    @Test void cancellationAfterBatchKeepsExactlyInsertedRoundsAndW47Overflow() {
        var p = batchTwo(5, 3);
        var ammo = new WeaponMagazine(p, 0, 3, 5);
        var cycle = new WeaponCycle();
        assertTrue(cycle.startReload(0, p, ammo));
        assertTrue(cycle.finishReload(7, ammo));
        cycle.cancelPending();
        assertFalse(cycle.finishReload(1000, ammo));
        counts(ammo, 2, 3, 3, 8);
        assertTrue(cycle.startReload(1000, p, ammo));
        assertEquals(7, cycle.reloadPhaseTicks());
        assertFalse(cycle.finishReload(1003, ammo));
        assertTrue(cycle.finishReload(1007, ammo));
        counts(ammo, 4, 3, 1, 8);
    }

    @Test void emptyMagazineCannotInterruptBeforeFirstBatchEvenWhenDeadlineIsOverdue() {
        var p = batchTwo(5, 10);
        var ammo = new WeaponMagazine(p, 0, 10);
        var cycle = new WeaponCycle();
        assertTrue(cycle.startReload(0, p, ammo));
        assertFalse(cycle.interruptReloadForShot(6, ammo));
        assertFalse(cycle.interruptReloadForShot(1000, ammo));
        assertFalse(cycle.fire(1000, p, ammo));
        counts(ammo, 0, 10, 0, 10);
        assertTrue(cycle.reloading());
        assertTrue(cycle.finishReload(1000, ammo));
        counts(ammo, 2, 8, 0, 10);
    }

    @Test void shotInterruptAfterBatchSpendsOnlyShotAndNeverTransfersNextBatch() {
        var p = batchTwo(5, 3);
        var ammo = new WeaponMagazine(p, 0, 3, 5);
        var cycle = new WeaponCycle();
        assertTrue(cycle.startReload(0, p, ammo));
        assertTrue(cycle.finishReload(7, ammo));
        assertFalse(cycle.fire(8, p, ammo));
        assertTrue(cycle.interruptReloadForShot(8, ammo));
        counts(ammo, 2, 3, 3, 8);
        assertFalse(cycle.reloading());
        assertTrue(cycle.fire(8, p, ammo));
        counts(ammo, 1, 3, 3, 7);
        assertFalse(cycle.finishReload(1000, ammo));
        assertFalse(cycle.interruptReloadForShot(1000, ammo));
        counts(ammo, 1, 3, 3, 7);
    }

    @Test void existingLoadedRoundCanInterruptWithoutGrantingFirstBatch() {
        var p = batchTwo(5, 10);
        var ammo = new WeaponMagazine(p, 1, 5);
        var cycle = new WeaponCycle();
        assertTrue(cycle.startReload(0, p, ammo));
        assertTrue(cycle.interruptReloadForShot(1, ammo));
        assertTrue(cycle.fire(1, p, ammo));
        counts(ammo, 0, 5, 0, 5);
        assertFalse(cycle.finishReload(1000, ammo));
    }

    @Test void interruptionRespectsSharedShotCooldownAndCancellationDoesNotResetIt() {
        var p = profile(5, 10, false, true, 2, 3, 2);
        var ammo = new WeaponMagazine(p, 1, 5);
        var cycle = new WeaponCycle();
        assertTrue(cycle.fire(0, p, ammo));
        assertTrue(cycle.startReload(0, p, ammo));
        assertTrue(cycle.finishReload(2, ammo));
        counts(ammo, 2, 3, 0, 5);
        assertFalse(cycle.interruptReloadForShot(9, ammo));
        assertTrue(cycle.reloading());
        assertTrue(cycle.interruptReloadForShot(10, ammo));
        assertTrue(cycle.fire(10, p, ammo));
        cycle.cancelPending();
        assertFalse(cycle.fire(19, p, ammo));
        assertTrue(cycle.fire(20, p, ammo));
        counts(ammo, 0, 3, 0, 3);
        assertFalse(cycle.finishReload(1000, ammo));
    }

    @Test void wholeMagazineReloadUsesFirstDeadlineAndCannotBeShotInterrupted() {
        var p = profile(5, 10, false, false, 7, 3, 0);
        var ammo = new WeaponMagazine(p, 1, 5);
        var cycle = new WeaponCycle();
        assertTrue(cycle.startReload(0, p, ammo));
        assertFalse(cycle.interruptReloadForShot(1, ammo));
        assertFalse(cycle.finishReload(3, ammo));
        assertFalse(cycle.finishReload(6, ammo));
        assertTrue(cycle.finishReload(7, ammo));
        counts(ammo, 5, 1, 0, 6);
        assertFalse(cycle.reloading());
        assertEquals(0, cycle.reloadPhaseTicks());
    }

    @Test void lateFirstCallTransfersAtMostOneBatchAndAnchorsRepeatToActualCall() {
        var p = batchTwo(7, 10);
        var ammo = new WeaponMagazine(p, 0, 10);
        var cycle = new WeaponCycle();
        assertTrue(cycle.startReload(0, p, ammo));
        assertTrue(cycle.finishReload(1000, ammo));
        counts(ammo, 2, 8, 0, 10);
        assertEquals(3, cycle.reloadPhaseTicks());
        assertEquals(3, cycle.reloadRemaining(1000));
        for (int duplicate = 0; duplicate < 20; duplicate++) {
            assertFalse(cycle.finishReload(1000, ammo));
        }
        assertFalse(cycle.finishReload(1002, ammo));
        counts(ammo, 2, 8, 0, 10);
        assertTrue(cycle.finishReload(1003, ammo));
        counts(ammo, 4, 6, 0, 10);
    }

    @Test void lateRepeatCallCannotCatchUpMissedBatchesOrDrainReserveInOneTick() {
        var p = batchTwo(9, 10);
        var ammo = new WeaponMagazine(p, 0, 10);
        var cycle = new WeaponCycle();
        assertTrue(cycle.startReload(0, p, ammo));
        assertTrue(cycle.finishReload(7, ammo));
        assertTrue(cycle.finishReload(1000, ammo));
        counts(ammo, 4, 6, 0, 10);
        assertEquals(3, cycle.reloadRemaining(1000));
        for (int duplicate = 0; duplicate < 20; duplicate++) {
            assertFalse(cycle.finishReload(1000, ammo));
        }
        assertFalse(cycle.finishReload(1002, ammo));
        assertTrue(cycle.finishReload(1003, ammo));
        counts(ammo, 6, 4, 0, 10);
        assertEquals(3, cycle.reloadRemaining(1003));
    }
}
