package kim.biryeong.destiny.weapon;

import org.junit.jupiter.api.Test;
import java.util.*;
import static org.junit.jupiter.api.Assertions.*;

/** W321 batch B: exact pinned pools, registration, and the new trigger/expiry/ammo/payload rules. */
class PerkBatchBW321Test {
    private static WeaponPerks.Roll r(String id, long hash, long perk, long plugSet) {
        return new WeaponPerks.Roll(id, hash, id.equals("bite_of_the_fox") && perk == 968510818L
            || id.equals("dimensional_hypotrochoid") && (perk == 968510818L || perk == 3987942396L) ? 3 : 4, perk, plugSet);
    }
    private static final Map<String, Set<WeaponPerks.Roll>> EXPECTED = Map.ofEntries(
        Map.entry("target_lock", Set.of(r("retrofit_escapade", 3103325054L, 365154968L, 2461260598L))),
        Map.entry("envious_assassin", Set.of(r("bite_of_the_fox", 1403800851L, 968510818L, 563442205L),
            r("dimensional_hypotrochoid", 1311684613L, 968510818L, 3235863202L))),
        Map.entry("envious_arsenal", Set.of(r("dimensional_hypotrochoid", 1311684613L, 3987942396L, 3235863202L))),
        Map.entry("harmony", Set.of(r("retraced_path", 548958835L, 438098033L, 398391969L),
            r("goldtusk", 3371413057L, 438098033L, 700250835L))),
        Map.entry("under_over", Set.of(r("allied_demand", 1532276803L, 1870851715L, 703779397L),
            r("bite_of_the_fox", 1403800851L, 1870851715L, 2442672691L))),
        Map.entry("golden_tricorn", Set.of(r("retraced_path", 548958835L, 2610012052L, 398391969L),
            r("retrofit_escapade", 3103325054L, 2610012052L, 2461260598L))),
        Map.entry("lasting_impression", Set.of(r("code_duello", 2496242052L, 3927722942L, 147528717L))),
        Map.entry("timed_payload", Set.of(r("seventh_seraph_officer_revolver", 3037520408L, 1954620775L, 3527094473L))),
        Map.entry("reservoir_burst", Set.of(r("null_composure", 1644680957L, 1427256713L, 273L))),
        Map.entry("explosive_head", Set.of(r("biting_winds", 1621657423L, 3365897133L, 2763203653L))),
        Map.entry("cluster_bomb", Set.of(r("bad_omens", 991314988L, 1275731761L, 2955928741L),
            r("bellowing_giant", 2186258845L, 1275731761L, 1722393382L),
            r("code_duello", 2496242052L, 1275731761L, 147528717L),
            r("pyroclastic_flow", 1289324202L, 1275731761L, 3838086002L))),
        Map.entry("chain_reaction", Set.of(r("salvager_s_salvo", 2060863616L, 2396489472L, 254L),
            r("canis_major", 2066434718L, 2396489472L, 2791121719L),
            r("dimensional_hypotrochoid", 1311684613L, 2396489472L, 1092097342L),
            r("code_duello", 2496242052L, 2396489472L, 147528717L),
            r("goldtusk", 3371413057L, 2396489472L, 700250835L))));

    @Test void exactPinnedPoolsAreRegistered() {
        assertEquals(EXPECTED.keySet(), new HashSet<>(PerkBatchBProfile.IDS));
        for (var id : PerkBatchBProfile.IDS) {
            var all = PerkBatchBProfile.rolls(id);
            assertEquals(EXPECTED.get(id), new HashSet<>(all.stream()
                .filter(r -> !LegendaryWeapons.contains(r.id())).toList()), id);
            var added = all.stream().filter(r -> LegendaryWeapons.contains(r.id())).toList();
            assertEquals(new HashSet<>(LegendaryPerks.extraRolls(id)), new HashSet<>(added), id);
            for (var roll : added) assertTrue(LegendaryWeapons.exactRoll(roll), roll.toString());
            assertEquals(all.size(), new HashSet<>(all).size(), id);
            assertTrue(WeaponPerks.ids().contains(id), id);
            assertTrue(PerkBatchBProfile.perk(id).source().row() > 0, id);
            assertFalse(PerkBatchBProfile.koName(id).isBlank());
            assertEquals(PerkBatchBProfile.koName(id), WeaponPerks.name(id));
        }
        assertEquals(new HashSet<>(WeaponPerks.ids()).size(), WeaponPerks.ids().size());
    }

