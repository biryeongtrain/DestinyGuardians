package kim.biryeong.destiny.fireteam;

import org.junit.jupiter.api.Test;

import java.util.List;
import java.util.UUID;

import static org.junit.jupiter.api.Assertions.*;

class FireteamRosterTest {
    final UUID a = UUID.randomUUID(), b = UUID.randomUUID(), c = UUID.randomUUID(), d = UUID.randomUUID();

    @Test void joinRespectsCapacityListingAndSingleMembership() {
        var r = new FireteamRoster();
        var t = r.create(a, "A", "devils_lair", true, 0);
        assertNull(r.join(b, "B", t.id, 3));
        assertNull(r.join(c, "C", t.id, 3));
        assertEquals(FireteamRoster.Error.FULL, r.join(d, "D", t.id, 3));
        assertEquals(FireteamRoster.Error.IN_FIRETEAM, r.join(b, "B", t.id, 3));
        assertEquals(List.of(a, b, c), t.members());
        var closed = r.create(d, "D", "devils_lair", false, 0);
        assertEquals(FireteamRoster.Error.IN_FIRETEAM, r.join(d, "D", closed.id, 3));
        assertEquals(FireteamRoster.Error.GONE, r.join(UUID.randomUUID(), "X", 999, 3));
        assertEquals(FireteamRoster.Error.CLOSED, r.join(UUID.randomUUID(), "X", closed.id, 3));
    }

    @Test void leaderLeavingPromotesNextAndEmptyTeamDisbands() {
        var r = new FireteamRoster();
        var t = r.create(a, "A", "devils_lair", true, 0);
        r.join(b, "B", t.id, 3);
        r.leave(a);
        assertEquals(b, t.leader());
        assertTrue(r.team(a).isEmpty());
        r.leave(b);
        assertTrue(r.byId(t.id).isEmpty());
        assertTrue(r.listings("devils_lair").isEmpty());
    }

    @Test void onlyTheLeaderManagesTheFireteam() {
        var r = new FireteamRoster();
        var t = r.create(a, "A", "devils_lair", true, 0);
        r.join(b, "B", t.id, 3);
        assertEquals(FireteamRoster.Error.NOT_LEADER, r.kick(b, a));
        assertEquals(FireteamRoster.Error.SELF, r.kick(a, a));
        assertEquals(FireteamRoster.Error.NOT_MEMBER, r.kick(a, c));
        assertEquals(FireteamRoster.Error.NOT_LEADER, r.listed(b, false));
        assertNull(r.promote(a, b));
        assertEquals(b, t.leader());
        assertNull(r.kick(b, a));
        assertTrue(r.team(a).isEmpty());
    }

    @Test void retargetRequiresTheMembersToFit() {
        var r = new FireteamRoster();
        var t = r.create(a, "A", "devils_lair", true, 0);
        r.join(b, "B", t.id, 3);
        assertEquals(FireteamRoster.Error.TOO_MANY, r.retarget(a, "guardian_rises", 1));
        r.leave(b);
        assertNull(r.retarget(a, "guardian_rises", 1));
        assertEquals("guardian_rises", t.activity());
    }

    @Test void tagsAreCappedAndToggle() {
        var r = new FireteamRoster();
        r.create(a, "A", "devils_lair", true, 0);
        for (int i = 0; i < FireteamRoster.MAX_TAGS; i++) assertNull(r.toggleTag(a, FireteamRoster.TAGS.get(i)));
        assertEquals(FireteamRoster.Error.TAG_LIMIT, r.toggleTag(a, FireteamRoster.TAGS.get(FireteamRoster.MAX_TAGS)));
        assertNull(r.toggleTag(a, FireteamRoster.TAGS.getFirst()));
        assertEquals(FireteamRoster.MAX_TAGS - 1, r.team(a).orElseThrow().tags().size());
        assertEquals(FireteamRoster.Error.UNKNOWN_TAG, r.toggleTag(a, "없는 태그"));
    }

    @Test void launchingOrPlayingTeamsLeaveTheListingsAndRefuseJoins() {
        var r = new FireteamRoster();
        var old = r.create(a, "A", "devils_lair", true, 0);
        var young = r.create(b, "B", "devils_lair", true, 5);
        r.create(c, "C", "guardian_rises", true, 1);
        assertEquals(List.of(old, young), r.listings("devils_lair"));
        r.launching(old, true);
        assertEquals(FireteamRoster.Error.BUSY, r.join(d, "D", old.id, 3));
        assertEquals(List.of(young), r.listings("devils_lair"));
        r.launching(old, false); r.inActivity(old, true);
        assertEquals(FireteamRoster.Error.CLOSED, r.join(d, "D", old.id, 3));
        assertEquals(List.of(young), r.listings("devils_lair"));
    }
}
