package kim.biryeong.destiny.strike.devils;

import org.junit.jupiter.api.Test;
import java.util.*;
import static org.junit.jupiter.api.Assertions.*;

class DevilsAdmissionTest {
    @Test void personalLeaveDuringPreparationOrAdmissionNeverBlocksRetainedReadyTeam() {
        UUID a = UUID.randomUUID(), b = UUID.randomUUID(), c = UUID.randomUUID();
        var roster = new DevilsRoster(List.of(a, b, c));
        var retained = new HashSet<>(List.of(a, b, c));
        roster.ready(b, true); roster.ready(c, true);
        assertFalse(DevilsAdmission.ready(roster.members(), retained::contains));
        roster.disconnected(a, 20); retained.remove(a);
        assertEquals(2, DevilsAdmission.count(roster.members(), retained::contains));
        assertTrue(DevilsAdmission.ready(roster.members(), retained::contains));
        roster.disconnected(b, 30); retained.remove(b);
        assertEquals(1, DevilsAdmission.count(roster.members(), retained::contains));
        assertTrue(DevilsAdmission.ready(roster.members(), retained::contains));
        retained.clear(); assertFalse(DevilsAdmission.ready(roster.members(), retained::contains));
    }
    @Test void retainedOfflineMemberStillNeedsReconnectAndWorldReadiness() {
        UUID a = UUID.randomUUID(), b = UUID.randomUUID(); var roster = new DevilsRoster(List.of(a, b));
        roster.ready(a, true); roster.ready(b, true); roster.disconnected(b, 0);
        assertFalse(DevilsAdmission.ready(roster.members(), x -> true));
        roster.rejoin(b, 1); assertFalse(DevilsAdmission.ready(roster.members(), x -> true));
        roster.ready(b, true); assertTrue(DevilsAdmission.ready(roster.members(), x -> true));
    }
}