    @Test void targetLockRampsByMagazineFractionAndResetsOnGap() {
        // DDC: nothing at or below 12.5% of magazine, 16.7% at the threshold, 40% at 110.33%.
        assertEquals(1f, PerkBatchBMath.targetLockMultiplier(12, 100, .125, 1.1033, .167, .40));
        assertEquals(1.167f, PerkBatchBMath.targetLockMultiplier(13, 100, .125, 1.1033, .167, .40), .01f);
        assertEquals(1.40f, PerkBatchBMath.targetLockMultiplier(200, 100, .125, 1.1033, .167, .40), 1e-5f);
        assertEquals(1.25f, PerkBatchBMath.targetLockMultiplier(200, 100, .125, 1.1033, .1046, .25), 1e-5f);
        var lock = new PerkBatchBMath.TargetLock();
        lock.hit(0, 4); lock.hit(4, 4); lock.hit(8, 4);
        assertEquals(3, lock.hits(12, 4));
        assertEquals(0, lock.hits(13, 4), "a miss longer than 0.2s resets");
        lock.hit(20, 4);
        assertEquals(1, lock.hits(20, 4));
        lock.reset();
        assertEquals(0, lock.hits(20, 4));
    }

    @Test void enviousAssassinOverflowsFromKillsWithCaps() {
        // 3 kills x 20% of a 6-round magazine -> +ceil(3.6)=4 rounds.
        assertEquals(4, PerkBatchBMath.enviousTarget(0, 6, 3, .2, 1, 3));
        // Each activation adds at most 100% of the magazine: full mag doubles.
        assertEquals(12, PerkBatchBMath.enviousTarget(6, 6, 50, .2, 1, 3));
        // Total capped at +200% (3x magazine); never removes rounds.
        assertEquals(18, PerkBatchBMath.enviousTarget(15, 6, 50, .2, 1, 3));
        assertEquals(20, PerkBatchBMath.enviousTarget(20, 6, 5, .2, 1, 3));
        assertEquals(5, PerkBatchBMath.enviousTarget(5, 6, 0, .2, 1, 3));
        assertEquals(1, PerkBatchBMath.enviousTarget(0, 10, 1, .1, 1, 3));
    }

    @Test void enviousArsenalNeedsBothOtherWeapons() {
        assertFalse(PerkBatchBMath.arsenalReady(1, 2));
        assertTrue(PerkBatchBMath.arsenalReady(2, 2));
    }

    @Test void payloadSplitMovesBodyEquivalentPortion() {
        assertEquals(55f, PerkBatchBMath.payloadMoved(100f, false, 1.5, .55), 1e-4f);
        // Precision: body equivalent 100 at x1.5 -> moved 55, impact keeps (1.5-0.55) body units = 95.
        assertEquals(55f, PerkBatchBMath.payloadMoved(150f, true, 1.5, .55), 1e-4f);
        assertEquals(0f, PerkBatchBMath.payloadMoved(100f, false, 1.5, 0));
        assertEquals(4, PerkBatchBMath.explosiveHeadDelay(0, .25, 4, 16));
        assertEquals(9, PerkBatchBMath.explosiveHeadDelay(20, .25, 4, 16));
        assertEquals(16, PerkBatchBMath.explosiveHeadDelay(400, .25, 4, 16));
    }

    @Test void radialFalloffMatchesDdcRadii() {
        assertEquals(1f, PerkBatchBMath.falloff(3, 3, 7, 0));
        assertEquals(.5f, PerkBatchBMath.falloff(5, 3, 7, 0), 1e-5f);
        assertEquals(0f, PerkBatchBMath.falloff(7.01, 3, 7, 0));
        assertEquals(.3f, PerkBatchBMath.falloff(1.5, 0, 1.5, .3), 1e-5f);
    }

    @Test void goldenTricornPromotesOnlyWhileActiveAndExpires() {
        var t = new PerkBatchBMath.Tricorn();
        assertFalse(t.abilityKill(0, 200), "ability kill without the weapon buff does nothing");
        t.weaponKill(0, 140);
        assertEquals(1.15f, t.multiplier(10, 1.15, 1.5));
        t.weaponKill(100, 140);
        assertEquals(1, t.level(239));
        assertEquals(0, t.level(240));
        t.weaponKill(300, 140);
        assertTrue(t.abilityKill(310, 200));
        assertEquals(1.5f, t.multiplier(400, 1.15, 1.5));
        t.weaponKill(450, 140);
        assertEquals(2, t.level(509), "a weapon kill does not demote x2");
        assertEquals(0, t.level(510));
        t.weaponKill(600, 140); t.clear();
        assertEquals(1f, t.multiplier(601, 1.15, 1.5), "stow clears");
    }

    @Test void harmonyWindowIsThreeSeconds() {
        assertTrue(PerkBatchBMath.harmonyActivates(160, 100, 60));
        assertFalse(PerkBatchBMath.harmonyActivates(161, 100, 60));
        assertFalse(PerkBatchBMath.harmonyActivates(100, Long.MIN_VALUE / 4, 60));
    }
}
