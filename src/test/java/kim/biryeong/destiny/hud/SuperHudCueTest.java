package kim.biryeong.destiny.hud;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class SuperHudCueTest {
    @Test void joiningReadyDoesNotReplayButNewChargeDoes() {
        var cue = new SuperHudCue();
        cue.sample(0, "arc", true, false);
        assertEquals(-1, cue.readyAge(0));
        cue.sample(1, "arc", false, false);
        cue.sample(2, "arc", true, false);
        assertEquals(0, cue.readyAge(2));
    }
    @Test void duplicateUpdatesCannotExtendTheCue() {
        var cue = charging();
        for (int i = 0; i < 100; i++) cue.sample(1, "arc", true, false);
        cue.sample(55, "arc", true, false);
        assertEquals(54, cue.readyAge(55));
        cue.sample(57, "arc", true, false);
        assertEquals(-1, cue.readyAge(57));
        cue.sample(999, "arc", true, false);
        assertEquals(-1, cue.readyAge(999));
    }
    @Test void castReplacesReadyAndExpiresWithoutReplay() {
        var cue = charging();
        cue.sample(2, "arc", true, true);
        assertEquals(-1, cue.readyAge(2));
        assertEquals(0, cue.castAge(2));
        cue.sample(14, "arc", false, true);
        assertEquals(-1, cue.castAge(14));
        cue.sample(15, "arc", false, false);
        assertEquals(-1, cue.castAge(15));
    }
    @Test void chargeLossCancelsAndRearms() {
        var cue = charging();
        cue.sample(2, "arc", false, false);
        assertEquals(-1, cue.readyAge(2));
        cue.sample(3, "arc", true, false);
        assertEquals(0, cue.readyAge(3));
    }
    @Test void oneShotSuperExitDoesNotTruncateRelease() {
        var cue = charging();
        cue.sample(2, "arc", false, true);
        cue.sample(3, "arc", false, false);
        assertEquals(1, cue.castAge(3));
        assertEquals(-1, cue.readyAge(3));
        cue.sample(14, "arc", false, false);
        assertEquals(-1, cue.castAge(14));
    }
    @Test void changedOrMissingSuperInvalidatesOldCue() {
        var cue = charging();
        cue.sample(2, "solar", true, false);
        assertEquals(-1, cue.readyAge(2));
        cue.sample(3, null, true, false);
        cue.sample(4, null, true, false);
        assertEquals(-1, cue.readyAge(4));
    }
    @Test void tickCounterWrapDoesNotBreakExpiry() {
        var cue = new SuperHudCue();
        cue.sample(Integer.MAX_VALUE - 10, "arc", false, false);
        cue.sample(Integer.MAX_VALUE - 9, "arc", true, false);
        cue.sample(Integer.MIN_VALUE + 1, "arc", true, false);
        assertEquals(11, cue.readyAge(Integer.MIN_VALUE + 1));
        cue.sample(Integer.MIN_VALUE + 47, "arc", true, false);
        assertEquals(-1, cue.readyAge(Integer.MIN_VALUE + 47));
    }
    private SuperHudCue charging() {
        var cue = new SuperHudCue();
        cue.sample(0, "arc", false, false);
        cue.sample(1, "arc", true, false);
        return cue;
    }
}
