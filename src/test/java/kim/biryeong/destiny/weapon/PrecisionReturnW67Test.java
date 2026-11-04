package kim.biryeong.destiny.weapon;

import org.junit.jupiter.api.Test;
import java.util.ArrayList;
import java.util.List;
import static org.junit.jupiter.api.Assertions.*;

/** Pure W67 contracts; runtime ownership, selected sockets and serialization belong to integration tests. */
class PrecisionReturnW67Test {
    private static WeaponProfile profile(int capacity, int reserve, boolean infinite) {
        return new WeaponProfile(WeaponProfile.Mode.HITSCAN, 1, 10, capacity, reserve,
                20, 48, 0, 1, 1, 0, 0, 0, 0, false, infinite,
                10, 0, false, false);
    }

    private static void ammo(WeaponMagazine magazine, int rounds, int reserve, long overflow, long total) {
        assertEquals(rounds, magazine.rounds(), "loaded rounds");
        assertEquals(reserve, magazine.reserve(), "reserve rounds");
        assertEquals(overflow, magazine.overflow(), "conserved overflow");
        assertEquals(total, magazine.total(), "total ammunition");
    }

    @Test void sameTickEventsCompleteExactlyThreeOrFourHitsAndNeverOverlapGroups() {
        var triple = new PrecisionReturnCycle(3, 40);
        int[] tripleProgress = {1, 2, 0, 1, 2, 0, 1};
        boolean[] tripleReturns = {false, false, true, false, false, true, false};
        for (int i = 0; i < tripleProgress.length; i++) {
            assertEquals(tripleReturns[i], triple.hit(100), "triple event " + i);
            assertEquals(tripleProgress[i], triple.progress(100));
        }
        var fourth = new PrecisionReturnCycle(4, 40);
        int[] fourthProgress = {1, 2, 3, 0, 1, 2, 3, 0, 1};
        boolean[] fourthReturns = {false, false, false, true, false, false, false, true, false};
        for (int i = 0; i < fourthProgress.length; i++) {
            assertEquals(fourthReturns[i], fourth.hit(100), "fourth event " + i);
            assertEquals(fourthProgress[i], fourth.progress(100));
        }
    }

    @Test void windowIsPairwiseAndThirtyNineTicksSurviveWhileExactlyFortyExpire() {
        var triple = new PrecisionReturnCycle(3, 40);
        assertFalse(triple.hit(10));
        assertFalse(triple.hit(49));
        assertEquals(2, triple.progress(88));
        assertTrue(triple.hit(88)); // 78 ticks since the first hit is still a valid group.
        assertEquals(0, triple.progress(88));
        var fourth = new PrecisionReturnCycle(4, 40);
        assertFalse(fourth.hit(10));
        assertFalse(fourth.hit(49));
        assertFalse(fourth.hit(88));
        assertEquals(3, fourth.progress(127));
        assertTrue(fourth.hit(127)); // 117 ticks from first to last, each gap is 39.
        assertEquals(0, fourth.progress(127));

        for (int required : new int[]{3, 4}) {
            var boundary = new PrecisionReturnCycle(required, 40);
            assertFalse(boundary.hit(0));
            assertFalse(boundary.hit(39));
            assertEquals(2, boundary.progress(78));
            assertEquals(0, boundary.progress(79));
            assertFalse(boundary.hit(79), "the hit at the deadline starts a fresh group");
            assertEquals(1, boundary.progress(79));
            assertFalse(boundary.hit(118));
            assertEquals(2, boundary.progress(118));
        }
    }

    @Test void skippedTicksResetBeforeCountingTheNewHitWithoutAnUpdateOrRead() {
        var cycle = new PrecisionReturnCycle(3, 40);
        assertFalse(cycle.hit(0));
        assertFalse(cycle.hit(1));
        assertFalse(cycle.hit(10000));
        assertEquals(1, cycle.progress(10000));
        assertFalse(cycle.hit(10039));
        assertEquals(2, cycle.progress(10039));
        assertFalse(cycle.hit(10079)); // Another exact 40-tick gap, with no intervening query.
        assertEquals(1, cycle.progress(10079));
        assertFalse(cycle.hit(10080));
        assertTrue(cycle.hit(10081));
        assertEquals(0, cycle.progress(10081));
        assertFalse(cycle.hit(1000000));
        assertEquals(1, cycle.progress(1000000));
    }

