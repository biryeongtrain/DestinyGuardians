package kim.biryeong.destiny.activity.presentation;

import org.junit.jupiter.api.Test;
import java.util.UUID;
import static org.junit.jupiter.api.Assertions.*;

class ActivityFailureStateTest {
    @Test void oneWipeWaitsForFullPresentationAndConsumesOnlyOneRecovery() {
        var state = new ActivityFailureState(UUID.randomUUID());
        assertTrue(state.scope(1, "RF", true));
        assertTrue(state.beginWipe(1)); var token = state.wipe();
        assertFalse(state.beginWipe(1));
        assertEquals(230, ActivityFailureState.WIPE_PRESENTATION_TICKS, "Full user-selected11.14s cue must not be truncated at6s");
        for (int i = 0; i < 229; i++) assertFalse(state.tick(1, true));
        assertEquals(1, state.remainingSeconds()); assertTrue(state.owns(token));
        assertTrue(state.tick(1, true)); assertEquals(0, state.remainingSeconds());
        for (int i = 0; i < 500; i++) assertFalse(state.tick(1, true));
        assertFalse(state.beginWipe(1));
    }
    @Test void offlineGapCannotConsumeSceneAndReconnectCannotChangeItsOwnership() {
        var state = new ActivityFailureState(UUID.randomUUID()); state.scope(5, "SP", true); state.beginWipe(5);
        var token = state.wipe();
        for (int i = 0; i < 300; i++) assertFalse(state.tick(5, false));
        assertEquals(0, state.wipeAge()); assertFalse(state.tick(4, true)); assertEquals(0, state.wipeAge());
        assertTrue(state.owns(token));
        state.scope(6, "SP", true);
        assertFalse(state.owns(token)); assertFalse(state.tick(5, true)); assertFalse(state.wiping());
        assertFalse(state.scope(5, "SP", true)); assertFalse(state.beginWipe(5));
    }
    @Test void phaseExitNewZoneCloseAndAnotherActivityInvalidateOldRecovery() {
        var a = new ActivityFailureState(UUID.randomUUID()); var b = new ActivityFailureState(UUID.randomUUID());
        a.scope(1, "RF", true); b.scope(1, "RF", true); a.beginWipe(1); b.beginWipe(1);
        var old = a.wipe(); assertFalse(b.owns(old));
        a.scope(1, "RF", false); assertFalse(a.wiping()); assertFalse(a.beginWipe(1));
        a.scope(1, "BL", true); assertTrue(a.beginWipe(1)); assertFalse(a.owns(old));
        a.close(); a.close(); assertFalse(a.tick(1, true)); assertFalse(a.scope(2, "RF", true));
        assertTrue(b.wiping()); assertTrue(b.restricted());
    }
}
