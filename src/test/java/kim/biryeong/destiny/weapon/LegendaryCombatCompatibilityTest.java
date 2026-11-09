package kim.biryeong.destiny.weapon;

import java.util.Set;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class LegendaryCombatCompatibilityTest {
    private static WeaponCatalog.Entry entry(WeaponPerks.Roll roll) {
        var entry = WeaponCatalog.find(roll.id()).orElseThrow();
        assertEquals(roll.hash(), WeaponCharacteristics.of(entry).bungieHash());
        return entry;
    }
    @Test void supplementalTimingUsesOwnWeaponAndKeepsFirstInsertTopology() {
        assertFalse(LegendaryPerks.extraRolls(FrenzyProfile.ID).isEmpty());
        for (var roll : LegendaryPerks.extraRolls(FrenzyProfile.ID)) {
            var e = entry(roll); var base = WeaponProfile.forEntry(e);
            assertTrue(FrenzyProfile.supports(e));
            var timing = FrenzyProfile.timing(e);
            assertEquals(e.id(), timing.id());
            assertTrue(timing.reloadTicks() > 0 && timing.reloadTicks() <= base.reloadTicks());
            assertTrue(FrenzyProfile.reloadTicks(e, .9) <= timing.reloadTicks());
            assertTrue(timing.readyTicks() > 0 && timing.stowTicks() > 0 && timing.adsTicks() > 0);
        }
        for (var roll : LegendaryPerks.extraRolls(ElementalCapacitorProfile.ID)) {
            var e = entry(roll); var base = WeaponProfile.forEntry(e);
            assertTrue(ElementalCapacitorProfile.supports(e));
            assertTrue(ElementalCapacitorProfile.reloadTicks(e, 50, 1) < base.reloadTicks());
            assertTrue(ElementalCapacitorProfile.handlingTicks(e, 50, 1, true) <= WeaponHandlingProfile.of(e).readyTicks());
            assertTrue(ElementalCapacitorProfile.adsTicks(e, 50, false) > 0);
        }
        for (var roll : LegendaryPerks.extraRolls(FeedingFrenzyProfile.ID)) {
            var e = entry(roll); int previous = WeaponProfile.forEntry(e).reloadTicks();
            for (int stacks = 1; stacks <= 5; stacks++) {
                var reload = FeedingFrenzyProfile.reload(e, stacks);
                assertTrue(reload.intervalTicks() > 0 && reload.intervalTicks() <= previous);
                previous = reload.intervalTicks();
            }
        }
        assertFalse(LegendaryPerks.extraRolls(OutlawProfile.ID).isEmpty());
        for (var roll : LegendaryPerks.extraRolls(OutlawProfile.ID)) {
            var e = entry(roll); var base = WeaponProfile.forEntry(e); var reload = OutlawProfile.reload(e);
            assertEquals(e.id(), reload.id());
            assertTrue(reload.firstTicks() > 0 && reload.firstTicks() <= base.firstReloadTicks());
            assertTrue(reload.intervalTicks() > 0 && reload.intervalTicks() <= base.reloadTicks());
            assertEquals(WeaponCharacteristics.of(e).stats().get("4188031367"), reload.baseReloadStat());
        }
    }
    @Test void demolitionistUsesFamilyNotSpecialAmmoClassification() {
        var special = Set.of("fusion_rifle", "glaive", "shotgun", "sniper_rifle");
        assertFalse(LegendaryPerks.extraRolls(DemolitionistProfile.ID).isEmpty());
        for (var roll : LegendaryPerks.extraRolls(DemolitionistProfile.ID)) {
            var e = entry(roll);
            assertEquals(special.contains(e.family()) ? 20 : 10, DemolitionistProfile.energyPercent(e));
        }
        assertEquals(10, DemolitionistProfile.energyPercent(WeaponCatalog.find("salvager_s_salvo").orElseThrow()));
    }
    @Test void overflowTargetsAndFiniteReserveTransferSurviveSaveReconstruction() {
        // These pinned new Overflow rolls are Primary; do not fabricate a Special pool.
        for (var roll : LegendaryPerks.extraRolls(OverflowProfile.ID)) {
            var e = entry(roll); var p = WeaponProfile.forEntry(e);
            assertTrue(OverflowProfile.supports(e));
            assertEquals(2 * p.magazine(), OverflowProfile.target(e));
            var ammo = new WeaponMagazine(p, p.magazine(), 0);
            if (p.infiniteReserve()) assertEquals(p.magazine(), ammo.reloadOverflow(OverflowProfile.target(e)));
        }
        // The same AmmoEconomy transaction is reserve-funded for finite weapons.
        var finite = WeaponProfile.forEntry(WeaponCatalog.find("succession").orElseThrow());
        assertFalse(finite.infiniteReserve());
        var ammo = new WeaponMagazine(finite, finite.magazine(), 1);
        long before = ammo.total();
        assertEquals(1, ammo.reloadOverflow(2 * finite.magazine()));
        assertEquals(before, ammo.total()); assertEquals(0, ammo.reserve());
        assertEquals(0, ammo.reloadOverflow(2 * finite.magazine()));
        var saved = new WeaponMagazine(finite, ammo.rounds(), ammo.reserve(), ammo.overflow(), ammo.loadedLimit());
        assertEquals(ammo.rounds(), saved.rounds()); assertEquals(before, saved.total());
    }
    @Test void supplementalAmmoAndBatchMembershipReachTheirRuntimeGates() {
        var raw = com.google.gson.JsonParser.parseReader(new java.io.InputStreamReader(
            getClass().getResourceAsStream("/destiny/weapons/w327-traits.json"), java.nio.charset.StandardCharsets.UTF_8)).getAsJsonObject();
        var traits = new com.google.gson.Gson().fromJson(raw.get("traits"), LegendaryPerks.Trait[].class);
        assertEquals(18, java.util.Arrays.stream(traits).filter(LegendaryPerks.Trait::added).count());
        for (var id : LegendaryWeapons.ids()) for (int socket : new int[]{3, 4})
            assertTrue(java.util.Arrays.stream(traits).anyMatch(t -> LegendaryPerks.extraRolls(t.id()).stream()
                .anyMatch(r -> r.id().equals(id) && r.socket() == socket)), id + " missing socket " + socket);
        for (var r : LegendaryPerks.extraRolls(SubsistenceProfile.ID)) {
            var e=entry(r); assertTrue(SubsistenceProfile.supports(e));
            int percent=Set.of("auto_rifle","submachine_gun").contains(e.family())?17:10;
            assertEquals((13*percent+99)/100, SubsistenceProfile.refillRounds(e,13));
        }
        for (var r : LegendaryPerks.extraRolls(AmbitiousAssassinProfile.ID)) {
            var e=entry(r); assertTrue(AmbitiousAssassinProfile.supports(e));
            assertTrue(AmbitiousAssassinProfile.target(e,1)>WeaponProfile.forEntry(e).magazine());
        }
        for (var r : LegendaryPerks.extraRolls(ClownCartridgeProfile.ID)) {
            var e=entry(r); assertTrue(ClownCartridgeProfile.supports(e));
            assertEquals((WeaponProfile.forEntry(e).magazine()*150+99)/100,ClownCartridgeProfile.maximumTarget(e));
        }
        for (var id : PerkBatchBProfile.IDS)
            assertTrue(PerkBatchBProfile.rolls(id).containsAll(LegendaryPerks.extraRolls(id)));
        for (var id : PerkBatchCProfile.ids()) for (var r : LegendaryPerks.extraRolls(id)) {
            assertTrue(PerkBatchCProfile.rolls(id).contains(r)); assertTrue(PerkBatchCProfile.rolledBy(r.id()));
        }
    }
}
