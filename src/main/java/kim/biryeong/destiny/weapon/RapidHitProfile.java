package kim.biryeong.destiny.weapon;

import com.google.gson.*;
import java.io.IOException;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.*;

/** Exact base Rapid Hit sockets, sourced tiers and historical W46 reload plans.
 * Lifecycle, combined-perk arithmetic and Minecraft stability integration belong to runtime.
 * Validation reads JSON directly: it must not initialize any selected registry.
 */
public final class RapidHitProfile {
    public static final String ID = "rapid_hit";
    public static final long HASH = 247725512L;
    private static final String RESOURCE = "/destiny/weapons/w169-rapid-hit.json";
    private static final int[] STABILITY = {2, 12, 14, 18, 25};
    private static final int[] BONUSES = {5, 30, 35, 42, 60};
    private static final double[] SCALARS = {.99, .96, .95, .945, .92};

    public record Reload(int firstTicks, int intervalTicks, int baseReloadStat, int effectiveReloadStat) {}
    public record Perk(String id, long hash, int durationTicks, int maxStacks,
                       String mechanicsSource, String timingSource) {}
    public record Policies(String sourceRefreshScope, String sourceExpirationMode,
                           String sourceStowPersistence, String sourceReloadConsumption,
                           String sourceReloadSnapshot, String sourceCombinedReloadPerks,
                           String hitRefresh, String expiration, String stowPersistence,
                           String reloadSnapshot, String weakenedBodyHits, String stabilityIntegration,
                           int statCap, int bowStatCap, String rounding, String bowTiming, String longArmTiming) {}
    private record Tier(int stacks, int stabilityBonus, int reloadBonus, double durationMultiplier) {}
    private record Curve(String id, double evpp, double vpp, double offset, int statCap) {
        double seconds(int stat) { return evpp * stat * stat + vpp * stat + offset; }
    }
    private record Row(String id, int stacks, int firstTicks, int intervalTicks,
                       int baseReloadStat, int effectiveReloadStat) {
        Reload reload() { return new Reload(firstTicks, intervalTicks, baseReloadStat, effectiveReloadStat); }
    }
    private record Data(String stage, Perk perk, Policies policies, Tier[] tiers,
                        WeaponPerks.Roll[] weapons, Curve[] curves, Row[] reloads) {}
    private record Source(String family, long hash, boolean exotic, int reloadStat,
                          boolean supported, boolean shellReload, Integer reloadTicks, Integer initialTicks) {}
    private static final Set<WeaponPerks.Roll> EXPECTED = Set.of(
        roll("duke_mk_44", 2112909414L, 2, 3744182842L),
        roll("patron_of_lost_causes", 2723241847L, 3, 2564227946L),
        roll("long_arm", 8293111L, 3, 3056706286L),
        roll("allied_demand", 1532276803L, 3, 3275836355L),
        roll("lonesome", 2199171672L, 3, 3612808001L),
        roll("brass_attacks", 2121785039L, 3, 100135553L),
        roll("biting_winds", 1621657423L, 3, 3968704963L),
        roll("bite_of_the_fox", 1403800851L, 3, 563442205L),
        roll("apostate", 2164448701L, 4, 2826016044L),
        roll("line_in_the_sand", 946443267L, 3, 1503774254L),
        roll("stormchaser", 3652506829L, 3, 897699284L));
    private static final Policies EXPECTED_POLICIES = new Policies(
        "UNKNOWN",
        "UNKNOWN",
        "UNKNOWN",
        "UNKNOWN",
        "UNKNOWN",
        "UNKNOWN",
        "WHOLE_WINDOW_40_TICKS_LOCAL_POLICY",
        "READ_ONLY_EXPIRE_LOCAL_POLICY",
        "SAME_IDENTITY_CLOCK_CONTINUES_LOCAL_POLICY",
        "AT_RELOAD_START_NONCONSUMING_NO_REFRESH_LOCAL_POLICY",
        "SOURCE_WEAKENED_AT_ACTUAL_IMPACT_LOCAL_MAPPING",
        "MINECRAFT_CURVE_MASTER_OWNED_LOCAL_POLICY",
        100,
        85,
        "CEIL_SECONDS_TIMES_20_ONCE",
        "HISTORICAL_W46_NOCK_ONLY_DRAW_UNCHANGED",
        "SOURCE_INSERT_UNKNOWN_LOCAL_BASE_PHASE_RATIO");
    private static final Map<String, Source> SOURCES = selectedJson();
    private static final Data DATA = load();
    private static final Map<String, Reload> RELOADS = index();

