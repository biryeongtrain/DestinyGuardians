package kim.biryeong.destiny.weapon;

import com.google.gson.Gson;
import net.minecraft.core.component.DataComponents;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.util.RandomSource;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.component.CustomData;

import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.*;

/**
 * W326 weapon components: the barrel and magazine columns of a Destiny weapon (Smallbore, Flared Magwell, ...).
 * They are flat stat plugs read from the Bungie manifest (w326-components.json) and bound to the exact stack.
 * Uncommon weapons roll barrel + magazine, Rare and above also roll a trait. Original low-tier Destiny weapons have
 * curated rolls; random rolls here are a deliberate local loot-shooter choice.
 *
 * Stat effects (all static while the stack is held, summed into the existing perk chains):
 * range, stability, handling (ready/stow/ADS), reload, magazine (rounds), recoil direction.
 * Stats with no local system (aim assist, airborne, impact, velocity, blast radius, ...) are shown but inert.
 */
public final class WeaponComponents {
    public static final String KEY = "destiny_weapon_components";
    public enum Slot { BARREL, MAGAZINE; public String id() { return name().toLowerCase(Locale.ROOT); } }
    public record Component(String id, long hash, String slot, String name, String nameKo, String descriptionKo,
                            String icon, Map<String, Integer> stats) {
        public int stat(String key) { return stats == null ? 0 : stats.getOrDefault(key, 0); }
        public Slot slotEnum() { return "barrel".equals(slot) ? Slot.BARREL : Slot.MAGAZINE; }
    }
    private record Data(String stage, String source, Component[] components, Map<String, Map<String, List<String>>> pools) {}
    private static final Map<String, Component> BY_ID = new LinkedHashMap<>();
    private static final Map<String, Map<Slot, List<Component>>> POOLS = new HashMap<>();
    static { load(); }
    private WeaponComponents() {}

    private static void load() {
        var in = WeaponComponents.class.getResourceAsStream("/destiny/weapons/w326-components.json");
        if (in == null) return; // No data: weapons simply have no components.
        try (var reader = new InputStreamReader(in, StandardCharsets.UTF_8)) {
            var data = new Gson().fromJson(reader, Data.class);
            if (data == null || !"W326".equals(data.stage) || data.components == null) throw new IllegalStateException("Invalid W326 components");
            for (var c : data.components) {
                if (c == null || c.id == null || c.id.isBlank() || !("barrel".equals(c.slot) || "magazine".equals(c.slot))
                        || BY_ID.putIfAbsent(c.id, c) != null)
                    throw new IllegalStateException("Invalid/duplicate W326 component " + (c == null ? null : c.id));
                if (c.stats != null) for (var v : c.stats.values()) if (v == null || Math.abs(v) > 100)
                    throw new IllegalStateException("Unsafe W326 stat " + c.id);
            }
            if (data.pools != null) for (var e : data.pools.entrySet()) {
                if (WeaponCatalog.find(e.getKey()).isEmpty()) continue;
                var bySlot = new EnumMap<Slot, List<Component>>(Slot.class);
                for (var s : Slot.values()) {
                    var ids = e.getValue().get(s.id());
                    if (ids == null) continue;
                    var list = new ArrayList<Component>();
                    for (String id : ids) {
                        var c = BY_ID.get(id);
                        if (c == null || c.slotEnum() != s) throw new IllegalStateException("W326 pool " + e.getKey() + " bad " + id);
                        if (!list.contains(c)) list.add(c);
                    }
                    if (!list.isEmpty()) bySlot.put(s, List.copyOf(list));
                }
                POOLS.put(e.getKey(), bySlot);
            }
        } catch (java.io.IOException e) { throw new IllegalStateException(e); }
    }

