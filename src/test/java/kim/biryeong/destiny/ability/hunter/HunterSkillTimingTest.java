package kim.biryeong.destiny.ability.hunter;

import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;

class HunterSkillTimingTest {
    @Test void repeatedSchedulerCallsCannotAdvanceServerTime() {
        var contact = new HunterSkillTiming(100, HunterSkillTiming.THROW_CONTACT_TICKS);
        for (int tick = 100; tick < 104; tick++) {
            for (int call = 0; call < 8; call++) assertFalse(contact.poll(tick, true));
        }
        assertTrue(contact.poll(104, true));
        for (int tick = 104; tick < 120; tick++) assertFalse(contact.poll(tick, true));
        assertTrue(contact.finished());
    }

    @Test void invalidationAtContactWinsOverDeliveryAndCannotRevive() {
        var contact = new HunterSkillTiming(100, 4);
        assertFalse(contact.poll(104, false));
        assertTrue(contact.finished());
        assertFalse(contact.poll(105, true));
    }

    @Test void invalidationDuringAnticipationIsTerminal() {
        var contact = new HunterSkillTiming(100, 4);
        assertFalse(contact.poll(101, false));
        assertFalse(contact.poll(104, true));
    }

    @Test void explicitCancelIsTerminal() {
        var contact = new HunterSkillTiming(100, 4);
        contact.cancel();
        assertFalse(contact.poll(104, true));
        assertTrue(contact.finished());
    }

    @Test void skippedObservationDeliversOnceWithoutWallClockCatchup() {
        var contact = new HunterSkillTiming(100, 4);
        assertFalse(contact.poll(100, true));
        assertTrue(contact.poll(107, true));
        assertFalse(contact.poll(107, true));
    }

    @Test void signedServerTickWrapDoesNotLoseContact() {
        var contact = new HunterSkillTiming(Integer.MAX_VALUE - 2, 4);
        assertFalse(contact.poll(Integer.MIN_VALUE, true));
        assertTrue(contact.poll(Integer.MIN_VALUE + 1, true));
        assertFalse(contact.poll(Integer.MIN_VALUE + 2, true));
    }

    @Test void lungeAndDodgeContactPrecedeAttackContact() {
        var lunge = new HunterSkillTiming(30, HunterSkillTiming.ARC_LUNGE_TICKS);
        var dodge = new HunterSkillTiming(30, HunterSkillTiming.DODGE_CONTACT_TICKS);
        var hit = new HunterSkillTiming(30, HunterSkillTiming.ARC_CONTACT_TICKS);
        assertTrue(lunge.poll(32, true));
        assertTrue(dodge.poll(32, true));
        assertFalse(hit.poll(32, true));
        assertTrue(hit.poll(34, true));
    }

    @Test void negativeDelayIsRejected() {
        assertThrows(IllegalArgumentException.class, () -> new HunterSkillTiming(1, -1));
    }
}
