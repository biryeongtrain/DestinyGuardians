package kim.biryeong.destiny.weapon;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class OpeningShotCycleW195Test {
    @Test void paidShotsRestartQuietTimeIncludingUnboostedSupplementalShots() {
        var c = new OpeningShotCycle();
        var opener = c.capture(10, true);
        assertTrue(c.boosted(10, opener));
        assertFalse(c.boosted(11, c.capture(11, false)));
        assertFalse(c.boosted(70, c.capture(70, true))); // 59 since the supplemental
        var next = c.capture(130, true);
        assertTrue(c.boosted(130, next));
        assertTrue(c.boosted(130, opener)); // paid snapshot, not live cooldown
    }
    @Test void supplementaryNeverGetsFreshBonusEvenAfterLongSilence() {
        var c = new OpeningShotCycle();
        assertFalse(c.boosted(100, c.capture(100, false)));
        assertFalse(c.boosted(101, c.capture(101, true)));
        assertTrue(c.boosted(161, c.capture(161, true)));
    }
    @Test void stowRevokesPaidEpochWithoutBypassingLastShotCooldown() {
        var c = new OpeningShotCycle();
        var old = c.capture(10, true);
        c.stowing(10);
        assertFalse(c.boosted(10, old));
        assertFalse(c.boosted(11, c.capture(11, true)));
        assertTrue(c.boosted(71, c.capture(71, true)));
    }
    @Test void probesCannotArmResetOrRevokeAndForeignOrEditedSourcesFailClosed() {
        var c = new OpeningShotCycle();
        var paid = c.capture(10, true);
        assertTrue(c.boosted(Long.MAX_VALUE, paid));
        assertFalse(c.boosted(9, paid));
        assertFalse(new OpeningShotCycle().boosted(10, paid));
        assertFalse(c.boosted(10, null));
        assertFalse(c.boosted(11, c.capture(11, true))); // far-future query did not change writer time
        c.clear();
        assertFalse(c.boosted(11, paid));
        assertTrue(c.boosted(11, c.capture(11, true)));
    }
    @Test void rollbackWriterRevokesAndRejectedCaptureDoesNotAdvanceCooldown() {
        var c = new OpeningShotCycle();
        var paid = c.capture(20, true);
        assertNull(c.capture(19, true));
        assertNull(c.capture(-1, true));
        assertTrue(c.boosted(20, paid));
        c.update(19);
        assertFalse(c.boosted(20, paid));
    }
}
