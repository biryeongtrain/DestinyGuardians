package kim.biryeong.destiny.weapon;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class EnsembleCycleW190Test {
    @Test void lossStartsAtObservationAndNeitherReadsNorAbsentSamplesRefreshIt() {
        var cycle = new EnsembleCycle();
        cycle.update(10, true, true);
        cycle.update(50, true, false);
        long expiry = 50 + EnsembleCycle.LINGER_TICKS;
        assertTrue(cycle.active(expiry - 1));
        assertFalse(cycle.active(expiry));
        // An out-of-order read is neutral and cannot consume or extend the actual state.
        assertFalse(cycle.active(49));
        assertTrue(cycle.active(expiry - 1));
        cycle.update(expiry - 1, true, false);
        assertFalse(cycle.active(expiry));
        cycle.update(expiry + 1, true, false);
        assertFalse(cycle.active(expiry + 1));
    }

    @Test void reacquisitionRearmsLingerAndSameTickLossDoesNotNeedAnotherTick() {
        var cycle = new EnsembleCycle();
        cycle.update(10, true, true);
        cycle.update(10, true, false);
        cycle.update(20, true, true);
        cycle.update(40, true, false);
        assertTrue(cycle.active(40 + EnsembleCycle.LINGER_TICKS - 1));
        assertFalse(cycle.active(40 + EnsembleCycle.LINGER_TICKS));
    }

    @Test void invalidationAndClearCannotLingerOrReviveWithoutANewAlly() {
        var cycle = new EnsembleCycle();
        cycle.update(10, true, true);
        cycle.update(10, false, true);
        cycle.update(10, true, false);
        assertFalse(cycle.active(10));
        cycle.update(11, true, true);
        cycle.clear();
        cycle.update(11, true, false);
        assertFalse(cycle.active(11));
    }

    @Test void clockRewindRevokesTheOldObservation() {
        var cycle = new EnsembleCycle();
        cycle.update(50, true, true);
        cycle.update(49, true, true);
        assertFalse(cycle.active(50));
        cycle.update(51, true, false);
        assertFalse(cycle.active(51));
    }
}