    private RapidHitProfile() {}
    private static WeaponPerks.Roll roll(String id, long hash, int socket, long pool) {
        return new WeaponPerks.Roll(id, hash, socket, HASH, pool);
    }
    private static IllegalStateException invalid(String detail) {
        return new IllegalStateException("Invalid W169 Rapid Hit profile: " + detail);
    }
    private static void check(boolean condition, String detail) {
        if (!condition) throw invalid(detail);
    }
    private static JsonElement read(String path) {
        var stream = RapidHitProfile.class.getResourceAsStream(path);
        if (stream == null) throw invalid("Missing resource " + path);
        try (var reader = new InputStreamReader(stream, StandardCharsets.UTF_8)) {
            return JsonParser.parseReader(reader);
        } catch (IOException | JsonParseException e) {
            throw new IllegalStateException("Cannot read W169 Rapid Hit source " + path, e);
        }
    }
    private static Data load() {
        var data = new Gson().fromJson(read(RESOURCE), Data.class);
        validate(data);
        return data;
    }

    /** Pure negative-resource tests. Does not mutate loaded data or call a selected registry. */
    static void validateResource(String json) {
        try {
            validate(new Gson().fromJson(json, Data.class));
        } catch (JsonParseException e) {
            throw new IllegalStateException("Invalid W169 Rapid Hit JSON", e);
        }
    }

    // JSON-only source records avoid catalog -> perk profile -> catalog initialization recursion.
    private static Map<String, JsonObject> byId(JsonArray rows) {
        var result = new HashMap<String, JsonObject>();
        for (var element : rows) {
            var row = element.getAsJsonObject();
            check(result.putIfAbsent(row.get("id").getAsString(), row) == null, "duplicate selected source ID");
        }
        return result;
    }
    private static Integer optionalInt(JsonObject object, String field) {
        return object.get(field).isJsonNull() ? null : object.get(field).getAsInt();
    }
    private static Map<String, Source> selectedJson() {
        var catalog = byId(read("/destiny/weapons/w30.json").getAsJsonArray());
        var characteristics = byId(read("/destiny/weapons/w40-characteristics.json").getAsJsonArray());
        var timings = byId(read("/destiny/weapons/w46-timing.json").getAsJsonArray());
        for (var path : List.of("/destiny/weapons/w83-exotics.json", "/destiny/weapons/w84-exotics.json")) {
            for (var element : read(path).getAsJsonArray()) {
                var row = element.getAsJsonObject();
                var c = row.getAsJsonObject("catalog");
                var m = row.getAsJsonObject("characteristics");
                var t = row.getAsJsonObject("timing");
                String id = c.get("id").getAsString();
                check(id.equals(m.get("id").getAsString()) && id.equals(t.get("id").getAsString())
                    && catalog.putIfAbsent(id, c) == null && characteristics.putIfAbsent(id, m) == null
                    && timings.putIfAbsent(id, t) == null, "unique additive selected ID");
            }
        }
        check(catalog.size() == 65 && catalog.keySet().equals(characteristics.keySet())
            && catalog.keySet().equals(timings.keySet()), "exact selected65 JSON coverage");
        var result = new HashMap<String, Source>();
        for (var id : catalog.keySet()) {
            var c = catalog.get(id);
            var m = characteristics.get(id);
            var t = timings.get(id).getAsJsonObject("timing");
            var stat = m.getAsJsonObject("stats").get("4188031367");
            result.put(id, new Source(c.get("family").getAsString(), m.get("bungieHash").getAsLong(),
                m.get("exotic").getAsBoolean(), stat == null ? -1 : stat.getAsInt(),
                t.get("supported").getAsBoolean(), t.get("shellReload").getAsBoolean(),
                optionalInt(t, "reloadTicks"), optionalInt(t, "reloadInitialTicks")));
        }
        return Map.copyOf(result);
    }

