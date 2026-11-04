package kim.biryeong.destiny.weapon;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class FocusedFuryCycleW174Test {
    @Test void cycleMatchesPinnedBaseDuration() { var c=new FocusedFuryCycle(1);c.precision(0);assertEquals(FocusedFuryProfile.durationTicks(),c.remaining(0)); }
    @Test void noWindowBeforeRequiredHitsAndExactDeadline() {
        var c=new FocusedFuryCycle(3);
        assertFalse(c.precision(1));assertFalse(c.precision(2));assertEquals(2,c.progress(2));
        assertEquals(0,c.remaining(2));assertTrue(c.precision(3));assertEquals(0,c.progress(3));
        assertEquals(220,c.remaining(3));assertEquals(1,c.remaining(222));assertEquals(0,c.remaining(223));
    }
    @Test void thresholdOneWorksButDoesNotPrebuffQualifyingEmission() {
        var c=new FocusedFuryCycle(1);int emissionSnapshot=c.remaining(8);
        assertTrue(c.precision(8));assertEquals(0,emissionSnapshot);assertEquals(220,c.remaining(8));
    }
    @Test void eachNewThresholdRefreshesNotEveryHit() {
        var c=new FocusedFuryCycle(2);c.precision(0);c.precision(1);
        assertFalse(c.precision(20));assertEquals(201,c.remaining(20));
        assertTrue(c.precision(30));assertEquals(220,c.remaining(30));
    }
    @Test void stowOrReloadResetPartialCounterButNotEarnedWindow() {
        var c=new FocusedFuryCycle(2);c.precision(0);c.precision(1);c.precision(2);
        c.resetCounter(4);assertEquals(0,c.progress(4));assertEquals(217,c.remaining(4));
        assertFalse(c.precision(5));assertTrue(c.precision(6));assertEquals(220,c.remaining(6));
    }
    @Test void deniedReadDoesNotMutateCounterOrDeadline() {
        var c=new FocusedFuryCycle(2);c.precision(8);c.precision(9);c.precision(10);
        for(int i=0;i<100;i++){assertEquals(1,c.progress(12));assertEquals(217,c.remaining(12));}
        assertEquals(219,c.remaining(10));assertTrue(c.precision(11));
    }
    @Test void negativeBackwardAndOverflowEventsAreInert() {
        var c=new FocusedFuryCycle(2);assertFalse(c.precision(-1));c.precision(4);c.update(10);
        assertFalse(c.precision(9));c.resetCounter(9);assertEquals(1,c.progress(10));
        assertEquals(0,c.progress(9));assertFalse(c.precision(Long.MAX_VALUE));assertEquals(1,c.progress(10));
        assertTrue(c.precision(10));assertEquals(220,c.remaining(10));
    }
    @Test void expiryDoesNotInventAStowOrReloadCounterReset() {
        var c=new FocusedFuryCycle(3);c.precision(0);c.precision(1);c.precision(2);c.precision(3);
        c.update(222);assertEquals(0,c.remaining(222));assertEquals(1,c.progress(222));
        assertFalse(c.precision(223));assertTrue(c.precision(224));
    }
    @Test void countersAreIndependentAndBadThresholdsRejected() {
        var a=new FocusedFuryCycle(1);var b=new FocusedFuryCycle(2);a.precision(1);
        assertEquals(0,b.progress(1));assertEquals(0,b.remaining(1));
        assertThrows(IllegalArgumentException.class,()->new FocusedFuryCycle(0));
        assertThrows(IllegalArgumentException.class,()->new FocusedFuryCycle(1001));
    }
}
