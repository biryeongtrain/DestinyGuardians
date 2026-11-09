package kim.biryeong.destiny.weapon;

import com.google.gson.*;
import java.io.IOException;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.*;

/** Pinned exact-base Frenzy sockets and historical stat curves. Combat integration is master-owned.
 * Static initialization reads JSON only and constructs Roll records; no registry outer calls.
 */
public final class FrenzyProfile {
    public static final String ID = "frenzy";
    public static final long HASH = 4104185692L;
    private static final String RESOURCE = "/destiny/weapons/w172-frenzy.json";
    public record Timing(String id, int reloadTicks, int readyTicks, int stowTicks, int adsTicks) {}
    public record Perk(String id, long hash, int activationTicks, int combatGraceTicks, int durationTicks,
                       float damageMultiplier, int handlingBonus, int reloadBonus, boolean worksStowed,
                       boolean refreshOnDealtDamage, boolean refreshOnReceivedDamage,
                       boolean selfDamageCounts, boolean environmentalDamageCounts) {}
    private record Quadratic(double evpp, double vpp, double offset) {
        double seconds(int stat) { return evpp * stat * stat + vpp * stat + offset; }
    }
    private record Curve(String id, int baseReloadStat, int baseHandlingStat, boolean neutralAds,
                         Quadratic reload, Quadratic ready, Quadratic stow, Quadratic ads) {}
    private record Data(String stage, Perk perk, JsonObject policies, WeaponPerks.Roll[] weapons,
                        Curve[] curves, JsonObject[] timings, Snapshot[] snapshotADS) {}
    private record Snapshot(String id, int frenzySocket, int snapshotSocket, long snapshotPlugSetHash,
                            long perkHash, int ammoType, double scalar, double adsSeconds, int adsTicks) {}
    private record Source(long hash, boolean exotic, int reload, int handling,
                          int reloadTicks, int readyTicks, int stowTicks, int adsTicks, JsonObject catalog) {}
    private static final Set<WeaponPerks.Roll> EXPECTED = Set.of(
        new WeaponPerks.Roll("austringer", 3055790362L, 4, HASH, 785215120L),
        new WeaponPerks.Roll("allied_demand", 1532276803L, 4, HASH, 703779397L),
        new WeaponPerks.Roll("farewell", 541188001L, 4, HASH, 3819615926L),
        new WeaponPerks.Roll("brass_attacks", 2121785039L, 4, HASH, 3403850295L),
        new WeaponPerks.Roll("dream_breaker", 2931957300L, 4, HASH, 1206254527L),
        new WeaponPerks.Roll("stormchaser", 3652506829L, 4, HASH, 4213354588L),
        new WeaponPerks.Roll("retraced_path", 548958835L, 4, HASH, 398391969L),
        new WeaponPerks.Roll("code_duello", 2496242052L, 4, HASH, 147528717L),
        new WeaponPerks.Roll("retrofit_escapade", 3103325054L, 4, HASH, 2461260598L),
        new WeaponPerks.Roll("nezarec_s_whisper", 254636484L, 4, HASH, 699056095L));
    private static final JsonObject POLICIES = JsonParser.parseString("""
{
  "statCap": 100,
  "durationMultiplier": 1.0,
  "rounding": "CEIL_SECONDS_TIMES_20_ONCE",
  "adsBounds": "CLAMP_TICKS_2_20_W44",
  "glaiveAds": "W44_UNSUPPORTED_NEUTRAL_2_TICKS_ZERO_ORACLE_CURVE",
  "handlingBounds": "W58_NO_EXTRA_TICK_CLAMP_STOW_AT_100_FLOOR",
  "combatDefinition": "DEALT_OR_RECEIVED_DAMAGE_WITHIN_LAST_5_SECONDS",
  "sourceDamageAttribution": "MASTER_OWNED_LOCAL_POLICY",
  "sourceCombinedPerks": "UNKNOWN_MASTER_OWNED_LOCAL_POLICY",
  "cycleIntegration": "MASTER_OWNED_LOCAL_POLICY",
  "snapshotComposition": "W68_ENTRY_SCALAR_AFTER_FRENZY_STAT100_BEFORE_SINGLE_CEIL_CLAMP1_20"
}
        """).getAsJsonObject();
    private static final Map<String, Source> SOURCES = selectedJson();
    private static final Data DATA = load();
    private static final Map<String, Timing> TIMINGS = index();
    private FrenzyProfile() {}