    private static void validate(Data data) {
        check(data != null && "W169".equals(data.stage), "stage");
        check(new Perk(ID, HASH, 40, 5, "art/weapons/w169/rapid-hit/clarity-source.json",
            "art/weapons/w169/rapid-hit/reload-timings.json").equals(data.perk), "exact sourced perk");
        check(EXPECTED_POLICIES.equals(data.policies), "source unknowns versus local policies");
        check(data.tiers != null && data.tiers.length == 5, "complete tiers");
        var tierNumbers = new HashSet<Integer>();
        for (var tier : data.tiers) {
            check(tier != null && tier.stacks >= 1 && tier.stacks <= 5 && tierNumbers.add(tier.stacks), "unique tier");
            int i = tier.stacks - 1;
            check(tier.stabilityBonus == STABILITY[i] && tier.reloadBonus == BONUSES[i]
                && Double.compare(tier.durationMultiplier, SCALARS[i]) == 0, "sourced tier values");
        }
        check(data.weapons != null && data.weapons.length == EXPECTED.size(), "exact socket count");
        var rolls = new HashSet<WeaponPerks.Roll>();
        var ids = new HashSet<String>();
        for (var roll : data.weapons) {
            check(roll != null && EXPECTED.contains(roll) && rolls.add(roll) && ids.add(roll.id()), "exact selected socket");
            var source = SOURCES.get(roll.id());
            check(source != null && source.hash == roll.hash() && !source.exotic, "official selected item");
        }
        check(rolls.equals(EXPECTED), "complete socket allowlist");
        check(data.curves != null && data.curves.length == ids.size(), "complete curves");
        var curves = new HashMap<String, Curve>();
        for (var curve : data.curves) {
            check(curve != null && ids.contains(curve.id) && curves.putIfAbsent(curve.id, curve) == null, "unique curve");
            check(expectedCurve(curve.id, SOURCES.get(curve.id).family).equals(curve), "pinned W46 coefficients/cap");
        }
        check(data.reloads != null && data.reloads.length == ids.size() * 5, "complete reload product");
        var plans = new HashSet<String>();
        for (var row : data.reloads) {
            check(row != null && ids.contains(row.id) && row.stacks >= 1 && row.stacks <= 5
                && plans.add(key(row.id, row.stacks)), "unique weapon/tier plan");
            var source = SOURCES.get(row.id);
            check(source.reloadStat >= 0 && source.reloadStat <= 100 && source.reloadStat == row.baseReloadStat,
                "official base reload stat");
            var curve = curves.get(row.id);
            int effective = Math.min(curve.statCap, source.reloadStat + BONUSES[row.stacks - 1]);
            double seconds = curve.seconds(effective) * SCALARS[row.stacks - 1];
            check(Double.isFinite(seconds) && seconds > 0 && seconds <= 60, "finite reload duration");
            int ticks = (int) Math.ceil(seconds * 20);
            check(row.effectiveReloadStat == effective && row.firstTicks == ticks && row.intervalTicks == ticks,
                "exact stat/scalar/single-ceil math");
            int baseline = (int) Math.ceil(curve.seconds(Math.min(curve.statCap, source.reloadStat)) * 20);
            check(source.supported && !source.shellReload && source.initialTicks == null
                && source.reloadTicks != null && source.reloadTicks == baseline && ticks <= baseline
                && seconds <= curve.seconds(Math.min(curve.statCap, source.reloadStat)),
                "supported W46 baseline, no invented insert delay");
        }
    }

