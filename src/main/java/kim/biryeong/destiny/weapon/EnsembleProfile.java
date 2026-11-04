package kim.biryeong.destiny.weapon;

import com.google.gson.*;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.security.*;
import java.util.*;

/** Exact base Ensemble. JSON-only loading avoids catalog/perk registry initialization cycles.
 * Current official sockets and DDC stats are separate from historical raw timing curves.
 */
public final class EnsembleProfile {
    public static final String ID = "ensemble";
    public static final long HASH = 2621346526L;
    private static final Gson GSON = new Gson();
    private static final WeaponPerks.Roll EXPECTED = new WeaponPerks.Roll("canis_major", 2066434718L, 3, HASH, 4037911937L);
    private record Quadratic(double evpp, double vpp, double offset) {
        double seconds(int stat) { return evpp * stat * stat + vpp * stat + offset; }
    }
    private record Perk(String id, long hash, double radiusMetres, int handlingBonus, int reloadBonus,
                        double lingerSeconds, int lingerTicks) {}
    private record Curve(String id, int baseReloadStat, int baseHandlingStat, boolean shellReload,
                         int reloadStatCap, Double snapshotScalar, Quadratic reload, Quadratic ready,
                         Quadratic stow, Quadratic ads) {}
    private record Companion(String id, String perk, WeaponPerks.Roll roll) {}
    private record Data(Perk perk, Curve curve, List<Companion> companions) {}
    private static final JsonObject CANONICAL = canonical();
    private static final Data DATA = load();
    private EnsembleProfile() {}