    public static Optional<Component> find(String id) { return Optional.ofNullable(BY_ID.get(id)); }
    public static Collection<Component> all() { return Collections.unmodifiableCollection(BY_ID.values()); }
    public static List<Component> pool(WeaponCatalog.Entry entry, Slot slot) {
        var p = POOLS.get(entry.id());
        return p == null ? List.of() : p.getOrDefault(slot, List.of());
    }

    /** The components rolled on this exact stack, barrel first. Unknown or out-of-pool saved ids are inert. */
    public static List<Component> of(ItemStack stack) {
        var entry = WeaponItems.entry(stack);
        if (entry.isEmpty()) return List.of();
        var data = stack.get(DataComponents.CUSTOM_DATA);
        if (data == null) return List.of();
        var tag = data.copyTag().getCompoundOrEmpty(KEY);
        var out = new ArrayList<Component>(2);
        for (var s : Slot.values()) {
            String id = tag.getStringOr(s.id(), "");
            var c = BY_ID.get(id);
            if (c != null && pool(entry.get(), s).contains(c)) out.add(c);
        }
        return out;
    }
    public static Optional<Component> get(ItemStack stack, Slot slot) {
        return of(stack).stream().filter(c -> c.slotEnum() == slot).findFirst();
    }

    /** Fill the first {@code columns} component slots (barrel, then magazine) at random. Returns the rolled set. */
    public static List<Component> roll(ItemStack stack, RandomSource random, int columns) {
        var entry = WeaponItems.entry(stack);
        if (entry.isEmpty() || columns <= 0) return List.of();
        var tag = new CompoundTag(); var out = new ArrayList<Component>();
        for (var s : Slot.values()) {
            if (out.size() >= columns) break;
            var pool = pool(entry.get(), s);
            if (pool.isEmpty()) continue;
            var c = pool.get(random.nextInt(pool.size()));
            tag.putString(s.id(), c.id()); out.add(c);
        }
        set(stack, tag);
        refill(stack);
        return out;
    }
    /** Explicit set (debug/admin). Null clears the slot. */
    public static boolean set(ItemStack stack, Slot slot, String id) {
        var entry = WeaponItems.entry(stack);
        if (entry.isEmpty()) return false;
        var data = stack.get(DataComponents.CUSTOM_DATA);
        var tag = (data == null ? new CompoundTag() : data.copyTag()).getCompoundOrEmpty(KEY).copy();
        if (id == null) tag.remove(slot.id());
        else {
            var c = BY_ID.get(id);
            if (c == null || !pool(entry.get(), slot).contains(c)) return false;
            tag.putString(slot.id(), id);
        }
        set(stack, tag);
        return true;
    }
    private static void set(ItemStack stack, CompoundTag components) {
        var data = stack.get(DataComponents.CUSTOM_DATA);
        var tag = data == null ? new CompoundTag() : data.copyTag();
        if (components.isEmpty()) tag.remove(KEY); else tag.put(KEY, components);
        stack.set(DataComponents.CUSTOM_DATA, CustomData.of(tag));
        WeaponAiming.perksEdited(stack);
    }
    /** A freshly rolled weapon starts with a full (component-sized) magazine. */
    private static void refill(ItemStack stack) {
        var entry = WeaponItems.entry(stack);
        if (entry.isEmpty() || SwordItems.isSword(stack)) return;
        var profile = WeaponProfile.forEntry(entry.get());
        var adjusted = profile(stack, profile);
        WeaponItems.save(stack, new WeaponMagazine(adjusted, adjusted.magazine(), adjusted.reserve()));
    }

    // ---------------------------------------------------------------- stats
    public static int stat(ItemStack stack, String key) {
        int sum = 0;
        for (var c : of(stack)) sum += c.stat(key);
        return sum;
    }
    private static ItemStack held(ServerPlayer p) { return p == null ? ItemStack.EMPTY : p.getMainHandItem(); }
    public static int rangeBonus(ServerPlayer p) { return stat(held(p), "range"); }
    public static int stabilityBonus(ServerPlayer p) { return stat(held(p), "stability"); }
    public static int recoilDirectionBonus(ServerPlayer p) { return stat(held(p), "recoilDirection"); }

