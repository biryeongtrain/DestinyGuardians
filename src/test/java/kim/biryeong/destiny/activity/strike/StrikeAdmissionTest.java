package kim.biryeong.destiny.activity.strike;

import org.junit.jupiter.api.Test;
import java.util.*;
import static org.junit.jupiter.api.Assertions.*;

class StrikeAdmissionTest {
    @Test void personalLeaveDuringPreparationOrAdmissionNeverBlocksRetainedReadyTeam() {
        UUID a = UUID.randomUUID(), b = UUID.randomUUID(), c = UUID.randomUUID();
        var roster = new StrikeRoster(List.of(a, b, c), 1, 3);
        var retained = new HashSet<>(List.of(a, b, c));
        roster.ready(b, true); roster.ready(c, true);
        assertFalse(StrikeAdmission.ready(roster.members(), retained::contains));
        roster.disconnected(a, 20); retained.remove(a);
        assertEquals(2, StrikeAdmission.count(roster.members(), retained::contains));
        assertTrue(StrikeAdmission.ready(roster.members(), retained::contains));
        roster.disconnected(b, 30); retained.remove(b);
        assertEquals(1, StrikeAdmission.count(roster.members(), retained::contains));
        assertTrue(StrikeAdmission.ready(roster.members(), retained::contains));
        retained.clear(); assertFalse(StrikeAdmission.ready(roster.members(), retained::contains));
    }
    @Test void retainedOfflineMemberStillNeedsReconnectAndWorldReadiness() {
        UUID a = UUID.randomUUID(), b = UUID.randomUUID(); var roster = new StrikeRoster(List.of(a, b), 1, 3);
        roster.ready(a, true); roster.ready(b, true); roster.disconnected(b, 0);
        assertFalse(StrikeAdmission.ready(roster.members(), x -> true));
        roster.rejoin(b, 1); assertFalse(StrikeAdmission.ready(roster.members(), x -> true));
        roster.ready(b, true); assertTrue(StrikeAdmission.ready(roster.members(), x -> true));
    }
}
