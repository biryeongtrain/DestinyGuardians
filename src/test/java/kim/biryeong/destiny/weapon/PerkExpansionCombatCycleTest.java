package kim.biryeong.destiny.weapon;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class PerkExpansionCombatCycleTest {
    private static PerkExpansionCombatCycle.Emission hit(PerkExpansionCombatCycle c, long t) {
        var s = c.paid(t, true, true, true);
        assertTrue(c.hit(s, t, false, false, false));
        return s;
    }
    private static WeaponProfile profile(int capacity, int reserve, boolean infinite, boolean shells) {
        return new WeaponProfile(WeaponProfile.Mode.HITSCAN, 1, 1, capacity, reserve, 8, 20, 0, 1, 1, 0,
                0, 0, 0, false, infinite, 1, 0, false, shells, 10, shells ? 1 : 0);
    }

    @Test void finalProjectileMustResolveAndDuplicatePelletsNeverInflateRewind() {
        var c = new PerkExpansionCombatCycle(0);
        for (int i = 0; i < 2; i++) { var s = hit(c, i); assertTrue(c.resolved(s, i)); }
        var last = c.paid(2, true, true, true);
        assertTrue(c.awaitingRewind(10));
        assertEquals(0, c.rewind(3, 10, 0, false));
        assertTrue(c.hit(last, 4, false, false, false));
        assertFalse(c.hit(last, 4, false, false, false));
        assertTrue(c.resolved(last, 4));
        assertFalse(c.resolved(last, 4));
        assertEquals(2, c.rewind(4, 10, 0, false));
        assertEquals(0, c.rewind(4, 10, 0, false));
        assertFalse(c.hit(last, 5, false, false, false));
    }

    @Test void insufficientShotsOrNonemptyMagazineCannotTrigger() {
        var c = new PerkExpansionCombatCycle(0);
        var s = hit(c, 0); c.resolved(s, 0);
        assertEquals(0, c.rewind(1, 10, 0, false));
        for (int i = 1; i < 3; i++) { s = hit(c, i); c.resolved(s, i); }
        assertEquals(0, c.rewind(3, 10, 1, false));
        assertEquals(2, c.rewind(3, 10, 0, false));
    }

    @Test void reloadRetiresInFlightOldMagazineButOtherWeaponsStayIndependent() {
        var a = new PerkExpansionCombatCycle(0); var b = new PerkExpansionCombatCycle(0);
        var old = a.paid(0, true, true, true); var other = b.paid(0, true, true, true);
        a.resetMagazine();
        assertTrue(a.hit(old, 1, false, false, false));
        assertTrue(a.resolved(old, 1));
        assertEquals(1, a.precisionStacks(1));
        assertTrue(b.hit(other, 1, false, false, false));
        b.resolved(other, 1);
        assertEquals(1, b.rewind(1, 1, 0, false));
        assertEquals(0, a.rewind(1, 1, 0, false));
    }

    @Test void rewindExclusionAndExpiredTerminalReceiptsAreBounded() {
        var c = new PerkExpansionCombatCycle(0);
        var s = hit(c, 0); c.resolved(s, 0); assertEquals(1, c.rewind(0, 1, 0, false));
        s = hit(c, 19); c.resolved(s, 19); assertEquals(0, c.rewind(19, 1, 0, false));
        s = hit(c, 20); c.resolved(s, 20); assertEquals(1, c.rewind(20, 1, 0, false));
        var lost = c.paid(40, true, true, true);
        c.expire(641);
        assertFalse(c.awaitingRewind(1));
        assertFalse(c.hit(lost, 641, false, false, false));
        assertFalse(c.resolved(lost, 641));
    }

    @Test void precisionStacksAffectNextShotExpireAndActualMissResets() {
        var c = new PerkExpansionCombatCycle(0);
        assertEquals(1, c.precisionMultiplier(0));
        var s = hit(c, 0); c.resolved(s, 0);
        assertEquals(1.0417, c.precisionMultiplier(1), 1e-6);
        assertEquals(1, c.precisionMultiplier(22));
        s = hit(c, 30); c.resolved(s, 30);
        var miss = c.paid(31, true, true, true); c.resolved(miss, 31);
        assertEquals(1, c.precisionMultiplier(31));
    }

    @Test void burstPoliciesCountTwoAdaptiveBoltsOrOneHeavyBurst() {
        var c = new PerkExpansionCombatCycle(0);
        var a = c.paid(0, true, true, true); c.hit(a, 0, true, false, true); c.resolved(a, 0);
        assertEquals(0, c.precisionStacks(0));
        var b = c.paid(1, false, false, true); c.hit(b, 1, true, false, true); c.resolved(b, 1);
        assertEquals(1, c.precisionStacks(1));
        assertEquals(1, c.precisionStacks(42));
        assertEquals(0, c.precisionStacks(43));
        var h = new PerkExpansionCombatCycle(0);
        a = h.paid(0, true, true, true); h.hit(a, 0, false, true, false); h.resolved(a, 0);
        b = h.paid(1, false, false, true); h.hit(b, 1, false, true, false); h.resolved(b, 1);
        assertEquals(1, h.precisionStacks(1));
    }

    @Test void reconstructionRespectsIdleDeadlineNoCatchupAndFiniteFunding() {
        var c = new PerkExpansionCombatCycle(0);
        assertEquals(0, c.reconstruction(119, 8, 0, false));
        assertEquals(0, c.reconstruction(120, 8, 0, true));
        assertEquals(2, c.reconstruction(121, 8, 0, false));
        assertEquals(0, c.reconstruction(121, 8, 2, false));
        c.paid(200, true, true, false);
        assertEquals(0, c.reconstruction(319, 8, 2, false));
        assertEquals(4, c.reconstruction(1000, 8, 2, false));
        assertEquals(0, c.reconstruction(1000, 8, 4, false));
        var ammo = new WeaponMagazine(profile(8, 30, false, false), 7, 3);
        long total = ammo.total();
        assertEquals(2, PerkExpansionCombatCycle.fund(ammo, 8, 9));
        assertEquals(9, ammo.rounds()); assertEquals(total, ammo.total());
        assertEquals(1, PerkExpansionCombatCycle.fund(ammo, 8, 11));
        assertEquals(10, ammo.rounds()); assertEquals(total, ammo.total());
        assertEquals(0, PerkExpansionCombatCycle.fund(ammo, 8, 16));
        assertEquals(16, PerkExpansionCombatCycle.reconstructionTarget(8, 15));
        assertEquals(20, PerkExpansionCombatCycle.reconstructionTarget(8, 20));
    }

    @Test void reserveFundedRewindCannotCreateSpecialAmmoAndPrimaryStillHasBoundedMagazine() {
        var finite = new WeaponMagazine(profile(10, 30, false, false), 0, 1);
        assertEquals(1, finite.reloadRounds(6)); assertEquals(1, finite.total());
        assertEquals(0, finite.reloadRounds(6));
        var primary = new WeaponMagazine(profile(10, 0, true, false), 0, 0);
        assertEquals(6, primary.reloadRounds(6)); assertEquals(4, primary.reloadRounds(6));
        assertEquals(10, primary.rounds());
    }

    @Test void warmUpExtendsCapsAndStowClearsOnlyItsOwnWindow() {
        var c = new PerkExpansionCombatCycle(0);
        c.weaponKill(0, true, true);
        assertEquals(13, c.chargeTicks(0, 20));
        c.weaponKill(10, true, true); assertEquals(190, c.warmRemaining(10));
        for (int i = 0; i < 9; i++) c.weaponKill(10, true, false);
        assertEquals(400, c.warmRemaining(10));
        c.stow(); assertEquals(20, c.chargeTicks(10, 20));
        assertEquals(1, c.desperateStacks(10));
    }

    @Test void desperateAbilityStacksDoNotDowngradeOnWeaponKillAndExpireExactly() {
        var c = new PerkExpansionCombatCycle(0);
        c.weaponKill(0, false, true); assertEquals(1.1, c.damageMultiplier(0), 1e-6);
        c.abilityKill(10); assertEquals(2, c.desperateStacks(10));
        c.abilityKill(20); assertEquals(3, c.desperateStacks(20));
        c.weaponKill(30, false, true); assertEquals(3, c.desperateStacks(30));
        assertEquals(3, c.desperateStacks(169)); assertEquals(0, c.desperateStacks(170));
        c.abilityKill(171); assertEquals(2, c.desperateStacks(171));
    }

    @Test void dualLoaderUsesAtomicExistingInsertAndCancelCannotTransferLaterShells() {
        var original = new WeaponReloadPolicy.Plan(10, 8, 1);
        var plan = PerkExpansionCombat.dualLoader(original);
        assertEquals(10, plan.firstTicks()); assertEquals(8, plan.intervalTicks());
        var p = PerkExpansionCombat.reloadProfile(profile(5, 10, false, true), plan);
        var ammo = new WeaponMagazine(p, 0, 3); var cycle = new WeaponCycle();
        assertTrue(cycle.startReload(0, p, ammo, plan));
        assertFalse(cycle.finishReload(9, ammo));
        assertTrue(cycle.finishReload(10, ammo)); assertEquals(2, ammo.rounds()); assertEquals(1, ammo.reserve());
        cycle.cancelPending(); assertFalse(cycle.finishReload(18, ammo));
        assertEquals(2, ammo.rounds());
        assertTrue(cycle.startReload(20, p, ammo, plan));
        assertTrue(cycle.finishReload(30, ammo)); assertEquals(3, ammo.rounds()); assertEquals(0, ammo.reserve());
        var whole = new WeaponReloadPolicy.Plan(20, 20, 0);
        assertSame(whole, PerkExpansionCombat.dualLoader(whole));
    }
}
