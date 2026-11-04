package kim.biryeong.destiny.weapon;

import com.google.gson.*;
import java.io.IOException;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.*;

/** Exact base sockets and stat-based historical timings. Movement lifecycle is master-owned.
 * Static loading reads JSON only; it must never initialize the perk/catalog registries.
 */
public final class PerpetualMotionProfile {
    public static final String ID = "perpetual_motion";
    public static final long HASH = 1428297954L;
    private static final String RESOURCE = "/destiny/weapons/w170-perpetual-motion.json";
    public record Timing(String id, int stacks, int reloadTicks, int readyTicks, int stowTicks,
                         int adsTicks, int stabilityBonus, int handlingBonus, int reloadBonus) {}
    public record Perk(String id, long hash, double minSpeed, int firstStackTicks,
                       int secondStackTicks, int stopGraceTicks, int maxStacks, boolean worksStowed) {}
    private record Quadratic(double evpp, double vpp, double offset) {
        double seconds(int stat) { return evpp * stat * stat + vpp * stat + offset; }
    }
    private record Curve(String id, int baseReloadStat, int baseHandlingStat, int baseStabilityStat,
                         Quadratic reload, Quadratic ready, Quadratic stow, Quadratic ads) {}
    private record Data(String stage, Perk perk, JsonObject policies, WeaponPerks.Roll[] weapons,
                        Curve[] curves, Timing[] timings) {}
    private record Source(long hash, boolean exotic, int reload, int handling, int stability,
                          int reloadTicks, int readyTicks, int stowTicks, int adsTicks) {}
    private static final Set<WeaponPerks.Roll> EXPECTED = Set.of(
        new WeaponPerks.Roll("aishas_embrace", 2638190703L, 3, HASH, 7997267L),
        new WeaponPerks.Roll("retraced_path", 548958835L, 3, HASH, 2945646047L));
    private static final JsonObject POLICIES = JsonParser.parseString("""
        {
          "statCap": 100,
          "durationMultiplier": 1.0,
          "rounding": "CEIL_SECONDS_TIMES_20_ONCE",
          "adsBounds": "CLAMP_TICKS_2_20_W44",
          "handlingBounds": "W58_NO_EXTRA_TICK_CLAMP_STOW_AT_100_FLOOR",
          "sourceMovementSampling": "UNKNOWN_MASTER_OWNED_LOCAL_POLICY",
          "sourceDiscontinuities": "UNKNOWN_MASTER_OWNED_LOCAL_POLICY",
          "sourceBriefPauseProgress": "UNKNOWN_MASTER_OWNED_LOCAL_POLICY",
          "sourceCombinedPerks": "UNKNOWN_MASTER_OWNED_LOCAL_POLICY",
          "stabilityIntegration": "MINECRAFT_CURVE_MASTER_OWNED_LOCAL_POLICY"
        }
        """).getAsJsonObject();
    private static final Map<String, Source> SOURCES = selectedJson();
    private static final Data DATA = load();
    private static final Map<String, Timing> TIMINGS = index();
    private PerpetualMotionProfile() {}

