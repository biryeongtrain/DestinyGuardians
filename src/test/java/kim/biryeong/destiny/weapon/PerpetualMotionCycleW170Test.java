package kim.biryeong.destiny.weapon;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;
class PerpetualMotionCycleW170Test {
    @Test void exactFirstAndSecondMovingSamples() {
        var c=new PerpetualMotionCycle();
        for(int t=0;t<39;t++)c.sample(t,true);assertEquals(0,c.stacks());
        c.sample(39,true);assertEquals(1,c.stacks());
        for(int t=40;t<199;t++)c.sample(t,true);assertEquals(1,c.stacks());
        c.sample(199,true);assertEquals(2,c.stacks());
        for(int t=200;t<500;t++)c.sample(t,true);assertEquals(200,c.movingTicks());
    }
    @Test void SlowGraceNineRetainsTenthClears() {
        var c=new PerpetualMotionCycle();for(int t=0;t<200;t++)c.sample(t,true);
        for(int t=200;t<209;t++)c.sample(t,false);assertEquals(2,c.stacks());
        c.sample(209,false);assertEquals(0,c.stacks());assertEquals(0,c.movingTicks());
        c.sample(210,true);assertEquals(1,c.movingTicks());assertEquals(0,c.stacks());
    }
    @Test void briefSlowPausesProgressWithoutInventingTime() {
        var c=new PerpetualMotionCycle();for(int t=0;t<39;t++)c.sample(t,true);
        for(int t=39;t<48;t++)c.sample(t,false);assertEquals(39,c.movingTicks());
        c.sample(48,true);assertEquals(1,c.stacks());assertEquals(0,c.slowTicks());
    }
    @Test void sameTickCannotAccumulateOrRevoke() {
        var c=new PerpetualMotionCycle();c.sample(10,true);
        for(int i=0;i<1000;i++)c.sample(10,i%2==0);
        assertEquals(1,c.movingTicks());assertEquals(0,c.slowTicks());assertEquals(0,c.stacks());
    }
    @Test void missingOrBackwardsSamplesResetWithoutCreditForGap() {
        var c=new PerpetualMotionCycle();for(int t=0;t<40;t++)c.sample(t,true);
        c.sample(100,true);assertEquals(1,c.movingTicks());assertEquals(0,c.stacks());
        c.sample(5,false);assertEquals(0,c.movingTicks());assertEquals(0,c.stacks());
    }
    @Test void longClockDoesNotOverflow() {
        var c=new PerpetualMotionCycle();for(long t=Long.MAX_VALUE-39;t<Long.MAX_VALUE;t++)c.sample(t,true);
        c.sample(Long.MAX_VALUE,true);assertEquals(1,c.stacks());c.sample(0,true);assertEquals(0,c.stacks());
    }
    @Test void negativeClockRejectedAndResetPure() {
        var c=new PerpetualMotionCycle();assertThrows(IllegalArgumentException.class,()->c.sample(-1,true));
        for(int t=0;t<200;t++)c.sample(t,true);c.reset();assertEquals(0,c.stacks());assertEquals(0,c.movingTicks());
    }
}
