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
            else candidate(entry.weapon(), random).ifPresent(c -> out.add(Reward.weapon(create(c, random))));
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

    /** One droppable weapon: a catalog weapon ({@code skin == null}) or a W325 skin over its base. */
    public record Candidate(WeaponCatalog.Entry entry, WeaponSkins.Skin skin) {
        public String id() { return skin == null ? entry.id() : skin.id(); }
        public WeaponRarity rarity() { return skin != null && skin.rarity() != null ? skin.rarity() : WeaponRarity.of(entry); }
    }

    /** Catalog weapons matching the filter, in catalog order (legendary/exotic catalog only). */
    public static List<WeaponCatalog.Entry> pool(LootTables.WeaponFilter f) {
        var out = new ArrayList<WeaponCatalog.Entry>();
        for (var c : candidates(f)) if (c.skin() == null) out.add(c.entry());
        return out;
    }

    /** Every droppable weapon matching the filter: catalog rows first, then tiered skins in registry order. */
    public static List<Candidate> candidates(LootTables.WeaponFilter f) {
        var all = new ArrayList<Candidate>();
        for (var e : WeaponCatalog.all()) all.add(new Candidate(e, null));
        for (var s : WeaponSkins.ALL)
            if (s.rarity() != null && s.rarity().ordinal() < WeaponRarity.LEGENDARY.ordinal())
                WeaponCatalog.find(s.base()).ifPresent(e -> all.add(new Candidate(e, s)));
        var out = new ArrayList<Candidate>();
        for (var cand : all) {
            var e = cand.entry();
            if (f == null) { if (cand.skin() == null) out.add(cand); continue; }
            var c = WeaponCharacteristics.of(e);
            if (f.rarity() == null ? cand.skin() != null : !f.rarity().contains(cand.rarity().id())) continue;
            if (f.exotic() != null && c.exotic() != f.exotic()) continue;
            if (f.slots() != null && !f.slots().contains(c.slot().name())) continue;
            if (f.ammo() != null && !f.ammo().contains(c.ammo().name())) continue;
            if (f.families() != null && !f.families().contains(e.family())) continue;
            if (f.ids() != null && !f.ids().contains(cand.id())) continue;
            if (f.exclude() != null && f.exclude().contains(cand.id())) continue;
            out.add(cand);
        }
        return out;
    }

    public static Optional<WeaponCatalog.Entry> weapon(LootTables.WeaponFilter filter, RandomSource random) {
        var pool = pool(filter);
        return pool.isEmpty() ? Optional.empty() : Optional.of(pool.get(random.nextInt(pool.size())));
    }

    public static Optional<Candidate> candidate(LootTables.WeaponFilter filter, RandomSource random) {
        var pool = candidates(filter);
        return pool.isEmpty() ? Optional.empty() : Optional.of(pool.get(random.nextInt(pool.size())));
    }

    /** A new combat stack of {@code entry} with a random trait in every trait column. */
    public static ItemStack create(WeaponCatalog.Entry entry, RandomSource random) {
        return create(new Candidate(entry, null), random);
    }

    /** A new combat stack of the candidate: skin applied, trait columns filled up to its tier's count. */
    public static ItemStack create(Candidate c, RandomSource random) {
        var stack = WeaponItems.create(c.entry());
        if (c.skin() != null) WeaponSkins.apply(stack, c.skin().id());
        rollPerks(stack, random, c.rarity().traitColumns());
        kim.biryeong.destiny.weapon.WeaponComponents.roll(stack, random, c.rarity().componentColumns()); // W326
        return stack;
    }

    /** A skinned starter/campaign weapon (keeps the skin's tier trait count). */
    public static ItemStack create(WeaponCatalog.Entry entry, String skinId, RandomSource random) {
        return create(new Candidate(entry, skinId == null ? null : WeaponSkins.find(skinId).orElse(null)), random);
    }

    /**
     * Destiny roll: each trait column (socket) independently gets one implemented trait from its own pool, never
     * the same trait twice. Columns with no implemented trait stay empty. Returns the chosen rolls.
     */
    public static List<WeaponPerks.Roll> rollPerks(ItemStack stack, RandomSource random) {
        return rollPerks(stack, random, Integer.MAX_VALUE);
    }

    /** As {@link #rollPerks(ItemStack, RandomSource)} but fills at most {@code columns} trait columns (W325 tiers). */
    public static List<WeaponPerks.Roll> rollPerks(ItemStack stack, RandomSource random, int columns) {
        var bySocket = new TreeMap<Integer, List<WeaponPerks.Roll>>();
        var idOf = new HashMap<WeaponPerks.Roll, String>();
        for (String id : WeaponPerks.ids()) for (var r : WeaponPerks.available(stack, id)) {
            bySocket.computeIfAbsent(r.socket(), k -> new ArrayList<>()).add(r);
            idOf.put(r, id);
        }
        var chosen = new ArrayList<WeaponPerks.Roll>();
        var used = new HashSet<String>();
        for (var column : bySocket.values()) {
            if (chosen.size() >= columns) break;
            var options = column.stream().filter(r -> !used.contains(idOf.get(r))).toList();
            if (options.isEmpty()) continue;
            var r = options.get(random.nextInt(options.size()));
            chosen.add(r); used.add(idOf.get(r));
        }
        if (chosen.isEmpty()) return List.of();
        if (!WeaponPerks.replaceSelection(stack, chosen)) return List.of();
        return List.copyOf(chosen);
    }
}
