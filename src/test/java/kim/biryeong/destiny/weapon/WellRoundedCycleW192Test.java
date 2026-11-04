package kim.biryeong.destiny.weapon;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class WellRoundedCycleW192Test {
    @Test void acceptedEventsStackRefreshAndExpireEvenWhileStowed() {
        var c=new WellRoundedCycle();assertEquals(0,c.stacks(10));
        c.used(10,1);assertEquals(1,c.stacks(10));
        c.used(250,1);assertEquals(2,c.stacks(250));
        assertEquals(1,c.remaining(549));assertEquals(0,c.stacks(550));
        c.used(551,1);assertEquals(1,c.stacks(551));
    }
    @Test void superReachesCapAndFurtherAcceptedEventRefreshes() {
        var c=new WellRoundedCycle();c.used(20,2);assertEquals(2,c.stacks(20));
        c.used(319,1);assertEquals(2,c.stacks(319));assertEquals(300,c.remaining(319));
        assertEquals(0,c.remaining(619));
    }
    @Test void rejectedEventsAndQueriesNeverExtendTheDeadline() {
        var c=new WellRoundedCycle();c.used(10,1);
        c.used(20,0);c.used(-1,2);assertEquals(1,c.remaining(309));
        assertEquals(0,c.remaining(310));assertEquals(1,c.remaining(309));
        assertEquals(0,c.remaining(9));
    }
}
