package kim.biryeong.destiny.weapon;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class WeaponHolsterCycleTest {
    @Test void stowUsesExactSeventyTickDeadlineWithoutEarlyAttempt() {
        var c = new WeaponHolsterCycle();
        assertFalse(c.observe(10, true, 70));
        assertFalse(c.observe(20, false, 70));
        assertFalse(c.observe(89, false, 70));
        assertTrue(c.observe(90, false, 70));
    }
    @Test void remainingHeldForHoursNeverBuildsAStowCredit() {
        var c = new WeaponHolsterCycle();
        assertFalse(c.observe(0, true, 70));
        assertFalse(c.observe(100000, true, 70));
        assertFalse(c.observe(100001, false, 70));
        assertFalse(c.observe(100070, false, 70));
        assertTrue(c.observe(100071, false, 70));
    }
    @Test void attemptIsConsumedOnceEvenForDuplicateTickAndLaterCalls() {
        var c = new WeaponHolsterCycle(); c.observe(0, false, 70);
        assertTrue(c.observe(70, false, 70));
        assertFalse(c.observe(70, false, 70));
        assertFalse(c.observe(700, false, 70));
    }
    @Test void sameTickDrawAndRestowRequiresAWholeNewWindow() {
        var c = new WeaponHolsterCycle(); c.observe(0, false, 70);
        assertFalse(c.observe(69, true, 70));
        assertFalse(c.observe(69, false, 70));
        assertFalse(c.observe(70, false, 70));
        assertFalse(c.observe(138, false, 70));
        assertTrue(c.observe(139, false, 70));
    }
    @Test void drawAfterACompletedStowArmsTheNextCycle() {
        var c = new WeaponHolsterCycle(); c.observe(0, false, 70);
        assertTrue(c.observe(70, false, 70));
        assertFalse(c.observe(75, true, 70));
        assertFalse(c.observe(80, false, 70));
        assertTrue(c.observe(150, false, 70));
    }
    @Test void serverClockRegressionRestartsRatherThanBackdates() {
        var c = new WeaponHolsterCycle(); c.observe(100, false, 70);
        assertFalse(c.observe(110, false, 70));
        assertFalse(c.observe(1, false, 70));
        assertFalse(c.observe(70, false, 70));
        assertTrue(c.observe(71, false, 70));
    }
    @Test void lateFirstObservationIsNotOfflineProgress() {
        var c = new WeaponHolsterCycle();
        assertFalse(c.observe(900000, false, 70));
        assertFalse(c.observe(900069, false, 70));
        assertTrue(c.observe(900070, false, 70));
    }
    @Test void unsafeDelayRejectedAndDeadlineCannotWrapNegative() {
        var c = new WeaponHolsterCycle();
        assertThrows(IllegalArgumentException.class, () -> c.observe(1, false, 0));
        assertThrows(IllegalArgumentException.class, () -> c.observe(1, false, 1201));
        assertFalse(c.observe(Long.MAX_VALUE - 69, false, 70));
        assertFalse(c.observe(Long.MAX_VALUE - 1, false, 70));
        assertTrue(c.observe(Long.MAX_VALUE, false, 70));
    }
}
