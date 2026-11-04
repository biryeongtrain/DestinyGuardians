package kim.biryeong.destiny.weapon;

import com.google.gson.*;
import java.io.IOException;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.*;

/** Exact base Stats for All sockets and pinned historical stat curves.
 * Bonus/scalar arguments are caller TOTALS including SFA: never add +35 or multiply .95 here.
 * Initialization reads JSON directly; no outer catalog, characteristics or perk-registry calls.
 * See art/weapons/w176/stats-for-all for source proofs and explicit local composition policies.
 */
public final class StatsForAllProfile {
    public static final String ID = "stats_for_all";
    public static final long HASH = 1583705720L;
    private static final String RESOURCE = "/destiny/weapons/w176-stats-for-all.json";
    private record Quadratic(double evpp, double vpp, double offset) {
        double seconds(int stat) { return evpp * stat * stat + vpp * stat + offset; }
    }
    private record Hip(double offsetStart, double vppStart, double offsetEnd, double vppEnd,
                       double floor, double precision) {}
    private record Curve(String id, int baseReloadStat, int baseHandlingStat, Integer baseRangeStat,
                         Hip ballistics, Quadratic reload, Quadratic ready, Quadratic stow, Quadratic ads) {}
    private record Data(List<WeaponPerks.Roll> rolls, Map<String, Curve> curves) {}
    private static final Gson GSON = new Gson();
    private static final List<WeaponPerks.Roll> EXPECTED = List.of(
        new WeaponPerks.Roll("ammit_ar2", 2119346509L, 3, HASH, 1723759242L),
        new WeaponPerks.Roll("aishas_embrace", 2638190703L, 3, HASH, 7997267L),
        new WeaponPerks.Roll("dimensional_hypotrochoid", 1311684613L, 3, HASH, 3235863202L),
        new WeaponPerks.Roll("retrofit_escapade", 3103325054L, 3, HASH, 3756086698L));
    private static final JsonObject PERK = JsonParser.parseString("""
{
  "id": "stats_for_all",
  "hash": 1583705720,
  "hitWindowTicks": 60,
  "durationTicks": 200,
  "handlingBonus": 35,
  "reloadBonus": 35,
  "stabilityBonus": 10,
  "rangeBonus": 10,
  "falloffScalar": 1.05,
  "reloadScalar": 0.95,
  "refresh": false
}
        """).getAsJsonObject();
    private static final JsonObject POLICIES = JsonParser.parseString("""
{
  "statCap": 100,
  "rounding": "CEIL_SECONDS_TIMES_20_ONCE",
  "bonusInputs": "TOTALS_INCLUDE_SFA_DO_NOT_ADD_35_AGAIN",
  "reloadScalarInput": "TOTAL_PRODUCT_INCLUDES_SFA_0_95_ONCE",
  "handling": "W58_STOW_AT100_FLOOR_NO_EXTRA_CLAMP",
  "ads": "W44_CLAMP_2_20_NO_COMPATIBLE_SNAPSHOT_ON_THESE_FOUR",
  "ballistics": "W43_HIP_RANGE_PLUS10_CAP100_THEN_1_05_BOTH_ENDPOINTS_MASTER_ADS_AFTER",
  "explosive": "RANGE_INDEPENDENT_SENTINEL_NEUTRAL_NO_TRAVEL_OR_BLAST_INVENTION",
  "collection": "NEW_DISTINCT_TARGET_RENEWS60_DUPLICATE_NO_EXTEND_NO_COLLECTION_WHILE_ACTIVE",
  "expiry": "INCLUSIVE_DEADLINE_EXPIRED_QUERIES_PURE",
  "stowReload": "LOCAL_PRESERVE_DEADLINES_TIME_CONTINUES_NOT_SOURCE_PROVEN",
  "lifecycle": "MASTER_IDENTITY_SESSIONS_ATTRIBUTION_LOCAL_POLICY"
}
        """).getAsJsonObject();
    private static final Map<String, JsonObject> CATALOG = byId("/destiny/weapons/w30.json");
    private static final Data DATA = load();
    private StatsForAllProfile() {}

