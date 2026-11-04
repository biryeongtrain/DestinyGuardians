package kim.biryeong.destiny.weapon;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class AdagioCycleW193Test {
    @Test void killingEmissionKeepsItsPreKillScalarAcrossEverySplashContact() {
        var c = new AdagioCycle();
        var killingShot = c.capture(10);
        assertEquals(0, c.remaining(10));
        assertEquals(1f, c.multiplier(10, killingShot));
        assertTrue(c.killed(11, killingShot, new Object(), true));
        assertEquals(140, c.remaining(11));
        // A first corpse cannot boost other contacts from that very same paid grenade.
        assertEquals(1f, c.multiplier(11, killingShot));
        assertTrue(c.killed(12, killingShot, new Object(), true));
        assertEquals(1f, c.multiplier(12, killingShot));
        assertEquals(1.3f, c.multiplier(12, c.capture(12)));
    }

    @Test void delayedPaidDamageSurvivesExpiryAndStowWhileNewShotsAreNeutral() {
        var c = new AdagioCycle();
        assertTrue(c.killed(0, c.capture(0), new Object(), true));
        var delayed = c.capture(139);
        c.update(140, true);
        assertEquals(0, c.remaining(140));
        assertEquals(1.3f, c.multiplier(140, delayed));
        assertEquals(1f, c.multiplier(140, c.capture(140)));
        // Direct and delayed splash use the same frozen value, including after explicit stow.
        c.stowing(141);
        assertEquals(1.3f, c.multiplier(200, delayed));
        assertTrue(c.killed(200, delayed, new Object(), true));
        assertEquals(140, c.remaining(200));
        assertEquals(1.3f, c.multiplier(200, delayed));
    }

    @Test void exactDeadlineAndDistinctKillRefreshDoNotDependOnPollingOrNewInput() {
        var c = new AdagioCycle();
        var paid = c.capture(10);
        assertTrue(c.killed(10, paid, new Object(), true));
        assertEquals(1, c.remaining(149));
        assertEquals(0, c.remaining(150));
        assertTrue(c.killed(150, paid, new Object(), true));
        c.update(289, true);
        assertEquals(1, c.remaining(289));
        c.update(290, true);
        assertEquals(0, c.remaining(290));
        // A long-lived original paid source can earn a later window without being recaptured.
        assertTrue(c.killed(500, paid, new Object(), true));
        assertEquals(140, c.remaining(500));
    }

    @Test void stowAwayBackDropsBuffAndStowedKillCannotBankOrReplayAProc() {
        var c = new AdagioCycle();
        assertTrue(c.killed(10, c.capture(10), new Object(), true));
        var paid = c.capture(11);
        c.stowing(11);
        c.stowing(11);
        c.update(11, true);
        assertEquals(0, c.remaining(11));
        assertEquals(1.3f, c.multiplier(11, paid));
        var corpse = new Object();
        assertTrue(c.killed(12, paid, corpse, false));
        c.update(13, true);
        assertEquals(0, c.remaining(13));
        assertFalse(c.killed(13, paid, corpse, true));
        assertEquals(0, c.remaining(13));
        assertEquals(1f, c.multiplier(13, c.capture(13)));
        assertTrue(c.killed(14, paid, new Object(), true));
        c.update(15, false); // Tick observation is also a stow writer if the explicit hook was missed.
        c.update(16, true);
        assertEquals(0, c.remaining(16));
    }

    @Test void duplicateDirectSplashCorpseDoesNotRefreshAndBoundNeverEvicts() {
        var c = new AdagioCycle();
        var paid = c.capture(10);
        class EqualCorpse {
            @Override public boolean equals(Object o) { return o instanceof EqualCorpse; }
            @Override public int hashCode() { return 1; }
        }
        var first = new EqualCorpse();
        assertTrue(c.killed(10, paid, first, true));
        assertFalse(c.killed(100, paid, first, true));
        assertEquals(50, c.remaining(100));
        for (int i = 1; i < AdagioCycle.MAX_CORPSES_PER_EMISSION; i++)
            assertTrue(c.killed(100, paid, new EqualCorpse(), true));
        assertFalse(c.killed(200, paid, new EqualCorpse(), true));
        assertFalse(c.killed(200, paid, first, true));
        assertEquals(40, c.remaining(200));
        // Separate emissions do not share or accumulate a weapon-lifetime corpse ledger.
        assertTrue(c.killed(200, c.capture(200), new EqualCorpse(), true));
        assertEquals(140, c.remaining(200));
    }

    @Test void arbitraryFutureAndInvalidPureQueriesCannotExpireOrObserveState() {
        var c = new AdagioCycle();
        assertTrue(c.killed(10, c.capture(10), new Object(), true));
        var paid = c.capture(11);
        assertEquals(0, c.remaining(1000));
        assertEquals(0, c.remaining(-1));
        assertEquals(0, c.remaining(10));
        assertEquals(1f, c.multiplier(10, paid));
        assertEquals(1f, c.multiplier(-1, paid));
        assertEquals(1f, c.multiplier(11, null));
        assertEquals(1.3f, c.multiplier(1000, paid));
        assertEquals(1, c.remaining(149));
        assertEquals(1.3f, c.multiplier(149, c.capture(149)));
    }

    @Test void foreignSourcesClearAndClockRollbackPermanentlyRevokeOldTokens() {
        var c = new AdagioCycle();
        assertTrue(c.killed(10, c.capture(10), new Object(), true));
        var old = c.capture(11);
        var foreign = new AdagioCycle();
        assertEquals(1f, foreign.multiplier(11, old));
        assertFalse(foreign.killed(11, old, new Object(), true));
        c.clear();
        assertEquals(0, c.remaining(11));
        assertEquals(1f, c.multiplier(11, old));
        assertFalse(c.killed(12, old, new Object(), true));
        assertTrue(c.killed(12, c.capture(12), new Object(), true));
        var beforeRollback = c.capture(13);
        c.update(12, true);
        assertEquals(0, c.remaining(13));
        assertEquals(1f, c.multiplier(14, beforeRollback));
        assertFalse(c.killed(14, beforeRollback, new Object(), true));
        assertTrue(c.killed(14, c.capture(14), new Object(), true));
    }

    @Test void invalidEventsCannotSpendCorpseCreditAndOverflowFailsClosed() {
        var c = new AdagioCycle();
        assertNull(c.capture(-1));
        assertNull(c.capture(Long.MAX_VALUE));
        var paid = c.capture(20);
        var corpse = new Object();
        assertFalse(c.killed(19, paid, corpse, true));
        assertFalse(c.killed(Long.MAX_VALUE, paid, corpse, true));
        assertFalse(c.killed(20, paid, null, true));
        assertFalse(c.killed(20, null, corpse, true));
        assertTrue(c.killed(20, paid, corpse, true));
        assertEquals(140, c.remaining(20));
        var edge = new AdagioCycle();
        long last = Long.MAX_VALUE - AdagioCycle.DURATION_TICKS;
        assertTrue(edge.killed(last, edge.capture(last), new Object(), true));
        assertEquals(1, edge.remaining(Long.MAX_VALUE - 1));
        assertEquals(0, edge.remaining(Long.MAX_VALUE));
        edge.update(Long.MAX_VALUE, true);
        assertEquals(0, edge.remaining(Long.MAX_VALUE));
    }

    @Test void killsCannotRetimeAcceptedShotAndExpiryCannotShortenItsRecovery() {
        for (String id : new String[]{"aishas_embrace", "canis_major"}) {
            var entry = WeaponCatalog.find(id).orElseThrow();
            var raw = WeaponProfile.forEntry(entry);
            var ammo = new WeaponMagazine(raw, raw.magazine(), raw.reserve());
            var fire = new WeaponCycle();
            var c = new AdagioCycle();
            assertTrue(fire.fire(10, raw, ammo));
            var killingShot = c.capture(10);
            double originalDeadline = fire.firingDeadline();
            assertTrue(c.killed(10, killingShot, new Object(), true));
            var activeProfile = AdagioProfile.firingProfile(entry, raw);
            assertTrue(activeProfile.cadenceTicks() > raw.cadenceTicks());
            assertEquals(raw.damage(), activeProfile.damage());
            assertEquals(originalDeadline, fire.firingDeadline());
            assertFalse(fire.ready((long)Math.floor(originalDeadline) - 1));

            // Capture active cadence just before expiry. Its already accepted recovery persists.
            assertEquals(1, c.remaining(149));
            assertTrue(fire.fire(149, activeProfile, ammo));
            var delayed = c.capture(149);
            double acceptedDeadline = fire.firingDeadline();
            c.update(150, true);
            assertEquals(0, c.remaining(150));
            assertEquals(acceptedDeadline, fire.firingDeadline());
            assertFalse(fire.ready(150));
            c.stowing(151);
            assertEquals(acceptedDeadline, fire.firingDeadline());
            assertEquals(1.3f, c.multiplier(151, delayed));
            assertTrue(fire.ready((long)Math.ceil(acceptedDeadline)));
            assertEquals(raw.magazine() - 2, ammo.rounds());
        }
    }
}