    private static void check(boolean condition, String detail) {
        if (!condition) throw new IllegalStateException("Invalid W172 Frenzy profile: " + detail);
    }
    private static JsonElement read(String path) {
        var stream = FrenzyProfile.class.getResourceAsStream(path);
        check(stream != null, "missing resource " + path);
        try (var reader = new InputStreamReader(stream, StandardCharsets.UTF_8)) {
            return JsonParser.parseReader(reader);
        } catch (IOException | JsonParseException e) {
            throw new IllegalStateException("Cannot read W172 Frenzy source " + path, e);
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
    private static Map<String, Source> selectedJson() {
        var catalog = byId("/destiny/weapons/w30.json");
        var stats = byId("/destiny/weapons/w40-characteristics.json");
        var reloads = byId("/destiny/weapons/w46-timing.json");
        var handling = byId("/destiny/weapons/w58-handling.json");
        var aim = byId("/destiny/weapons/w44-aim.json");
        check(stats.size() == 63 && stats.keySet().equals(catalog.keySet())
            && stats.keySet().equals(reloads.keySet()) && stats.keySet().equals(handling.keySet())
            && stats.keySet().equals(aim.keySet()), "source coverage");
        var result = new HashMap<String, Source>();
        for (var roll : EXPECTED) {
            var row = stats.get(roll.id());
            var s = row.getAsJsonObject("stats");
            var t = reloads.get(roll.id()).getAsJsonObject("timing");
            var h = handling.get(roll.id()).getAsJsonObject("profile");
            check(t.get("supported").getAsBoolean() && h.get("supported").getAsBoolean()
                && !t.get("shellReload").getAsBoolean() && t.get("reloadPerRoundTicks").isJsonNull()
                && t.get("reloadInitialTicks").isJsonNull(), "supported whole magazine; never omit eligible topology");
            result.put(roll.id(), new Source(row.get("bungieHash").getAsLong(), row.get("exotic").getAsBoolean(),
                s.get("4188031367").getAsInt(), s.get("943549884").getAsInt(),
                t.get("reloadTicks").getAsInt(), h.get("readyTicks").getAsInt(), h.get("stowTicks").getAsInt(),
                aim.get(roll.id()).getAsJsonObject("profile").get("transitionTicks").getAsInt(), catalog.get(roll.id())));
        }
        return Map.copyOf(result);
    }
    private static Data load() {
        var data = new Gson().fromJson(read(RESOURCE), Data.class);
        validate(data);
        return data;
    }
    /** Pure validation for malformed-resource regression; never mutates loaded state. */
    static void validateResource(String json) {
        try { validate(new Gson().fromJson(json, Data.class)); }
        catch (RuntimeException e) { throw new IllegalStateException("Invalid W172 Frenzy JSON", e); }
    }
    private static Curve expectedCurve(String id) {
        return switch (id) {
            case "austringer" -> new Curve(id, 46, 47, false,
                new Quadratic(6.137590643e-05, -0.02385522011, 3.600042253),
                new Quadratic(0.0, -0.002942857143, 0.4782571429),
                new Quadratic(0.0, -0.002952380952, 0.5133809524),
                new Quadratic(0.0, -0.001666666667, 0.3316666667));
            case "allied_demand" -> new Curve(id, 30, 48, false,
                new Quadratic(2.38311e-05, -0.0124553, 2.14667245),
                new Quadratic(0.0, -0.00264010989, 0.4232582418),
                new Quadratic(0.0, -0.00197527473, 0.4298956044),
                new Quadratic(0.0, -0.0022293956, 0.3435796703));
            case "farewell" -> new Curve(id, 49, 64, false,
                new Quadratic(2.38311e-05, -0.0124553, 2.14667245),
                new Quadratic(0.0, -0.00264010989, 0.4232582418),
                new Quadratic(0.0, -0.00197527473, 0.4298956044),
                new Quadratic(0.0, -0.0022293956, 0.3435796703));
            case "brass_attacks" -> new Curve(id, 27, 36, false,
                new Quadratic(2.38311e-05, -0.0124553, 2.14667245),
                new Quadratic(0.0, -0.00264010989, 0.4232582418),
                new Quadratic(0.0, -0.00197527473, 0.4298956044),
                new Quadratic(0.0, -0.0022293956, 0.3435796703));
            case "dream_breaker" -> new Curve(id, 30, 27, false,
                new Quadratic(6.15281e-05, -0.0198054, 2.8285704),
                new Quadratic(0.0, -0.001448069241, 0.4990612517),
                new Quadratic(0.0, -0.002863515313, 0.4445712383),
                new Quadratic(0.0, -0.001693741678, 0.4112330226));
            case "stormchaser" -> new Curve(id, 25, 30, false,
                new Quadratic(5.88462e-05, -0.0199884, 2.87206463333),
                new Quadratic(0.0, -0.001448069241, 0.4990612517),
                new Quadratic(0.0, -0.002863515313, 0.4445712383),
                new Quadratic(0.0, -0.001693741678, 0.4112330226));
            case "retraced_path" -> new Curve(id, 45, 46, false,
                new Quadratic(5e-05, -0.0155, 2.65),
                new Quadratic(0.0, -0.00279338, 0.51985381),
                new Quadratic(0.0, -0.00268436, 0.48414822),
                new Quadratic(0.0, -0.001875, 0.38975));
            case "code_duello" -> new Curve(id, 35, 69, false,
                new Quadratic(0.000103959, -0.0252069, 4.09182213333333),
                new Quadratic(0.0, -0.003998740554, 0.6635944584),
                new Quadratic(0.0, -0.003296509536, 0.5463332134),
                new Quadratic(0.0, -0.002139258726, 0.528984167));
            case "retrofit_escapade" -> new Curve(id, 67, 56, false,
                new Quadratic(9.05351e-05, -0.0305819, 6.1219905),
                new Quadratic(0.0, -0.002391721353, 0.4950499748),
                new Quadratic(0.0, -0.002041393236, 0.4547501262),
                new Quadratic(0.0, -0.001234477537, 0.4574687027));
            case "nezarec_s_whisper" -> new Curve(id, 25, 42, true,
                new Quadratic(0.0, -0.0175, 3.5),
                new Quadratic(0.0, -0.002139219, 0.42369),
                new Quadratic(0.0, -0.002827674, 0.5147),
                new Quadratic(0.0, -0.0, 0.0));
            default -> throw new IllegalStateException("Unreviewed Frenzy weapon " + id);
        };
    }
    static int effectiveStat(int base) { return (int) Math.clamp((long) base + 100L, 0L, 100L); }
    static int durationTicks(double seconds, boolean ads) {
        check(Double.isFinite(seconds) && seconds > 0 && seconds <= 60, "finite positive bounded seconds");
        int ticks = (int) Math.ceil(seconds * 20);
        return ads ? Math.clamp(ticks, 2, 20) : ticks;
    }
    static int snapshotDurationTicks(double seconds, double scalar) {
        check(Double.isFinite(seconds) && seconds > 0 && seconds <= 60, "finite Snapshot ADS seconds");
        check(scalar == .5 || scalar == .8, "W68 measured primary/special scalar only");
        return Math.clamp((int) Math.ceil(seconds * scalar * 20), 1, 20);
    }
    private static Timing calculate(Curve c, boolean active) {
        int reload = active ? effectiveStat(c.baseReloadStat) : c.baseReloadStat;
        int handling = active ? effectiveStat(c.baseHandlingStat) : c.baseHandlingStat;
        double ads = c.ads.seconds(handling);
        check(!c.neutralAds || ads == 0, "glaive zero ADS evidence");
        return new Timing(c.id, durationTicks(c.reload.seconds(reload), false),
            durationTicks(c.ready.seconds(handling), false),
            durationTicks(Math.max(c.stow.seconds(handling), c.stow.seconds(100)), false),
            c.neutralAds ? 2 : durationTicks(ads, true));
    }
    private static void validate(Data data) {
        check(data != null && "W172".equals(data.stage), "stage");
        check(new Perk(ID, HASH, 240, 100, 144, 1.15f, 100, 100, true, true, true, false, false)
            .equals(data.perk), "exact sourced mechanics");
        check(POLICIES.equals(data.policies), "source mechanics and local bounds");
        check(data.weapons != null && data.weapons.length == EXPECTED.size(), "exact ten sockets");
        var rolls = new HashSet<WeaponPerks.Roll>();
        var ids = new HashSet<String>();
        for (var roll : data.weapons) {
            check(roll != null && EXPECTED.contains(roll) && rolls.add(roll) && ids.add(roll.id()), "exact base membership");
            var source = SOURCES.get(roll.id());
            check(source != null && source.hash == roll.hash() && !source.exotic, "official base identity");
        }
        check(rolls.equals(EXPECTED), "complete membership");
        check(data.curves != null && data.curves.length == EXPECTED.size(), "ten curves");
        var curves = new HashMap<String, Curve>();
        for (var c : data.curves) {
            check(c != null && ids.contains(c.id) && curves.putIfAbsent(c.id, c) == null, "unique eligible curve");
            check(expectedCurve(c.id).equals(c), "pinned coefficients and official stats");
            var source = SOURCES.get(c.id);
            check(c.baseReloadStat == source.reload && c.baseHandlingStat == source.handling, "physical stats");
            check(c.neutralAds == "glaive".equals(source.catalog.get("family").getAsString()), "W44 neutral glaive ADS");
            var base = calculate(c, false);
            check(base.reloadTicks == source.reloadTicks && base.readyTicks == source.readyTicks
                && base.stowTicks == source.stowTicks && base.adsTicks == source.adsTicks, "four reproduced baselines");
        }
        check(data.timings != null && data.timings.length == EXPECTED.size(), "ten active plans");
        var keys = new HashSet<String>();
        for (var raw : data.timings) {
            check(raw != null, "non-null timing");
            var row = new Gson().fromJson(raw, Timing.class);
            check(row != null && ids.contains(row.id) && keys.add(row.id), "unique eligible plan");
            var c = curves.get(row.id);
            var expected = new Gson().toJsonTree(calculate(c, true)).getAsJsonObject();
            expected.addProperty("shellReload", false);
            expected.add("reloadPerRoundTicks", JsonNull.INSTANCE);
            expected.add("reloadInitialTicks", JsonNull.INSTANCE);
            expected.addProperty("reloadPlanKind", "WHOLE_MAGAZINE");
            expected.addProperty("adsSupported", !c.neutralAds);
            check(expected.equals(raw), "exact single-ceil timing and explicit reload/ADS topology");
            var base = calculate(c, false);
            check(row.reloadTicks <= base.reloadTicks && row.readyTicks <= base.readyTicks
                && row.stowTicks <= base.stowTicks && row.adsTicks <= base.adsTicks, "buff cannot slow baseline");
        }
        check(data.snapshotADS != null && data.snapshotADS.length == 2, "exact Snapshot intersection");
        var snapshotIds = new HashSet<String>();
        var w68 = read("/destiny/weapons/w68-snapshot.json").getAsJsonObject();
        check(w68.get("perkHash").getAsLong() == 957782887L
            && w68.get("primaryScalar").getAsDouble() == .5 && w68.get("specialScalar").getAsDouble() == .8,
            "W68 scalar policy");
        for (var row : data.snapshotADS) {
            check(row != null && snapshotIds.add(row.id), "unique Snapshot pair");
            var expected = switch (row.id) {
                case "austringer" -> new Snapshot(row.id, 4, 3, 2750499928L, 957782887L, 1, .5, .165, 2);
                case "dream_breaker" -> new Snapshot(row.id, 4, 3, 3785896921L, 957782887L, 2, .8, .2418588548, 4);
                default -> throw new IllegalStateException("Unsupported Frenzy/Snapshot pair");
            };
            check(expected.equals(row), "exact distinct sockets, raw seconds, scalar and combined ticks");
            check(row.adsSeconds == curves.get(row.id).ads.seconds(100)
                && row.adsTicks == snapshotDurationTicks(row.adsSeconds, row.scalar), "scale before single quantization");
            var frenzy = EXPECTED.stream().filter(r -> r.id().equals(row.id)).findFirst().orElseThrow();
            var snapshot = new JsonObject();
            snapshot.addProperty("id", row.id); snapshot.addProperty("hash", frenzy.hash());
            snapshot.addProperty("socket", row.snapshotSocket); snapshot.addProperty("perkHash", row.perkHash);
            snapshot.addProperty("plugSetHash", row.snapshotPlugSetHash);
            check(w68.getAsJsonArray("rolls").asList().contains(snapshot)
                && row.snapshotSocket != frenzy.socket(), "W68 selectable base roll in different socket");
        }
    }
    private static Map<String, Timing> index() {
        var result = new HashMap<String, Timing>();
        for (var row : DATA.timings) {
            var timing = new Gson().fromJson(row, Timing.class);
            result.put(timing.id, timing);
        }
        return Map.copyOf(result);
    }
    public static List<WeaponPerks.Roll> rolls() { return LegendaryPerks.expandRolls(ID, List.of(DATA.weapons)); }
    public static Perk perk() { return DATA.perk; }
    public static int activationTicks() { return DATA.perk.activationTicks; }
    public static int combatGraceTicks() { return DATA.perk.combatGraceTicks; }
    public static int durationTicks() { return DATA.perk.durationTicks; }
    public static float multiplier() { return DATA.perk.damageMultiplier; }
    public static int handlingBonus() { return DATA.perk.handlingBonus; }
    public static int reloadBonus() { return DATA.perk.reloadBonus; }
    public static boolean worksStowed() { return DATA.perk.worksStowed; }

    /** Compare selected JSON fields without an outer WeaponCatalog or WeaponPerks call. */
    public static boolean supports(WeaponCatalog.Entry entry) {
        if (entry == null || entry.id() == null) return false;
        var source = SOURCES.get(entry.id());
        if (source == null) return LegendaryWeapons.contains(entry.id())
            && WeaponCatalog.find(entry.id()).filter(entry::equals).isPresent()
            && LegendaryPerks.extraRolls(ID).stream().anyMatch(r -> r.id().equals(entry.id()));
        var row = source.catalog;
        return Objects.equals(entry.family(), row.get("family").getAsString())
            && Objects.equals(entry.frame(), row.get("frame").getAsString())
            && Objects.equals(entry.name(), row.get("name").getAsString())
            && Objects.equals(entry.source_frame_label(), row.get("source_frame_label").getAsString())
            && Objects.equals(entry.item_model(), row.get("item_model").getAsString());
    }
    /** Compose the consumer's validated reload-duration scalar with raw active stat100 seconds.
     * The caller owns active Outlaw/Feeding Frenzy/Rapid Hit state; no registry is consulted here.
     */
    public static int reloadTicks(WeaponCatalog.Entry entry, double durationScalar) {
        if (!supports(entry)) throw new IllegalArgumentException("No Frenzy reload for unsupported/noncanonical entry");
        if (!Double.isFinite(durationScalar) || durationScalar <= 0 || durationScalar > 1)
            throw new IllegalArgumentException("Frenzy reload duration scalar must be finite and in (0,1]");
        for (var curve : DATA.curves) if (curve.id.equals(entry.id()))
            return durationTicks(curve.reload.seconds(100) * durationScalar, false);
        return WeaponStatCurves.reloadTicks(entry.id(), WeaponProfile.forEntry(entry).reloadTicks(), reloadBonus(), durationScalar);
    }
    /** Active Frenzy ADS entry: W68 Snapshot scalar applies to stat100 seconds before a single ceil.
     * Only the two exact distinct-socket co-selections are accepted; false retains the W44 bound.
     * Glaive's 2 ticks remain W44 neutral policy, never an original ADS-curve measurement.
     */
    public static int adsTicks(WeaponCatalog.Entry entry, boolean snapshotSelected) {
        var active = timing(entry);
        if (!snapshotSelected) return active.adsTicks;
        for (var row : DATA.snapshotADS) if (row.id.equals(entry.id()))
            return snapshotDurationTicks(row.adsSeconds, row.scalar);
        if (LegendaryWeapons.contains(entry.id()) && LegendaryPerks.extraRolls(SnapshotAimProfile.ID).stream()
                .anyMatch(r -> r.id().equals(entry.id()) && LegendaryPerks.extraRolls(ID).stream()
                    .anyMatch(f -> f.id().equals(entry.id()) && f.socket() != r.socket()))) {
            double scalar = WeaponCharacteristics.of(entry).ammo() == WeaponAmmoType.PRIMARY ? .5 : .8;
            return WeaponStatCurves.adsTicks(entry.id(), WeaponAimProfile.of(entry).transitionTicks(), handlingBonus(), scalar);
        }
        throw new IllegalArgumentException("No distinct-socket Frenzy/Snapshot selection for " + entry.id());
    }
    public static Timing timing(WeaponCatalog.Entry entry) {
        if (!supports(entry)) throw new IllegalArgumentException("No Frenzy timing for unsupported/noncanonical entry");
        var legacy = TIMINGS.get(entry.id());
        if (legacy != null) return legacy;
        var handling = WeaponHandlingProfile.of(entry);
        return new Timing(entry.id(), reloadTicks(entry, 1),
            WeaponStatCurves.handlingTicks(entry.id(), true, handling.readyTicks(), handlingBonus(), 1),
            WeaponStatCurves.handlingTicks(entry.id(), false, handling.stowTicks(), handlingBonus(), 1),
            WeaponStatCurves.adsTicks(entry.id(), WeaponAimProfile.of(entry).transitionTicks(), handlingBonus(), 1));
    }
}