    /** Magazine stat → rounds. Destiny maps magazine stat per frame; locally +1 stat ≈ +0.67% rounds, rounded,
     * with at least ±1 round for a non-zero bonus on magazines of 5+ rounds. Never below one round. */
    public static int magazine(int base, int bonus) {
        if (bonus == 0 || base <= 0) return base;
        double delta = base * bonus * 0.0067;
        int d = (int) Math.round(delta);
        if (d == 0 && base >= 5) d = Integer.signum(bonus);
        return Math.max(1, base + d);
    }
    /** The weapon profile with this stack's magazine components applied. */
    public static WeaponProfile profile(ItemStack stack, WeaponProfile p) {
        if (p == null || p.mode() == WeaponProfile.Mode.MELEE) return p;
        int bonus = stat(stack, "magazine");
        int mag = magazine(p.magazine(), bonus);
        if (mag == p.magazine()) return p;
        return new WeaponProfile(p.mode(), p.damage(), p.intervalTicks(), mag, p.reserve(), p.reloadTicks(), p.range(),
                p.chargeTicks(), p.burst(), p.pellets(), p.spread(), p.speed(), p.gravity(), p.blastRadius(), p.automatic(),
                p.infiniteReserve(), p.cadenceTicks(), p.burstSpacingTicks(), p.sharedBurstAmmo(), p.shellReload(),
                p.firstReloadTicks(), p.roundsPerInsert());
    }

    /** Duration ratio of a stat bonus: the weapon's W320 curve when known, else a flat ~0.4%/point approximation. */
    private static int scaleHandling(String id, boolean ready, int base, int bonus) {
        if (bonus == 0 || base <= 0) return base;
        if (WeaponStatCurves.supports(id)) return WeaponStatCurves.handlingTicks(id, ready, base, bonus, 1);
        return WeaponStatCurves.scale(base, Math.clamp(1 - bonus * 0.004, 0.6, 1.5));
    }
    public static int handlingTicks(ItemStack stack, boolean ready, int base) {
        var e = WeaponItems.entry(stack);
        return e.isEmpty() ? base : scaleHandling(e.get().id(), ready, base, stat(stack, "handling"));
    }
    public static int adsTicks(ServerPlayer p, WeaponCatalog.Entry entry, int base) {
        var stack = held(p);
        if (WeaponItems.entry(stack).filter(entry::equals).isEmpty()) return base;
        int bonus = stat(stack, "handling");
        if (bonus == 0 || base <= 0) return base;
        if (WeaponStatCurves.supports(entry.id())) return WeaponStatCurves.adsTicks(entry.id(), base, bonus, 1);
        return Math.max(Math.min(base, 2), WeaponStatCurves.scale(base, Math.clamp(1 - bonus * 0.004, 0.6, 1.5)));
    }
    private static int reload(String id, int base, int bonus) {
        if (bonus == 0 || base <= 0) return base;
        if (WeaponStatCurves.supports(id)) return WeaponStatCurves.reloadTicks(id, base, bonus, 1);
        return WeaponStatCurves.scale(base, Math.clamp(1 - bonus * 0.004, 0.6, 1.5));
    }
    public static WeaponReloadPolicy.Plan plan(ServerPlayer p, WeaponCatalog.Entry entry, WeaponReloadPolicy.Plan plan) {
        var stack = held(p);
        if (WeaponItems.entry(stack).filter(entry::equals).isEmpty()) return plan;
        int bonus = stat(stack, "reload");
        if (bonus == 0) return plan;
        return new WeaponReloadPolicy.Plan(reload(entry.id(), plan.firstTicks(), bonus),
                reload(entry.id(), plan.intervalTicks(), bonus), plan.roundsPerInsert());
    }
}