    private static void check(boolean ok, String detail) {
        if (!ok) throw new IllegalStateException("Invalid W190 Ensemble: " + detail);
    }
    private static byte[] bytes(String path) {
        var input = EnsembleProfile.class.getResourceAsStream(path);
        check(input != null, "missing " + path);
        try (input) { return input.readAllBytes(); }
        catch (IOException e) { throw new IllegalStateException(e); }
    }
    private static JsonObject row(String path) {
        for (var value : JsonParser.parseString(new String(bytes(path), StandardCharsets.UTF_8)).getAsJsonArray()) {
            var row = value.getAsJsonObject();
            if (row.get("id").getAsString().equals(EXPECTED.id())) return row;
        }
        throw new IllegalStateException("Missing canonical Canis Major: " + path);
    }
    private static JsonObject canonical() { return row("/destiny/weapons/w30.json"); }
    private static Data load() {
        var raw = bytes("/destiny/weapons/w190-ensemble.json");
        try {
            check(HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw))
                .equals("c9bb34781cac526b2269a88527c3f91c20cc628e850f0ea23f188357e96e6d3d"), "resource checksum");
        } catch (NoSuchAlgorithmException e) { throw new IllegalStateException(e); }
        var root = JsonParser.parseString(new String(raw, StandardCharsets.UTF_8)).getAsJsonObject();
        check(root.keySet().equals(Set.of("stage", "perk", "policies", "weapons", "curves", "coSelections"))
            && root.get("stage").getAsString().equals("W190"), "schema");
        check(root.getAsJsonArray("weapons").size() == 1
            && root.getAsJsonArray("weapons").get(0).equals(GSON.toJsonTree(EXPECTED)), "exact base socket3");
        var perk = GSON.fromJson(root.get("perk"), Perk.class);
        check(perk.id.equals(ID) && perk.hash == HASH && perk.lingerTicks == EnsembleCycle.LINGER_TICKS
            && perk.lingerSeconds * 20 == perk.lingerTicks, "base identity and exact tick conversion");
        check(root.getAsJsonArray("curves").size() == 1, "single curve");
        var curve = GSON.fromJson(root.getAsJsonArray("curves").get(0), Curve.class);
        var stats = row("/destiny/weapons/w40-characteristics.json");
        var timing = row("/destiny/weapons/w46-timing.json").getAsJsonObject("timing");
        var handling = row("/destiny/weapons/w58-handling.json").getAsJsonObject("profile");
        var aim = row("/destiny/weapons/w44-aim.json").getAsJsonObject("profile");
        check(curve.id.equals(EXPECTED.id()) && stats.get("bungieHash").getAsLong() == EXPECTED.hash()
            && !stats.get("exotic").getAsBoolean() && curve.baseReloadStat == stats.getAsJsonObject("stats").get("4188031367").getAsInt()
            && curve.baseHandlingStat == stats.getAsJsonObject("stats").get("943549884").getAsInt()
            && !curve.shellReload && curve.reloadStatCap == 100 && curve.snapshotScalar == null, "canonical stats/topology");
        check(timing.get("supported").getAsBoolean() && !timing.get("shellReload").getAsBoolean()
            && handling.get("supported").getAsBoolean()
            && ticks(curve.reload.seconds(curve.baseReloadStat)) == timing.get("reloadTicks").getAsInt()
            && ticks(curve.ready.seconds(curve.baseHandlingStat)) == handling.get("readyTicks").getAsInt()
            && ticks(Math.max(curve.stow.seconds(curve.baseHandlingStat), curve.stow.seconds(100))) == handling.get("stowTicks").getAsInt()
            && Math.clamp(ticks(curve.ads.seconds(curve.baseHandlingStat)), 2, 20) == aim.get("transitionTicks").getAsInt(), "raw timing baselines");
        var companions = new ArrayList<Companion>();
        for (var value : root.getAsJsonArray("coSelections")) {
            var pair = GSON.fromJson(value, Companion.class);
            check(pair.id.equals(EXPECTED.id()) && pair.roll.id().equals(pair.id) && pair.roll.hash() == EXPECTED.hash()
                && pair.roll.socket() == 4 && pair.roll.plugSetHash() == 2791121719L
                && !companions.contains(pair), "exact distinct companion");
            companions.add(pair);
        }
        check(companions.size() == 3 && companions.stream().map(Companion::perk).collect(java.util.stream.Collectors.toSet())
            .equals(Set.of("kill_clip", "rampage", "vorpal")), "no co-selected stat providers; Surplus is same socket");
        return new Data(perk, curve, List.copyOf(companions));
    }
    public static List<WeaponPerks.Roll> rolls() { return List.of(EXPECTED); }
    public static boolean supports(WeaponCatalog.Entry entry) {
        return entry != null && Objects.equals(entry, GSON.fromJson(CANONICAL, WeaponCatalog.Entry.class));
    }
    public static int handlingBonus() { return DATA.perk.handlingBonus; }
    public static int reloadBonus() { return DATA.perk.reloadBonus; }
    public static double radius() { return DATA.perk.radiusMetres; }
    public static int lingerTicks() { return DATA.perk.lingerTicks; }
    public static boolean withinRadius(double dx, double dy, double dz) {
        return Double.isFinite(dx) && Double.isFinite(dy) && Double.isFinite(dz)
            && dx * dx + dy * dy + dz * dz <= radius() * radius();
    }
    static boolean compatible(WeaponCatalog.Entry entry, String perk, WeaponPerks.Roll selected) {
        return supports(entry) && DATA.companions.stream().anyMatch(c -> c.perk.equals(perk) && c.roll.equals(selected));
    }
    private static Curve curve(WeaponCatalog.Entry entry) {
        if (!supports(entry)) throw new IllegalArgumentException("Noncanonical Ensemble source");
        return DATA.curve;
    }
    private static int stat(int base, int totalBonus) { return (int)Math.clamp((long)base + totalBonus, 0L, 100L); }
    private static int ticks(double seconds) {
        check(Double.isFinite(seconds) && seconds > 0 && seconds <= 60, "safe raw seconds");
        return Math.max(1, (int)Math.ceil(seconds * 20));
    }
    /** Total bonuses, never rounded prior ticks. There is no legal companion scalar in exact1. */
    public static int handlingTicks(WeaponCatalog.Entry entry, int totalHandlingBonus, boolean ready) {
        var c = curve(entry);
        int h = stat(c.baseHandlingStat, totalHandlingBonus);
        return ticks(ready ? c.ready.seconds(h) : Math.max(c.stow.seconds(h), c.stow.seconds(100)));
    }
    public static int adsTicks(WeaponCatalog.Entry entry, int totalHandlingBonus) {
        var c = curve(entry);
        return Math.clamp(ticks(c.ads.seconds(stat(c.baseHandlingStat, totalHandlingBonus))), 2, 20);
    }
    public static int reloadTicks(WeaponCatalog.Entry entry, int totalReloadBonus) {
        var c = curve(entry);
        return ticks(c.reload.seconds(stat(c.baseReloadStat, totalReloadBonus)));
    }
    /** Whole-magazine Canis Major only; the immutable accepted Plan is never retimed later. */
    static WeaponReloadPolicy.Plan reloadPlan(WeaponCatalog.Entry entry, int totalReloadBonus, WeaponReloadPolicy.Plan base) {
        if (base.incremental()) throw new IllegalArgumentException("Foreign incremental Ensemble plan");
        int ticks = reloadTicks(entry, totalReloadBonus);
        return new WeaponReloadPolicy.Plan(ticks, ticks, base.roundsPerInsert());
    }
}
