package kim.biryeong.destiny.weapon;

import org.junit.jupiter.api.Test;
import java.util.UUID;
import static org.junit.jupiter.api.Assertions.*;

class OneForAllCycleTest {
    private static final UUID A = new UUID(0, 1), B = new UUID(0, 2), C = new UUID(0, 3), D = new UUID(0, 4);

    private static OneForAllCycle active(long tick) {
        var cycle = new OneForAllCycle();
        assertTrue(cycle.confirmed(tick, A));
        assertTrue(cycle.confirmed(tick, B));
        assertTrue(cycle.confirmed(tick, C));
        return cycle;
    }

    @Test void sequentialDistinctTargetsRenewWindowAtZero59And118() {
        var cycle = new OneForAllCycle();
        assertTrue(cycle.confirmed(0, A));
        assertEquals(1, cycle.progress(58));
        assertEquals(0, cycle.remaining(58));
        assertTrue(cycle.confirmed(59, B));
        assertEquals(2, cycle.progress(117));
        float thirdHitSnapshot = cycle.multiplier(118);
        assertTrue(cycle.confirmed(118, C));
        assertEquals(1f, thirdHitSnapshot);
        assertEquals(1.35f, cycle.multiplier(118));
        assertEquals(200, cycle.remaining(118));
        assertEquals(0, cycle.progress(118));
    }

    @Test void duplicateUuidDoesNotRefreshOrAdvance() {
        var cycle = new OneForAllCycle();
        cycle.confirmed(0, A);
        assertFalse(cycle.confirmed(59, UUID.fromString(A.toString())));
        assertEquals(1, cycle.progress(59));
        assertEquals(0, cycle.progress(60));
        assertTrue(cycle.confirmed(60, B));
        assertEquals(1, cycle.progress(60));
        assertEquals(0, cycle.remaining(60));
    }

    @Test void duplicateOfEitherCollectedTargetDoesNotExtendSecondWindow() {
        var cycle = new OneForAllCycle();
        cycle.confirmed(0, A);
        cycle.confirmed(59, B);
        assertFalse(cycle.confirmed(117, A));
        assertFalse(cycle.confirmed(118, B));
        assertEquals(2, cycle.progress(118));
        assertTrue(cycle.confirmed(119, C));
        assertEquals(1, cycle.progress(119));
        assertEquals(0, cycle.remaining(119));
    }

    @Test void exactFirstCollectionBoundaryStartsFreshIncludingSameTarget() {
        var cycle = new OneForAllCycle();
        cycle.confirmed(10, A);
        assertEquals(1, cycle.progress(69));
        assertEquals(0, cycle.progress(70));
        assertTrue(cycle.confirmed(70, A));
        assertEquals(1, cycle.progress(70));
    }

    @Test void activeNeverRefreshesAndCollectsNothingForNextCycle() {
        var cycle = active(10);
        assertFalse(cycle.confirmed(11, D));
        assertFalse(cycle.confirmed(209, A));
        assertEquals(1, cycle.remaining(209));
        assertEquals(0, cycle.progress(209));
        assertEquals(0, cycle.remaining(210));
        assertEquals(1f, cycle.multiplier(210));
        assertTrue(cycle.confirmed(210, D));
        assertEquals(1, cycle.progress(210));
        assertEquals(0, cycle.remaining(210));
    }

    @Test void exactActiveDeadlineCanBeginNewThreeTargetSequence() {
        var cycle = active(0);
        cycle.confirmed(200, A);
        cycle.confirmed(259, B);
        assertTrue(cycle.confirmed(318, C));
        assertEquals(200, cycle.remaining(318));
    }

    @Test void simultaneousSplashTargetsActivateOnlyAfterThirdDamageSnapshot() {
        var cycle = new OneForAllCycle();
        for (var target : new UUID[]{A, B, C}) {
            assertEquals(1f, cycle.multiplier(20));
            cycle.confirmed(20, target);
        }
        assertEquals(1.35f, cycle.multiplier(20));
        assertFalse(cycle.confirmed(20, D));
        assertEquals(200, cycle.remaining(20));
    }

