package kim.biryeong.destiny.weapon;

import com.google.gson.*;
import java.io.IOException;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.*;

/** Exact base AJ membership and pinned historical handling curves. Runtime kill attribution is master-owned.
 * Static initialization reads JSON and constructs Roll records without calling the catalog/perk registry.
 */
public final class AdrenalineJunkieProfile {
    public static final String ID = "adrenaline_junkie";
    public static final long HASH = 11612903L;
    private static final String RESOURCE = "/destiny/weapons/w173-adrenaline-junkie.json";
    /** supported=false means no handling override: all tick fields are null (Goldtusk).
     * adsSupported=false on a supported glaive plan retains W44 neutral ADS policy, not a measured curve.
     */
    public record Timing(String id, boolean supported, Integer readyTicks, Integer stowTicks,
                         Integer adsTicks, boolean adsSupported) {}
    public record Perk(String id, long hash, int durationTicks, int maxStacks, int weaponKillStacks,
                       int grenadeKillStacks, boolean grenadeKillsWorkStowed, int handlingBonus,
                       List<Float> damageMultipliers) {
        public Perk { damageMultipliers = List.copyOf(damageMultipliers); }
    }
    private record Quadratic(double evpp, double vpp, double offset) {
        double seconds(int stat) { return evpp * stat * stat + vpp * stat + offset; }
    }
    private record Curve(String id, boolean supported, Integer baseHandlingStat, boolean neutralAds,
                         Quadratic ready, Quadratic stow, Quadratic ads) {}
    private record Source(long hash, boolean exotic, Integer handling, boolean handlingSupported,
                          Integer readyTicks, Integer stowTicks, int adsTicks, JsonObject catalog) {}
    private record Data(String stage, Perk perk, JsonObject policies, WeaponPerks.Roll[] weapons,
                        JsonObject[] curves, JsonObject[] timings, JsonArray snapshotADS) {}
    private static final Gson GSON = new GsonBuilder().serializeNulls().create();
    private static final Set<WeaponPerks.Roll> EXPECTED = Set.of(
        new WeaponPerks.Roll("ammit_ar2", 2119346509L, 4, HASH, 560115158L),
        new WeaponPerks.Roll("long_arm", 8293111L, 4, HASH, 619833418L),
        new WeaponPerks.Roll("farewell", 541188001L, 4, HASH, 3819615926L),
        new WeaponPerks.Roll("goldtusk", 3371413057L, 4, HASH, 700250835L),
        new WeaponPerks.Roll("nezarec_s_whisper", 254636484L, 4, HASH, 699056095L));
    private static final JsonObject PERK = JsonParser.parseString("""
{
  "id": "adrenaline_junkie",
  "hash": 11612903,
  "durationTicks": 90,
  "maxStacks": 5,
  "weaponKillStacks": 1,
  "grenadeKillStacks": 5,
  "grenadeKillsWorkStowed": true,
  "handlingBonus": 20,
  "damageMultipliers": [
    1.067,
    1.133,
    1.2,
    1.266,
    1.333
  ]
}
        """).getAsJsonObject();
    private static final JsonObject POLICIES = JsonParser.parseString("""
{
  "statCap": 100,
  "durationMultiplier": 1.0,
  "rounding": "CEIL_SECONDS_TIMES_20_ONCE",
  "adsBounds": "CLAMP_TICKS_2_20_W44",
  "glaiveAds": "W44_UNSUPPORTED_NEUTRAL_2_TICKS_ZERO_ORACLE_CURVE",
  "swordHandling": "UNSUPPORTED_NO_OFFICIAL_HANDLING_STAT_OR_ORACLE_CURVE_NULL_TIMINGS_DAMAGE_ELIGIBLE",
  "handlingBounds": "W58_NO_EXTRA_TICK_CLAMP_STOW_AT_100_FLOOR",
  "reload": "NO_BONUS_NO_RELOAD_CURVE_OR_TIMING_OVERRIDE",
  "sourceDamageAttribution": "MASTER_OWNED_LOCAL_POLICY",
  "cycleIntegration": "MASTER_OWNED_LOCAL_POLICY",
  "snapshotComposition": "W68_ENTRY_SCALAR_AFTER_AJ_HANDLING20_BEFORE_SINGLE_CEIL_CLAMP1_20_EXACT_INTERSECTION_EMPTY"
}
        """).getAsJsonObject();
    private static final Map<String, Source> SOURCES = selectedJson();
    private static final Data DATA = load();
    private static final Map<String, Timing> TIMINGS = index();
    private AdrenalineJunkieProfile() {}

