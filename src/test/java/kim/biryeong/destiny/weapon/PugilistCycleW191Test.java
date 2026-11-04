package kim.biryeong.destiny.weapon;

import org.junit.jupiter.api.Test;
import java.util.UUID;
import static org.junit.jupiter.api.Assertions.*;

class PugilistCycleW191Test {
    @Test void acceptedInputAloneDoesNothingAndExactDeadlineExpiresWithoutReadMutation() {
        var c = new PugilistCycle();
        var melee = c.meleeAccepted(10);
        assertEquals(0, c.remaining(10));
        assertTrue(c.meleeConfirmed(13, melee, UUID.randomUUID()));
        assertEquals(1, c.remaining(72));
        assertEquals(0, c.remaining(73));
        assertEquals(0, c.remaining(12));
        assertEquals(1, c.remaining(72));
    }

    @Test void repeatedContactCannotRefreshButNewAcceptedMeleeOnSameTargetCan() {
        var c = new PugilistCycle();
        var target = UUID.randomUUID();
        var first = c.meleeAccepted(10);
        assertTrue(c.meleeConfirmed(11, first, target));
        assertFalse(c.meleeConfirmed(60, first, target));
        assertEquals(0, c.remaining(71));
        var second = c.meleeAccepted(72);
        assertTrue(c.meleeConfirmed(73, second, target));
        assertEquals(1, c.remaining(132));
        assertEquals(0, c.remaining(133));
    }

    @Test void stowRevokesPendingContactsAndBuffUntilANewAcceptedMelee() {
        var c = new PugilistCycle();
        var melee = c.meleeAccepted(10);
        assertTrue(c.meleeConfirmed(10, melee, UUID.randomUUID()));
        c.stow();
        assertEquals(0, c.remaining(10));
        assertFalse(c.meleeConfirmed(10, melee, UUID.randomUUID()));
        assertTrue(c.meleeConfirmed(12, c.meleeAccepted(12), UUID.randomUUID()));
    }

    @Test void foreignEpochAndClockRewindCannotResurrectOldContacts() {
        var c = new PugilistCycle();
        var other = new PugilistCycle();
        var melee = c.meleeAccepted(20);
        assertFalse(other.meleeConfirmed(20, melee, UUID.randomUUID()));
        assertTrue(c.meleeConfirmed(20, melee, UUID.randomUUID()));
        c.update(19);
        assertEquals(0, c.remaining(20));
        assertFalse(c.meleeConfirmed(21, melee, UUID.randomUUID()));
        assertNull(c.meleeAccepted(-1));
        assertNull(c.meleeAccepted(Long.MAX_VALUE));
        assertTrue(c.meleeConfirmed(22, c.meleeAccepted(22), UUID.randomUUID()));
        c.clear();
        assertEquals(0, c.remaining(22));
        assertFalse(c.meleeConfirmed(23, melee, UUID.randomUUID()));
    }
}
