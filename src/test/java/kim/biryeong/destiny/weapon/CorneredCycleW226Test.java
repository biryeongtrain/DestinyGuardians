package kim.biryeong.destiny.weapon;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class CorneredCycleW226Test {
    @Test void thresholdNeedsTwoEnemiesAndFirstLossStartsLinger() {
        var cycle = new CorneredCycle();
        cycle.update(10, true, 1);
        assertFalse(cycle.active(10));
        cycle.update(10, true, 2);
        assertTrue(cycle.active(10));
        cycle.update(10, true, 1); // same-tick resample before accepted charge
        assertTrue(cycle.active(39));
        assertFalse(cycle.active(40));
    }

    @Test void absentSamplesAndPureReadsNeverExtendTheExclusiveDeadline() {
        var cycle = new CorneredCycle();
        cycle.update(50, true, 3);
        cycle.update(100, true, 0); // first actual loss, not last positive observation
        assertEquals(30, cycle.remaining(100));
        assertFalse(cycle.active(99)); // pure out-of-order read
        assertTrue(cycle.active(129));
        cycle.update(129, true, 1);
        assertEquals(1, cycle.remaining(129));
        assertFalse(cycle.active(130));
        cycle.update(140, true, 0);
        assertFalse(cycle.active(140));
    }

    @Test void reacquisitionRearmsOnlyAfterAnotherActualThresholdObservation() {
        var cycle = new CorneredCycle();
        cycle.update(10, true, 2);
        cycle.update(11, true, 0);
        cycle.update(40, true, 2);
        cycle.update(45, true, 1);
        assertTrue(cycle.active(74));
        assertFalse(cycle.active(75));
    }

    @Test void invalidationClearAndRewindRevokeWithoutTransferringLinger() {
        var cycle = new CorneredCycle();
        cycle.update(20, true, 2);
        cycle.update(21, false, 2);
        cycle.update(21, true, 1);
        assertFalse(cycle.active(21));
        cycle.update(22, true, 2);
        cycle.clear();
        cycle.update(22, true, 0);
        assertFalse(cycle.active(22));
        cycle.update(50, true, 2);
        cycle.update(49, true, 2);
        assertFalse(cycle.active(50));
        cycle.update(51, true, 1);
        assertFalse(cycle.active(51));
    }

    @Test void deadlineArithmeticDoesNotOverflowNearTheClockLimit() {
        var cycle = new CorneredCycle();
        cycle.update(Long.MAX_VALUE - 20, true, 2);
        cycle.update(Long.MAX_VALUE - 10, true, 0);
        assertEquals(20, cycle.remaining(Long.MAX_VALUE));
        cycle.update(-1, true, 2);
        assertFalse(cycle.active(Long.MAX_VALUE));
    }
}
