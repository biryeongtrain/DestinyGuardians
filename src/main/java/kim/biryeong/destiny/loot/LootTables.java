package kim.biryeong.destiny.loot;

import com.google.gson.Gson;

import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.*;

/**
 * Data-driven drop tables ({@code /destiny/loot/tables.json}). Shared by every activity: strikes, dungeons, raids
 * and open-world enemies pick tables by id; nothing here knows about a particular activity.
 *
 * <p>A table rolls {@code rolls} times, each roll first passing {@code chance} (0..1) and then choosing one weighted
 * entry. An entry gives either a weapon chosen by {@link WeaponFilter} or an engram of a tier, or nothing.
 */
public final class LootTables {
    /**
     * Weapon pool filter. Null fields match everything. {@code rarity} (W325) selects item tiers: common, uncommon,
     * rare (Red War skins), legendary, exotic; null keeps the catalog pool (legendary + exotic, narrowed by
     * {@code exotic}). {@code ids}/{@code exclude} match catalog ids or skin ids.
     */
    public record WeaponFilter(Boolean exotic, List<String> slots, List<String> ammo, List<String> families,
                               List<String> ids, List<String> exclude, List<String> rarity) {
        public WeaponFilter(Boolean exotic, List<String> slots, List<String> ammo, List<String> families,
                            List<String> ids, List<String> exclude) {
            this(exotic, slots, ammo, families, ids, exclude, null);
        }
    }
    public record Entry(int weight, WeaponFilter weapon, String engram) {
        public boolean empty() { return weapon == null && engram == null; }
    }
    public record Table(String id, int rolls, double chance, List<Entry> entries) { }
    /**
     * Activity hook: completion reward table, end chest table, and the Glimmer the chest bursts out as
     * {@code [min, max]} (inclusive; one value = fixed; absent = none).
     */
    public record Activity(String completion, String chest, List<Long> glimmer) {
        public Activity(String completion, String chest) { this(completion, chest, null); }
        public long rollGlimmer(net.minecraft.util.RandomSource random) {
            if (glimmer == null || glimmer.isEmpty()) return 0;
            long lo = Math.max(0, glimmer.getFirst()), hi = Math.max(lo, glimmer.getLast());
            return lo + (hi > lo ? (long) random.nextInt((int) Math.min(Integer.MAX_VALUE, hi - lo + 1)) : 0);
        }
    }
    /** Enemy drop tables by tier (minor / major / boss). */
    public record Enemies(String minor, String major, String boss) { }
    private record File(Map<String, Table> tables, Map<String, Activity> activities, Enemies enemies,
                        Map<String, String> engramTables) { }

    private static final File DATA = load();

    private LootTables() { }

    private static File load() {
        var in = LootTables.class.getResourceAsStream("/destiny/loot/tables.json");
        if (in == null) throw new IllegalStateException("Missing /destiny/loot/tables.json");
        try (var reader = new InputStreamReader(in, StandardCharsets.UTF_8)) {
            var raw = new Gson().fromJson(reader, File.class);
            var tables = new LinkedHashMap<String, Table>();
            for (var e : raw.tables.entrySet()) {
                var t = e.getValue();
                int rolls = t.rolls() <= 0 ? 1 : t.rolls();
                double chance = t.chance() <= 0 ? 1 : Math.min(1, t.chance());
                if (t.entries() == null || t.entries().isEmpty()) throw new IllegalStateException("Loot table without entries: " + e.getKey());
                for (var entry : t.entries()) if (entry.weight() <= 0) throw new IllegalStateException("Non-positive weight in " + e.getKey());
                tables.put(e.getKey(), new Table(e.getKey(), rolls, chance, List.copyOf(t.entries())));
            }
            var file = new File(Map.copyOf(tables), raw.activities == null ? Map.of() : Map.copyOf(raw.activities),
                    raw.enemies, raw.engramTables == null ? Map.of() : Map.copyOf(raw.engramTables));
            for (var a : file.activities.values()) {
                require(file, a.completion()); require(file, a.chest());
                if (a.glimmer() != null && (a.glimmer().size() > 2 || a.glimmer().stream().anyMatch(g -> g == null || g < 0)))
                    throw new IllegalStateException("Activity glimmer must be [min, max] >= 0");
            }
            if (file.enemies != null) { require(file, file.enemies.minor()); require(file, file.enemies.major()); require(file, file.enemies.boss()); }
            for (var t : file.engramTables.values()) require(file, t);
            for (var t : tables.values()) for (var entry : t.entries()) {
                if (entry.weapon() != null && entry.weapon().rarity() != null)
                    for (var r : entry.weapon().rarity())
                        if (kim.biryeong.destiny.weapon.WeaponRarity.parse(r).isEmpty())
                            throw new IllegalStateException("Unknown rarity " + r + " in " + t.id());
                if (entry.engram() != null && !file.engramTables.containsKey(entry.engram()))
                    throw new IllegalStateException("Unknown engram tier " + entry.engram() + " in " + t.id());
            }
            return file;
        } catch (java.io.IOException e) { throw new IllegalStateException(e); }
    }

    private static void require(File file, String id) {
        if (id != null && !file.tables.containsKey(id)) throw new IllegalStateException("Unknown loot table " + id);
    }

    public static Optional<Table> table(String id) { return Optional.ofNullable(id == null ? null : DATA.tables.get(id)); }
    public static Optional<Activity> activity(String id) { return Optional.ofNullable(DATA.activities.get(id)); }
    public static Optional<Enemies> enemies() { return Optional.ofNullable(DATA.enemies); }
    /** The table an engram of {@code tier} decodes from. */
    public static Optional<String> engramTable(String tier) { return Optional.ofNullable(DATA.engramTables.get(tier)); }
    public static Set<String> engramTiers() { return DATA.engramTables.keySet(); }
}
