package kim.biryeong.destiny.weapon;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

/** Cosmetic phase observation may not restart or move W58's existing deadlines. */
class SwapProgressW91Test {
    @Test void initialAndFinishedAreRestingWithoutTimers() {
        var c = new WeaponSwapCycle();
        c.select(new Object(), 0, 0, 0);
        assertEquals(WeaponSwapCycle.Phase.NONE, c.phase(0));
        assertEquals(1f, c.progress(0));
        assertEquals(0, c.remaining(0));
    }
    @Test void stowAndReadyUseTheirOwnExactOrigins() {
        var c = new WeaponSwapCycle(); c.select(new Object(), 0, 0, 0);
        c.select(new Object(), 10, 8, 12);
        assertEquals(0f, c.progress(10));
        assertEquals(.5f, c.progress(14));
        assertEquals(0f, c.progress(18));
        assertEquals(.5f, c.progress(24));
        assertEquals(1f, c.progress(30));
        assertEquals(0, c.remaining(30));
    }
    @Test void stowRetargetKeepsActualOutgoingClock() {
        var c = new WeaponSwapCycle(); c.select(new Object(), 0, 0, 0);
        c.select(new Object(), 10, 8, 9);
        c.select(new Object(), 14, 100, 12);
        assertEquals(.5f, c.progress(14));
        assertEquals(WeaponSwapCycle.Phase.READY, c.phase(18));
        assertEquals(0f, c.progress(18));
        assertEquals(0, c.remaining(30));
    }
    @Test void readyInterruptionStartsNewOutgoingClock() {
        var c = new WeaponSwapCycle(); c.select(new Object(), 0, 0, 0);
        c.select(new Object(), 10, 8, 12);
        c.select(new Object(), 20, 6, 8);
        assertEquals(0f, c.progress(20));
        assertEquals(.5f, c.progress(23));
        assertEquals(WeaponSwapCycle.Phase.READY, c.phase(26));
        assertEquals(0f, c.progress(26));
        assertEquals(.5f, c.progress(30));
        assertEquals(0, c.remaining(34));
    }
    @Test void zeroPhasesNeverDivideByZeroOrCreateDelay() {
        var c = new WeaponSwapCycle(); c.select(new Object(), 0, 0, 0);
        c.select(new Object(), 10, 0, 8);
        assertEquals(WeaponSwapCycle.Phase.READY, c.phase(10));
        assertEquals(0f, c.progress(10));
        c.select(new Object(), 30, 6, 0);
        assertEquals(.5f, c.progress(33));
        assertEquals(1f, c.progress(36));
        assertEquals(0, c.remaining(36));
        c.select(new Object(), 40, 0, 0);
        assertEquals(1f, c.progress(40));
        assertEquals(0, c.remaining(40));
    }
    @Test void repeatedQueriesDoNotMutatePhaseOrRemaining() {
        var c = new WeaponSwapCycle(); c.select(new Object(), 0, 0, 0);
        c.select(new Object(), 10, 8, 12);
        for (int i = 0; i < 100; i++) assertEquals(.5f, c.progress(14));
        assertEquals(16, c.remaining(14));
        assertEquals(WeaponSwapCycle.Phase.STOW, c.phase(14));
    }
}
