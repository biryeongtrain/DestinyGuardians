package kim.biryeong.destiny.weapon;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class DynamicSwayCycleW195Test {
    @Test void onlyPaidEventsAdvanceAndEveryShotKeepsItsOwnSnapshot() {
        var c = new DynamicSwayCycle();
        var first = c.paid(10);
        // Repeated use input and polling do not call paid; no duration can build stacks.
        for (int i = 0; i < 20; i++) c.update(10, true);
        assertEquals(1, c.stacks(10));
        c.update(1_000_000, true);
        assertEquals(1, c.stacks(1_000_000));
        var second = c.paid(1_000_000);
        assertEquals(1, c.capturedStacks(1_000_000, first));
        assertEquals(2, c.capturedStacks(1_000_000, second));
        // Multiple independently paid emissions in one tick must each count.
        for (int i = 0; i < 20; i++) c.paid(1_000_000);
        assertEquals(10, c.stacks(1_000_000));
        assertEquals(2, c.capturedStacks(1_000_000, second));
    }

    @Test void sameTickReleaseRevokesSnapshotsAndNextPaidShotStartsFresh() {
        var c = new DynamicSwayCycle();
        c.paid(20);
        var old = c.paid(20);
        c.released(20); // actual release/reload/cancel/lease expiry share this boundary
        assertEquals(0, c.stacks(20));
        assertEquals(0, c.capturedStacks(20, old));
        var fresh = c.paid(20);
        assertEquals(1, c.capturedStacks(20, fresh));
        assertEquals(0, c.capturedStacks(20, old));
        c.update(21, false); // polling an unheld source also revokes
        c.update(22, true);
        assertEquals(0, c.stacks(22));
        assertEquals(0, c.capturedStacks(22, fresh));
    }

    @Test void pureFutureOrInvalidProbesCannotChangeAcceptedChainOrEpoch() {
        var c = new DynamicSwayCycle();
        var shot = c.paid(30);
        assertEquals(1, c.stacks(Long.MAX_VALUE));
        assertEquals(0, c.capturedStacks(29, shot));
        assertEquals(0, c.stacks(-1));
        var next = c.paid(31);
        assertEquals(2, c.capturedStacks(31, next));
        assertEquals(1, c.capturedStacks(31, shot));
        assertEquals(0, new DynamicSwayCycle().capturedStacks(31, shot));
    }

    @Test void editClearAndWriterRollbackPermanentlyRevokePriorEpochs() {
        var c = new DynamicSwayCycle();
        var old = c.paid(40);
        c.clear();
        var successor = c.paid(40);
        assertEquals(0, c.capturedStacks(40, old));
        assertEquals(1, c.capturedStacks(40, successor));
        c.update(39, true);
        assertEquals(0, c.capturedStacks(40, successor));
        assertNull(c.paid(-1));
        assertEquals(0, c.stacks(41));
    }
}
