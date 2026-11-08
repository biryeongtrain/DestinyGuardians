package kim.biryeong.destiny.strike.devils;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class DevilsBriefingGateTest {
    @Test void commandStartsWithoutAnyCurtainBeginImmediately() {
        var gate = new DevilsBriefingGate(100);
        assertTrue(gate.ready(100, false));
    }

    @Test void launchCurtainHoldsTheBriefingUntilItLiftsPlusABeat() {
        var gate = new DevilsBriefingGate(100);
        for (long t = 100; t < 160; t++) assertFalse(gate.ready(t, true), "still dark at " + t);
        assertFalse(gate.ready(160, false), "the picture just came back; Zavala waits");
        assertFalse(gate.ready(160 + DevilsBriefingGate.BEAT - 1, false));
        assertTrue(gate.ready(160 + DevilsBriefingGate.BEAT, false));
    }

    @Test void curtainReturningRestartsTheBeat() {
        var gate = new DevilsBriefingGate(0);
        assertFalse(gate.ready(1, true));
        assertFalse(gate.ready(5, false));
        assertFalse(gate.ready(15, true), "a member went dark again (reconnect)");
        assertFalse(gate.ready(16, false));
        assertFalse(gate.ready(16 + DevilsBriefingGate.BEAT - 1, false));
        assertTrue(gate.ready(16 + DevilsBriefingGate.BEAT, false));
    }

    @Test void aCurtainThatNeverLiftsCannotHoldTheRunForever() {
        var gate = new DevilsBriefingGate(10);
        assertFalse(gate.ready(11, true));
        assertFalse(gate.ready(10 + DevilsBriefingGate.TIMEOUT - 1, true));
        assertTrue(gate.ready(10 + DevilsBriefingGate.TIMEOUT, true));
    }
}
