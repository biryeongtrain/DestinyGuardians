package kim.biryeong.destiny.activity.presentation;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;
import static kim.biryeong.destiny.activity.presentation.DeliveryTimeline.Phase.*;

class DeliveryTimelineTest {
    @Test void earlyDeliveryStillCompletesApproachAndSettlesBeforeDeparture() {
        var t = new DeliveryTimeline(40, 180, 20, 60); t.delivered();
        for(int i=0;i<39;i++)t.tick(false); assertEquals(APPROACH,t.phase());
        t.tick(false);assertEquals(HOLD,t.phase());
        for(int i=0;i<19;i++)t.tick(false);assertEquals(HOLD,t.phase());
        t.tick(false);assertEquals(DEPART,t.phase());assertEquals(0,t.fraction());
        for(int i=0;i<60;i++)t.tick(false);assertEquals(CLOSED,t.phase());
    }
    @Test void missingActorsHaveBoundedVisualLifetimeWithoutSyntheticCompletionCallback() {
        var t = new DeliveryTimeline(10, 20, 5, 10);
        for(int i=0;i<29;i++)t.tick(false);assertEquals(HOLD,t.phase());
        t.tick(false);assertEquals(DEPART,t.phase());
        for(int i=0;i<10;i++)t.tick(false);assertEquals(CLOSED,t.phase());
    }
    @Test void pauseCancellationAndDuplicateDeliveryAreStable() {
        var t = new DeliveryTimeline(10, 20, 5, 10);
        for(int i=0;i<8;i++)t.tick(false);double before=t.fraction();
        for(int i=0;i<100;i++)t.tick(true);assertEquals(before,t.fraction());
        t.delivered();for(int i=0;i<7;i++){t.delivered();t.tick(false);}assertEquals(DEPART,t.phase());
        t.close();t.delivered();t.tick(false);assertEquals(CLOSED,t.phase());
    }
}