    private static void check(boolean condition, String detail) {
        if (!condition) throw new IllegalStateException("Invalid W176 Stats for All profile: " + detail);
    }
    private static JsonElement read(String path) {
        var stream = StatsForAllProfile.class.getResourceAsStream(path);
        check(stream != null, "missing resource " + path);
        try (var reader = new InputStreamReader(stream, StandardCharsets.UTF_8)) {
            return JsonParser.parseReader(reader);
        } catch (IOException | JsonParseException e) {
            throw new IllegalStateException("Cannot read W176 source " + path, e);
        }
    }
    private static Map<String, JsonObject> byId(String path) {
        var result = new HashMap<String, JsonObject>();
        for (var element : read(path).getAsJsonArray()) {
            var row = element.getAsJsonObject();
            check(result.putIfAbsent(row.get("id").getAsString(), row) == null, "duplicate source ID");
        }
        return Map.copyOf(result);
    }
    private static Curve expectedCurve(String id) {
        return switch (id) {
            case "ammit_ar2" -> new Curve(id, 38, 46, 61,
                new Hip(10.75, 0.125, 40.0, 0.0, 0.5, 1.5588235294117647),
                new Quadratic(8.55689e-05, -0.0242021, 2.80673006666667),
                new Quadratic(0.0, -0.00279338, 0.51985381),
                new Quadratic(0.0, -0.00268436, 0.48414822),
                new Quadratic(0.0, -0.001875, 0.38975));
            case "aishas_embrace" -> new Curve(id, 35, 26, 34,
                new Hip(30.25, 0.1568, 60.75, 0.0, 0.5, 1.696078431372549),
                new Quadratic(0.000102915, -0.0276889, 3.11797356666666),
                new Quadratic(0.0, -0.00285336856, 0.540561867),
                new Quadratic(0.0, -0.002941215324, 0.527217745),
                new Quadratic(0.0, -0.001693527081, 0.4114236019));
            case "dimensional_hypotrochoid" -> new Curve(id, 42, 42, null,
                new Hip(999.0, 0.0, 999.9, 0.0, 0.999, 1.0),
                new Quadratic(7.55233e-05, -0.0248947, 4.12880153333333),
                new Quadratic(0.0, -0.00272791, 0.55133684),
                new Quadratic(0.0, -0.00232786, 0.48726765),
                new Quadratic(0.0, -0.00187072, 0.50019128));
            case "retrofit_escapade" -> new Curve(id, 67, 56, 23,
                new Hip(28.5, 0.0223, 38.2, 0.0, 0.5, 1.303921568627451),
                new Quadratic(9.05351e-05, -0.0305819, 6.1219905),
                new Quadratic(0.0, -0.002391721353, 0.4950499748),
                new Quadratic(0.0, -0.002041393236, 0.4547501262),
                new Quadratic(0.0, -0.001234477537, 0.4574687027));
            default -> throw new IllegalStateException("Unreviewed SFA curve " + id);
        };
    }
    private static Data validate(JsonObject root) {
        check(root.keySet().equals(Set.of("stage", "perk", "policies", "weapons", "curves"))
            && root.get("stage").equals(new JsonPrimitive("W176"))
            && root.get("perk").equals(PERK) && root.get("policies").equals(POLICIES), "schema/mechanics/policies");
        var rolls = new ArrayList<WeaponPerks.Roll>();
        var weapons = root.getAsJsonArray("weapons");
        check(weapons.size() == EXPECTED.size(), "roll coverage");
        for (var row : weapons) {
            var roll = GSON.fromJson(row, WeaponPerks.Roll.class);
            check(EXPECTED.contains(roll) && row.equals(GSON.toJsonTree(roll)) && !rolls.contains(roll),
                "exact unique base socket identity");
            rolls.add(roll);
        }
        var curves = new HashMap<String, Curve>();
        check(root.getAsJsonArray("curves").size() == EXPECTED.size(), "curve coverage");
        for (var row : root.getAsJsonArray("curves")) {
            var curve = GSON.fromJson(row, Curve.class);
            var expected = expectedCurve(curve.id);
            // serializeNulls is needed only for the range-independent explosive's absent Range.
            var canonical = new GsonBuilder().serializeNulls().create().toJsonTree(expected);
            check(row.equals(canonical) && curve.equals(expected)
                && curves.putIfAbsent(curve.id, curve) == null, "pinned unique curve/stats/hip fields");
        }
        check(curves.keySet().equals(EXPECTED.stream().map(WeaponPerks.Roll::id).collect(java.util.stream.Collectors.toSet())),
            "exact curve IDs");
        return new Data(List.copyOf(rolls), Map.copyOf(curves));
    }
    /** Malformed-resource tests use the same fail-closed validator; loaded data is never mutated. */
    static void validateResource(String json) {
        try { validate(JsonParser.parseString(json).getAsJsonObject()); }
        catch (RuntimeException e) { throw new IllegalStateException("Invalid W176 Stats for All JSON", e); }
    }
    private static Data load() {
        var result = validate(read(RESOURCE).getAsJsonObject());
        var stats = byId("/destiny/weapons/w40-characteristics.json");
        var reloads = byId("/destiny/weapons/w46-timing.json");
        var handling = byId("/destiny/weapons/w58-handling.json");
        var aim = byId("/destiny/weapons/w44-aim.json");
        var hip = byId("/destiny/weapons/w43-ballistics.json");
        for (var roll : result.rolls) {
            var c = result.curves.get(roll.id());
            var w = stats.get(roll.id());
            var s = w.getAsJsonObject("stats");
            check(w.get("bungieHash").getAsLong() == roll.hash() && !w.get("exotic").getAsBoolean()
                && s.get("4188031367").getAsInt() == c.baseReloadStat
                && s.get("943549884").getAsInt() == c.baseHandlingStat
                && (c.baseRangeStat == null ? !s.has("1240592695")
                    : s.get("1240592695").getAsInt() == c.baseRangeStat), "official stat identity");
            var t = reloads.get(roll.id()).getAsJsonObject("timing");
            var h = handling.get(roll.id()).getAsJsonObject("profile");
            check(t.get("supported").getAsBoolean() && h.get("supported").getAsBoolean()
                && !t.get("shellReload").getAsBoolean() && t.get("reloadPerRoundTicks").isJsonNull()
                && t.get("reloadInitialTicks").isJsonNull(), "whole magazine topology");
            check(quantize(c.reload.seconds(c.baseReloadStat)) == t.get("reloadTicks").getAsInt()
                && quantize(c.ready.seconds(c.baseHandlingStat)) == h.get("readyTicks").getAsInt()
                && quantize(Math.max(c.stow.seconds(c.baseHandlingStat), c.stow.seconds(100))) == h.get("stowTicks").getAsInt()
                && Math.clamp(quantize(c.ads.seconds(c.baseHandlingStat)), 2, 20)
                    == aim.get(roll.id()).getAsJsonObject("profile").get("transitionTicks").getAsInt(),
                "reproduce all four W46/W58/W44 baselines");
            var b = hip.get(roll.id()).deepCopy();
            b.remove("id");
            check(b.equals(GSON.toJsonTree(c.ballistics)) && CATALOG.containsKey(roll.id()), "W43 hip/catalog identity");
        }
        return result;
    }
    /** Wide addition prevents overflow before the official 0..100 cap. */
    static int effectiveStat(int base, int totalBonus) {
        return (int) Math.clamp((long) base + totalBonus, 0L, 100L);
    }
    private static int quantize(double seconds) {
        check(Double.isFinite(seconds) && seconds > 0 && seconds <= 60, "unsafe seconds");
        return Math.max(1, (int) Math.ceil(seconds * 20));
    }
    public static List<WeaponPerks.Roll> rolls() { return DATA.rolls; }
    public static int hitWindowTicks() { return 60; }
    public static int durationTicks() { return 200; }
    public static int handlingBonus() { return 35; }
    public static int reloadBonus() { return 35; }
    public static int stabilityBonus() { return 10; }
    public static int rangeBonus() { return 10; }
    public static double reloadScalar() { return .95; }
    public static double falloffScalar() { return 1.05; }

