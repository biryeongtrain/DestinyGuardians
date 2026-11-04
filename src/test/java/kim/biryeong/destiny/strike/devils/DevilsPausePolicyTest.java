package kim.biryeong.destiny.strike.devils;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class DevilsPausePolicyTest {
    @Test void fallbackCaptionClosesBeforeTheNextEncounterCanSpawn() {
        int[] closed={0}, spawned={0};
        var director=new DevilsDirector(new DevilsDirector.Host() {
            public boolean spawn(DevilsDirector.Spawn spawn) { assertEquals(1,closed[0]);spawned[0]++;return true; }
            public void retire(DevilsDirector.ActorRef actor,DevilsDirector.Retirement reason) { }
            public DevilsDirector.CuePlayback cue(DevilsDirector.Cue cue) { return DevilsDirector.CuePlayback.unavailable(); }
            public void cueFallbackFinished(DevilsDirector.Cue cue) { assertEquals("80b59f27",cue.lineId());closed[0]++; }
        });
        director.begin(1);
        for(int i=0;i<59;i++)director.tick();
        assertEquals(0,closed[0]);
        for(int i=0;i<80;i++)director.tick();
        assertEquals(1,closed[0]);assertTrue(spawned[0]>0);
    }

    private static DevilsDirector briefing() {
        var director = new DevilsDirector(new DevilsDirector.Host() {
            public boolean spawn(DevilsDirector.Spawn spawn) { return true; }
            public void retire(DevilsDirector.ActorRef actor, DevilsDirector.Retirement reason) { }
            public DevilsDirector.CuePlayback cue(DevilsDirector.Cue cue) { return DevilsDirector.CuePlayback.unavailable(); }
        });
        assertTrue(director.begin(1));
        return director;
    }
    @Test void lockedCinematicAudienceAllowsUnavailableBriefingToFinishAfterThreeSeconds() {
        var director=briefing();
        var policy=DevilsPausePolicy.forPresence(false,true,false);
        assertTrue(policy.actors(), "Enemies remain paused while every player is input locked");
        director.pause(policy.progress());
        for(int i=0;i<59;i++) director.tick();
        assertEquals(DevilsDirector.Phase.BRIEFING,director.phase());
        director.tick();
        assertEquals(DevilsDirector.Phase.RY_APPROACH,director.phase(), "Missing audio cannot deadlock the briefing lock");
    }
    @Test void absentUnreadyOrDownAudienceFreezesProgressAndActorClocks() {
        var director=briefing();
        var policy=DevilsPausePolicy.forPresence(false,false,false);
        director.pause(policy.progress());
        assertTrue(policy.actors());
        for(int i=0;i<1000;i++) director.tick();
        assertEquals(0,director.snapshot().tick());
        assertEquals(DevilsDirector.Phase.BRIEFING,director.phase());
        director.pause(DevilsPausePolicy.forPresence(false,true,false).progress());
        for(int i=0;i<60;i++)director.tick();
        assertEquals(DevilsDirector.Phase.RY_APPROACH,director.phase());
    }
    @Test void checkpointPlacementSuspendsBothClocksEvenWithAnAudience() {
        var paused=DevilsPausePolicy.forPresence(true,true,true);
        assertTrue(paused.progress());assertTrue(paused.actors());
        var active=DevilsPausePolicy.forPresence(false,true,true);
        assertFalse(active.progress());assertFalse(active.actors());
    }
}
