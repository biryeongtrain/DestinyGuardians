package kim.biryeong.destiny.hud;

import org.junit.jupiter.api.Test;
import java.util.HashSet;
import static org.junit.jupiter.api.Assertions.*;

/** Local received-damage presentation policy, not measured Destiny angles/timing or a radar. */
class IncomingDamageStateTest {
    private static final double EPS=1e-5;
    @Test void boundedFourSlotsSixTickHoldAndTwentyTickLifeAreExplicitLocalPolicy() {
        assertEquals(4,IncomingDamageState.CAPACITY);assertEquals(6,IncomingDamageState.HOLD_TICKS);
        assertEquals(20,IncomingDamageState.LIFE_TICKS);assertEquals(.30f,IncomingDamageState.CRITICAL_FRACTION);
        var s=new IncomingDamageState();assertTrue(s.cues(0).isEmpty());
        assertTrue(s.hit(0,0,0,0,4));assertEquals(1,s.cues(0).size());assertEquals(0,s.cues(0).getFirst().slot());
    }
    @Test void invalidCoincidentAndNearVerticalOriginsCannotInventAHeading() {
        var s=new IncomingDamageState();
        assertFalse(s.hit(0,1,1,1,1));assertFalse(s.hit(0,0,0,.009,0));assertTrue(s.hit(0,0,0,.011,0));
        for(double n:new double[]{Double.NaN,Double.POSITIVE_INFINITY,Double.NEGATIVE_INFINITY}) {
            assertFalse(s.hit(1,n,0,4,0));assertFalse(s.hit(1,0,n,4,0));
            assertFalse(s.hit(1,0,0,n,0));assertFalse(s.hit(1,0,0,4,n));
        }
        assertFalse(s.hit(1,-Double.MAX_VALUE,0,Double.MAX_VALUE,0));assertEquals(1,s.cues(1).size());
    }
    @Test void cueCoordinatesAndReturnedListsAreImmutableWorldSnapshots() {
        var s=new IncomingDamageState();assertTrue(s.hit(5,10,10,14,12));var list=s.cues(5);var cue=list.getFirst();
        assertEquals(new IncomingDamageState.Cue(0,14,12,5),cue);
        assertThrows(UnsupportedOperationException.class,()->list.clear());
        s.hit(6,10,10,15,12);assertEquals(new IncomingDamageState.Cue(0,14,12,5),cue);
        assertEquals(new IncomingDamageState.Cue(0,15,12,6),s.cues(6).getFirst());
    }
    @Test void twoBlockMergeBoundaryRefreshesOneSlotButDistinctOriginsUseAnother() {
        var s=new IncomingDamageState();s.hit(0,0,0,0,5);s.hit(1,0,0,2,5);
        assertEquals(1,s.cues(1).size());assertEquals(new IncomingDamageState.Cue(0,2,5,1),s.cues(1).getFirst());
        s.hit(2,0,0,4.001,5);assertEquals(2,s.cues(2).size());assertEquals(1,s.cues(2).get(1).slot());
    }
    @Test void fullPoolReplacesOldestAndSameTickTiesRemainDeterministic() {
        var s=new IncomingDamageState();for(int i=0;i<4;i++)assertTrue(s.hit(i,0,0,i*4+4,5));
        assertEquals(4,s.cues(3).size());s.hit(4,0,0,24,5);
        assertEquals(new IncomingDamageState.Cue(0,24,5,4),s.cues(4).getFirst());assertEquals(4,s.cues(4).size());
        var tied=new IncomingDamageState();for(int i=0;i<4;i++)tied.hit(10,0,0,i*4+4,5);
        tied.hit(10,0,0,24,5);assertEquals(24,tied.cues(10).getFirst().x());assertEquals(4,tied.cues(10).size());
    }
    @Test void exactExpiryAndClockRollbackRetireCuesWithoutResurrection() {
        var s=new IncomingDamageState();s.hit(100,0,0,4,0);assertEquals(1,s.cues(119).size());
        assertTrue(s.cues(120).isEmpty());assertTrue(s.cues(121).isEmpty());
        s.hit(200,0,0,4,0);assertTrue(s.cues(199).isEmpty());assertTrue(s.cues(200).isEmpty());
        assertTrue(s.hit(201,0,0,4,0));assertEquals(0,s.cues(201).getFirst().slot());
    }
    @Test void mergedRefreshRestartsOnlyThatSourcesAgeAndReusesFreedSlots() {
        var s=new IncomingDamageState();s.hit(0,0,0,0,4);s.hit(1,0,0,4,0);s.hit(10,0,0,0,5);
        assertEquals(2,s.cues(20).size());assertEquals(1,s.cues(21).size());
        assertEquals(new IncomingDamageState.Cue(0,0,5,10),s.cues(21).getFirst());
        s.hit(22,0,0,-4,0);assertEquals(1,s.cues(22).get(1).slot());
        assertEquals(2,s.cues(29).size());assertEquals(1,s.cues(30).size());
    }
    @Test void eightFadeFramesFollowExactHoldAndMonotonicTwentyTickEnvelope() {
        var cue=new IncomingDamageState.Cue(0,0,4,100);var seen=new HashSet<Integer>();int previous=0;
        assertEquals(-1,IncomingDamageState.fadeFrame(99,cue));
        for(int age=0;age<20;age++) {
            int expected=Math.clamp((age-6)*8/14,0,7),actual=IncomingDamageState.fadeFrame(100+age,cue);
            assertEquals(expected,actual,"age="+age);assertTrue(actual>=previous);seen.add(actual);previous=actual;
        }
        assertEquals(8,seen.size());assertEquals(-1,IncomingDamageState.fadeFrame(120,cue));
    }
    @Test void cardinalBearingsAndYawWrappingMatchMinecraftScreenConvention() {
        assertEquals(0,IncomingDamageState.bearing(0,4,0),EPS);
        assertEquals(90,IncomingDamageState.bearing(-4,0,0),EPS);
        assertEquals(-90,IncomingDamageState.bearing(4,0,0),EPS);
        assertEquals(-180,IncomingDamageState.bearing(0,-4,0),EPS);
        assertEquals(0,IncomingDamageState.bearing(4,0,-90),EPS);
        for(float yaw:new float[]{-1080,-360,0,360,1080})assertEquals(90,IncomingDamageState.bearing(-4,0,yaw),EPS);
        assertTrue(Float.isNaN(IncomingDamageState.bearing(0,0,0)));
        for(double n:new double[]{Double.NaN,Double.POSITIVE_INFINITY,Double.NEGATIVE_INFINITY}) {
            assertTrue(Float.isNaN(IncomingDamageState.bearing(n,1,0)));assertTrue(Float.isNaN(IncomingDamageState.bearing(1,n,0)));
        }
        assertTrue(Float.isNaN(IncomingDamageState.bearing(1,1,Float.NaN)));
    }
    @Test void bearingRecomputesFromCurrentVictimBodyAndYawNotALiveAttackerReference() {
        var s=new IncomingDamageState();s.hit(0,10,10,10,14);var cue=s.cues(0).getFirst();
        assertEquals(0,IncomingDamageState.bearing(cue.x()-10,cue.z()-10,0),EPS);
        assertEquals(-90,IncomingDamageState.bearing(cue.x()-10,cue.z()-10,90),EPS);
        assertEquals(-90,IncomingDamageState.bearing(cue.x()-6,cue.z()-14,0),EPS);
        assertTrue(Float.isNaN(IncomingDamageState.bearing(cue.x()-10,cue.z()-14,0)));
        assertEquals(new IncomingDamageState.Cue(0,10,14,0),cue);
    }
    @Test void criticalThresholdUsesCurrentPositiveHpFractionNotAbsorptionOrRecentDamage() {
        assertTrue(IncomingDamageState.criticalFrame(0,.30f)>=0);assertTrue(IncomingDamageState.criticalFrame(0,.299f)>=0);
        for(float fraction:new float[]{0,-1,.3001f,.35f,1,Float.NaN,Float.POSITIVE_INFINITY,Float.NEGATIVE_INFINITY})
            assertEquals(-1,IncomingDamageState.criticalFrame(0,fraction));
    }
    @Test void criticalPulseUsesEightFrameBankTwoTickStepsAndBoundedSeverity() {
        assertEquals(2,IncomingDamageState.criticalFrame(0,.3f));assertEquals(3,IncomingDamageState.criticalFrame(6,.3f));
        assertEquals(0,IncomingDamageState.criticalFrame(18,.3f));var frames=new HashSet<Integer>();
        for(int t=0;t<48;t++)for(float fraction:new float[]{.3f,.2f,.1f,.001f}) {
            int frame=IncomingDamageState.criticalFrame(t,fraction);assertTrue(frame>=0&&frame<=7);frames.add(frame);
            assertEquals(frame,IncomingDamageState.criticalFrame(t+24,fraction));
            if((t&1)==0)assertEquals(frame,IncomingDamageState.criticalFrame(t+1,fraction));
            assertTrue(IncomingDamageState.criticalFrame(t,.001f)>=IncomingDamageState.criticalFrame(t,.3f));
        }
        assertEquals(8,frames.size());
    }
}
