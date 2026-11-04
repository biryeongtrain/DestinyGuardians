package kim.biryeong.destiny.loot;

import kim.biryeong.destiny.weapon.*;
import net.minecraft.util.RandomSource;
import net.minecraft.world.item.ItemStack;

import java.util.*;

/** Pure rolls: table entries, weapons from the catalog and one trait per trait column. No player state. */
public final class LootRoller {
    /** One rolled reward: a fresh weapon stack (perks already rolled) or an engram tier. */
    public record Reward(ItemStack weapon, String engram) {
        public static Reward weapon(ItemStack stack) { return new Reward(stack, null); }
        public static Reward engram(String tier) { return new Reward(null, tier); }
    }

    private LootRoller() { }

    public static List<Reward> roll(LootTables.Table table, RandomSource random) {
        var out = new ArrayList<Reward>();
        for (int i = 0; i < table.rolls(); i++) {
            if (random.nextDouble() >= table.chance()) continue;
            var entry = pick(table.entries(), random);
            if (entry == null || entry.empty()) continue;
            if (entry.engram() != null) out.add(Reward.engram(entry.engram()));
            else weapon(entry.weapon(), random).ifPresent(e -> out.add(Reward.weapon(create(e, random))));
        }
        return out;
    }

    static LootTables.Entry pick(List<LootTables.Entry> entries, RandomSource random) {
        int total = 0;
        for (var e : entries) total += e.weight();
        if (total <= 0) return null;
        int r = random.nextInt(total);
        for (var e : entries) { r -= e.weight(); if (r < 0) return e; }
        return entries.getLast();
    }

    /** Catalog weapons matching the filter, in catalog order. */
    public static List<WeaponCatalog.Entry> pool(LootTables.WeaponFilter f) {
        var out = new ArrayList<WeaponCatalog.Entry>();
        for (var e : WeaponCatalog.all()) {
            var c = WeaponCharacteristics.of(e);
            if (f == null) { out.add(e); continue; }
            if (f.exotic() != null && c.exotic() != f.exotic()) continue;
            if (f.slots() != null && !f.slots().contains(c.slot().name())) continue;
            if (f.ammo() != null && !f.ammo().contains(c.ammo().name())) continue;
            if (f.families() != null && !f.families().contains(e.family())) continue;
            if (f.ids() != null && !f.ids().contains(e.id())) continue;
            if (f.exclude() != null && f.exclude().contains(e.id())) continue;
            out.add(e);
        }
        return out;
    }

    public static Optional<WeaponCatalog.Entry> weapon(LootTables.WeaponFilter filter, RandomSource random) {
        var pool = pool(filter);
        return pool.isEmpty() ? Optional.empty() : Optional.of(pool.get(random.nextInt(pool.size())));
    }

    /** A new combat stack of {@code entry} with a random trait in every trait column. */
    public static ItemStack create(WeaponCatalog.Entry entry, RandomSource random) {
        var stack = WeaponItems.create(entry);
        rollPerks(stack, random);
        return stack;
    }

    /**
     * Destiny roll: each trait column (socket) independently gets one implemented trait from its own pool, never
     * the same trait twice. Columns with no implemented trait stay empty. Returns the chosen rolls.
     */
    public static List<WeaponPerks.Roll> rollPerks(ItemStack stack, RandomSource random) {
        var bySocket = new TreeMap<Integer, List<WeaponPerks.Roll>>();
        var idOf = new HashMap<WeaponPerks.Roll, String>();
        for (String id : WeaponPerks.ids()) for (var r : WeaponPerks.available(stack, id)) {
            bySocket.computeIfAbsent(r.socket(), k -> new ArrayList<>()).add(r);
            idOf.put(r, id);
        }
        var chosen = new ArrayList<WeaponPerks.Roll>();
        var used = new HashSet<String>();
        for (var column : bySocket.values()) {
            var options = column.stream().filter(r -> !used.contains(idOf.get(r))).toList();
            if (options.isEmpty()) continue;
            var r = options.get(random.nextInt(options.size()));
            chosen.add(r); used.add(idOf.get(r));
        }
        if (!WeaponPerks.replaceSelection(stack, chosen)) return List.of();
        return List.copyOf(chosen);
    }
}
