package kim.biryeong.destiny.campaign.presentation;

import kim.biryeong.destiny.guardian.GuardianClass;
import net.minecraft.world.entity.player.Input;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;

class OpeningClassChoiceTest {
    private static Input in(boolean left, boolean right, boolean jump) {
        return new Input(false, false, left, right, jump, false, false);
    }

    @Test void startsOnHunterWithoutClassAndOnCurrentClassOtherwise() {
        assertEquals(GuardianClass.HUNTER, new OpeningScan.ClassChoice(GuardianClass.NONE, null).selected());
        assertEquals(GuardianClass.WARLOCK, new OpeningScan.ClassChoice(GuardianClass.WARLOCK, null).selected());
    }

    @Test void aAndDCycleOnKeyPressEdgesAndWrap() {
        var c = new OpeningScan.ClassChoice(GuardianClass.NONE, null);
        assertTrue(c.step(in(false, true, false)));
        assertEquals(GuardianClass.WARLOCK, c.selected());
        assertFalse(c.step(in(false, true, false)), "holding D must not repeat");
        c.step(Input.EMPTY);
        c.step(in(false, true, false));
        assertEquals(GuardianClass.TITAN, c.selected(), "D wraps around");
        c.step(Input.EMPTY);
        c.step(in(true, false, false));
        assertEquals(GuardianClass.WARLOCK, c.selected(), "A wraps back");
    }

    @Test void spaceConfirmsButAlreadyHeldSpaceDoesNot() {
        var c = new OpeningScan.ClassChoice(GuardianClass.NONE, in(false, false, true));
        c.step(in(false, false, true));
        assertFalse(c.confirmed);
        c.step(Input.EMPTY);
        c.step(in(false, false, true));
        assertTrue(c.confirmed);
        assertFalse(c.step(in(true, false, false)), "no changes after confirming");
        assertEquals(GuardianClass.HUNTER, c.selected());
    }
}
