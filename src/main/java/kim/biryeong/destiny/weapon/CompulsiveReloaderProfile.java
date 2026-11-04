package kim.biryeong.destiny.weapon;

import com.google.gson.*;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.*;

/** Base Compulsive Reloader only. Initialization reads JSON, never the live perk/catalog registry.
 * Total stat bonuses and duration scalars are evaluated on raw W46 seconds before one ceil.
 */
public final class CompulsiveReloaderProfile {
    public static final String ID = "compulsive_reloader";
    public static final long HASH = 671806388L;
    private static final String RESOURCE = "/destiny/weapons/w190-compulsive-reloader.json";
    private static final String SHA256 = "475fa0b2c5c944758ed25d5d2dbd5d0178ac1e53e69577cde27dd9a0a243840b";
    private static final Gson GSON = new Gson();
    private static final Set<WeaponPerks.Roll> EXPECTED = Set.of(
        new WeaponPerks.Roll("aishas_embrace", 2638190703L, 3, HASH, 7997267L),
        new WeaponPerks.Roll("austringer", 3055790362L, 3, HASH, 2750499928L),
        new WeaponPerks.Roll("beloved", 3107853529L, 3, HASH, 1196545279L),
        new WeaponPerks.Roll("long_arm", 8293111L, 3, HASH, 3056706286L),
        new WeaponPerks.Roll("nezarec_s_whisper", 254636484L, 3, HASH, 210449465L));
    private record Quadratic(double evpp, double vpp, double offset) {
        double seconds(int stat) { return evpp * stat * stat + vpp * stat + offset; }
    }
    private record Curve(String id, int baseReloadStat, int magazine, Quadratic reload,
                         Double firstSeconds, Double intervalSeconds, int roundsPerInsert) {}
    private record Companion(String id, String perk, WeaponPerks.Roll roll) {}
    private record Data(List<WeaponPerks.Roll> rolls, Map<String, Curve> curves, List<Companion> companions) {}
    private static final Map<String, JsonObject> CATALOG = byId("/destiny/weapons/w30.json");
    private static final Data DATA = load();
    private CompulsiveReloaderProfile() {}