    @Test void repeatedFutureNegativeAndBackwardProgressReadsNeverMutateOrRefresh() {
        var cycle = new PrecisionReturnCycle(3, 40);
        for (long tick : new long[]{Long.MIN_VALUE, -1, 0, 100, Long.MAX_VALUE})
            assertEquals(0, cycle.progress(tick));
        assertFalse(cycle.hit(100));
        assertFalse(cycle.hit(101));
        for (int read = 0; read < 8; read++) {
            assertEquals(2, cycle.progress(101));
            assertEquals(2, cycle.progress(140));
            assertEquals(0, cycle.progress(141));
            assertEquals(0, cycle.progress(Long.MAX_VALUE));
            assertEquals(0, cycle.progress(Long.MIN_VALUE));
            assertEquals(0, cycle.progress(-1));
            assertEquals(0, cycle.progress(100));
            assertEquals(2, cycle.progress(101));
        }
        assertTrue(cycle.hit(102), "future reads did not commit expiration or advance lastHit");
        assertEquals(0, cycle.progress(102));

        var unrefreshed = new PrecisionReturnCycle(3, 40);
        assertFalse(unrefreshed.hit(100));
        for (int read = 0; read < 8; read++) assertEquals(1, unrefreshed.progress(139));
        assertEquals(0, unrefreshed.progress(140));
        assertFalse(unrefreshed.hit(140), "queries at 139 cannot refresh the deadline");
        assertEquals(1, unrefreshed.progress(140));
    }

    @Test void negativeAndBackwardHitsRetainProgressAndTheLastAcceptedTickEvenAfterSuccess() {
        var cycle = new PrecisionReturnCycle(3, 40);
        assertFalse(cycle.hit(Long.MIN_VALUE));
        assertFalse(cycle.hit(-1));
        assertEquals(0, cycle.progress(0));
        assertFalse(cycle.hit(100));
        assertFalse(cycle.hit(110));
        for (long bad : new long[]{Long.MIN_VALUE, -1, 0, 99, 100, 109}) {
            assertFalse(cycle.hit(bad));
            assertEquals(2, cycle.progress(110));
            assertEquals(2, cycle.progress(149));
            assertEquals(0, cycle.progress(150));
        }
        assertTrue(cycle.hit(110));
        assertEquals(0, cycle.progress(110));
        assertFalse(cycle.hit(109));
        assertFalse(cycle.hit(-1));
        assertEquals(0, cycle.progress(110));
        assertFalse(cycle.hit(110));
        assertEquals(1, cycle.progress(110));
        assertFalse(cycle.hit(110));
        assertEquals(2, cycle.progress(110));
        assertTrue(cycle.hit(110));
    }

    @Test void constructorRejectsUnsafeArgumentsAndAcceptsBothDocumentedExtremes() {
        for (int required : new int[]{Integer.MIN_VALUE, -1, 0, 1, 17, Integer.MAX_VALUE})
            assertThrows(IllegalArgumentException.class, () -> new PrecisionReturnCycle(required, 40));
        for (int window : new int[]{Integer.MIN_VALUE, -1, 0, 1201, Integer.MAX_VALUE})
            assertThrows(IllegalArgumentException.class, () -> new PrecisionReturnCycle(3, window));
        var minimum = new PrecisionReturnCycle(2, 1);
        assertFalse(minimum.hit(0));
        assertEquals(1, minimum.progress(0));
        assertEquals(0, minimum.progress(1));
        assertFalse(minimum.hit(1));
        assertTrue(minimum.hit(1));
        assertEquals(0, minimum.progress(1));
        var maximum = new PrecisionReturnCycle(16, 1200);
        assertFalse(maximum.hit(100));
        assertEquals(1, maximum.progress(1299));
        assertEquals(0, maximum.progress(1300));
        for (int count = 2; count <= 15; count++) {
            assertFalse(maximum.hit(1299));
            assertEquals(count, maximum.progress(1299));
        }
        assertTrue(maximum.hit(1299));
        assertEquals(0, maximum.progress(1299));
    }

