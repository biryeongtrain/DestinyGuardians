package kim.biryeong.destiny.weapon;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;
class TapTheTriggerCycleW171Test {
    @Test void noPaidShotNoWindow() {var c=new TapTheTriggerCycle();c.released();assertEquals(0,c.remaining(0));}
    @Test void exactTwelveTickWindow() {var c=new TapTheTriggerCycle();c.paid(10,false);assertEquals(12,c.remaining(10));assertEquals(1,c.remaining(21));assertEquals(0,c.remaining(22));}
    @Test void heldAutomaticCannotRefreshEvenAfterExpiry() {var c=new TapTheTriggerCycle();c.paid(0,false);for(int t=1;t<100;t++){c.paid(t,false);assertEquals(Math.max(0,12-t),c.remaining(t));}}
    @Test void releaseRearmsWithoutExtendingExistingWindow() {var c=new TapTheTriggerCycle();c.paid(0,false);c.released();assertEquals(7,c.remaining(5));c.paid(6,false);assertEquals(12,c.remaining(6));}
    @Test void eachPaidFusionBurstCanRefresh() {var c=new TapTheTriggerCycle();c.paid(0,true);c.paid(5,true);assertEquals(12,c.remaining(5));assertEquals(0,c.remaining(17));}
    @Test void resetRemovesBothClockAndLatch() {var c=new TapTheTriggerCycle();c.paid(5,false);c.reset();assertEquals(0,c.remaining(5));c.paid(6,false);assertEquals(12,c.remaining(6));}
    @Test void badClockAndSaturation() {var c=new TapTheTriggerCycle();assertThrows(IllegalArgumentException.class,()->c.paid(-1,false));c.paid(Long.MAX_VALUE-5,false);assertEquals(5,c.remaining(Long.MAX_VALUE-5));assertEquals(0,c.remaining(Long.MAX_VALUE));}
}
