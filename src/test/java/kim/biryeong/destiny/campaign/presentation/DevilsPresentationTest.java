package kim.biryeong.destiny.campaign.presentation;

import org.junit.jupiter.api.Test;
import java.util.UUID;
import static org.junit.jupiter.api.Assertions.*;

class DevilsPresentationTest {
    @Test void cameraTimeoutNeverCompletesAnAnimation() {
        UUID actor=UUID.randomUUID();var gate=new DevilsPresentation.IntroGate(7,actor);gate.started=true;
        for(int tick=0;tick<10000;tick++)assertFalse(gate.consume(7,actor));
    }
    @Test void normalCallbackIsConsumedOnce() {
        UUID actor=UUID.randomUUID();var gate=new DevilsPresentation.IntroGate(7,actor);gate.started=true;
        gate.naturalEnd(7,actor);assertTrue(gate.consume(7,actor));assertFalse(gate.consume(7,actor));
    }
    @Test void cancellationInvalidatesQueuedCallback() {
        UUID actor=UUID.randomUUID();var gate=new DevilsPresentation.IntroGate(7,actor);gate.started=true;
        gate.cancel();gate.naturalEnd(7,actor);assertFalse(gate.consume(7,actor));
    }
    @Test void cancellationAfterCompletionBeforeServerTickStillCannotSucceed() {
        UUID actor=UUID.randomUUID();var gate=new DevilsPresentation.IntroGate(7,actor);gate.started=true;
        gate.naturalEnd(7,actor);gate.cancel();assertFalse(gate.consume(7,actor));
    }
    @Test void oldGenerationOrReplacementActorCannotReleaseNewBoss() {
        UUID actor=UUID.randomUUID();var gate=new DevilsPresentation.IntroGate(7,actor);gate.started=true;
        gate.naturalEnd(6,actor);gate.naturalEnd(7,UUID.randomUUID());assertFalse(gate.consume(7,actor));
        gate.naturalEnd(7,actor);assertFalse(gate.consume(8,actor));assertFalse(gate.consume(7,UUID.randomUUID()));
    }
    @Test void elapsedClipFinishesOnlyAfterAuthoredLengthAndGrace() {
        UUID actor=UUID.randomUUID();var gate=new DevilsPresentation.IntroGate(7,actor);gate.started=true;
        gate.clipElapsed(7,actor,99,80);assertFalse(gate.consume(7,actor));
        gate.clipElapsed(7,actor,100,80);assertTrue(gate.consume(7,actor));
        var unknown=new DevilsPresentation.IntroGate(7,actor);unknown.started=true;
        unknown.clipElapsed(7,actor,10000,0);assertFalse(unknown.consume(7,actor));
        var cancelled=new DevilsPresentation.IntroGate(7,actor);cancelled.started=true;cancelled.cancel();
        cancelled.clipElapsed(7,actor,10000,80);assertFalse(cancelled.consume(7,actor));
    }
    @Test void rejectedAnimationCannotSignalCompletion() {
        UUID actor=UUID.randomUUID();var gate=new DevilsPresentation.IntroGate(7,actor);
        gate.naturalEnd(7,actor);assertFalse(gate.consume(7,actor));
    }
}