    @Test void elapsedArithmeticPreservesGroupsAndTheExactDeadlineNearLongMaxValue() {
        var triple = new PrecisionReturnCycle(3, 40);
        assertFalse(triple.hit(Long.MAX_VALUE - 78));
        assertFalse(triple.hit(Long.MAX_VALUE - 39));
        assertEquals(2, triple.progress(Long.MAX_VALUE));
        assertTrue(triple.hit(Long.MAX_VALUE));
        assertEquals(0, triple.progress(Long.MAX_VALUE));
        var fourth = new PrecisionReturnCycle(4, 40);
        assertFalse(fourth.hit(Long.MAX_VALUE - 117));
        assertFalse(fourth.hit(Long.MAX_VALUE - 78));
        assertFalse(fourth.hit(Long.MAX_VALUE - 39));
        assertTrue(fourth.hit(Long.MAX_VALUE));

        var deadline = new PrecisionReturnCycle(3, 40);
        assertFalse(deadline.hit(Long.MAX_VALUE - 40));
        assertEquals(1, deadline.progress(Long.MAX_VALUE - 1));
        assertEquals(0, deadline.progress(Long.MAX_VALUE));
        assertFalse(deadline.hit(Long.MAX_VALUE));
        assertEquals(1, deadline.progress(Long.MAX_VALUE));
        assertFalse(deadline.hit(Long.MAX_VALUE - 1));
        assertEquals(1, deadline.progress(Long.MAX_VALUE));
        assertFalse(deadline.hit(Long.MAX_VALUE));
        assertTrue(deadline.hit(Long.MAX_VALUE));

        var jumped = new PrecisionReturnCycle(3, 40);
        assertFalse(jumped.hit(0));
        assertEquals(0, jumped.progress(Long.MAX_VALUE));
        assertFalse(jumped.hit(Long.MAX_VALUE));
        assertEquals(1, jumped.progress(Long.MAX_VALUE));
        assertEquals(0, jumped.progress(Long.MIN_VALUE));
    }

    @Test void fullMagazineCallbackConsumesTheGroupAndSpaceLaterRequiresAWholeNewGroup() {
        for (int[] trait : new int[][]{{3, 1}, {4, 2}}) {
            var cycle = new PrecisionReturnCycle(trait[0], 40);
            var magazine = new WeaponMagazine(profile(4, 20, false), 4, 0);
            int callbacks = 0;
            int granted = 0;
            for (int event = 0; event < trait[0]; event++) {
                if (cycle.hit(100)) {
                    callbacks++;
                    granted += magazine.generateLoaded(trait[1]);
                }
            }
            assertEquals(1, callbacks);
            assertEquals(0, granted);
            assertEquals(0, cycle.progress(100));
            ammo(magazine, 4, 0, 0, 4);
            assertTrue(magazine.consume(2));
            for (int event = 1; event < trait[0]; event++) {
                assertFalse(cycle.hit(101));
                assertEquals(event, cycle.progress(101));
                ammo(magazine, 2, 0, 0, 2);
            }
            assertTrue(cycle.hit(101));
            assertEquals(trait[1], magazine.generateLoaded(trait[1]));
            assertEquals(0, cycle.progress(101));
            if (trait[0] == 3) ammo(magazine, 3, 0, 0, 3);
            else ammo(magazine, 4, 0, 0, 4);
            assertFalse(cycle.hit(101));
            assertEquals(1, cycle.progress(101));
        }
        var partialCycle = new PrecisionReturnCycle(4, 40);
        var partialAmmo = new WeaponMagazine(profile(4, 20, false), 3, 0);
        assertFalse(partialCycle.hit(0));
        assertFalse(partialCycle.hit(0));
        assertFalse(partialCycle.hit(0));
        assertTrue(partialCycle.hit(0));
        assertEquals(1, partialAmmo.generateLoaded(2));
        assertEquals(0, partialCycle.progress(0));
        ammo(partialAmmo, 4, 0, 0, 4);
    }