    private static void check(boolean condition, String detail) {
        if (!condition) throw new IllegalStateException("Invalid W170 Perpetual Motion profile: " + detail);
    }
    private static JsonElement read(String path) {
        var stream = PerpetualMotionProfile.class.getResourceAsStream(path);
        check(stream != null, "missing resource " + path);
        try (var reader = new InputStreamReader(stream, StandardCharsets.UTF_8)) {
            return JsonParser.parseReader(reader);
        } catch (IOException | JsonParseException e) {
            throw new IllegalStateException("Cannot read W170 Perpetual Motion source " + path, e);
        }
    }
    private static Map<String, JsonObject> byId(String path) {
        var result = new HashMap<String, JsonObject>();
        for (var element : read(path).getAsJsonArray()) {
            var row = element.getAsJsonObject();
            check(result.putIfAbsent(row.get("id").getAsString(), row) == null, "duplicate source ID");
        }
        return result;
    }
    // Sources are read directly to avoid catalog -> perk profile -> catalog initialization recursion.
    private static Map<String, Source> selectedJson() {
        var stats = byId("/destiny/weapons/w40-characteristics.json");
        var reloads = byId("/destiny/weapons/w46-timing.json");
        var handling = byId("/destiny/weapons/w58-handling.json");
        var aim = byId("/destiny/weapons/w44-aim.json");
        check(stats.size() == 63 && stats.keySet().equals(reloads.keySet())
            && stats.keySet().equals(handling.keySet()) && stats.keySet().equals(aim.keySet()), "source coverage");
        var result = new HashMap<String, Source>();
        for (var roll : EXPECTED) {
            var row = stats.get(roll.id());
            var s = row.getAsJsonObject("stats");
            var t = reloads.get(roll.id()).getAsJsonObject("timing");
            var h = handling.get(roll.id()).getAsJsonObject("profile");
            check(t.get("supported").getAsBoolean() && h.get("supported").getAsBoolean()
                && !t.get("shellReload").getAsBoolean() && t.get("reloadInitialTicks").isJsonNull(), "supported whole magazine");
            result.put(roll.id(), new Source(row.get("bungieHash").getAsLong(), row.get("exotic").getAsBoolean(),
                s.get("4188031367").getAsInt(), s.get("943549884").getAsInt(), s.get("155624089").getAsInt(),
                t.get("reloadTicks").getAsInt(), h.get("readyTicks").getAsInt(), h.get("stowTicks").getAsInt(),
                aim.get(roll.id()).getAsJsonObject("profile").get("transitionTicks").getAsInt()));
        }
        return Map.copyOf(result);
    }
    private static Data load() {
        var data = new Gson().fromJson(read(RESOURCE), Data.class);
        validate(data);
        return data;
    }
    /** Pure negative-resource validation; does not mutate loaded data. */
    static void validateResource(String json) {
        try {
            validate(new Gson().fromJson(json, Data.class));
        } catch (JsonParseException e) {
            throw new IllegalStateException("Invalid W170 Perpetual Motion JSON", e);
        }
    }
    private static Curve expectedCurve(String id) {
        return switch (id) {
            case "aishas_embrace" -> new Curve(id, 35, 26, 46,
                new Quadratic(0.000102915, -0.0276889, 3.11797356666666),
                new Quadratic(0.0, -0.00285336856, 0.540561867),
                new Quadratic(0.0, -0.002941215324, 0.527217745),
                new Quadratic(0.0, -0.001693527081, 0.4114236019));
            case "retraced_path" -> new Curve(id, 45, 46, 75,
                new Quadratic(5e-05, -0.0155, 2.65),
                new Quadratic(0.0, -0.00279338, 0.51985381),
                new Quadratic(0.0, -0.00268436, 0.48414822),
                new Quadratic(0.0, -0.001875, 0.38975));
            default -> throw new IllegalStateException("Unreviewed Perpetual Motion weapon " + id);
        };
    }
    static int effectiveStat(int base, int stacks) {
        return (int) Math.clamp((long) base + 10L * stacks, 0L, 100L);
    }
    static int durationTicks(double seconds, boolean ads) {
        check(Double.isFinite(seconds) && seconds > 0 && seconds <= 60, "finite positive bounded seconds");
        int ticks = (int) Math.ceil(seconds * 20);
        return ads ? Math.clamp(ticks, 2, 20) : ticks;
    }
    private static Timing calculate(Curve c, int stacks) {
        int reload = effectiveStat(c.baseReloadStat, stacks), handling = effectiveStat(c.baseHandlingStat, stacks);
        return new Timing(c.id, stacks, durationTicks(c.reload.seconds(reload), false),
            durationTicks(c.ready.seconds(handling), false),
            durationTicks(Math.max(c.stow.seconds(handling), c.stow.seconds(100)), false),
            durationTicks(c.ads.seconds(handling), true), 10 * stacks, 10 * stacks, 10 * stacks);
    }
    private static void validate(Data data) {
        check(data != null && "W170".equals(data.stage), "stage");
        check(new Perk(ID, HASH, 2.0, 40, 200, 10, 2, true).equals(data.perk), "exact sourced mechanics");
        check(POLICIES.equals(data.policies), "source unknowns/local bounds/scalar");
        check(data.weapons != null && data.weapons.length == 2, "exact two sockets");
        var rolls = new HashSet<WeaponPerks.Roll>();
        var ids = new HashSet<String>();
        for (var roll : data.weapons) {
            check(roll != null && EXPECTED.contains(roll) && rolls.add(roll) && ids.add(roll.id()), "exact base socket membership");
            var source = SOURCES.get(roll.id());
            check(source != null && source.hash == roll.hash() && !source.exotic, "official base identity");
        }
        check(rolls.equals(EXPECTED), "complete membership");
        check(data.curves != null && data.curves.length == 2, "exact two curves");
        var curves = new HashMap<String, Curve>();
        for (var c : data.curves) {
            check(c != null && ids.contains(c.id) && curves.putIfAbsent(c.id, c) == null, "unique eligible curve");
            check(expectedCurve(c.id).equals(c), "pinned coefficients and base stats");
            var s = SOURCES.get(c.id);
            check(c.baseReloadStat == s.reload && c.baseHandlingStat == s.handling
                && c.baseStabilityStat == s.stability, "official physical base stats");
            var base = calculate(c, 0);
            check(base.reloadTicks == s.reloadTicks && base.readyTicks == s.readyTicks
                && base.stowTicks == s.stowTicks && base.adsTicks == s.adsTicks, "four reproduced baselines");
        }
        check(data.timings != null && data.timings.length == 4, "exact four active plans");
        var keys = new HashSet<String>();
        for (var row : data.timings) {
            check(row != null && ids.contains(row.id) && row.stacks >= 1 && row.stacks <= 2
                && keys.add(key(row.id, row.stacks)), "unique weapon/tier");
            var c = curves.get(row.id);
            check(calculate(c, row.stacks).equals(row), "exact single-ceil timings and +10 bonuses");
            var base = calculate(c, 0);
            check(row.reloadTicks <= base.reloadTicks && row.readyTicks <= base.readyTicks
                && row.stowTicks <= base.stowTicks && row.adsTicks <= base.adsTicks, "buff cannot slow baseline");
        }
    }
    private static String key(String id, int stacks) { return id + ":" + stacks; }
    private static Map<String, Timing> index() {
        var result = new HashMap<String, Timing>();
        for (var row : DATA.timings) result.put(key(row.id, row.stacks), row);
        return Map.copyOf(result);
    }
    public static List<WeaponPerks.Roll> rolls() { return List.of(DATA.weapons); }
    public static Perk perk() { return DATA.perk; }
    public static double minSpeed() { return DATA.perk.minSpeed; }
    public static int firstStackTicks() { return DATA.perk.firstStackTicks; }
    public static int secondStackTicks() { return DATA.perk.secondStackTicks; }
    public static int stopGraceTicks() { return DATA.perk.stopGraceTicks; }
    public static int maxStacks() { return DATA.perk.maxStacks; }
    public static boolean worksStowed() { return DATA.perk.worksStowed; }

    /** Active tiers only. Reject inactive/unsupported/noncanonical entries, rather than saturating tiers. */
    public static Timing timing(WeaponCatalog.Entry entry, int count) {
        if (entry == null || count < 1 || count > 2
            || WeaponCatalog.find(entry.id()).filter(entry::equals).isEmpty())
            throw new IllegalArgumentException("Invalid Perpetual Motion entry/stacks");
        var result = TIMINGS.get(key(entry.id(), count));
        if (result == null) throw new IllegalArgumentException("No Perpetual Motion timing for " + entry.id());
        return result;
    }
}