    @Test void readOnlyQueriesNeitherExpireMutablyNorRefreshCollectionOrActiveTime() {
        var cycle = new OneForAllCycle();
        cycle.confirmed(0, A);
        assertEquals(0, cycle.progress(10_000));
        assertEquals(1, cycle.progress(10)); // Read did not discard the state.
        cycle.confirmed(59, B);
        cycle.confirmed(118, C);
        for (int i = 0; i < 50; i++) {
            assertEquals(100, cycle.remaining(218));
            assertEquals(0, cycle.progress(218));
        }
        assertEquals(0, cycle.remaining(318));
        assertEquals(200, cycle.remaining(118)); // Read did not reset active state.
    }

    @Test void sourceAndOwnerCyclesCannotShareTargetsOrActiveTime() {
        var ownerOneSourceOne = new OneForAllCycle();
        var ownerOneSourceTwo = new OneForAllCycle();
        var ownerTwoSourceOne = new OneForAllCycle();
        ownerOneSourceOne.confirmed(0, A);
        ownerOneSourceOne.confirmed(1, B);
        ownerOneSourceTwo.confirmed(2, C);
        ownerTwoSourceOne.confirmed(2, C);
        assertEquals(2, ownerOneSourceOne.progress(2));
        assertEquals(1, ownerOneSourceTwo.progress(2));
        assertEquals(1, ownerTwoSourceOne.progress(2));
        ownerOneSourceOne.confirmed(3, C);
        assertEquals(200, ownerOneSourceOne.remaining(3));
        assertEquals(0, ownerOneSourceTwo.remaining(3));
        assertEquals(0, ownerTwoSourceOne.remaining(3));
    }

    @Test void backwardsConfirmedEventsFailClosedWithoutDestroyingValidState() {
        var cycle = active(100);
        assertFalse(cycle.confirmed(99, D));
        assertEquals(0, cycle.remaining(99));
        assertEquals(1f, cycle.multiplier(99));
        assertFalse(cycle.confirmed(150, D));
        assertFalse(cycle.confirmed(149, A));
        assertEquals(0, cycle.remaining(149));
        assertEquals(150, cycle.remaining(150));
        assertEquals(0, cycle.remaining(300));
    }

    @Test void invalidTargetsAndTicksDoNotAdvanceOrWrapState() {
        var cycle = new OneForAllCycle();
        cycle.confirmed(0, A);
        assertFalse(cycle.confirmed(59, null));
        assertFalse(cycle.confirmed(-1, B));
        assertFalse(cycle.confirmed(Long.MIN_VALUE, B));
        assertFalse(cycle.confirmed(Long.MAX_VALUE, B));
        assertEquals(1, cycle.progress(59));
        assertEquals(0, cycle.progress(60));
        assertEquals(0, cycle.progress(-1));
        assertEquals(0, cycle.remaining(Long.MIN_VALUE));
        assertEquals(0, cycle.remaining(Long.MAX_VALUE));
    }

    @Test void nearLongLimitSupportsExactExpiryWithoutOverflow() {
        long start = Long.MAX_VALUE - 200;
        var cycle = active(start);
        assertEquals(200, cycle.remaining(start));
        assertEquals(1, cycle.remaining(Long.MAX_VALUE - 1));
        assertEquals(0, cycle.remaining(Long.MAX_VALUE));
        assertFalse(cycle.confirmed(Long.MAX_VALUE - 199, D));
        assertEquals(0, cycle.progress(Long.MAX_VALUE));
    }

    @Test void constructorRejectsUnsafeDurationsAndCustomValidDurationsRespectBounds() {
        for (int bad : new int[]{Integer.MIN_VALUE, -1, 0, 1201, Integer.MAX_VALUE}) {
            assertThrows(IllegalArgumentException.class, () -> new OneForAllCycle(bad, 200));
            assertThrows(IllegalArgumentException.class, () -> new OneForAllCycle(60, bad));
        }
        var cycle = new OneForAllCycle(1, 1);
        cycle.confirmed(0, A); cycle.confirmed(0, B); cycle.confirmed(0, C);
        assertEquals(1, cycle.remaining(0));
        assertEquals(0, cycle.remaining(1));
    }
}