    @Test void explicitGrantsWorkWithEmptyReservesForFiniteSpecialHeavyAndInfinitePrimary() {
        // Synthetic capacities keep this independent of unfinished catalog/socket eligibility data.
        // Columns: base capacity, reserve capacity, infinite flag, accepted after the first two rounds.
        for (int[] row : new int[][]{{4, 20, 0, 2}, {6, 18, 0, 4}, {10, 0, 1, 8}}) {
            var magazine = new WeaponMagazine(profile(row[0], row[1], row[2] == 1), 0, 0);
            ammo(magazine, 0, 0, 0, 0);
            for (int invalid : new int[]{Integer.MIN_VALUE, -1, 0}) {
                assertEquals(0, magazine.generateLoaded(invalid));
                ammo(magazine, 0, 0, 0, 0);
            }
            if (row[2] == 0) {
                assertFalse(magazine.canReload());
                assertEquals(0, magazine.reload());
            }
            assertEquals(0, magazine.addLoaded(2), "ordinary ranged pools cannot use sword pickup grants");
            assertEquals(2, magazine.generateLoaded(2));
            ammo(magazine, 2, 0, 0, 2);
            assertEquals(row[3], magazine.generateLoaded(Integer.MAX_VALUE));
            ammo(magazine, row[0], 0, 0, row[0]);
            assertEquals(0, magazine.generateLoaded(1));
            assertFalse(magazine.canReload());
            assertTrue(magazine.consume(row[0]));
            ammo(magazine, 0, 0, 0, 0);
            assertFalse(magazine.consume(), "infinite primary reserves never make firing free");
        }
    }

    @Test void grantsPreserveFiniteReserveAndLegacyOverflowWhileRealReloadTransfersAmmo() {
        var finite = new WeaponMagazine(profile(4, 20, false), 1, 20, 7);
        ammo(finite, 1, 20, 7, 28);
        assertEquals(2, finite.generateLoaded(2));
        ammo(finite, 3, 20, 7, 30);
        assertEquals(1, finite.generateLoaded(Integer.MAX_VALUE));
        ammo(finite, 4, 20, 7, 31);
        assertTrue(finite.consume(3));
        ammo(finite, 1, 20, 7, 28);
        assertEquals(3, finite.reload());
        ammo(finite, 4, 20, 4, 28);

        var primary = new WeaponMagazine(profile(4, 0, true), 1, 999, 7);
        ammo(primary, 1, 0, 7, 8);
        assertEquals(2, primary.generateLoaded(2));
        ammo(primary, 3, 0, 7, 10);
        assertEquals(1, primary.reload());
        ammo(primary, 4, 0, 6, 10); // Ordinary primary reload retires overflow; a grant did not.
    }

    @Test void grantsRespectTheTotalCeilingAndIntegerMaxAmountsWithoutOverflowOrDebtTransfer() {
        assertEquals(Long.MAX_VALUE, WeaponAmmoMigration.MAX_TOTAL);
        for (boolean infinite : new boolean[]{false, true}) {
            var magazine = new WeaponMagazine(profile(4, infinite ? 0 : 20, infinite), 1,
                    infinite ? 0 : 20, infinite ? Long.MAX_VALUE - 2 : Long.MAX_VALUE - 22);
            long savedOverflow = infinite ? Long.MAX_VALUE - 2 : Long.MAX_VALUE - 22;
            int savedReserve = infinite ? 0 : 20;
            ammo(magazine, 1, savedReserve, savedOverflow, Long.MAX_VALUE - 1);
            assertEquals(1, magazine.generateLoaded(Integer.MAX_VALUE));
            ammo(magazine, 2, savedReserve, savedOverflow, Long.MAX_VALUE);
            for (int amount : new int[]{Integer.MIN_VALUE, -1, 0, 1, Integer.MAX_VALUE}) {
                assertEquals(0, magazine.generateLoaded(amount));
                ammo(magazine, 2, savedReserve, savedOverflow, Long.MAX_VALUE);
            }
            assertTrue(magazine.consume());
            ammo(magazine, 1, savedReserve, savedOverflow, Long.MAX_VALUE - 1);
            assertEquals(1, magazine.generateLoaded(2));
            ammo(magazine, 2, savedReserve, savedOverflow, Long.MAX_VALUE);
        }
        var huge = new WeaponMagazine(profile(Integer.MAX_VALUE, 0, false), 0, 0);
        assertEquals(Integer.MAX_VALUE, huge.generateLoaded(Integer.MAX_VALUE));
        ammo(huge, Integer.MAX_VALUE, 0, 0, 2147483647L);
        assertEquals(0, huge.generateLoaded(Integer.MAX_VALUE));
        ammo(huge, Integer.MAX_VALUE, 0, 0, 2147483647L);
    }

