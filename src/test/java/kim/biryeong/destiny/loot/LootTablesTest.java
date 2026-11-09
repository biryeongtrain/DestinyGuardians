package kim.biryeong.destiny.loot;

import kim.biryeong.destiny.weapon.WeaponCharacteristics;
import net.minecraft.util.RandomSource;
import org.junit.jupiter.api.Test;

import java.util.*;

import static org.junit.jupiter.api.Assertions.*;

class LootTablesTest {
    @Test void sharedTablesResolveEveryHook() {
        var devils = LootTables.activity("devils_lair").orElseThrow();
        assertTrue(LootTables.table(devils.completion()).isPresent());
        assertTrue(LootTables.table(devils.chest()).isPresent());
        var enemies = LootTables.enemies().orElseThrow();
        for (String t : List.of(enemies.minor(), enemies.major(), enemies.boss())) assertTrue(LootTables.table(t).isPresent(), t);
        for (String tier : LootTables.engramTiers()) assertTrue(LootTables.engramTable(tier).flatMap(LootTables::table).isPresent(), tier);
    }

    @Test void weightedPickFollowsWeights() {
        var entries = List.of(new LootTables.Entry(3, null, "legendary"), new LootTables.Entry(1, null, "exotic"));
        var random = RandomSource.create(7);
        int legendary = 0;
        for (int i = 0; i < 4000; i++) if ("legendary".equals(LootRoller.pick(entries, random).engram())) legendary++;
        assertEquals(.75, legendary / 4000.0, .03);
    }

    @Test void weaponFiltersSplitLegendaryAndExotic() {
        var legendary = LootRoller.pool(new LootTables.WeaponFilter(false, null, null, null, null, null));
        var exotic = LootRoller.pool(new LootTables.WeaponFilter(true, null, null, null, null, null));
        assertFalse(legendary.isEmpty()); assertFalse(exotic.isEmpty());
        assertTrue(legendary.stream().noneMatch(e -> WeaponCharacteristics.of(e).exotic()));
        assertTrue(exotic.stream().allMatch(e -> WeaponCharacteristics.of(e).exotic()));
        var heavy = LootRoller.pool(new LootTables.WeaponFilter(null, List.of("POWER"), null, null, null, null));
        assertTrue(heavy.stream().allMatch(e -> WeaponCharacteristics.of(e).slot().name().equals("POWER")));
    }

    /** W325 loot-shooter pacing: frequent low-tier drops, legendaries stay a small share of trash-mob loot. */
    @Test void enemyDropPacing() {
        var minor = LootTables.table("enemy_minor").orElseThrow();
        assertTrue(minor.chance() <= .2);
        assertTrue(LootTables.table("enemy_major").orElseThrow().chance() <= .5);
        int total = 0, legendaryOrBetter = 0;
        for (var e : minor.entries()) {
            total += e.weight();
            boolean low = e.weapon() != null && e.weapon().rarity() != null
                    && e.weapon().rarity().stream().allMatch(r -> List.of("common", "uncommon", "rare").contains(r));
            if (!low) legendaryOrBetter += e.weight();
        }
        assertTrue(legendaryOrBetter * 10 <= total, "legendary share of minor drops");
    }

    @Test void tieredSkinsAreDroppableAndRollFewerTraits() {
        var rare = LootRoller.candidates(new LootTables.WeaponFilter(null, null, null, null, null, null, List.of("rare")));
        assertFalse(rare.isEmpty());
        for (var c : rare) {
            assertNotNull(c.skin());
            assertEquals(kim.biryeong.destiny.weapon.WeaponRarity.RARE, c.rarity());
        }
        // Without a rarity filter the pool stays the legendary/exotic catalog.
        assertTrue(LootRoller.candidates(new LootTables.WeaponFilter(false, null, null, null, null, null)).stream().allMatch(c -> c.skin() == null));
        assertEquals(0, kim.biryeong.destiny.weapon.WeaponRarity.COMMON.traitColumns());
        assertEquals(0, kim.biryeong.destiny.weapon.WeaponRarity.UNCOMMON.traitColumns()); // W326: green = barrel + magazine only
        assertEquals(1, kim.biryeong.destiny.weapon.WeaponRarity.RARE.traitColumns());
        for (String t : List.of("common", "uncommon", "rare")) assertTrue(LootTables.engramTable(t).isPresent(), t);
    }

    @Test void profileCodecRoundTrips() {
        var p = LootProfile.EMPTY.plus("legendary").plus("exotic").withStarter();
        var json = LootProfile.CODEC.encodeStart(com.mojang.serialization.JsonOps.INSTANCE, p).getOrThrow();
        assertEquals(p, LootProfile.CODEC.parse(com.mojang.serialization.JsonOps.INSTANCE, json).getOrThrow());
        assertEquals(List.of("exotic"), p.minus(0).engrams());
    }

    @Test void strikeChestBurstsGlimmer() {
        var hook = LootTables.activity("devils_lair").orElseThrow();
        var rng = RandomSource.create(7);
        for (int i = 0; i < 200; i++) { long g = hook.rollGlimmer(rng); assertTrue(g >= 40 && g <= 60, "glimmer " + g); }
        assertEquals(0, new LootTables.Activity("strike_completion", "strike_chest").rollGlimmer(rng));
    }

    @Test void strikeChestIsEightyPercentLegendaryOrBetterPerOpening() {
        for (String activity : List.of("devils_lair", "exodus_crash")) {
            var hook = LootTables.activity(activity).orElseThrow();
            var chest = LootTables.table(hook.chest()).orElseThrow();
            assertEquals(1, chest.rolls()); assertEquals(1.0, chest.chance());
            int total = 0, rare = 0, legendary = 0, exotic = 0;
            for (var entry : chest.entries()) {
                total += entry.weight();
                if ("exotic".equals(entry.engram())) exotic += entry.weight();
                else if ("legendary".equals(entry.engram()) || entry.weapon() != null && Boolean.FALSE.equals(entry.weapon().exotic())) legendary += entry.weight();
                else {
                    assertNotNull(entry.weapon()); assertEquals(List.of("rare"), entry.weapon().rarity());
                    rare += entry.weight();
                }
            }
            assertEquals(.2, rare / (double) total, 1e-12);
            assertEquals(.72, legendary / (double) total, 1e-12);
            assertEquals(.08, exotic / (double) total, 1e-12);
            var completion = LootTables.table(hook.completion()).orElseThrow();
            assertEquals(1.0, completion.chance());
            assertEquals(activity.equals("exodus_crash") ? 2 : 1, completion.rolls());
            assertTrue(completion.entries().stream().allMatch(e -> e.weapon() != null && Boolean.FALSE.equals(e.weapon().exotic())));
        }
    }
}
