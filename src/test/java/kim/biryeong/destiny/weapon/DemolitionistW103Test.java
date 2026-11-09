package kim.biryeong.destiny.weapon;

import com.google.gson.JsonParser;
import org.junit.jupiter.api.Test;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.Set;
import static org.junit.jupiter.api.Assertions.*;

/** Literal frozen base-socket oracle and local adaptation boundaries, not measured live D2 energy. */
class DemolitionistW103Test {
    /** Historical source assertions remain frozen; new identities require exact official tuples. */
    private static java.util.List<WeaponPerks.Roll> legacyRolls() {
        var all = DemolitionistProfile.rolls();
        var added = all.stream().filter(r -> LegendaryWeapons.contains(r.id())).toList();
        assertEquals(java.util.Set.of("age_old_bond", "apex_predator", "brigands_law", "circular_logic", "deliverance", "forbearance", "heritage", "insidious", "iterative_loop", "origin_story", "rufuss_fury", "submission", "succession"), added.stream().map(WeaponPerks.Roll::id)
            .collect(java.util.stream.Collectors.toSet()));
        for (var roll : added) assertTrue(LegendaryWeapons.exactRoll(roll), roll.toString());
        assertEquals(all.size(), new java.util.HashSet<>(all).size());
        return all.stream().filter(r -> !LegendaryWeapons.contains(r.id())).toList();
    }

    private static final long HASH = 3523296417L;
    private static final Set<WeaponPerks.Roll> ROWS = Set.of(
            new WeaponPerks.Roll("austringer",3055790362L,4,HASH,785215120L),
            new WeaponPerks.Roll("gnawing_hunger",821154603L,4,HASH,594510568L),
            new WeaponPerks.Roll("bug_out_bag",2744715540L,4,HASH,575371383L),
            new WeaponPerks.Roll("lonesome",2199171672L,4,HASH,167712635L),
            new WeaponPerks.Roll("high_albedo",1197486957L,4,HASH,718633408L),
            new WeaponPerks.Roll("whispering_slab",211938782L,4,HASH,967526625L),
            new WeaponPerks.Roll("first_in_last_out",3616586446L,4,HASH,1439234589L),
            new WeaponPerks.Roll("stormchaser",3652506829L,4,HASH,4213354588L),
            new WeaponPerks.Roll("retraced_path",548958835L,4,HASH,398391969L),
            new WeaponPerks.Roll("salvager_s_salvo",2060863616L,3,HASH,253L),
            new WeaponPerks.Roll("nezarec_s_whisper",254636484L,3,HASH,210449465L));

    @Test void exactElevenBaseSocketsAndImmutableProfileExcludeEnhanced() {
        assertEquals("demolitionist", DemolitionistProfile.ID);
        assertEquals(HASH, DemolitionistProfile.HASH);
        assertEquals(11, legacyRolls().size());
        assertEquals(ROWS, Set.copyOf(legacyRolls()));
        assertTrue(legacyRolls().stream().noneMatch(r -> r.perkHash() == 1906147653L));
        assertThrows(UnsupportedOperationException.class, () -> legacyRolls().clear());
        var p = DemolitionistProfile.perk();
        assertEquals(HASH, p.hash()); assertEquals("demolitionist", p.id());
        assertEquals(10, p.energyPercent()); assertEquals(20, p.specialEnergyPercent());
        assertEquals(List.of("sniper_rifle","shotgun","glaive","fusion_rifle"), p.specialEnergyFamilies());
        assertThrows(UnsupportedOperationException.class, () -> p.specialEnergyFamilies().clear());
        assertEquals(60, p.reloadCooldownTicks());
        assertTrue(p.reloadFromReserves()); assertTrue(p.energyIsBaseChunk());
    }

    @Test void exactRosterNotBlanketSpecialAmmoDeterminesBaselineEnergy() {
        int eligible = 0, twenty = 0;
        for (var e : WeaponCatalog.all().stream().filter(w -> !LegendaryWeapons.contains(w.id())).toList()) {
            boolean present = ROWS.stream().anyMatch(r -> r.id().equals(e.id()));
            int expected = !present ? 0 : Set.of("first_in_last_out","nezarec_s_whisper").contains(e.id()) ? 20 : 10;
            assertEquals(expected, DemolitionistProfile.energyPercent(e), e.id());
            if (expected > 0) eligible++;
            if (expected == 20) twenty++;
        }
        assertEquals(11, eligible); assertEquals(2, twenty);
        for (String id : List.of("retraced_path","salvager_s_salvo","stormchaser","whispering_slab"))
            assertEquals(10, DemolitionistProfile.energyPercent(WeaponCatalog.find(id).orElseThrow()), id);
    }