    @Test void rewardedRoundsAreStillPaidAndCannotResetCooldownOrCompleteAnActiveReload() {
        var p = profile(4, 20, false);
        var magazine = new WeaponMagazine(p, 3, 5);
        var cycle = new WeaponCycle();
        assertTrue(cycle.fire(0, p, magazine));
        ammo(magazine, 2, 5, 0, 7);
        assertFalse(cycle.fire(0, p, magazine));
        assertEquals(2, magazine.generateLoaded(2));
        ammo(magazine, 4, 5, 0, 9);
        assertFalse(cycle.reloading());
        assertEquals(10.0, cycle.firingDeadline());
        assertFalse(cycle.fire(9, p, magazine));
        assertTrue(cycle.fire(10, p, magazine));
        ammo(magazine, 3, 5, 0, 8);
        assertTrue(magazine.consume(2));
        ammo(magazine, 1, 5, 0, 6);
        for (int invalid : new int[]{Integer.MIN_VALUE, -1, 0, 2, Integer.MAX_VALUE}) {
            assertFalse(magazine.consume(invalid));
            ammo(magazine, 1, 5, 0, 6);
        }
        assertTrue(magazine.consume());
        assertFalse(magazine.consume());
        assertFalse(cycle.fire(20, p, magazine));
        ammo(magazine, 0, 5, 0, 5);
        assertEquals(2, magazine.generateLoaded(2));
        assertTrue(cycle.startReload(20, p, magazine));
        assertEquals(1, magazine.generateLoaded(1));
        ammo(magazine, 3, 5, 0, 8);
        assertTrue(cycle.reloading());
        assertEquals(20, cycle.reloadPhaseTicks());
        assertEquals(20, cycle.reloadRemaining(20));
        assertFalse(cycle.fire(30, p, magazine));
        assertFalse(cycle.finishReload(39, magazine));
        ammo(magazine, 3, 5, 0, 8);
        assertTrue(cycle.finishReload(40, magazine));
        ammo(magazine, 4, 4, 0, 8);
        assertFalse(cycle.reloading());
        assertTrue(cycle.fire(40, p, magazine));
        ammo(magazine, 3, 4, 0, 7);
    }

    @Test void profileCollectionsAreImmutableAndPerkDefensivelyCopiesItsWeaponList() {
        var original = new WeaponPerks.Roll("test_original", 11L, 3, 3400784728L, 22L);
        var replacement = new WeaponPerks.Roll("test_replacement", 33L, 4, 3400784728L, 44L);
        var source = new ArrayList<>(List.of(original));
        var perk = new PrecisionReturnProfile.Perk("triple_tap", 3400784728L, 3, 1, 40, source);
        source.set(0, replacement);
        source.clear();
        source.add(replacement);
        assertEquals(List.of(original), perk.weapons());
        assertEquals("triple_tap", perk.id());
        assertEquals(3400784728L, perk.hash());
        assertEquals(3, perk.hits());
        assertEquals(1, perk.returnRounds());
        assertEquals(40, perk.windowTicks());
        assertThrows(UnsupportedOperationException.class, () -> perk.weapons().add(replacement));
        assertThrows(UnsupportedOperationException.class, () -> perk.weapons().set(0, replacement));
        assertThrows(UnsupportedOperationException.class, () -> perk.weapons().remove(0));
        assertEquals(List.of(original), perk.weapons());

        // Deliberately no eligibility count or weapon identity assertion while source data is being frozen.
        var profiles = PrecisionReturnProfile.perks();
        assertThrows(UnsupportedOperationException.class, () -> profiles.add(perk));
        assertThrows(UnsupportedOperationException.class, profiles::clear);
        for (var loaded : profiles) {
            assertThrows(UnsupportedOperationException.class, () -> loaded.weapons().add(original));
            assertThrows(UnsupportedOperationException.class, () -> loaded.weapons().set(0, replacement));
            assertThrows(UnsupportedOperationException.class, () -> loaded.weapons().remove(0));
        }
    }
}
