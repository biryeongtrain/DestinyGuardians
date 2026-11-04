package kim.biryeong.destiny.weapon;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class AssassinsBladeCycleW195Test {
    @Test void ownKillDoesNotRetroactivelyBoostItsDamageAndKillsRefreshExactExpiry() {
        var c = new AssassinsBladeCycle();
        var first = c.capture(10);
        assertEquals(0, c.remaining(10));
        assertTrue(c.killed(10, first, new Object()));
        assertEquals(1f, c.multiplier(10, first)); // own direct/splash retains pre-kill scalar
        var active = c.capture(11);
        assertTrue(c.multiplier(11, active) > 1f);
        c.update(109); // ordinary stow/tick never cancels the source buff
        assertEquals(1, c.remaining(109));
        assertTrue(c.killed(109, active, new Object()));
        assertEquals(100, c.remaining(109));
        assertEquals(1, c.remaining(208));
        assertEquals(0, c.remaining(209));
        assertEquals(1f, c.multiplier(209, c.capture(209)));
        assertTrue(c.multiplier(209, active) > 1f); // immutable original paid snapshot
    }

    @Test void sharedDirectSplashCorpseCannotRefreshTwiceAndBoundNeverEvicts() {
        var c = new AssassinsBladeCycle();
        var paid = c.capture(10);
        var corpse = new Object();
        assertTrue(c.killed(10, paid, corpse));
        assertFalse(c.killed(50, paid, corpse));
        assertEquals(60, c.remaining(50)); // duplicate must not refresh
        for (int i = 1; i < AssassinsBladeCycle.MAX_CORPSES_PER_EMISSION; i++)
            assertTrue(c.killed(50, paid, new Object()));
        assertFalse(c.killed(51, paid, new Object()));
        assertFalse(c.killed(51, paid, corpse));
        assertTrue(c.killed(51, c.capture(51), new Object())); // not a source-lifetime cap
    }

    @Test void pureExpiryProbesDoNotConsumeEventsOrAdvanceTimeAndSourcesCannotBorrowAuthority() {
        var c = new AssassinsBladeCycle();
        var other = new AssassinsBladeCycle();
        var paid = c.capture(20);
        var corpse = new Object();
        assertFalse(c.killed(19, paid, corpse));
        assertFalse(c.killed(20, paid, null));
        assertFalse(other.killed(20, paid, corpse));
        assertTrue(c.killed(20, paid, corpse));
        var active = c.capture(21);
        assertEquals(0, c.remaining(Long.MAX_VALUE));
        assertEquals(0, c.remaining(-1));
        assertEquals(1f, other.multiplier(21, active));
        assertTrue(c.multiplier(21, active) > 1f);
        assertEquals(99, c.remaining(21));
        assertTrue(c.killed(22, active, new Object()));
        assertEquals(100, c.remaining(22));
        assertEquals(0, other.remaining(22));
    }

    @Test void editLifecycleAndRollbackInvalidateTokensEvenAfterSameTickRebind() {
        var c = new AssassinsBladeCycle();
        var old = c.capture(30);
        c.killed(30, old, new Object());
        var boosted = c.capture(30);
        c.clear(); // same object edit-away-and-back / old-owner lifecycle revoke
        var next = c.capture(30);
        assertEquals(0, c.remaining(30));
        assertEquals(1f, c.multiplier(30, boosted));
        assertFalse(c.killed(30, old, new Object()));
        assertTrue(c.killed(30, next, new Object()));
        c.update(29);
        assertEquals(0, c.remaining(30));
        assertFalse(c.killed(30, next, new Object()));
        assertNull(c.capture(-1));
    }
}
