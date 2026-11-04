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

    @Test void enemyDropChancesStayLow() {
        assertTrue(LootTables.table("enemy_minor").orElseThrow().chance() <= .05);
        assertTrue(LootTables.table("enemy_major").orElseThrow().chance() <= .2);
    }

    @Test void profileCodecRoundTrips() {
        var p = LootProfile.EMPTY.plus("legendary").plus("exotic").withStarter();
        var json = LootProfile.CODEC.encodeStart(com.mojang.serialization.JsonOps.INSTANCE, p).getOrThrow();
        assertEquals(p, LootProfile.CODEC.parse(com.mojang.serialization.JsonOps.INSTANCE, json).getOrThrow());
        assertEquals(List.of("exotic"), p.minus(0).engrams());
    }
}