    private static void check(boolean ok, String detail) {
        if (!ok) throw new IllegalStateException("Invalid W190 Compulsive Reloader: " + detail);
    }
    private static byte[] bytes(String path) {
        var stream = CompulsiveReloaderProfile.class.getResourceAsStream(path);
        check(stream != null, "missing " + path);
        try (stream) { return stream.readAllBytes(); }
        catch (IOException e) { throw new IllegalStateException("Unreadable " + path, e); }
    }
    private static Map<String, JsonObject> byId(String path) {
        var result = new HashMap<String, JsonObject>();
        for (var value : JsonParser.parseString(new String(bytes(path), StandardCharsets.UTF_8)).getAsJsonArray()) {
            var row = value.getAsJsonObject();
            check(result.putIfAbsent(row.get("id").getAsString(), row) == null, "duplicate source ID");
        }
        return Map.copyOf(result);
    }
    private static Data load() {
        var raw = bytes(RESOURCE);
        try { check(HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw)).equals(SHA256), "resource checksum"); }
        catch (NoSuchAlgorithmException e) { throw new IllegalStateException(e); }
        var root = JsonParser.parseString(new String(raw, StandardCharsets.UTF_8)).getAsJsonObject();
        check(root.get("stage").getAsString().equals("W190"), "stage");
        var perk = root.getAsJsonObject("perk");
        check(ID.equals(perk.get("id").getAsString()) && perk.get("hash").getAsLong() == HASH
            && perk.get("reloadBonus").getAsInt() == 50 && perk.get("durationMultiplier").getAsDouble() == .95, "base mechanics");
        var rolls = new ArrayList<WeaponPerks.Roll>();
        for (var value : root.getAsJsonArray("weapons")) {
            var roll = GSON.fromJson(value, WeaponPerks.Roll.class);
            check(EXPECTED.contains(roll) && !rolls.contains(roll), "exact unique base roll");
            rolls.add(roll);
        }
        check(Set.copyOf(rolls).equals(EXPECTED), "complete five rolls");
        var stats = byId("/destiny/weapons/w40-characteristics.json");
        var timing = byId("/destiny/weapons/w46-timing.json");
        var curves = new HashMap<String, Curve>();
        for (var value : root.getAsJsonArray("curves")) {
            var c = GSON.fromJson(value, Curve.class);
            var roll = rolls.stream().filter(r -> r.id().equals(c.id)).findFirst().orElseThrow();
            var s = stats.get(c.id);
            var t = timing.get(c.id).getAsJsonObject("timing");
            check(curves.putIfAbsent(c.id, c) == null && CATALOG.containsKey(c.id)
                && s.get("bungieHash").getAsLong() == roll.hash() && !s.get("exotic").getAsBoolean()
                && s.getAsJsonObject("stats").get("4188031367").getAsInt() == c.baseReloadStat
                && t.get("magazine").getAsInt() == c.magazine && t.get("supported").getAsBoolean()
                && !t.get("shellReload").getAsBoolean()
                && quantize(c.reload.seconds(c.baseReloadStat)) == t.get("reloadTicks").getAsInt(), "raw baseline/stat/capacity");
            check(c.id.equals("long_arm") ? c.roundsPerInsert == 2 && Double.valueOf(1).equals(c.firstSeconds)
                && Double.valueOf(.65).equals(c.intervalSeconds)
                : c.roundsPerInsert == 0 && c.firstSeconds == null && c.intervalSeconds == null, "reload topology");
        }
        check(curves.size() == 5, "complete curves");
        var companions = new ArrayList<Companion>();
        for (var value : root.getAsJsonArray("coSelections")) {
            var c = GSON.fromJson(value, Companion.class);
            var source = rolls.stream().filter(r -> r.id().equals(c.id)).findFirst().orElseThrow();
            check(c.roll.id().equals(c.id) && c.roll.hash() == source.hash() && c.roll.socket() != source.socket()
                && !companions.contains(c), "distinct companion roll");
            companions.add(c);
        }
        return new Data(List.copyOf(rolls), Map.copyOf(curves), List.copyOf(companions));
    }
    public static List<WeaponPerks.Roll> rolls() { return DATA.rolls; }
    public static int reloadBonus() { return 50; }
    public static double durationMultiplier() { return .95; }
    /** Integer comparison handles odd capacities; exactly half is inactive. Invalid counts are inert. */
    public static boolean aboveThreshold(int roundsBefore, int capacity) {
        return capacity > 0 && roundsBefore >= 0 && roundsBefore <= capacity && 2L * roundsBefore > capacity;
    }
    public static boolean supports(WeaponCatalog.Entry entry) {
        return entry != null && entry.id() != null && DATA.curves.containsKey(entry.id())
            && entry.equals(GSON.fromJson(CATALOG.get(entry.id()), WeaponCatalog.Entry.class));
    }
    public static boolean compatible(WeaponCatalog.Entry entry, String perk, WeaponPerks.Roll selected) {
        return supports(entry) && DATA.companions.stream().anyMatch(c -> c.id.equals(entry.id())
            && c.perk.equals(perk) && c.roll.equals(selected));
    }
    private static Curve curve(WeaponCatalog.Entry entry) {
        if (!supports(entry)) throw new IllegalArgumentException("Unsupported/noncanonical Compulsive Reloader entry");
        return DATA.curves.get(entry.id());
    }
    private static int quantize(double seconds) {
        check(Double.isFinite(seconds) && seconds > 0 && seconds <= 60, "safe raw seconds");
        return Math.max(1, (int)Math.ceil(seconds * 20));
    }
    /** TOTAL bonuses/scalars, including W190 and the actual active legal companion. */
    public static double reloadSeconds(WeaponCatalog.Entry entry, int totalReloadBonus, double totalScalar) {
        var c = curve(entry);
        if (!Double.isFinite(totalScalar) || totalScalar <= 0 || totalScalar > 1)
            throw new IllegalArgumentException("Reload scalar must be finite in (0,1]");
        int stat = (int)Math.clamp((long)c.baseReloadStat + totalReloadBonus, 0L, 100L);
        return c.reload.seconds(stat) * totalScalar;
    }
    /** Historical whole-magazine ratio; Long Arm insert durations are local policy, not measurements. */
    public static double reloadMultiplier(WeaponCatalog.Entry entry, int totalReloadBonus, double totalScalar) {
        var c = curve(entry);
        return reloadSeconds(entry, totalReloadBonus, totalScalar) / c.reload.seconds(c.baseReloadStat);
    }
    public static WeaponReloadPolicy.Plan reloadPlan(WeaponCatalog.Entry entry, int totalReloadBonus,
                                                    double totalScalar, WeaponReloadPolicy.Plan base) {
        var c = curve(entry);
        if (base.roundsPerInsert() != c.roundsPerInsert)
            throw new IllegalArgumentException("Foreign Compulsive Reloader insertion topology");
        if (c.roundsPerInsert == 2) {
            double ratio = reloadMultiplier(entry, totalReloadBonus, totalScalar);
            return new WeaponReloadPolicy.Plan(quantize(c.firstSeconds * ratio), quantize(c.intervalSeconds * ratio), 2);
        }
        int ticks = quantize(reloadSeconds(entry, totalReloadBonus, totalScalar));
        return new WeaponReloadPolicy.Plan(ticks, ticks, base.roundsPerInsert());
    }
}
