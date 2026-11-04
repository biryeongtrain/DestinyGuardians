package kim.biryeong.destiny.weapon;

import com.google.gson.*;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.*;

/** Exact base Threat Detector, not enhanced or a family grant.
 * All timing arguments are TOTALS; apply capped stats and scalars to raw seconds, ceil once.
 * Initialization is JSON-only, with no catalog/perk registry/characteristics initialization cycle.
 * Official current sockets and historical community curves have separate pinned provenance.
 */
public final class ThreatDetectorProfile {
    public static final String ID = "threat_detector";
    public static final long HASH = 4071163871L;
    private static final String RESOURCE = "/destiny/weapons/w178-threat-detector.json";
    private static final String SHA256 = "7d5e1938eb8fcf2cc3b2b1f2da63496e87d16c55f60ae455323d7f497dbbabae";
    private static final Gson GSON = new Gson();
    private static final List<WeaponPerks.Roll> EXPECTED = List.of(
        new WeaponPerks.Roll("seventh_seraph_officer_revolver", 3037520408L, 3, HASH, 903350103L),
        new WeaponPerks.Roll("cold_denial", 1216130969L, 3, HASH, 330841869L),
        new WeaponPerks.Roll("claws_of_the_wolf", 1280933460L, 3, HASH, 206409262L),
        new WeaponPerks.Roll("bug_out_bag", 2744715540L, 3, HASH, 907333373L),
        new WeaponPerks.Roll("dead_man_walking_xx7463", 3751622019L, 3, HASH, 3268663985L),
        new WeaponPerks.Roll("high_albedo", 1197486957L, 3, HASH, 2797218184L),
        new WeaponPerks.Roll("brass_attacks", 2121785039L, 3, HASH, 100135553L),
        new WeaponPerks.Roll("mindbender_s_ambition_adept", 912150785L, 3, HASH, 1732284294L),
        new WeaponPerks.Roll("dust_rock_blues", 636912560L, 3, HASH, 3511609070L),
        new WeaponPerks.Roll("parcel_of_stardust_fell_to_earth", 2217366863L, 3, HASH, 2514419370L),
        new WeaponPerks.Roll("dream_breaker", 2931957300L, 3, HASH, 3785896921L),
        new WeaponPerks.Roll("ikelos_smg_v1_0_1", 1723472487L, 4, HASH, 1329L), // curated fixed-roll legendary
        new WeaponPerks.Roll("ikelos_sg_v1_0_1", 1887808042L, 4, HASH, 1324L), // curated fixed-roll legendary
        new WeaponPerks.Roll("line_in_the_sand", 946443267L, 3, HASH, 1503774254L),
        new WeaponPerks.Roll("deafening_whisper", 981718087L, 4, HASH, 3588287812L),
        new WeaponPerks.Roll("edge_transit", 218335759L, 3, HASH, 447678063L),
        new WeaponPerks.Roll("dimensional_hypotrochoid", 1311684613L, 3, HASH, 3235863202L),
        new WeaponPerks.Roll("bellowing_giant", 2186258845L, 4, HASH, 1722393382L),
        new WeaponPerks.Roll("hammerhead", 603242241L, 3, HASH, 2515290473L));
    private record Quadratic(double evpp, double vpp, double offset) {
        double seconds(int stat) { return evpp * stat * stat + vpp * stat + offset; }
    }
    private record Curve(String id, int baseReloadStat, int baseHandlingStat, boolean shellReload,
                         Double snapshotScalar, Quadratic reload, Quadratic ready, Quadratic stow, Quadratic ads) {}
    private record Companion(String id, String perk, WeaponPerks.Roll roll) {}
    private record Data(JsonObject document, List<WeaponPerks.Roll> rolls, Map<String, Curve> curves,
                        List<Companion> companions) {}
    private static final Map<String, JsonObject> CATALOG = byId("/destiny/weapons/w30.json");
    private static final Data DATA = load();
    private ThreatDetectorProfile() {}
    private static void check(boolean ok, String detail) {
        if (!ok) throw new IllegalStateException("Invalid W178 Threat Detector: " + detail);
    }
    private static byte[] bytes(String path) {
        var stream = ThreatDetectorProfile.class.getResourceAsStream(path);
        check(stream != null, "missing " + path);
        try (stream) { return stream.readAllBytes(); }
        catch (IOException e) { throw new IllegalStateException("Unreadable " + path, e); }
    }
    private static Map<String, JsonObject> byId(String path) {
        var map = new HashMap<String, JsonObject>();
        for (var e : JsonParser.parseString(new String(bytes(path), StandardCharsets.UTF_8)).getAsJsonArray()) {
            var row = e.getAsJsonObject();
            check(map.putIfAbsent(row.get("id").getAsString(), row) == null, "duplicate source ID");
        }
        return Map.copyOf(map);
    }
    private static Data load() {
        var raw = bytes(RESOURCE);
        try { check(HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw)).equals(SHA256), "resource checksum"); }
        catch (NoSuchAlgorithmException e) { throw new IllegalStateException(e); }
        var root = JsonParser.parseString(new String(raw, StandardCharsets.UTF_8)).getAsJsonObject();
        check(root.keySet().equals(Set.of("stage", "perk", "policies", "weapons", "curves", "coSelections"))
            && root.get("stage").getAsString().equals("W178"), "schema");
        var rolls = new ArrayList<WeaponPerks.Roll>();
        for (var row : root.getAsJsonArray("weapons")) {
            var roll = GSON.fromJson(row, WeaponPerks.Roll.class);
            check(EXPECTED.contains(roll) && !rolls.contains(roll) && row.equals(GSON.toJsonTree(roll)), "exact unique base roll");
            rolls.add(roll);
        }
        check(rolls.size() == 19, "complete exact19");
        var curves = new HashMap<String, Curve>();
        var stats = byId("/destiny/weapons/w40-characteristics.json");
        var reloads = byId("/destiny/weapons/w46-timing.json");
        var handling = byId("/destiny/weapons/w58-handling.json");
        var aim = byId("/destiny/weapons/w44-aim.json");
        for (var row : root.getAsJsonArray("curves")) {
            var c = GSON.fromJson(row, Curve.class);
            check(curves.putIfAbsent(c.id, c) == null && CATALOG.containsKey(c.id), "unique selected curve");
            var roll = EXPECTED.stream().filter(r -> r.id().equals(c.id)).findFirst().orElseThrow();
            var s = stats.get(c.id);
            check(s.get("bungieHash").getAsLong() == roll.hash() && !s.get("exotic").getAsBoolean()
                && s.getAsJsonObject("stats").get("4188031367").getAsInt() == c.baseReloadStat
                && s.getAsJsonObject("stats").get("943549884").getAsInt() == c.baseHandlingStat, "official stats");
            var t = reloads.get(c.id).getAsJsonObject("timing");
            var h = handling.get(c.id).getAsJsonObject("profile");
            check(t.get("supported").getAsBoolean() && h.get("supported").getAsBoolean()
                && t.get("shellReload").getAsBoolean() == c.shellReload, "supported reload topology");
            check(quantize(c.reload.seconds(c.baseReloadStat)) == t.get(c.shellReload ? "reloadPerRoundTicks" : "reloadTicks").getAsInt()
                && quantize(c.ready.seconds(c.baseHandlingStat)) == h.get("readyTicks").getAsInt()
                && quantize(Math.max(c.stow.seconds(c.baseHandlingStat), c.stow.seconds(100))) == h.get("stowTicks").getAsInt()
                && Math.clamp(quantize(c.ads.seconds(c.baseHandlingStat)), 2, 20)
                    == aim.get(c.id).getAsJsonObject("profile").get("transitionTicks").getAsInt(), "four raw baselines");
        }
        check(curves.size() == 19, "complete curves");
        var companions = new ArrayList<Companion>();
        for (var row : root.getAsJsonArray("coSelections")) {
            var pair = GSON.fromJson(row, Companion.class);
            var source = EXPECTED.stream().filter(r -> r.id().equals(pair.id)).findFirst().orElseThrow();
            check(source.socket() != pair.roll.socket() && source.hash() == pair.roll.hash()
                && pair.id.equals(pair.roll.id()) && !companions.contains(pair), "distinct compatible pair");
            companions.add(pair);
        }
        check(companions.size() == 6, "six compatible pairs");
        return new Data(root, List.copyOf(rolls), Map.copyOf(curves), List.copyOf(companions));
    }
    /** Test the same pinned semantic document, without changing live state. */
    static void validateResource(String json) {
        try { check(JsonParser.parseString(json).equals(DATA.document), "mutated resource"); }
        catch (RuntimeException e) { throw new IllegalStateException("Invalid W178 JSON", e); }
    }
    public static List<WeaponPerks.Roll> rolls() { return DATA.rolls; }
    public static double radius() { return 15.0; }
    private static int tier(int stacks) {
        if (stacks < 0 || stacks > 2) throw new IllegalArgumentException("Threat Detector stacks must be 0..2");
        return stacks;
    }
    public static int stabilityBonus(int stacks) { return new int[]{0, 15, 40}[tier(stacks)]; }
    public static int handlingBonus(int stacks) { return new int[]{0, 25, 100}[tier(stacks)]; }
    public static int reloadBonus(int stacks) { return new int[]{0, 18, 60}[tier(stacks)]; }
    public static double handlingScalar(int stacks) { return new double[]{1, .9, .81}[tier(stacks)]; }
    /** Local inclusive Euclidean footpoint sphere. Nonfinite points never count. */
    public static boolean withinRadius(double dx, double dy, double dz) {
        return Double.isFinite(dx) && Double.isFinite(dy) && Double.isFinite(dz)
            && dx * dx + dy * dy + dz * dz <= 225.0;
    }
    public static boolean supports(WeaponCatalog.Entry entry) {
        if (entry == null || entry.id() == null || !DATA.curves.containsKey(entry.id())) return false;
        var row = CATALOG.get(entry.id());
        return Objects.equals(entry, GSON.fromJson(row, WeaponCatalog.Entry.class));
    }
    private static Curve curve(WeaponCatalog.Entry entry) {
        if (!supports(entry)) throw new IllegalArgumentException("Unsupported/noncanonical Threat Detector entry");
        return DATA.curves.get(entry.id());
    }
    static int effectiveStat(int base, int bonus) { return (int)Math.clamp((long)base + bonus, 0L, 100L); }
    private static void scalar(double value) {
        if (!Double.isFinite(value) || value <= 0 || value > 1) throw new IllegalArgumentException("Finite scalar in (0,1] required");
    }
    private static int quantize(double seconds) {
        check(Double.isFinite(seconds) && seconds >= 0 && seconds <= 60, "unsafe seconds");
        return Math.max(1, (int)Math.ceil(seconds * 20));
    }
    public static int handlingTicks(WeaponCatalog.Entry entry, int totalHandlingBonus, double scalar, boolean ready) {
        var c = curve(entry); scalar(scalar);
        int stat = effectiveStat(c.baseHandlingStat, totalHandlingBonus);
        double seconds = ready ? c.ready.seconds(stat) : Math.max(c.stow.seconds(stat), c.stow.seconds(100));
        return quantize(seconds * scalar);
    }
    /** No Threat Detector ADS animation scalar. Only compatible Snapshot entry scales raw ADS seconds. */
    public static int adsTicks(WeaponCatalog.Entry entry, int totalHandlingBonus, boolean snapshotEntering) {
        var c = curve(entry);
        if (snapshotEntering && c.snapshotScalar == null) throw new IllegalArgumentException("No compatible Snapshot socket");
        double seconds = c.ads.seconds(effectiveStat(c.baseHandlingStat, totalHandlingBonus));
        if (snapshotEntering) seconds *= c.snapshotScalar;
        return Math.clamp(quantize(seconds), snapshotEntering ? 1 : 2, 20);
    }
    private static double reloadSeconds(Curve c, int totalReloadBonus, double reloadScalar) {
        scalar(reloadScalar);
        return c.reload.seconds(effectiveStat(c.baseReloadStat, totalReloadBonus)) * reloadScalar;
    }
    public static int reloadTicks(WeaponCatalog.Entry entry, int totalReloadBonus, double reloadScalar) {
        return quantize(reloadSeconds(curve(entry), totalReloadBonus, reloadScalar));
    }
    /** Exact finite co-selection proof; the selected companion must equal the pinned official roll. */
    static boolean compatible(WeaponCatalog.Entry entry, String perk, WeaponPerks.Roll selected) {
        return supports(entry) && DATA.companions.stream().anyMatch(p -> p.id.equals(entry.id()) && p.perk.equals(perk) && p.roll.equals(selected));
    }
    /** Keep accepted reload topology. Whole magazines and ordinary per-shell curves recompute raw.
     * A distinct authored first/interval delay is not an official measured phase: retain both
     * supplied phases using the ratio between raw TOTAL and raw existing-companion durations.
     * Never compound an already-applied Outlaw/FF scalar, or replace a first delay with interval.
     */
    static WeaponReloadPolicy.Plan reloadPlan(WeaponCatalog.Entry entry, int totalReloadBonus, double reloadScalar,
                                              int existingReloadBonus, double existingReloadScalar,
                                              WeaponReloadPolicy.Plan base) {
        var c = curve(entry);
        double seconds = reloadSeconds(c, totalReloadBonus, reloadScalar);
        if (c.shellReload && base.firstTicks() != base.intervalTicks()) {
            double ratio = seconds / reloadSeconds(c, existingReloadBonus, existingReloadScalar);
            return new WeaponReloadPolicy.Plan(Math.max(1, (int)Math.ceil(base.firstTicks() * ratio)),
                Math.max(1, (int)Math.ceil(base.intervalTicks() * ratio)), base.roundsPerInsert());
        }
        int ticks = quantize(seconds);
        return new WeaponReloadPolicy.Plan(ticks, ticks, base.roundsPerInsert());
    }
}