    /** Compare every canonical catalog field without calling any outer registry. */
    public static boolean supports(WeaponCatalog.Entry entry) {
        if (entry == null || entry.id() == null || !DATA.curves.containsKey(entry.id())) return false;
        var row = CATALOG.get(entry.id());
        return Objects.equals(entry.family(), row.get("family").getAsString())
            && Objects.equals(entry.frame(), row.get("frame").getAsString())
            && Objects.equals(entry.name(), row.get("name").getAsString())
            && Objects.equals(entry.source_frame_label(), row.get("source_frame_label").getAsString())
            && Objects.equals(entry.item_model(), row.get("item_model").getAsString());
    }
    private static Curve curve(WeaponCatalog.Entry entry) {
        if (!supports(entry)) throw new IllegalArgumentException("No SFA profile for unsupported/noncanonical entry");
        return DATA.curves.get(entry.id());
    }
    /** totalBonus already includes SFA and any compatible active trait, e.g. AJ +20 at ANY stack.
     * Evaluate raw W58 seconds at clamp(base+total,0,100), retaining stow-at100 floor; ceil once.
     */
    public static int handlingTicks(WeaponCatalog.Entry entry, int totalBonus, boolean ready) {
        var c = curve(entry);
        int stat = effectiveStat(c.baseHandlingStat, totalBonus);
        return quantize(ready ? c.ready.seconds(stat) : Math.max(c.stow.seconds(stat), c.stow.seconds(100)));
    }
    /** Ordinary entry/exit uses false. None of these four can select Snapshot, so true is rejected.
     * No fabricated Heavy Snapshot scalar. W44's ordinary 2..20 bound applies after one ceil.
     */
    public static int adsTicks(WeaponCatalog.Entry entry, int totalHandlingBonus, boolean snapshotEntering) {
        var c = curve(entry);
        if (snapshotEntering) throw new IllegalArgumentException("No compatible SFA/Snapshot sockets on selected4");
        return Math.clamp(quantize(c.ads.seconds(effectiveStat(c.baseHandlingStat, totalHandlingBonus))), 2, 20);
    }
    /** totalReloadBonus and totalScalar already include SFA (+35 and .95).
     * Retrofit Frenzy+SFA passes135,.95: clamp before evaluating, multiply raw seconds, ceil ONCE.
     * Master validates co-selection; this pure arithmetic API accepts any total int bonus.
     */
    public static int reloadTicks(WeaponCatalog.Entry entry, int totalReloadBonus, double totalScalar) {
        var c = curve(entry);
        if (!Double.isFinite(totalScalar) || totalScalar <= 0 || totalScalar > 1)
            throw new IllegalArgumentException("SFA total reload scalar must be finite in (0,1]");
        double seconds = c.reload.seconds(effectiveStat(c.baseReloadStat, totalReloadBonus)) * totalScalar;
        // Positive subnormal scalar products can underflow: retain the minimum one-tick deadline.
        return seconds == 0 ? 1 : quantize(seconds);
    }
    /** Active hip curve: +10 Range capped100, then1.05 falloff on BOTH endpoints.
     * Master applies W44 ADS distance scalar afterward. Floor and precision are untouched.
     * The explosive no-Range sentinel stays neutral; never invent travel distance or blast radius.
     */
    public static WeaponBallistics.Profile ballistics(WeaponCatalog.Entry entry) {
        var c = curve(entry);
        var b = c.ballistics;
        if (c.baseRangeStat == null) return new WeaponBallistics.Profile(b.offsetStart, b.offsetEnd, b.floor, b.precision);
        int stat = effectiveStat(c.baseRangeStat, 10);
        return new WeaponBallistics.Profile((b.offsetStart + b.vppStart * stat) * 1.05,
            (b.offsetEnd + b.vppEnd * stat) * 1.05, b.floor, b.precision);
    }
}