    @Test void ceilingUsesFullDurationAndNeverRepeatedFractionOfRemaining() {
        assertEquals(1, WeaponDemolitionist.grantTicks(1,10));
        assertEquals(10, WeaponDemolitionist.grantTicks(100,10));
        assertEquals(11, WeaponDemolitionist.grantTicks(101,10));
        assertEquals(21, WeaponDemolitionist.grantTicks(101,20));
        for (int full = 1; full < 4000; full += 7) for (int percent : new int[]{1,10,20,99,100}) {
            int grant = WeaponDemolitionist.grantTicks(full,percent);
            assertEquals(((long)full * percent + 99)/100, grant);
            assertTrue(grant > 0 && grant <= full);
            int remaining = full;
            int expectedStep = grant;
            for (int kill = 0; kill < 12; kill++) {
                int after = Math.max(0, remaining - WeaponDemolitionist.grantTicks(full,percent));
                assertEquals(Math.min(remaining,expectedStep), remaining-after);
                remaining = after;
            }
        }
    }

    @Test void invalidDurationsPercentagesAndIntegerLimitCannotOverflowOrGrant() {
        for (int full : new int[]{Integer.MIN_VALUE,-1,0})
            for (int percent : new int[]{10,20,100}) assertEquals(0, WeaponDemolitionist.grantTicks(full,percent));
        for (int percent : new int[]{Integer.MIN_VALUE,-1,0,101,Integer.MAX_VALUE})
            assertEquals(0, WeaponDemolitionist.grantTicks(Integer.MAX_VALUE,percent));
        assertEquals(214748365, WeaponDemolitionist.grantTicks(Integer.MAX_VALUE,10));
        assertEquals(429496730, WeaponDemolitionist.grantTicks(Integer.MAX_VALUE,20));
        assertEquals(Integer.MAX_VALUE, WeaponDemolitionist.grantTicks(Integer.MAX_VALUE,100));
    }

    private static WeaponProfile finite() {
        return new WeaponProfile(WeaponProfile.Mode.HITSCAN,1,10,6,12,20,48,0,1,1,0,0,0,0,
                false,false,10,0,false,false);
    }
    @Test void reserveOnlyRefillConservesPartialEmptyFullAndLegacyOverflow() {
        var partial = new WeaponMagazine(finite(),0,2);
        assertEquals(2,partial.reload()); assertEquals(2,partial.rounds());
        assertEquals(0,partial.reserve()); assertEquals(2,partial.total());
        assertEquals(0,partial.reload()); assertEquals(2,partial.total());
        var empty = new WeaponMagazine(finite(),0,0);
        assertEquals(0,empty.reload()); assertEquals(0,empty.total());
        var full = new WeaponMagazine(finite(),6,2);
        assertEquals(0,full.reload()); assertEquals(8,full.total());
        var legacy = new WeaponMagazine(finite(),0,0,20);
        long before = legacy.total();
        assertEquals(6,legacy.reload()); assertEquals(6,legacy.rounds());
        assertEquals(before,legacy.total()); assertEquals(14,legacy.reserve()+legacy.overflow());
    }

    @Test void pinnedResearchExplicitlyRetainsMissingCurrentScalarsAndLocalScope() throws Exception {
        assertEquals("art/weapons/w103/references/mechanics.json",DemolitionistProfile.perk().mechanicsSource());
        var mechanics = JsonParser.parseString(Files.readString(Path.of(DemolitionistProfile.perk().mechanicsSource()))).getAsJsonObject();
        assertEquals(HASH,mechanics.getAsJsonObject("officialDescription").get("hash").getAsLong());
        assertTrue(mechanics.getAsJsonObject("officialDescription").get("description").getAsString().contains("from reserves"));
        assertEquals(10,mechanics.get("baseEnergyPercent").getAsInt());
        assertEquals(20,mechanics.get("exceptionEnergyPercent").getAsInt());
        assertEquals(60,mechanics.get("reloadCooldownTicks").getAsInt());
        assertFalse(mechanics.getAsJsonObject("reloadCooldownScope").get("proven").getAsBoolean());
        assertFalse(mechanics.getAsJsonObject("numericSource").get("primary").getAsBoolean());
        assertTrue(mechanics.getAsJsonObject("unimplementedEnergyModifiers").get("abilityTierScalar").isJsonNull());
        assertTrue(mechanics.getAsJsonObject("unimplementedEnergyModifiers").get("grenadeStatScalar").isJsonNull());
        assertEquals(1906147653L,mechanics.getAsJsonObject("enhanced").get("hash").getAsLong());
        assertFalse(mechanics.getAsJsonObject("enhanced").get("implemented").getAsBoolean());
    }
}
