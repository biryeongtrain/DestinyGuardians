package kim.biryeong.destiny.weapon;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class SympatheticArsenalCycleW194Test {
    @Test void killWindowIsMeasuredAtPositiveCreditInclusive72NotReloadAcceptance() {
        for (int boundary : new int[]{72, 73}) {
            var c = new SympatheticArsenalCycle();
            c.killed(0, c.capture(0), new Object(), true);
            var reload = c.acceptedReload(1);
            assertEquals(boundary == 72, c.reloaded(boundary, reload, 1));
            assertFalse(c.reloaded(boundary, reload, 1));
        }
    }

    @Test void killDuringAlreadyAcceptedReloadCanQualifyAndLatestDistinctKillRefreshes() {
        var c = new SympatheticArsenalCycle();
        var paid = c.capture(0);
        var reload = c.acceptedReload(5); // deliberately no kill yet
        assertTrue(c.killed(10, paid, new Object(), true));
        assertTrue(c.killed(80, paid, new Object(), true));
        assertTrue(c.reloaded(90, reload, 2));
        assertFalse(c.eligible(90));
        assertFalse(c.reloaded(91, c.acceptedReload(91), 1));
    }

    @Test void zeroCreditDoesNotTriggerButFirstPositiveDecisionRetiresAuthorityEvenWithoutKill() {
        var c = new SympatheticArsenalCycle();
        var reload = c.acceptedReload(0);
        assertFalse(c.reloaded(1, reload, 0));
        c.killed(2, c.capture(2), new Object(), true);
        assertFalse(c.reloaded(3, reload, -1));
        assertTrue(c.reloaded(3, reload, 1));
        assertFalse(c.reloaded(3, reload, 1));
        var noKill = c.acceptedReload(4);
        assertFalse(c.reloaded(4, noKill, 1));
        c.killed(5, c.capture(5), new Object(), true);
        assertFalse(c.reloaded(5, noKill, 1));
        assertTrue(c.reloaded(6, c.acceptedReload(6), 1));
    }

    @Test void cancellationReplacementStowAndLifecycleRevokeReloadAuthority() {
        var c = new SympatheticArsenalCycle();
        c.killed(0, c.capture(0), new Object(), true);
        var cancelled = c.acceptedReload(0);
        c.reloadCancelled();
        assertFalse(c.reloaded(1, cancelled, 1));
        var old = c.acceptedReload(1);
        var replacement = c.acceptedReload(1);
        assertFalse(c.reloaded(2, old, 1));
        assertTrue(c.reloaded(2, replacement, 1));
        var paid = c.capture(3);
        c.killed(3, paid, new Object(), true);
        var stowed = c.acceptedReload(3);
        c.stowing(3); c.update(4, true);
        assertFalse(c.reloaded(4, stowed, 1));
        assertTrue(c.killed(4, paid, new Object(), true));
        assertFalse(c.eligible(4)); // no banking delayed pre-stow emissions
        var cleared = c.acceptedReload(4);
        c.clear();
        assertFalse(c.reloaded(5, cleared, 1));
        assertFalse(c.killed(5, paid, new Object(), true));
    }

    @Test void directSplashDedupCannotRefreshAndBoundNeverEvicts() {
        var c = new SympatheticArsenalCycle();
        var paid = c.capture(0);
        var first = new Object();
        assertTrue(c.killed(0, paid, first, true));
        assertFalse(c.killed(60, paid, first, true));
        assertFalse(c.eligible(73));
        for (int i = 1; i < SympatheticArsenalCycle.MAX_CORPSES_PER_EMISSION; i++)
            assertTrue(c.killed(73, paid, new Object(), true));
        assertFalse(c.killed(100, paid, new Object(), true));
        assertFalse(c.killed(100, paid, first, true));
        assertFalse(c.eligible(146));
        assertTrue(c.killed(146, c.capture(146), new Object(), true));
    }

    @Test void foreignAuthorityPureProbesAndRollbackCannotInventAWindow() {
        var c = new SympatheticArsenalCycle();
        var foreign = new SympatheticArsenalCycle();
        var paid = c.capture(10);
        var reload = c.acceptedReload(10);
        assertFalse(foreign.killed(10, paid, new Object(), true));
        assertFalse(foreign.reloaded(10, reload, 1));
        assertFalse(c.killed(9, paid, new Object(), true));
        assertTrue(c.killed(10, paid, new Object(), true));
        assertFalse(c.eligible(1000));
        assertTrue(c.eligible(10)); // query did not observe time
        c.update(9, true);
        assertFalse(c.killed(11, paid, new Object(), true));
        assertFalse(c.reloaded(11, reload, 1));
        assertNull(c.capture(-1));
        assertNull(c.acceptedReload(-1));
    }

    @Test void actualFiniteMagazineCreditTriggersBeforeRecoveryWithoutMovingStowedAmmoHere() {
        var entry = WeaponCatalog.find("hollow_words").orElseThrow();
        var profile = WeaponProfile.forEntry(entry);
        var ammo = new WeaponMagazine(profile, 0, 2);
        var cycle = new WeaponCycle();
        var plan = new WeaponReloadPolicy.Plan(100, 100, 0);
        var sa = new SympatheticArsenalCycle();
        sa.killed(0, sa.capture(0), new Object(), true);
        assertTrue(cycle.startReload(1, profile, ammo, plan, 71));
        var reload = sa.acceptedReload(1);
        assertFalse(cycle.finishReload(71, ammo));
        assertFalse(sa.reloaded(71, reload, 0));
        int before = ammo.rounds();
        long total = ammo.total();
        assertTrue(cycle.finishReload(72, ammo));
        assertTrue(cycle.reloading());
        assertTrue(sa.reloaded(72, reload, ammo.rounds() - before));
        assertEquals(total, ammo.total());
        assertEquals(0, ammo.reserve());
        assertFalse(cycle.finishReload(101, ammo));
        assertFalse(sa.reloaded(101, reload, 1));
        assertFalse(cycle.reloading());
    }
}
