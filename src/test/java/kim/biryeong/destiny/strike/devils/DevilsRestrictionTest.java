package kim.biryeong.destiny.strike.devils;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class DevilsRestrictionTest {
    @Test void clearingEncounterRemovesWipePolicyBeforeZoneTransition() {
        var f = new DevilsRecoveryTest.Fixture(DevilsPlan.Zone.RF);
        f.down(DevilsRecoveryTest.A); f.down(DevilsRecoveryTest.B); f.down(DevilsRecoveryTest.C);
        f.ticks(60); assertTrue(f.recovery.snapshot().wipeRemaining() > 0);
        f.recovery.restricted(false); f.ticks(200);
        assertTrue(f.wipes.isEmpty()); assertEquals(-1, f.recovery.snapshot().wipeRemaining());
        assertEquals(0, f.member(DevilsRecoveryTest.A).readyIn());
    }
    @Test void activeRestrictedPhasesAndClearPhasesMatchPresentationAndRecovery() {
        for (var phase : DevilsDirector.Phase.values()) {
            boolean expected = phase.zone() != DevilsPlan.Zone.RY && phase != DevilsDirector.Phase.RF_CLEAR
                    && phase != DevilsDirector.Phase.BL_CLEAR && phase != DevilsDirector.Phase.COMPLETE && phase != DevilsDirector.Phase.CLOSED;
            assertEquals(expected, DevilsSession.restricted(phase), phase.name());
        }
    }
}
