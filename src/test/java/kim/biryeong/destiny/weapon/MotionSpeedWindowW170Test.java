package kim.biryeong.destiny.weapon;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;
class MotionSpeedWindowW170Test {
    @Test void exactThresholdAndSubthreshold() {
        var a=new MotionSpeedWindow();var b=new MotionSpeedWindow();
        for(int i=0;i<300;i++){assertTrue(a.sample(.1));assertFalse(b.sample(.099));}
    }
    @Test void alternatingPacketBatchesDoNotHalveProgress() {
        var speed=new MotionSpeedWindow();var cycle=new PerpetualMotionCycle();
        for(int t=0;t<205;t++)cycle.sample(t,speed.sample(t%2==0?0:.432));
        assertEquals(2,cycle.stacks());
    }
    @Test void threeTickPacketBatchesReachTwoTiers() {
        var speed=new MotionSpeedWindow();var cycle=new PerpetualMotionCycle();
        for(int t=0;t<207;t++)cycle.sample(t,speed.sample(t%3==2?.648:0));
        assertEquals(2,cycle.stacks());
    }
    @Test void stationaryRawGraceIsNotExtendedByWindow() {
        var speed=new MotionSpeedWindow();for(int i=0;i<200;i++)speed.sample(.216);
        for(int i=0;i<9;i++){speed.sample(0);assertFalse(speed.stopGraceElapsed());}
        assertFalse(speed.sample(0));assertTrue(speed.stopGraceElapsed());
        assertFalse(speed.sample(0));assertTrue(speed.stopGraceElapsed());
    }
    @Test void briefFastPulseCannotProduceATierWhileStationary() {
        var speed=new MotionSpeedWindow();var cycle=new PerpetualMotionCycle();
        for(int t=0;t<100;t++){
            boolean moving=speed.sample(t==0?1:0);
            if(speed.stopGraceElapsed())cycle.reset();cycle.sample(t,moving);
        }
        assertEquals(0,cycle.stacks());assertEquals(0,cycle.movingTicks());
    }
    @Test void resetClearsTravelAndStopHistory() {
        var speed=new MotionSpeedWindow();speed.sample(2);speed.reset();
        assertFalse(speed.sample(0));assertFalse(speed.stopGraceElapsed());
        assertFalse(speed.sample(.099));
    }
    @Test void invalidSamplesRejectedWithoutMutating() {
        var speed=new MotionSpeedWindow();
        for(double d:new double[]{-1,2.01,Double.NaN,Double.POSITIVE_INFINITY})
            assertThrows(IllegalArgumentException.class,()->speed.sample(d));
        assertTrue(speed.sample(.1));
    }
}
