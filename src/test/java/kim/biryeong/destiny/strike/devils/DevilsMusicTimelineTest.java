package kim.biryeong.destiny.strike.devils;

import com.google.gson.*;
import org.junit.jupiter.api.Test;
import java.io.*;
import java.util.Objects;
import static org.junit.jupiter.api.Assertions.*;

class DevilsMusicTimelineTest {
    private JsonObject data() throws Exception {
        try(var reader=new InputStreamReader(Objects.requireNonNull(getClass().getResourceAsStream("/destiny/devils_lair/music.json")))) {
            return JsonParser.parseReader(reader).getAsJsonObject();
        }
    }
    private static long ms(double value){return (long)(value*1e6);}
    @Test void nextMarkerUsesInternalCueInsteadOfWaitingForThreeMinuteTrack() throws Exception {
        var clip=data().getAsJsonObject("segments").getAsJsonObject("88480404");
        assertEquals(ms(3636.36363636364),DevilsMusicTimeline.synchronization(clip,0,ms(1000),4));
        assertEquals(ms(18181.8181818182),DevilsMusicTimeline.synchronization(clip,0,ms(4000),4));
    }
    @Test void barGridAndSilenceUseDistinctSourceRules() throws Exception {
        var d=data();var clip=d.getAsJsonObject("segments").getAsJsonObject("949958315");
        assertEquals(ms(2000),DevilsMusicTimeline.synchronization(clip,0,ms(100),2));
        assertEquals(ms(1000),DevilsMusicTimeline.synchronization(clip,0,ms(100),1));
        assertEquals(ms(100),DevilsMusicTimeline.synchronization(clip,0,ms(100),0));
        var t=new DevilsMusicTimeline(d,1);assertNotNull(t.update(0,0).segment());
        assertEquals(629984384,t.update(1,ms(100)).segment()); // 12s fade remains a transport limitation, sync is immediate.
        assertEquals(933801940,t.update(2,ms(200)).segment()); // segment-specific immediate rule wins.
    }
    @Test void refineryTransitionUsesNextMarkerAndActualTransitionClip() throws Exception {
        var t=new DevilsMusicTimeline(data(),1);
        assertEquals(933801940,t.update(2,0).segment());
        assertNull(t.update(3,ms(1000)).segment());
        assertNull(t.update(3,ms(3000)).segment());
        var change=t.update(3,ms(3637));
        assertEquals(829866489,change.segment());assertTrue(change.transition());assertTrue(change.stop());
        assertNull(t.update(3,ms(4000)).segment());
        assertEquals(88480404,t.update(3,ms(7052)).segment());
    }
    @Test void laterDestinationRuleOverridesEarlierSourceTransition() throws Exception {
        var t=new DevilsMusicTimeline(data(),1);t.update(2,0);t.update(5,ms(1000));
        var change=t.update(5,ms(3637));
        assertNotNull(change.segment());assertNotEquals(829866489,change.segment());assertFalse(change.transition());
    }
    @Test void normalAndMetalVictoryUseDifferentJumpTargets() throws Exception {
        var d=data();var normal=new DevilsMusicTimeline(d,1);normal.update(7,0);
        assertNull(normal.update(9,ms(100)).segment());
        assertEquals(657632137,normal.update(9,ms(1000)).segment());
        var metal=new DevilsMusicTimeline(d,1);metal.update(8,0);metal.update(9,ms(100));
        assertEquals(268741950,metal.update(9,ms(3000)).segment());
        var joinedAfterVictory=new DevilsMusicTimeline(d,1);
        assertEquals(619788219,joinedAfterVictory.update(9,0).segment());
    }
    @Test void lateListenerStartsCurrentPhaseWithoutRestartingExistingListener() throws Exception {
        var d=data();var first=new DevilsMusicTimeline(d,7);first.update(7,0);
        assertNull(first.update(7,ms(20000)).segment());
        var late=new DevilsMusicTimeline(d,7);
        assertEquals(949958315,late.update(7,ms(20000)).segment());
        assertNull(first.update(7,ms(20001)).segment());
        assertEquals(21796713,first.update(7,ms(68000)).segment());
        assertNull(late.update(7,ms(68000)).segment());
        first.reset();assertEquals(949958315,first.update(7,ms(70000)).segment());
    }
    @Test void cancellationAndNewRequestedPhaseReplacePendingBoundary() throws Exception {
        var t=new DevilsMusicTimeline(data(),1);t.update(3,0);t.update(4,ms(1000));
        assertNull(t.update(3,ms(4000)).segment()); // cancelling pending phase does not play transition.
        var stop=t.update(-1,ms(5000));assertTrue(stop.stop());assertNull(stop.segment());
        assertEquals(949958315,t.update(7,ms(5001)).segment());
    }
}
