package kim.biryeong.destiny.weapon;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class WeaponSwapCycleTest {
    @Test void initialEquippedObservationAndRepeatedSameIdentityDoNotAnimate() {
        var c = new WeaponSwapCycle(); var a = new Object();
        assertFalse(c.select(a, 20, 8, 7)); assertEquals(0, c.remaining(20));
        assertFalse(c.select(a, 21, 8, 7)); assertEquals(WeaponSwapCycle.Phase.NONE, c.phase(21));
    }
    @Test void outgoingStowThenIncomingReadyAtExactServerTick() {
        var c = new WeaponSwapCycle(); c.select(new Object(), 20, 0, 0);
        assertTrue(c.select(new Object(), 30, 8, 12));
        assertEquals(20, c.remaining(30)); assertEquals(WeaponSwapCycle.Phase.STOW, c.phase(37));
        assertEquals(WeaponSwapCycle.Phase.READY, c.phase(38)); assertEquals(1, c.remaining(49));
        assertEquals(0, c.remaining(50)); assertEquals(WeaponSwapCycle.Phase.NONE, c.phase(50));
    }
    @Test void sameTickAwayAndBackCannotEraseUnfinishedStow() {
        var c = new WeaponSwapCycle(); var a = new Object(); c.select(a, 0, 0, 0);
        c.select(new Object(), 5, 10, 6); c.select(a, 5, 1, 7);
        assertEquals(17, c.remaining(5)); assertEquals(WeaponSwapCycle.Phase.STOW, c.phase(14));
        assertEquals(0, c.remaining(22));
    }
    @Test void retargetDuringStowDoesNotRepeatOrExtendTheOutgoingAnimation() {
        var c = new WeaponSwapCycle(); c.select(new Object(), 0, 0, 0);
        c.select(new Object(), 10, 8, 9); c.select(new Object(), 15, 15, 12);
        assertEquals(15, c.remaining(15)); assertEquals(WeaponSwapCycle.Phase.READY, c.phase(18));
        assertEquals(0, c.remaining(30));
    }
    @Test void interruptingAnActualDrawStowsThatIncomingWeapon() {
        var c = new WeaponSwapCycle(); c.select(new Object(), 0, 0, 0);
        c.select(new Object(), 10, 8, 12); c.select(new Object(), 20, 7, 6);
        assertEquals(13, c.remaining(20)); assertEquals(WeaponSwapCycle.Phase.STOW, c.phase(26));
        assertEquals(WeaponSwapCycle.Phase.READY, c.phase(27)); assertEquals(0, c.remaining(33));
    }
    @Test void buildingItemDetourStillPaysRemainingStowAndNewReady() {
        var c = new WeaponSwapCycle(); var a = new Object(); c.select(a, 0, 0, 0);
        c.select(null, 10, 8, 0); c.select(a, 11, 0, 7);
        assertEquals(14, c.remaining(11)); assertEquals(0, c.remaining(25));
    }
    @Test void equalButDistinctStacksAreNotTheSameIdentity() {
        var c = new WeaponSwapCycle(); c.select(new String("gun"), 0, 0, 0);
        assertTrue(c.select(new String("gun"), 1, 8, 7)); assertEquals(15, c.remaining(1));
    }
    @Test void sameTargetSpamCannotExtendPendingDeadline() {
        var c = new WeaponSwapCycle(); var b = new Object(); c.select(new Object(), 0, 0, 0);
        c.select(b, 1, 8, 7);
        for (int t = 2; t < 16; t++) assertFalse(c.select(b, t, 1200, 1200));
        assertEquals(0, c.remaining(16));
    }
    @Test void unknownSideCanHaveZeroDurationWithoutInventingTiming() {
        var c = new WeaponSwapCycle(); c.select(new Object(), 0, 0, 0);
        c.select(new Object(), 1, 0, 8); assertEquals(8, c.remaining(1));
        assertEquals(WeaponSwapCycle.Phase.READY, c.phase(1));
        c.select(new Object(), 20, 7, 0); assertEquals(7, c.remaining(20));
    }
    @Test void invalidOrOverflowingClocksAreRejectedBeforeMutation() {
        var c = new WeaponSwapCycle(); var a = new Object(); c.select(a, 0, 0, 0);
        assertThrows(IllegalArgumentException.class, () -> c.select(new Object(), -1, 0, 1));
        assertThrows(IllegalArgumentException.class, () -> c.select(new Object(), Long.MAX_VALUE, 0, 1));
        assertThrows(IllegalArgumentException.class, () -> c.select(new Object(), 1, -1, 1));
        assertThrows(IllegalArgumentException.class, () -> c.select(new Object(), 1, 1, 1201));
        assertFalse(c.select(a, 1, 0, 0));
    }
}
