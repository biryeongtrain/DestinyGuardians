package kim.biryeong.destiny.activity.strike;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class StrikeCoordinatorInfoTest {
    private static StrikeCoordinator.Info info(String id, int min, int max) {
        return new StrikeCoordinator.Info(id, "이름", "공격전", "설명", "fireteam/banner", "fireteam/icon", min, max, 10);
    }
    @Test void validListingIsAccepted() {
        var info = info("devils_lair", 1, 3);
        assertEquals("devils_lair", info.id());
        assertEquals(3, info.maxPlayers());
    }
    @Test void blankIdAndBadFireteamSizesAreRejected() {
        assertThrows(IllegalArgumentException.class, () -> info(" ", 1, 3));
        assertThrows(IllegalArgumentException.class, () -> info("x", 0, 3));
        assertThrows(IllegalArgumentException.class, () -> info("x", 3, 2));
    }
    @Test void nullTextIsRejected() {
        assertThrows(IllegalArgumentException.class, () -> new StrikeCoordinator.Info("x", null, "t", "d", "b", "i", 1, 3, 1));
    }
}
