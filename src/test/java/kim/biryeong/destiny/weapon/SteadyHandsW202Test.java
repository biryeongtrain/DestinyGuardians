package kim.biryeong.destiny.weapon;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

/** New event/lifecycle clock behavior only; no per-weapon numerical perk tests. */
class SteadyHandsW202Test {
    @Test void firstKillStartsInitialWindowAndActiveKillReplacesItWithShorterRefresh() {
        var c = new SteadyHandsCycle();
        var paid = c.capture(10);
        assertEquals(0, c.remaining(10));
        assertTrue(c.killed(10, paid, new Object()));
        assertEquals(SteadyHandsProfile.initialTicks(), c.remaining(10));
        assertTrue(c.killed(11, c.capture(11), new Object()));
        assertEquals(SteadyHandsProfile.refreshTicks(), c.remaining(11));
        assertEquals(1, c.remaining(140));
        assertEquals(0, c.remaining(141));
        assertTrue(c.killed(141, c.capture(141), new Object()));
        assertEquals(SteadyHandsProfile.initialTicks(), c.remaining(141));
    }

    @Test void paidProjectileSurvivesOrdinaryStowAndBuffExpiryButClearRevokesAuthority() {
        var c = new SteadyHandsCycle();
        var inFlight = c.capture(20);
        c.update(100); // ordinary stow/tick has no revoke
        assertTrue(c.killed(100, inFlight, new Object()));
        c.update(270); // expired buff is not an expired paid emission
        assertEquals(0, c.remaining(270));
        assertTrue(c.killed(271, inFlight, new Object()));
        assertEquals(SteadyHandsProfile.initialTicks(), c.remaining(271));
        c.clear(); // actual replacement/edit, death, dimension/class/runtime change
        assertEquals(0, c.remaining(271));
        assertFalse(c.killed(271, inFlight, new Object()));
        assertTrue(c.killed(271, c.capture(271), new Object()));
    }

    @Test void duplicateTargetNeverRefreshesAcrossPelletsEmissionsOrExpiredWindows() {
        var c = new SteadyHandsCycle();
        var corpse = new Object(); var first = c.capture(10); var second = c.capture(10);
        assertTrue(c.killed(10, first, corpse));
        assertFalse(c.killed(11, first, corpse));
        assertFalse(c.killed(11, second, corpse));
        assertEquals(SteadyHandsProfile.initialTicks() - 1, c.remaining(11));
        c.update(200);
        assertFalse(c.killed(200, c.capture(200), corpse));
        assertEquals(0, c.remaining(200));
        assertTrue(c.killed(201, c.capture(201), new Object()));
    }

    @Test void emissionLedgerBoundNeverEvictsOrImposesSourceLifetimeKillLimit() {
        var c = new SteadyHandsCycle(); var paid = c.capture(10); var corpse = new Object();
        assertTrue(c.killed(10, paid, corpse));
        for (int n = 1; n < SteadyHandsCycle.MAX_CORPSES_PER_EMISSION; n++)
            assertTrue(c.killed(11, paid, new Object()));
        assertFalse(c.killed(12, paid, new Object()));
        assertFalse(c.killed(12, paid, corpse));
        assertTrue(c.killed(12, c.capture(12), new Object()));
    }

    @Test void pureFutureQueriesDoNotAdvanceTimeAndForeignOrStaleTokensCannotBeBorrowed() {
        var c = new SteadyHandsCycle(); var other = new SteadyHandsCycle(); var paid = c.capture(30);
        assertFalse(other.killed(30, paid, new Object()));
        assertFalse(c.killed(29, paid, new Object()));
        assertFalse(c.killed(30, paid, null));
        assertFalse(c.killed(30, null, new Object()));
        assertTrue(c.killed(30, paid, new Object()));
        assertEquals(0, c.remaining(Long.MAX_VALUE));
        assertEquals(0, c.remaining(-1));
        assertEquals(SteadyHandsProfile.initialTicks() - 1, c.remaining(31));
        assertTrue(c.killed(31, paid, new Object()));
        c.update(29); // writer rollback revokes the epoch
        assertEquals(0, c.remaining(31));
        assertFalse(c.killed(31, paid, new Object()));
        assertNull(c.capture(-1));
    }

    @Test void longClockDoesNotOverflowIntoAnAlreadyExpiredBuff() {
        var c = new SteadyHandsCycle(); long tick = Long.MAX_VALUE - 10;
        assertTrue(c.killed(tick, c.capture(tick), new Object()));
        assertEquals(10, c.remaining(tick));
        assertEquals(1, c.remaining(Long.MAX_VALUE - 1));
        assertEquals(0, c.remaining(Long.MAX_VALUE));
    }
}
