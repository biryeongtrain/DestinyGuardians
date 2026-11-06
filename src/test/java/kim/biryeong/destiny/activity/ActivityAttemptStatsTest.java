package kim.biryeong.destiny.activity;

import org.junit.jupiter.api.Test;
import java.util.*;
import static org.junit.jupiter.api.Assertions.*;

class ActivityAttemptStatsTest {
    static final UUID A = UUID.randomUUID(), B = UUID.randomUUID();
    static List<ActivityAttemptStats.Member> members() { return List.of(
            new ActivityAttemptStats.Member(A, "Alpha", ActivityAttemptStats.Presence.PRESENT),
            new ActivityAttemptStats.Member(B, "Beta", ActivityAttemptStats.Presence.PRESENT)); }
    @Test void actualLossBossSubsetFinalBlowsAndDownLivesAreDistinct() {
        var stats = new ActivityAttemptStats(UUID.randomUUID()); stats.reset(1, "RF", members()); var token = stats.token();
        UUID enemy = UUID.randomUUID();
        stats.damage(token, A, enemy, 4.25, false, true); stats.damage(token, B, enemy, 2, true, true);
        assertFalse(stats.damage(token, A, enemy, 0, true, false));
        assertTrue(stats.death(token, A, 1)); assertFalse(stats.death(token, A, 1));
        var rows = stats.snapshot().rows(); assertEquals(0, rows.get(0).kills()); assertEquals(1, rows.get(1).kills());
        assertEquals(4.25, rows.get(0).damage()); assertEquals(4.25, rows.get(0).bossDamage()); assertEquals(1, rows.get(0).deaths());
    }
    @Test void wipeFreezesLateDamageDeathsAndPresenceAndRestartStartsEmptyNextAttempt() {
        var stats = new ActivityAttemptStats(UUID.randomUUID()); stats.reset(1, "RF", members()); var old = stats.token();
        stats.damage(old, A, UUID.randomUUID(), 8, true, false); stats.death(old, A, 1);
        var frozen = stats.freeze(old); assertSame(frozen, stats.freeze(old));
        assertFalse(stats.damage(old, B, UUID.randomUUID(), 100, true, true)); assertFalse(stats.death(old, B, 1));
        stats.presence(A, ActivityAttemptStats.Presence.LEFT); assertEquals(frozen, stats.snapshot());
        assertTrue(stats.reset(2, "RF", members())); assertEquals(2, stats.snapshot().attempt());
        assertEquals(0, stats.snapshot().rows().getFirst().damage()); assertFalse(stats.damage(old, A, UUID.randomUUID(), 9, true, false));
    }
    @Test void normalCheckpointAdvanceResetsAttemptNumberAndDepartedRowsOnlyPersistInCurrentAttempt() {
        var stats = new ActivityAttemptStats(UUID.randomUUID()); stats.reset(1, "RF", members());
        stats.presence(B, ActivityAttemptStats.Presence.LEFT);
        assertEquals(2, stats.snapshot().rows().size()); assertFalse(stats.damage(stats.token(), B, UUID.randomUUID(), 3, false, false));
        stats.reset(2, "BL", members().subList(0, 1)); assertEquals(1, stats.snapshot().attempt()); assertEquals(1, stats.snapshot().rows().size());
        assertFalse(stats.reset(1, "RF", members()));
    }
    @Test void foreignActivityAndClosedTokensCannotMutateAnotherRun() {
        var a = new ActivityAttemptStats(UUID.randomUUID()); var b = new ActivityAttemptStats(UUID.randomUUID());
        a.reset(1, "RF", members()); b.reset(1, "RF", members());
        assertFalse(a.damage(b.token(), A, UUID.randomUUID(), 4, true, false));
        a.close(); assertFalse(a.death(a.token(), A, 2)); assertNull(a.freeze(a.token())); assertFalse(a.reset(2, "RF", members()));
        assertTrue(b.damage(b.token(), B, UUID.randomUUID(), 2, false, false));
    }
    @Test void sameGenerationNewCheckpointResetsAndReturningCannotReuseOldCheckpointToken() {
        var stats = new ActivityAttemptStats(UUID.randomUUID()); stats.reset(7, "RF", members());
        var originalRf = stats.token(); stats.damage(originalRf, A, UUID.randomUUID(), 20, true, true);
        stats.death(originalRf, A, 1); stats.freeze(originalRf);
        assertTrue(stats.reset(7, "BL", members()));
        var bl = stats.token(); assertEquals(1, stats.snapshot().attempt()); assertFalse(stats.frozen());
        assertEquals(0, stats.snapshot().rows().getFirst().damage()); assertEquals(0, stats.snapshot().rows().getFirst().deaths());
        assertFalse(stats.damage(originalRf, A, UUID.randomUUID(), 9, true, false));
        assertFalse(stats.reset(7, "BL", members()), "Same authoritative scope is idempotent");
        assertTrue(stats.reset(7, "RF", members())); assertNotEquals(originalRf, stats.token());
        assertFalse(stats.death(bl, A, 2)); assertFalse(stats.damage(originalRf, A, UUID.randomUUID(), 9, true, false));
        assertFalse(stats.reset(6, "SP", members()), "Older generation stays rejected even with another checkpoint");
    }
}
