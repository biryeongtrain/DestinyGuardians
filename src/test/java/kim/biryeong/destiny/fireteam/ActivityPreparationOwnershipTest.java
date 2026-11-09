package kim.biryeong.destiny.fireteam;

import org.junit.jupiter.api.Test;
import java.util.*;
import static org.junit.jupiter.api.Assertions.*;

class ActivityPreparationOwnershipTest {
    private record Token(String value) { }
    @Test void onlyTheCapturedRunMayBeCancelledEvenWhenAnotherTokenIsEqual() {
        var player = UUID.randomUUID(); var captured = new Token("run"); var replacement = new Token("run");
        assertEquals(captured, replacement);
        var expected = Map.<UUID, Object>of(player, captured);
        assertTrue(ActivityCatalog.ownsPreparation(expected, player, captured));
        assertFalse(ActivityCatalog.ownsPreparation(expected, player, replacement));
    }
    @Test void aDepartedMemberOrDifferentPlayerCannotApproveCancellation() {
        var player = UUID.randomUUID(); var token = new Object(); var expected = Map.of(player, token);
        assertFalse(ActivityCatalog.ownsPreparation(expected, player, null));
        assertFalse(ActivityCatalog.ownsPreparation(expected, UUID.randomUUID(), token));
        assertFalse(ActivityCatalog.ownsPreparation(Map.of(), player, token));
    }
}
