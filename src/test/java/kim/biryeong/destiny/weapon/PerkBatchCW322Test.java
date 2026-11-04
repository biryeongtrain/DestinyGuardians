package kim.biryeong.destiny.weapon;

import kim.biryeong.destiny.combat.CombatantShields;
import kim.biryeong.destiny.combat.DamageVulnerability;
import kim.biryeong.destiny.combat.FrostArmor;
import kim.biryeong.destiny.combat.StasisCrystals;
import net.minecraft.world.phys.Vec3;
import org.junit.jupiter.api.Test;
import java.util.HashSet;
import static org.junit.jupiter.api.Assertions.*;

/** W322 batch C trigger/expiry/stack behaviour and registry coverage. No numeric mirror tests. */
class PerkBatchCW322Test {
    @Test void everyOfficialRollIsRegisteredAndSelectableThroughTheCentralPool() {
        var ids = new HashSet<>(WeaponPerks.ids());
        for (var id : PerkBatchCProfile.ids()) {
            assertTrue(ids.contains(id), id);
            assertFalse(PerkBatchCProfile.rolls(id).isEmpty(), id);
            assertNotEquals(id, PerkBatchCProfile.name(id), "Korean label " + id);
            for (var r : PerkBatchCProfile.rolls(id)) {
                assertEquals(PerkBatchCProfile.hash(id), r.perkHash());
                assertTrue(PerkBatchCProfile.rolledBy(r.id()));
            }
        }
        assertEquals(WeaponPerks.ids().size(), new HashSet<>(WeaponPerks.ids()).size(), "no duplicate ids");
    }
    @Test void pulseMonitorAliasKeepsLegacySelectionsAndAddsNewHash() {
        var rolls = PulseMonitorProfile.rolls();
        assertTrue(rolls.stream().anyMatch(r -> r.perkHash() == PulseMonitorProfile.HASH && r.id().equals("seventh_seraph_officer_revolver")));
        assertTrue(rolls.stream().anyMatch(r -> r.perkHash() == PerkBatchCProfile.PULSE_MONITOR_ALIAS_HASH && r.id().equals("patron_of_lost_causes")));
        // Legacy tuples are ordered first: an old saved 972757866 selection matches before the alias.
        assertEquals(PulseMonitorProfile.HASH, rolls.getFirst().perkHash());
        var patron = WeaponCatalog.find("patron_of_lost_causes").orElseThrow();
        assertTrue(PulseMonitorProfile.supports(patron));
        assertFalse(PulseMonitorProfile.hasCurve(patron), "alias-only weapon has no pinned W200 curve");
    }
    @Test void adaptiveStacksOnlyOnNonMatchingShieldsAndResets() {
        var a = new BatchCRules.Adaptive();
        assertEquals(1, a.multiplier(true, .1, .5));
        a.hit(true, false); a.hit(true, false);
        assertEquals(1.2, a.multiplier(true, .1, .5), 1e-9);
        assertEquals(1, a.multiplier(false, .1, .5), "bonus is shield-only");
        for (int i = 0; i < 20; i++) a.hit(true, false);
        assertEquals(1.5, a.multiplier(true, .1, .5), 1e-9, "cap");
        a.hit(true, true); assertEquals(0, a.hits(), "matching shield clears");
        a.hit(true, false); a.hit(false, false); assertEquals(0, a.hits(), "unshielded hit clears");
    }
    @Test void redirectionBanksCapsAndConsumesBeforeDamage() {
        var r = new BatchCRules.Redirection();
        for (int i = 0; i < 20; i++) r.gain(2, 30);
        assertEquals(30, r.stacks());
        assertEquals(3, r.consume(3)); assertEquals(27, r.stacks());
        assertEquals(2.0, BatchCRules.Redirection.multiplier(3, 3, .33, 1), 1e-9, "full consume = 100%");
        assertEquals(1.33, BatchCRules.Redirection.multiplier(1, 3, .33, 1), 1e-9);
        assertEquals(1, BatchCRules.Redirection.multiplier(0, 3, .33, 1));
        var empty = new BatchCRules.Redirection(); assertEquals(0, empty.consume(3));
    }
    @Test void oneTwoPunchNeedsAllPelletsWindowAndIsConsumedOnce() {
        assertTrue(BatchCRules.OneTwoPunch.qualifies(12, 12, 12));
        assertFalse(BatchCRules.OneTwoPunch.qualifies(11, 12, 12));
        assertTrue(BatchCRules.OneTwoPunch.qualifies(8, 8, 12), "low-pellet frames need every pellet");
        assertFalse(BatchCRules.OneTwoPunch.qualifies(0, 0, 12));
        var p = new BatchCRules.OneTwoPunch();
        p.grant(100, 60);
        assertTrue(p.active(159)); assertFalse(p.active(160));
        assertTrue(p.consume(120)); assertFalse(p.consume(121), "single melee hit");
        p.grant(200, 60); assertFalse(p.consume(260), "expired");
        p.grant(300, 60); p.clear(); assertFalse(p.active(301), "stow clears");
    }
    @Test void corpsebloomFirstKillArmsAndRapidKillsReleaseSeekers() {
        var c = new BatchCRules.Corpsebloom();
        assertFalse(c.kill(100, 80));
        assertTrue(c.kill(150, 80));
        assertTrue(c.kill(229, 80), "each rapid kill refreshes the window");
        assertFalse(c.kill(400, 80), "a slow kill only re-arms");
    }
    @Test void energyTransferUsesDestinyPointsAndBlockedRates() {
        var r = PerkBatchCProfile.energyTransfer();
        // 20 HP guardian: 1 MC HP unblocked = 11.5 points * 0.5%.
        assertEquals(5.75, BatchCRules.energyTransferPercent(1, false, false, 20, r), 1e-9);
        // Blocked loss is 5% of the incoming hit, so 0.05 loss == 1 MC HP blocked.
        assertEquals(17.25, BatchCRules.energyTransferPercent(.05f, true, true, 20, r), 1e-4);
        assertEquals(11.5, BatchCRules.energyTransferPercent(.05f, true, false, 20, r), 1e-4);
        assertEquals(100, BatchCRules.energyTransferPercent(100, false, false, 20, r));
        assertEquals(0, BatchCRules.energyTransferPercent(0, true, false, 20, r));
        assertEquals(0, BatchCRules.energyTransferPercent(Float.NaN, true, false, 20, r));
        assertEquals(90, BatchCRules.cooldownAfter(200, 100, 5));
        assertEquals(0, BatchCRules.cooldownAfter(200, 5, 50));
        assertEquals(0, BatchCRules.cooldownAfter(200, 0, 50), "charged slot untouched");
    }
    @Test void vulnerabilityStacksMultiplyWithIndependentExpiry() {
        var s = new DamageVulnerability.Stacks();
        s.add(0, 110, 1.5); s.add(50, 110, 1.5);
        assertEquals(2.25, s.multiplier(60), 1e-9);
        assertEquals(1.5, s.multiplier(110), 1e-9, "first stack expires on its own");
        assertEquals(1, s.multiplier(160));
        var bad = new DamageVulnerability.Stacks(); bad.add(0, 0, 1.5); bad.add(0, 10, Double.NaN); assertEquals(0, bad.active(0));
    }
    @Test void frostArmorStacksCapRefreshAndExpire() {
        var a = new FrostArmor.Stacks();
        a.grant(0, 1, 5, 200); a.grant(10, 1, 5, 200);
        assertEquals(2, a.stacks(100));
        assertEquals(9f, a.resist(100, 10, .05), 1e-5);
        for (int i = 0; i < 10; i++) a.grant(20, 1, 5, 200);
        assertEquals(5, a.stacks(21));
        assertFalse(a.active(220)); assertEquals(10f, a.resist(220, 10, .05));
        a.grant(300, 1, 5, 200); assertEquals(1, a.stacks(301), "expired stacks do not return");
    }
    @Test void shieldMatchingTreatsBarrierAsElementless() {
        assertTrue(CombatantShields.matches(CombatantShields.Type.ARC, WeaponCharacteristics.Damage.ARC));
        assertFalse(CombatantShields.matches(CombatantShields.Type.ARC, WeaponCharacteristics.Damage.SOLAR));
        for (var d : WeaponCharacteristics.Damage.values())
            assertFalse(CombatantShields.matches(CombatantShields.Type.BARRIER, d));
        assertFalse(CombatantShields.Snapshot.NONE.shielded());
    }
    @Test void crystalRayGeometry() {
        assertEquals(1, StasisCrystals.segmentDistance(Vec3.ZERO, new Vec3(10, 0, 0), new Vec3(5, 1, 0)), 1e-9);
        assertEquals(5, StasisCrystals.segmentDistance(Vec3.ZERO, new Vec3(10, 0, 0), new Vec3(15, 0, 0)), 1e-9);
        assertEquals(2, StasisCrystals.segmentDistance(Vec3.ZERO, Vec3.ZERO, new Vec3(0, 2, 0)), 1e-9);
    }
}