    private static Curve expectedCurve(String id, String family) {
        return switch (family) {
            case "hand_cannon" -> new Curve(id, 6.137590643e-05, -.02385522011, 3.600042253, 100);
            case "scout_rifle" -> new Curve(id, .000102915, -.0276889, 3.11797356666666, 100);
            case "sidearm" -> new Curve(id, 2.38311e-05, -.0124553, 2.14667245, 100);
            case "bow" -> new Curve(id, 5.35476056419958e-05, -.0102410419405799, 1.10091136388022, 85);
            case "sniper_rifle" -> new Curve(id, 6.74498e-05, -.0231542, 3.8384, 100);
            case "linear_fusion_rifle" -> new Curve(id, 5.88462e-05, -.0199884, 2.87206463333, 100);
            default -> throw invalid("unreviewed curve family " + family);
        };
    }
    private static String key(String id, int stacks) { return id + ":" + stacks; }
    private static Map<String, Reload> index() {
        var result = new HashMap<String, Reload>();
        for (var row : DATA.reloads) result.put(key(row.id, row.stacks), row.reload());
        return Map.copyOf(result);
    }
    /** Already validated sourced scalar; used before the final tick rounding in combined stat buffs. */
    public static double durationMultiplier(int stacks) {
        if (stacks < 1 || stacks > 5) throw new IllegalArgumentException("Invalid active reload tier");
        return SCALARS[stacks-1];
    }
    public static int durationTicks() { return DATA.perk.durationTicks; }
    public static int maxStacks() { return DATA.perk.maxStacks; }
    public static Perk perk() { return DATA.perk; }
    public static Policies policies() { return DATA.policies; }
    public static List<WeaponPerks.Roll> rolls() { return List.of(DATA.weapons); }

    /** Zero is inactive. Other out-of-range counts are programming errors, not saturated tiers. */
    public static int stabilityBonus(int stacks) {
        if (stacks < 0 || stacks > 5) throw new IllegalArgumentException("Invalid Rapid Hit stacks");
        return stacks == 0 ? 0 : STABILITY[stacks - 1];
    }

    /** Exact unrounded historical curve ratio, not a ratio of already rounded tick plans.
     * Long Arm runtime applies ceil(existingPhaseTicks * ratio) separately to its local
     * first/interval phases, preserving two-round inserts. This adaptation is LOCAL:
     * source insert timings remain unknown; the whole-magazine curve is not an insert measurement.
     */
    public static double reloadMultiplier(WeaponCatalog.Entry entry, int stacks) {
        var plan = reload(entry, stacks);
        var curve = Arrays.stream(DATA.curves).filter(c -> c.id.equals(entry.id())).findFirst().orElseThrow();
        return curve.seconds(plan.effectiveReloadStat) * SCALARS[stacks - 1]
            / curve.seconds(Math.min(curve.statCap, plan.baseReloadStat));
    }

    /** Only Apostate in the selected catalog can pair these two base traits in distinct sockets.
     * Local combination policy (the pinned sources do not measure this pair): add capped
     * reload-stat bonuses and multiply duration scalars, then ceil once. Never multiply an
     * already rounded Outlaw tick plan or let Rapid Hit replace a stronger active Outlaw.
     */
    public static Reload reloadWithOutlaw(WeaponCatalog.Entry entry, int stacks) {
        var base=reload(entry,stacks);
        var rapid=EXPECTED.stream().filter(r->r.id().equals(entry.id())).findFirst().orElseThrow();
        if(!entry.id().equals("apostate") || OutlawProfile.rolls().stream().noneMatch(r->
                r.id().equals(entry.id()) && r.socket()!=rapid.socket()))
            throw new IllegalArgumentException("No selected distinct Rapid Hit/Outlaw socket pair");
        var curve=Arrays.stream(DATA.curves).filter(c->c.id.equals(entry.id())).findFirst().orElseThrow();
        int effective=Math.min(curve.statCap,base.baseReloadStat+BONUSES[stacks-1]+OutlawProfile.perk().reloadBonus());
        int ticks=(int)Math.ceil(curve.seconds(effective)*SCALARS[stacks-1]
                *OutlawProfile.perk().durationMultiplier()*20);
        return new Reload(ticks,ticks,base.baseReloadStat,effective);
    }

    /** Active tiers only; unsupported, inactive and noncanonical entries fail closed.
     * Biting Winds returns nock duration, never draw/full-cycle duration. Long Arm
     * returns historical whole-magazine reference only: runtime must adapt its existing
     * distinct phases with reloadMultiplier(), never replace insert timing with this plan.
     */
    public static Reload reload(WeaponCatalog.Entry entry, int stacks) {
        if (entry == null || stacks < 1 || stacks > 5
            || WeaponCatalog.find(entry.id()).filter(entry::equals).isEmpty())
            throw new IllegalArgumentException("Invalid Rapid Hit entry/stacks");
        var result = RELOADS.get(key(entry.id(), stacks));
        if (result == null) throw new IllegalArgumentException("No Rapid Hit reload for " + entry.id());
        return result;
    }
}
