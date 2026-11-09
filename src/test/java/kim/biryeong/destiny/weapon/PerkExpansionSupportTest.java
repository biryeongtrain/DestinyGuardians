package kim.biryeong.destiny.weapon;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;
import static kim.biryeong.destiny.weapon.WeaponCharacteristics.Damage.*;

class PerkExpansionSupportTest {
    private static WeaponMagazine ammo(int rounds, int reserve) {
        return new WeaponMagazine(new WeaponProfile(WeaponProfile.Mode.HITSCAN, 1, 1, 5, 20,
            20, 20, 0, 1, 1, 0, 0, 0, 0, false, false), rounds, reserve);
    }
    @Test void healClipRequiresRecentKillAndConsumesItsCreditExactlyOnce() {
        var cycle = new PerkExpansionSupportCycle();
        assertFalse(cycle.reload(0));
        cycle.killed(100); assertTrue(cycle.reload(205)); assertFalse(cycle.reload(205));
        cycle.killed(300); assertFalse(cycle.reload(406));
        cycle.killed(500); cycle.killed(520); assertTrue(cycle.reload(625));
    }
    @Test void looseChangeRefreshesPersistsStowedAndExpiresWithoutQueryMutation() {
        var cycle = new PerkExpansionSupportCycle();
        assertFalse(cycle.loose(0)); cycle.debuffed(10); cycle.stow();
        assertTrue(cycle.loose(189)); assertFalse(cycle.loose(190));
        cycle.debuffed(100); assertTrue(cycle.loose(279)); assertFalse(cycle.loose(280));
    }
    @Test void headstoneBudgetCountsSuccessfulSpawnsAndResetsAfterCooldown() {
        var cycle = new PerkExpansionSupportCycle();
        for (int i=0;i<5;i++) { assertTrue(cycle.canCrystal(i)); cycle.crystalSpawned(i); }
        assertFalse(cycle.canCrystal(103)); assertTrue(cycle.canCrystal(104));
        cycle.crystalSpawned(104); assertTrue(cycle.canCrystal(105));
        var sparse = new PerkExpansionSupportCycle();
        for (int i=0;i<20;i++) { assertTrue(sparse.canCrystal(i*100)); sparse.crystalSpawned(i*100); }
    }
    @Test void permeabilityUsesFiniteReservesAndSuccessfulClassUseOncePerStowEpisode() {
        var cycle = new PerkExpansionSupportCycle(); var ammo = ammo(0, 4);
        var token = cycle.accepted(VOID);
        assertEquals(KINETIC, cycle.damage(KINETIC)); assertEquals(0, ammo.rounds());
        assertEquals(3, cycle.classUsed(token, ammo, 5));
        assertEquals(4, ammo.total()); assertEquals(1, ammo.reserve()); assertEquals(VOID, cycle.damage(KINETIC));
        assertEquals(0, cycle.classUsed(token, ammo, 5));
        ammo.consume(3); assertEquals(0, cycle.classUsed(cycle.accepted(ARC), ammo, 5));
        assertEquals(ARC, cycle.damage(KINETIC));
        cycle.stow(); assertEquals(KINETIC, cycle.damage(KINETIC));
        assertEquals(1, cycle.classUsed(cycle.accepted(SOLAR), ammo, 5)); assertEquals(0, ammo.reserve());
    }
    @Test void failedFullAndStaleClassTokensCannotBankOrReplayRefills() {
        var cycle = new PerkExpansionSupportCycle(); var ammo = ammo(5, 10);
        var stale = cycle.accepted(VOID); cycle.stow();
        assertEquals(0, cycle.classUsed(stale, ammo, 5)); assertEquals(KINETIC, cycle.damage(KINETIC));
        assertEquals(0, cycle.classUsed(cycle.accepted(ARC), ammo, 5)); ammo.consume(5);
        assertEquals(0, cycle.classUsed(cycle.accepted(ARC), ammo, 5));
        var foreign = new PerkExpansionSupportCycle();
        assertEquals(0, foreign.classUsed(cycle.accepted(VOID), ammo, 5));
    }
    @Test void emissionLedgerDeduplicatesOneCorpseButAllowsDifferentVictims() {
        var ledger = new WeaponEnergyCredit.Corpses<Object>(); Object a = new Object(), b = new Object();
        assertTrue(ledger.admit(a)); assertFalse(ledger.admit(a)); assertTrue(ledger.admit(b)); assertFalse(ledger.admit(null));
    }
}
