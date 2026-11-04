package kim.biryeong.destiny.weapon;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

/** Episode/event/timer behavior only, no sourced numeric mirror tests. */
class PulseMonitorW200Test {
    @Test void firstLowObservationIsOneDecisionAndNeitherTicksNorDamageReplayIt() {
        var c=new PulseMonitorCycle();
        assertTrue(c.update(10,5,20));
        for(int t=10;t<80;t++) {
            assertFalse(c.update(t,4,20));
            assertFalse(c.damaged(t,1,3,20));
            assertTrue(c.active(t));
        }
    }
    @Test void zeroAbsorbedNegativeAndNonfiniteDamageDoNotBindOrRearm() {
        var c=new PulseMonitorCycle();
        for(float loss:new float[]{0,-1,Float.NaN,Float.POSITIVE_INFINITY}) {
            assertFalse(c.damaged(10,loss,4,20));assertFalse(c.active(10));
        }
        assertTrue(c.damaged(11,2,4,20));
        assertFalse(c.damaged(12,0,20,20));
        assertFalse(c.damaged(13,1,3,20),"zero-loss callback cannot fake recovery");
    }
    @Test void firstRecoveryObservationStartsLingerAndQueriesCannotExtendIt() {
        var c=new PulseMonitorCycle();assertTrue(c.update(100,4,20));
        assertFalse(c.update(107,15,20));
        for(int i=0;i<100;i++)assertTrue(c.active(126));
        assertFalse(c.active(127));
        assertFalse(c.update(128,20,20));assertFalse(c.active(128));
    }
    @Test void genuineRecoveryRearmsEvenIfNextLowEpisodeOccursDuringLinger() {
        var c=new PulseMonitorCycle();assertTrue(c.damaged(10,12,4,20));
        assertFalse(c.update(11,20,20));assertTrue(c.active(11));
        assertTrue(c.damaged(12,16,4,20));assertFalse(c.update(13,4,20));
        assertTrue(c.active(1000),"sustained low lasts beyond the old linger");
    }
    @Test void invalidHealthDeathRollbackAndExplicitClearRetireTheEpisode() {
        var c=new PulseMonitorCycle();assertTrue(c.update(10,4,20));
        assertFalse(c.active(9));assertFalse(c.update(9,4,20));assertFalse(c.active(10));
        assertTrue(c.update(11,4,20));assertFalse(c.update(12,0,20));assertFalse(c.active(12));
        assertTrue(c.update(13,4,20));assertFalse(c.update(14,Float.NaN,20));assertFalse(c.active(14));
        assertTrue(c.update(15,4,20));c.clear();assertFalse(c.active(15));
        assertTrue(c.update(16,4,20));
    }
    @Test void thresholdUsesNativeHealthRatioAndMaximumChangesAreObservedAsEpisodeChanges() {
        var c=new PulseMonitorCycle();assertFalse(c.update(1,7,20));
        assertTrue(c.update(2,6,20));
        assertFalse(c.update(3,6,10),"native max health change can recover the ratio");
        assertTrue(c.update(4,6,40));
        assertFalse(PulseMonitorCycle.lowHealth(4,Float.POSITIVE_INFINITY));
    }
}
