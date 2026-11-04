package kim.biryeong.destiny.weapon;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class BoxBreathingCycleW195Test {
    @Test void adsInputStartsClockAndPaidShotConsumesReadyBeforeAnotherEmission() {
        var c = new BoxBreathingCycle();
        c.update(10, true, true);
        assertFalse(c.ready(39));
        var paid = c.capture(40, 3, true);
        assertTrue(c.boosted(40, paid));
        assertFalse(c.boosted(40, c.capture(40, 2, true)));
        assertFalse(c.ready(69));
        assertTrue(c.ready(70));
        assertTrue(c.boosted(70, paid));
    }
    @Test void lastRoundSnapshotSurvivesSubsequentEmptyMagazinePoll() {
        var c = new BoxBreathingCycle();
        c.update(1, true, true);
        var paid = c.capture(31, 1, true);
        assertTrue(c.boosted(31, paid));
        c.update(31, true, false);
        assertFalse(c.ready(100));
        assertTrue(c.boosted(100, paid));
        assertNull(c.capture(100, 0, true));
        c.update(101, true, true);
        assertFalse(c.ready(130));
        assertTrue(c.ready(131));
    }
    @Test void falseTrueSameTickAndExplicitReleaseRestartInsteadOfPausing() {
        var c = new BoxBreathingCycle();
        c.update(1, true, true);
        c.update(31, false, true);
        c.update(31, true, true);
        assertFalse(c.ready(31));
        assertTrue(c.ready(61));
        var paid = c.capture(61, 3, true);
        c.released(61);
        c.update(61, true, true);
        assertFalse(c.boosted(61, paid));
        assertFalse(c.ready(90));
        assertTrue(c.ready(91));
    }
    @Test void firingBeforeReadyOrWithoutAdsResetsTheUnpaidWindow() {
        var c = new BoxBreathingCycle();
        c.update(1, true, true);
        assertFalse(c.boosted(20, c.capture(20, 3, true)));
        assertFalse(c.ready(49));
        assertTrue(c.ready(50));
        assertFalse(c.boosted(50, c.capture(50, 2, false)));
        c.update(60, true, true);
        assertFalse(c.ready(89));
        assertTrue(c.ready(90));
    }
    @Test void emptyMagazineNeverArmsAndPureQueriesDoNotEraseValidWindow() {
        var c = new BoxBreathingCycle();
        c.update(1, true, false);
        assertFalse(c.ready(100));
        c.update(100, true, true);
        assertTrue(c.ready(Long.MAX_VALUE));
        assertFalse(c.ready(99));
        assertFalse(c.ready(129));
        assertTrue(c.boosted(130, c.capture(130, 1, true)));
    }
    @Test void foreignClearedRollbackAndRejectedEventsCannotUsePaidEpoch() {
        var c = new BoxBreathingCycle();
        c.update(1, true, true);
        var paid = c.capture(31, 2, true);
        assertFalse(new BoxBreathingCycle().boosted(31, paid));
        assertFalse(c.boosted(30, paid));
        assertFalse(c.boosted(31, null));
        assertNull(c.capture(30, 2, true));
        assertNull(c.capture(31, 0, true));
        assertTrue(c.boosted(31, paid));
        c.clear();
        assertFalse(c.boosted(31, paid));
        c.update(40, true, true);
        var next = c.capture(70, 1, true);
        c.update(69, true, true);
        assertFalse(c.boosted(70, next));
    }
}
