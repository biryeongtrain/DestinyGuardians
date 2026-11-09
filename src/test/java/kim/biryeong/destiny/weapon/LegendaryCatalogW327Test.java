package kim.biryeong.destiny.weapon;

import java.util.*;
import kim.biryeong.destiny.loot.LootRoller;
import kim.biryeong.destiny.loot.LootTables;
import net.minecraft.util.RandomSource;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class LegendaryCatalogW327Test {
    @Test void newCatalogWeaponsHaveIndependentGameplayAndCompleteProfiles() {
        assertEquals(24, LegendaryWeapons.ids().size());
        var hashes = new HashSet<Long>();
        for (var id : LegendaryWeapons.ids()) {
            var e = WeaponCatalog.find(id).orElseThrow(); var base = LegendaryWeapons.base(e);
            var own = WeaponCharacteristics.of(e); var timing = WeaponTiming.forEntry(e);
            assertNotEquals(base.id(), e.id());
            assertNotEquals(WeaponCharacteristics.of(base).bungieHash(), own.bungieHash());
            assertTrue(hashes.add(own.bungieHash())); assertFalse(own.exotic());
            assertEquals(WeaponRarity.LEGENDARY, WeaponRarity.of(e));
            assertTrue(timing.supported()); assertTrue(WeaponHandlingProfile.of(e).supported());
            assertTrue(WeaponAimProfile.supports(e)); assertTrue(WeaponStatCurves.supports(id));
            var profile = WeaponProfile.forEntry(e);
            assertTrue(profile.magazine() > 0); assertTrue(profile.reloadTicks() > 0);
            assertEquals(timing.magazine().orElseThrow(), profile.magazine());
        }
        // Same visual donor cannot erase different magazine/stat/element identities.
        var krait = WeaponCatalog.find("krait").orElseThrow();
        assertEquals(2852052802L, WeaponCharacteristics.of(krait).bungieHash());
        assertEquals(53, WeaponProfile.forEntry(krait).magazine());
        assertEquals(WeaponCharacteristics.Damage.STASIS, WeaponCharacteristics.of(krait).damage());
        assertNotEquals(WeaponCharacteristics.of(LegendaryWeapons.base(krait)).stats(), WeaponCharacteristics.of(krait).stats());
    }
    @Test void lootUsesActualUniqueIdsAndFillsBothExactTraitColumns() {
        var filter = new LootTables.WeaponFilter(false, null, null, null,
            List.copyOf(LegendaryWeapons.ids()), null, List.of("legendary"));
        var pool = LootRoller.candidates(filter);
        assertEquals(24, pool.size());
        assertEquals(LegendaryWeapons.ids(), new HashSet<>(pool.stream().map(LootRoller.Candidate::id).toList()));
        for (var candidate : pool) {
            assertNull(candidate.skin()); assertEquals(candidate.id(), candidate.entry().id());
            var sockets = new HashSet<Integer>();
            for (var perk : WeaponPerks.ids()) for (var roll : LegendaryPerks.extraRolls(perk))
                if (roll.id().equals(candidate.id())) {
                    assertEquals(WeaponCharacteristics.of(candidate.entry()).bungieHash(), roll.hash());
                    sockets.add(roll.socket());
                }
            assertEquals(Set.of(3, 4), sockets);
            var only = new LootTables.WeaponFilter(false, null, null, null, List.of(candidate.id()), null, List.of("legendary"));
            assertEquals(candidate.id(), LootRoller.candidate(only, RandomSource.create(1)).orElseThrow().id());
        }
    }
    @Test void promotedLegendaryIdsDoNotRemainInCosmeticRarityPools() {
        assertTrue(WeaponSkins.ofRarity(WeaponRarity.LEGENDARY).stream().noneMatch(s -> LegendaryWeapons.contains(s.id())));
        for (var id : LegendaryWeapons.ids()) assertTrue(WeaponSkins.find(id).isPresent());
        var excluded = new LootTables.WeaponFilter(false, null, null, null, null, List.copyOf(LegendaryWeapons.ids()), List.of("legendary"));
        assertTrue(LootRoller.candidates(excluded).stream().noneMatch(c -> LegendaryWeapons.contains(c.id())));
    }
}
