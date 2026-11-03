package kim.biryeong.destiny.activity.reinforcement;

import org.junit.jupiter.api.Test;
import java.util.*;
import static org.junit.jupiter.api.Assertions.*;

class SpawnWarningsTest {
    @Test void relocatedPadRequiresNewFullWarningAndOldGenerationCannotReadIt() {
        var warnings = new SpawnWarnings<String, String, String>();
        warnings.begin(1, "enemy", "old-pad", "old-body", 10, 40);
        assertFalse(warnings.get(1, "enemy").ready(49));
        warnings.begin(1, "enemy", "safe-pad", "safe-body", 45, 40);
        assertFalse(warnings.get(1, "enemy").ready(50));
        assertTrue(warnings.get(1, "enemy").ready(85));
        assertNull(warnings.get(2, "enemy"));
        assertEquals(List.of("safe-body"), warnings.reservations("other"));
        assertEquals(List.of(), warnings.reservations("enemy"));
        assertEquals(List.of("enemy"), warnings.retain(2, Set.of("enemy")));
        assertNull(warnings.get(1, "enemy"));
    }
}
