package kim.biryeong.destiny.weapon;

import org.junit.jupiter.api.Test;
import java.util.List;
import static org.junit.jupiter.api.Assertions.*;

/** Pure transport flag ownership, not actual animation/shoulder-contact acceptance. */
class WeaponCrouchPresentationW161Test {
    @Test void absentStandingPoseDoesNotAddPadding() {
        assertEquals(1, WeaponCrouchPresentation.FLAG_INDEX);
        assertEquals(List.of(), WeaponCrouchPresentation.flags(List.of(), false));
        assertEquals(List.of(true), WeaponCrouchPresentation.flags(List.of(true), false));
    }

    @Test void crouchWritesOnlyFlagOneAndPreservesGripAndHigherSlots() {
        for (boolean grip : new boolean[]{false, true}) {
            var original = List.of(grip, false, true, false, true);
            assertEquals(List.of(grip, true, true, false, true), WeaponCrouchPresentation.flags(original, true));
            assertEquals(List.of(grip, false, true, false, true), original);
        }
        assertEquals(List.of(false, true), WeaponCrouchPresentation.flags(List.of(), true));
    }

    @Test void standingNeutralizesEvenStalePersistedCrouch() {
        assertEquals(List.of(true, false, true),
                WeaponCrouchPresentation.flags(List.of(true, true, true), false));
    }

    @Test void retiringRemovesOnlyOwnedTailAndUnchangedPadding() {
        assertEquals(List.of(), WeaponCrouchPresentation.retiredFlags(List.of(false, true), 0));
        assertEquals(List.of(true), WeaponCrouchPresentation.retiredFlags(List.of(true, true), 0));
        assertEquals(List.of(false), WeaponCrouchPresentation.retiredFlags(List.of(false, true), 1));
        assertEquals(List.of(true), WeaponCrouchPresentation.retiredFlags(List.of(true, true), 1));
    }

    @Test void retiringNeverShiftsLiveHigherSlotsAndDoesNotRestoreAStalePose() {
        for (int size : new int[]{0, 1, 2, 9}) {
            assertEquals(List.of(true, false, true, false),
                    WeaponCrouchPresentation.retiredFlags(List.of(true, true, true, false), size));
        }
        assertEquals(List.of(true, false), WeaponCrouchPresentation.retiredFlags(List.of(true, true), 2));
    }

    @Test void updatesAndCleanupAreIdempotentAndNeverMutateInputLists() {
        var original = List.of(true, false, true);
        var crouch = WeaponCrouchPresentation.flags(original, true);
        assertEquals(crouch, WeaponCrouchPresentation.flags(crouch, true));
        var retired = WeaponCrouchPresentation.retiredFlags(crouch, 3);
        assertEquals(retired, WeaponCrouchPresentation.retiredFlags(retired, 3));
        assertEquals(original, retired);
        assertThrows(UnsupportedOperationException.class, () -> crouch.set(1, false));
    }
}
