package kim.biryeong.destiny.weapon;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class WeaponCadenceBankTest {
    @Test void differentRangedWeaponDoesNotInheritOldRpm() {
        var b = new WeaponCadenceBank(); var a = new Object(); var other = new Object();
        b.remember(a, 48, 0, false);
        assertEquals(0, b.deadline(other, 5)); assertEquals(48, b.deadline(a, 5));
    }
    @Test void actualIdentityNotEqualComponentsRetainsFractionalReadyTime() {
        var b = new WeaponCadenceBank(); var a = new String("gun"); b.remember(a, 21.75, 10, false);
        assertEquals(21.75, b.deadline(a, 21)); assertEquals(0, b.deadline(new String("gun"), 21));
        assertEquals(0, b.deadline(a, 22));
    }
    @Test void anotherShotCannotEraseAStowedWeaponClock() {
        var b = new WeaponCadenceBank(); var a = new Object(); var c = new Object();
        b.remember(a, 48, 0, false); b.remember(c, 21.5, 15, false);
        assertEquals(48, b.deadline(a, 20)); assertEquals(21.5, b.deadline(c, 20));
    }
    @Test void swordActorRecoveryStillAppliesAcrossItemReplacement() {
        var b = new WeaponCadenceBank(); b.remember(new Object(), 18, 0, true);
        assertEquals(18, b.deadline(new Object(), 10)); assertEquals(0, b.deadline(new Object(), 18));
    }
    @Test void expirationIsBoundedAndPrunedOnEveryWrite() {
        var b = new WeaponCadenceBank(); b.remember(new Object(), 5, 0, false);
        b.remember(new Object(), 10, 5, false); assertEquals(1, b.retainedClocks());
        b.remember(new Object(), 10, 10, false); assertEquals(0, b.retainedClocks());
    }
    @Test void capacityCannotEvictAnUnexpiredClockAndFailsClosed() {
        var b = new WeaponCadenceBank(); var first = new Object(); b.remember(first, 30, 0, false);
        for (int i = 1; i < WeaponCadenceBank.CAPACITY; i++) b.remember(new Object(), 30, 0, false);
        b.remember(new Object(), 40, 0, false);
        assertEquals(WeaponCadenceBank.CAPACITY, b.retainedClocks()); assertEquals(40, b.deadline(first, 5));
        assertEquals(40, b.deadline(new Object(), 5)); assertEquals(0, b.deadline(first, 40));
    }
    @Test void unsafeSnapshotsAreRejectedWithoutMutation() {
        var b = new WeaponCadenceBank(); var a = new Object();
        assertThrows(IllegalArgumentException.class, () -> b.remember(a, Double.NaN, 0, false));
        assertThrows(IllegalArgumentException.class, () -> b.remember(a, Double.POSITIVE_INFINITY, 0, false));
        assertThrows(IllegalArgumentException.class, () -> b.remember(a, -1, 0, false));
        assertThrows(IllegalArgumentException.class, () -> b.remember(a, 1202, 0, false));
        assertEquals(0, b.retainedClocks());
    }
    @Test void restoringAClockNeverRestoresChargeOrPendingReload() {
        var cycle = new WeaponCycle(); cycle.restoreFiringDeadline(8.25);
        assertFalse(cycle.ready(8)); assertTrue(cycle.ready(9)); assertEquals(8.25, cycle.firingDeadline());
        cycle.startCharge(9); assertThrows(IllegalArgumentException.class, () -> cycle.restoreFiringDeadline(0));
        cycle.cancelPending(); cycle.restoreFiringDeadline(8.25);
        assertFalse(cycle.charging()); assertFalse(cycle.reloading()); assertFalse(cycle.bursting());
        assertThrows(IllegalArgumentException.class, () -> cycle.restoreFiringDeadline(Double.NaN));
    }
}
