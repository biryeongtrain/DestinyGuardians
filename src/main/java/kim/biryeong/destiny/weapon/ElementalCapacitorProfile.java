package kim.biryeong.destiny.weapon;

import com.google.gson.*;
import kim.biryeong.destiny.guardian.Element;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.*;

/** Exact base Elemental Capacitor, not enhanced or a family grant.
 * All timing arguments are TOTALS; apply capped stats and scalars to raw seconds, ceil once.
 * Initialization is JSON-only, with no catalog/perk registry/characteristics initialization cycle.
 * Official current sockets and historical community curves have separate pinned provenance.
 */
public final class ElementalCapacitorProfile {
    public static final String ID = "elemental_capacitor";
    public static final long HASH = 3511092054L;
    private static final String RESOURCE = "/destiny/weapons/w184-elemental_capacitor.json";
    private static final String SHA256 = "254c688e41275e59e153238523a36e22a6b107945c0c8a48ed0ef0966fa5ff1c";
    private static final Gson GSON = new GsonBuilder().serializeNulls().create();
    private static final List<WeaponPerks.Roll> EXPECTED = List.of(
        new WeaponPerks.Roll("steelfeather_repeater",1251729046L,4,HASH,2645685327L),
        new WeaponPerks.Roll("patron_of_lost_causes",2723241847L,4,HASH,120674550L));
    private record Quadratic(double evpp, double vpp, double offset) {
        double seconds(int stat) { return evpp * stat * stat + vpp * stat + offset; }
    }
    private record Curve(String id, int baseReloadStat, int baseHandlingStat, boolean shellReload, int reloadStatCap,
                         Double snapshotScalar, Quadratic reload, Quadratic ready, Quadratic stow, Quadratic ads) {}
    private record Companion(String id, String perk, WeaponPerks.Roll roll) {}
    private record Data(JsonObject document, List<WeaponPerks.Roll> rolls, Map<String, Curve> curves,
                        List<Companion> companions) {}
    private static final Map<String, JsonObject> CATALOG = byId("/destiny/weapons/w30.json");
    private static final Data DATA = load();
    private ElementalCapacitorProfile() {}
    private static void check(boolean ok, String detail) {
        if (!ok) throw new IllegalStateException("Invalid W184 ElementalCapacitor: " + detail);
    }
    private static byte[] bytes(String path) {
        var stream = ElementalCapacitorProfile.class.getResourceAsStream(path);
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
            && root.get("stage").getAsString().equals("W184"), "schema");
        var rolls = new ArrayList<WeaponPerks.Roll>();
        for (var row : root.getAsJsonArray("weapons")) {
            var roll = GSON.fromJson(row, WeaponPerks.Roll.class);
            check(EXPECTED.contains(roll) && !rolls.contains(roll) && row.equals(GSON.toJsonTree(roll)), "exact unique base roll");
            rolls.add(roll);
        }
        check(rolls.size() == 2, "complete exact2");
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
                && t.get("shellReload").getAsBoolean() == c.shellReload
                && c.reloadStatCap == ("bow".equals(CATALOG.get(c.id).get("family").getAsString()) ? 85 : 100), "supported reload topology");
            check(quantize(c.reload.seconds(Math.min(c.reloadStatCap, c.baseReloadStat))) == t.get(c.shellReload ? "reloadPerRoundTicks" : "reloadTicks").getAsInt()
                && quantize(c.ready.seconds(c.baseHandlingStat)) == h.get("readyTicks").getAsInt()
                && quantize(Math.max(c.stow.seconds(c.baseHandlingStat), c.stow.seconds(100))) == h.get("stowTicks").getAsInt()
                && Math.clamp(quantize(c.ads.seconds(c.baseHandlingStat)), 2, 20)
                    == aim.get(c.id).getAsJsonObject("profile").get("transitionTicks").getAsInt(), "four raw baselines");
        }
        check(curves.size() == 2, "complete two curves");
        var companions = new ArrayList<Companion>();
        for (var row : root.getAsJsonArray("coSelections")) {
            var pair = GSON.fromJson(row, Companion.class);
            var source = EXPECTED.stream().filter(r -> r.id().equals(pair.id)).findFirst().orElseThrow();
            check(source.socket() != pair.roll.socket() && source.hash() == pair.roll.hash()
                && pair.id.equals(pair.roll.id()) && !companions.contains(pair), "distinct compatible pair");
            companions.add(pair);
        }
        check(companions.size() == 5, "five compatible implemented pairs");
        return new Data(root, List.copyOf(rolls), Map.copyOf(curves), List.copyOf(companions));
    }
    /** Test the same pinned semantic document, without changing live state. */
    static void validateResource(String json) {
        try { check(JsonParser.parseString(json).equals(DATA.document), "mutated resource"); }
        catch (RuntimeException e) { throw new IllegalStateException("Invalid W184 JSON", e); }
    }
    public static List<WeaponPerks.Roll> rolls() { return DATA.rolls; }
    /** KINETIC and absent element are invalid/neutral; Stasis/Strand do not exist in Element. */
    public static int stabilityBonus(Element element) { return element == Element.VOID ? 20 : 0; }
    public static int handlingBonus(Element element) { return element == Element.ARC ? 50 : 0; }
    public static int reloadBonus(Element element) { return element == Element.SOLAR ? 50 : 0; }
    public static boolean supports(WeaponCatalog.Entry entry) {
        if (entry == null || entry.id() == null || !DATA.curves.containsKey(entry.id())) return false;
        var row = CATALOG.get(entry.id());
        return Objects.equals(entry, GSON.fromJson(row, WeaponCatalog.Entry.class));
    }
    private static Curve curve(WeaponCatalog.Entry entry) {
        if (!supports(entry)) throw new IllegalArgumentException("Unsupported/noncanonical ElementalCapacitor entry");
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
    /** No EC ADS scalar; only the ARC handling stat changes raw ADS duration. No selected Snapshot pair. */
    public static int adsTicks(WeaponCatalog.Entry entry, int totalHandlingBonus, boolean snapshotEntering) {
        var c = curve(entry);
        if (snapshotEntering && c.snapshotScalar == null) throw new IllegalArgumentException("No compatible Snapshot socket");
        double seconds = c.ads.seconds(effectiveStat(c.baseHandlingStat, totalHandlingBonus));
        if (snapshotEntering) seconds *= c.snapshotScalar;
        return Math.clamp(quantize(seconds), snapshotEntering ? 1 : 2, 20);
    }
    private static double reloadSeconds(Curve c, int totalReloadBonus, double reloadScalar) {
        scalar(reloadScalar);
        return c.reload.seconds(Math.min(c.reloadStatCap, effectiveStat(c.baseReloadStat, totalReloadBonus))) * reloadScalar;
    }
    public static int reloadTicks(WeaponCatalog.Entry entry, int totalReloadBonus, double reloadScalar) {
        return quantize(reloadSeconds(curve(entry), totalReloadBonus, reloadScalar));
    }
    /** Exact finite co-selection proof; the selected companion must equal the pinned official roll. */
    static boolean compatible(WeaponCatalog.Entry entry, String perk, WeaponPerks.Roll selected) {
        return supports(entry) && DATA.companions.stream().anyMatch(p -> p.id.equals(entry.id()) && p.perk.equals(perk) && p.roll.equals(selected));
    }
    /** Both exact selected weapons use whole-magazine reload. Compute raw total once and retain
     * the accepted plan's insertion topology. No multiplication of already rounded ticks.
     */
    static WeaponReloadPolicy.Plan reloadPlan(WeaponCatalog.Entry entry, int totalReloadBonus, double reloadScalar,
                                              WeaponReloadPolicy.Plan base) {
        int ticks = reloadTicks(entry, totalReloadBonus, reloadScalar);
        return new WeaponReloadPolicy.Plan(ticks, ticks, base.roundsPerInsert());
    }
}
