package kim.biryeong.destiny.activity.strike;

import java.util.List;
import java.util.UUID;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class StrikeRosterTest {
    private final UUID a = UUID.randomUUID(), b = UUID.randomUUID(), c = UUID.randomUUID();
    @Test void admissionAllowsOneToThreeDistinctReadyIdentities() {
        assertThrows(IllegalArgumentException.class, () -> new StrikeRoster(List.of(), 1, 3));
        assertThrows(IllegalArgumentException.class, () -> new StrikeRoster(List.of(a, b, c, UUID.randomUUID()), 1, 3));
        for (var ids : List.of(List.of(a), List.of(a, b), List.of(a, b, c))) {
            var roster = new StrikeRoster(ids, 1, 3);
            assertFalse(roster.allReady());
            ids.forEach(id -> roster.ready(id, true));
            assertTrue(roster.allReady());
            assertEquals(ids.size(), roster.living());
        }
        assertThrows(IllegalArgumentException.class, () -> new StrikeRoster(List.of(a, b, a), 1, 3));
        var team = new StrikeRoster(List.of(a, b, c), 1, 3);
        team.ready(a, true); team.ready(b, true);
        assertFalse(team.allReady());
        team.ready(c, true);
        assertTrue(team.allReady());
        assertEquals(StrikeRoster.Join.UNKNOWN, team.rejoin(UUID.randomUUID(), 0));
    }
    @Test void reconnectDoesNotReplaceRosterOrAutomaticallyMarkWorldReady() {
        var team = new StrikeRoster(List.of(a, b, c), 1, 3);
        for (var id : List.of(a, b, c)) team.ready(id, true);
        team.down(b, true);
        team.disconnected(a, 100);
        assertEquals(1, team.living());
        assertEquals(StrikeRoster.Join.ACCEPTED, team.rejoin(a, 2499));
        assertEquals(3, team.connected());
        assertEquals(1, team.living());
        team.ready(a, true);
        assertEquals(2, team.living());
        assertEquals(3, team.members().size());
    }
    @Test void repeatedDisconnectCannotRefreshExpiredSlots() {
        var team = new StrikeRoster(List.of(a, b, c), 1, 3);
        team.disconnected(a, 100);
        team.disconnected(a, 2000);
        assertEquals(StrikeRoster.Join.EXPIRED, team.rejoin(a, 2500));
        assertEquals(StrikeRoster.Join.EXPIRED, team.rejoin(a, 2501));
        assertEquals(2, team.connected());
    }
    @Test void offlineTimeoutUsesRealServerTicksAndCancelsOnReturn() {
        var team = new StrikeRoster(List.of(a, b, c), 1, 3);
        team.disconnected(a, 0); team.disconnected(b, 100); team.disconnected(c, 200);
        assertFalse(team.abandoned(2599));
        assertEquals(StrikeRoster.Join.ACCEPTED, team.rejoin(c, 2599));
        assertFalse(team.abandoned(2600));
        team.disconnected(c, 2700);
        assertTrue(team.abandoned(5100));
    }
}