    private static void check(boolean condition, String detail) {
        if (!condition) throw new IllegalStateException("Invalid W173 Adrenaline Junkie profile: " + detail);
    }
    private static JsonElement read(String path) {
        var stream = AdrenalineJunkieProfile.class.getResourceAsStream(path);
        check(stream != null, "missing resource " + path);
        try (var reader = new InputStreamReader(stream, StandardCharsets.UTF_8)) {
            return JsonParser.parseReader(reader);
        } catch (IOException | JsonParseException e) {
            throw new IllegalStateException("Cannot read W173 source " + path, e);
        }
    }
    private static Map<String, JsonObject> byId(String path) {
        var result = new HashMap<String, JsonObject>();
        for (var e : read(path).getAsJsonArray()) {
            var row = e.getAsJsonObject();
            check(result.putIfAbsent(row.get("id").getAsString(), row) == null, "duplicate source ID");
        }
        return result;
    }
    private static Integer nullableInt(JsonObject row, String name) {
        return row.get(name).isJsonNull() ? null : row.get(name).getAsInt();
    }
    private static Map<String, Source> selectedJson() {
        var catalog = byId("/destiny/weapons/w30.json");
        var stats = byId("/destiny/weapons/w40-characteristics.json");
        var handling = byId("/destiny/weapons/w58-handling.json");
        var aim = byId("/destiny/weapons/w44-aim.json");
        check(stats.size() == 63 && stats.keySet().equals(catalog.keySet())
            && stats.keySet().equals(handling.keySet()) && stats.keySet().equals(aim.keySet()), "source coverage");
        var result = new HashMap<String, Source>();
        for (var roll : EXPECTED) {
            var row = stats.get(roll.id());
            var s = row.getAsJsonObject("stats");
            var h = handling.get(roll.id()).getAsJsonObject("profile");
            Integer stat = s.has("943549884") ? s.get("943549884").getAsInt() : null;
            boolean sword = "sword".equals(catalog.get(roll.id()).get("family").getAsString());
            check(h.get("supported").getAsBoolean() == !sword && (stat == null) == sword,
                "sword remains eligible with no invented handling stat");
            result.put(roll.id(), new Source(row.get("bungieHash").getAsLong(), row.get("exotic").getAsBoolean(),
                stat, !sword, nullableInt(h, "readyTicks"), nullableInt(h, "stowTicks"),
                aim.get(roll.id()).getAsJsonObject("profile").get("transitionTicks").getAsInt(), catalog.get(roll.id())));
        }
        return Map.copyOf(result);
    }
    private static Data load() {
        var root = read(RESOURCE).getAsJsonObject();
        validate(root);
        return GSON.fromJson(root, Data.class);
    }
    /** Pure malformed-resource validation; no mutation of the loaded profile. */
    static void validateResource(String json) {
        try { validate(JsonParser.parseString(json).getAsJsonObject()); }
        catch (RuntimeException e) { throw new IllegalStateException("Invalid W173 Adrenaline Junkie JSON", e); }
    }
    private static Curve expectedCurve(String id) {
        return switch (id) {
            case "ammit_ar2" -> new Curve(id, true, 46, false,
                new Quadratic(0.0, -0.00279338, 0.51985381),
                new Quadratic(0.0, -0.00268436, 0.48414822),
                new Quadratic(0.0, -0.001875, 0.38975));
            case "long_arm" -> new Curve(id, true, 53, false,
                new Quadratic(0.0, -0.00285336856, 0.540561867),
                new Quadratic(0.0, -0.002941215324, 0.527217745),
                new Quadratic(0.0, -0.001693527081, 0.4114236019));
            case "farewell" -> new Curve(id, true, 64, false,
                new Quadratic(0.0, -0.00264010989, 0.4232582418),
                new Quadratic(0.0, -0.00197527473, 0.4298956044),
                new Quadratic(0.0, -0.0022293956, 0.3435796703));
            case "goldtusk" -> new Curve(id, false, null, false, null, null, null);
            case "nezarec_s_whisper" -> new Curve(id, true, 42, true,
                new Quadratic(0.0, -0.002139219, 0.42369),
                new Quadratic(0.0, -0.002827674, 0.5147),
                new Quadratic(0.0, -0.0, 0.0));
            default -> throw new IllegalStateException("Unreviewed AJ weapon " + id);
        };
    }
    static int effectiveStat(int base) { return (int) Math.clamp((long) base + 20L, 0L, 100L); }
    static int durationTicks(double seconds, boolean ads) {
        check(Double.isFinite(seconds) && seconds > 0 && seconds <= 60, "finite positive bounded seconds");
        int ticks = (int) Math.ceil(seconds * 20);
        return ads ? Math.clamp(ticks, 2, 20) : ticks;
    }
    /** W68 order for any future reviewed co-selection; current official intersection is empty. */
    static int snapshotDurationTicks(double seconds, double scalar) {
        check(Double.isFinite(seconds) && seconds > 0 && seconds <= 60, "finite Snapshot ADS seconds");
        check(scalar == .5 || scalar == .8, "W68 measured primary/special scalar only");
        return Math.clamp((int) Math.ceil(seconds * scalar * 20), 1, 20);
    }
    private static Timing calculate(Curve c, boolean active) {
        if (!c.supported) return new Timing(c.id, false, null, null, null, false);
        int handling = active ? effectiveStat(c.baseHandlingStat) : c.baseHandlingStat;
        double ads = c.ads.seconds(handling);
        check(!c.neutralAds || ads == 0, "glaive zero ADS evidence");
        return new Timing(c.id, true, durationTicks(c.ready.seconds(handling), false),
            durationTicks(Math.max(c.stow.seconds(handling), c.stow.seconds(100)), false),
            c.neutralAds ? 2 : durationTicks(ads, true), !c.neutralAds);
    }
    private static void validate(JsonObject root) {
        check(root.keySet().equals(Set.of("stage", "perk", "policies", "weapons", "curves", "timings", "snapshotADS")),
            "exact resource fields; no reload override");
        check("W173".equals(root.get("stage").getAsString()), "stage");
        check(PERK.equals(root.get("perk")), "exact pinned Clarity mechanics");
        check(POLICIES.equals(root.get("policies")), "source mechanics and local bounds");
        var data = GSON.fromJson(root, Data.class);
        check(data.weapons != null && data.weapons.length == EXPECTED.size(), "exact five sockets");
        var rolls = new HashSet<WeaponPerks.Roll>();
        var ids = new HashSet<String>();
        for (int n = 0; n < data.weapons.length; n++) {
            var roll = data.weapons[n];
            check(roll != null && EXPECTED.contains(roll) && rolls.add(roll) && ids.add(roll.id()), "exact base membership");
            check(GSON.toJsonTree(roll).equals(root.getAsJsonArray("weapons").get(n)), "exact roll fields");
            var source = SOURCES.get(roll.id());
            check(source != null && source.hash == roll.hash() && !source.exotic, "official base identity");
        }
        check(rolls.equals(EXPECTED), "complete membership");
        check(data.curves != null && data.curves.length == EXPECTED.size(), "five explicit curve policies");
        var curves = new HashMap<String, Curve>();
        for (var raw : data.curves) {
            check(raw != null, "non-null curve policy");
            var c = GSON.fromJson(raw, Curve.class);
            check(c != null && ids.contains(c.id) && curves.putIfAbsent(c.id, c) == null, "unique eligible curve");
            check(expectedCurve(c.id).equals(c), "pinned coefficients and official handling");
            var expectedRaw = GSON.toJsonTree(c).getAsJsonObject();
            // Oracle linear curves omit the zero quadratic coefficient. Missing any other field is invalid.
            if (c.supported) for (var field : List.of("ready", "stow", "ads"))
                expectedRaw.getAsJsonObject(field).remove("evpp");
            check(expectedRaw.equals(raw), "exact curve schema; no reload or fabricated sword curve");
            var source = SOURCES.get(c.id);
            check(Objects.equals(c.baseHandlingStat, source.handling) && c.supported == source.handlingSupported,
                "physical handling stat and support policy");
            check(c.neutralAds == "glaive".equals(source.catalog.get("family").getAsString()), "W44 neutral glaive ADS");
            var base = calculate(c, false);
            check(Objects.equals(base.readyTicks, source.readyTicks) && Objects.equals(base.stowTicks, source.stowTicks)
                && (!c.supported || base.adsTicks == source.adsTicks), "reproduced handling and ADS baselines");
        }
        check(data.timings != null && data.timings.length == EXPECTED.size(), "five plans including unsupported sword");
        var keys = new HashSet<String>();
        for (var raw : data.timings) {
            check(raw != null, "non-null timing");
            var row = GSON.fromJson(raw, Timing.class);
            check(row != null && ids.contains(row.id) && keys.add(row.id), "unique eligible plan");
            var c = curves.get(row.id);
            check(GSON.toJsonTree(calculate(c, true)).equals(raw), "exact single-ceil timing and unsupported policy");
            if (c.supported) {
                var base = calculate(c, false);
                check(row.readyTicks <= base.readyTicks && row.stowTicks <= base.stowTicks
                    && row.adsTicks <= base.adsTicks, "handling bonus cannot slow baseline");
            }
        }
        check(data.snapshotADS != null && data.snapshotADS.isEmpty(), "official AJ/Snapshot intersection is empty");
        var w68 = read("/destiny/weapons/w68-snapshot.json").getAsJsonObject();
        check(w68.get("perkHash").getAsLong() == 957782887L
            && w68.get("primaryScalar").getAsDouble() == .5 && w68.get("specialScalar").getAsDouble() == .8,
            "W68 scalar policy");
        for (var e : w68.getAsJsonArray("rolls"))
            check(!ids.contains(e.getAsJsonObject().get("id").getAsString()), "no W68 co-eligible AJ roll");
    }
    private static Map<String, Timing> index() {
        var result = new HashMap<String, Timing>();
        for (var row : DATA.timings) {
            var timing = GSON.fromJson(row, Timing.class);
            result.put(timing.id, timing);
        }
        return Map.copyOf(result);
    }
    public static List<WeaponPerks.Roll> rolls() { return List.of(DATA.weapons); }
    public static Perk perk() { return DATA.perk; }
    public static int durationTicks() { return DATA.perk.durationTicks; }
    public static int handlingBonus() { return DATA.perk.handlingBonus; }
    public static float damageMultiplier(int stacks) {
        return stacks <= 0 ? 1.0f : DATA.perk.damageMultipliers.get(Math.min(stacks, 5) - 1);
    }
    /** Damage eligibility includes Goldtusk even though its handling plan is unsupported. */
    public static boolean supports(String id) { return id != null && SOURCES.containsKey(id); }
    /** Compare every canonical catalog field without calling outer catalog/perk registries. */
    public static boolean supports(WeaponCatalog.Entry entry) {
        if (entry == null || !supports(entry.id())) return false;
        var row = SOURCES.get(entry.id()).catalog;
        return Objects.equals(entry.family(), row.get("family").getAsString())
            && Objects.equals(entry.frame(), row.get("frame").getAsString())
            && Objects.equals(entry.name(), row.get("name").getAsString())
            && Objects.equals(entry.source_frame_label(), row.get("source_frame_label").getAsString())
            && Objects.equals(entry.item_model(), row.get("item_model").getAsString());
    }
    public static Timing timing(WeaponCatalog.Entry entry) {
        if (!supports(entry)) throw new IllegalArgumentException("No AJ timing for unsupported/noncanonical entry");
        return TIMINGS.get(entry.id());
    }
    /** Snapshot can only compose on officially co-eligible distinct sockets. Current intersection is empty.
     * Glaive false returns W44 neutral2ticks. Sword has no timing override and throws explicitly.
     */
    public static int adsTicks(WeaponCatalog.Entry entry, boolean snapshotSelected) {
        var active = timing(entry);
        if (snapshotSelected) throw new IllegalArgumentException("No official distinct-socket AJ/Snapshot selection for " + entry.id());
        if (!active.supported) throw new UnsupportedOperationException("No AJ sword handling/ADS curve for " + entry.id());
        return active.adsTicks;
    }
}
