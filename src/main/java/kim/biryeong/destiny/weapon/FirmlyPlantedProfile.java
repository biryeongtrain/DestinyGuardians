package kim.biryeong.destiny.weapon;

import com.google.gson.*;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.security.*;
import java.util.*;

/** Exact base Firmly Planted effects only; actual crouch and source authority belong to the caller.
 * Unsupported/noncanonical entries have neutral effects (0/1); timing queries reject them.
 * Timing arguments are TOTAL bonuses, including this perk and all legal companions. Evaluate
 * original raw seconds at capped total handling, apply caller scalar, then ceil once at 20 TPS.
 * No registry/catalog initialization calls, gameplay state, reload/damage or proc HUD behavior.
 */
public final class FirmlyPlantedProfile {
    public static final String ID = "firmly_planted";
    public static final long HASH = 280464955L;
    private static final String RESOURCE = "/destiny/weapons/w189-firmly_planted.json";
    private static final String SHA256 = "fe895460277f88f51fa7e05d593589b0c935fc17ba218a67c3786f3a918dd10b";
    private static final Gson GSON = new GsonBuilder().serializeNulls().create();
    private static final List<WeaponPerks.Roll> EXPECTED = List.of(
        new WeaponPerks.Roll("seventh_seraph_officer_revolver",3037520408L,3,HASH,903350103L),
        new WeaponPerks.Roll("steelfeather_repeater",1251729046L,3,HASH,473189353L),
        new WeaponPerks.Roll("distant_relation",2034817450L,4,HASH,3824767299L),
        new WeaponPerks.Roll("whispering_slab",211938782L,3,HASH,1885424927L),
        new WeaponPerks.Roll("bite_of_the_fox",1403800851L,3,HASH,563442205L),
        new WeaponPerks.Roll("beloved",3107853529L,3,HASH,1196545279L),
        new WeaponPerks.Roll("apostate",2164448701L,3,HASH,1306932196L),
        new WeaponPerks.Roll("dream_breaker",2931957300L,3,HASH,3785896921L));
    private record Quadratic(double evpp, double vpp, double offset) {
        double seconds(int stat) { return evpp * stat * stat + vpp * stat + offset; }
    }
    private record Curve(String id, int baseHandlingStat, Double snapshotScalar,
                         Quadratic ready, Quadratic stow, Quadratic ads) {}
    private record Effect(int stabilityBonus, int handlingBonus, double accuracyScalar,
                          double growthScalar, double yawScalar) {}
    private record Companion(String id, String perk, WeaponPerks.Roll roll) {}
    private record Data(JsonObject document, List<WeaponPerks.Roll> rolls, Map<String, Curve> curves,
                        List<Companion> companions, Effect ordinary, Effect fusion) {}
    private static final Map<String, JsonObject> CATALOG = byId("/destiny/weapons/w30.json");
    private static final Data DATA = load();
    private FirmlyPlantedProfile() {}
    private static void check(boolean ok, String detail) {
        if (!ok) throw new IllegalStateException("Invalid W189 Firmly Planted: " + detail);
    }
    private static byte[] bytes(String path) {
        var in = FirmlyPlantedProfile.class.getResourceAsStream(path);
        check(in != null, "missing " + path);
        try (in) { return in.readAllBytes(); }
        catch (IOException e) { throw new IllegalStateException(e); }
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
        try { check(HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw)).equals(SHA256), "checksum"); }
        catch (NoSuchAlgorithmException e) { throw new IllegalStateException(e); }
        var root = JsonParser.parseString(new String(raw, StandardCharsets.UTF_8)).getAsJsonObject();
        check(root.keySet().equals(Set.of("stage","perk","policies","weapons","curves","coSelections"))
            && root.get("stage").getAsString().equals("W189"), "schema");
        var perk = root.getAsJsonObject("perk");
        check(perk.get("id").getAsString().equals(ID) && perk.get("hash").getAsLong() == HASH, "base identity");
        var ordinary = GSON.fromJson(perk.get("ordinary"), Effect.class);
        var fusion = GSON.fromJson(perk.get("fusion"), Effect.class);
        check(ordinary.equals(new Effect(20,30,.6,.83,.2)) && fusion.equals(new Effect(10,15,.8,.915,.6)), "DDC base effects");
        var rolls = new ArrayList<WeaponPerks.Roll>();
        for (var value : root.getAsJsonArray("weapons")) {
            var roll = GSON.fromJson(value, WeaponPerks.Roll.class);
            check(EXPECTED.contains(roll) && !rolls.contains(roll) && value.equals(GSON.toJsonTree(roll)), "exact unique base roll");
            rolls.add(roll);
        }
        check(rolls.equals(EXPECTED), "complete exact8");
        var stats = byId("/destiny/weapons/w40-characteristics.json");
        var handling = byId("/destiny/weapons/w58-handling.json");
        var aim = byId("/destiny/weapons/w44-aim.json");
        var curves = new HashMap<String, Curve>();
        for (var value : root.getAsJsonArray("curves")) {
            var c = GSON.fromJson(value, Curve.class);
            check(curves.putIfAbsent(c.id,c) == null && CATALOG.containsKey(c.id), "unique canonical curve");
            var roll = EXPECTED.stream().filter(r -> r.id().equals(c.id)).findFirst().orElseThrow();
            var s = stats.get(c.id); var h = handling.get(c.id).getAsJsonObject("profile");
            check(s.get("bungieHash").getAsLong() == roll.hash() && !s.get("exotic").getAsBoolean()
                && s.getAsJsonObject("stats").get("943549884").getAsInt() == c.baseHandlingStat, "original/current base stat");
            check(h.get("supported").getAsBoolean()
                && quantize(c.ready.seconds(c.baseHandlingStat)) == h.get("readyTicks").getAsInt()
                && quantize(Math.max(c.stow.seconds(c.baseHandlingStat),c.stow.seconds(100))) == h.get("stowTicks").getAsInt()
                && Math.clamp(quantize(c.ads.seconds(c.baseHandlingStat)),2,20)
                    == aim.get(c.id).getAsJsonObject("profile").get("transitionTicks").getAsInt(), "raw timing baselines");
            check(c.id.equals("apostate") ? Objects.equals(c.snapshotScalar,.8) : c.snapshotScalar == null, "exact Snapshot scalar");
        }
        check(curves.keySet().equals(EXPECTED.stream().map(WeaponPerks.Roll::id).collect(java.util.stream.Collectors.toSet())), "complete eight curves");
        var companions = new ArrayList<Companion>();
        for (var value : root.getAsJsonArray("coSelections")) {
            var pair = GSON.fromJson(value, Companion.class);
            var source = EXPECTED.stream().filter(r -> r.id().equals(pair.id)).findFirst().orElseThrow();
            check(pair.roll != null && source.socket() != pair.roll.socket() && source.hash() == pair.roll.hash()
                && pair.id.equals(pair.roll.id()) && !companions.contains(pair)
                && value.equals(GSON.toJsonTree(pair)), "exact distinct companion");
            companions.add(pair);
        }
        check(companions.size() == 32, "complete implemented distinct pairs");
        return new Data(root,List.copyOf(rolls),Map.copyOf(curves),List.copyOf(companions),ordinary,fusion);
    }
    public static List<WeaponPerks.Roll> rolls() { return DATA.rolls; }
    public static boolean supports(WeaponCatalog.Entry entry) {
        return entry != null && entry.id() != null && DATA.curves.containsKey(entry.id())
            && entry.equals(GSON.fromJson(CATALOG.get(entry.id()),WeaponCatalog.Entry.class));
    }
    private static Effect effect(WeaponCatalog.Entry entry) {
        return !supports(entry) ? null : entry.family().equals("fusion_rifle") ? DATA.fusion : DATA.ordinary;
    }
    public static int stabilityBonus(WeaponCatalog.Entry entry) { var e=effect(entry); return e==null ? 0 : e.stabilityBonus; }
    public static int handlingBonus(WeaponCatalog.Entry entry) { var e=effect(entry); return e==null ? 0 : e.handlingBonus; }
    public static double accuracyScalar(WeaponCatalog.Entry entry) { var e=effect(entry); return e==null ? 1 : e.accuracyScalar; }
    public static double growthScalar(WeaponCatalog.Entry entry) { var e=effect(entry); return e==null ? 1 : e.growthScalar; }
    /** Horizontal recoil only. No pitch scalar or recoil-direction-stat bonus. */
    public static double yawScalar(WeaponCatalog.Entry entry) { var e=effect(entry); return e==null ? 1 : e.yawScalar; }
    public static boolean compatible(WeaponCatalog.Entry entry, String perk, WeaponPerks.Roll selected) {
        return supports(entry) && DATA.companions.stream().anyMatch(c -> c.id.equals(entry.id()) && c.perk.equals(perk) && c.roll.equals(selected));
    }
    private static Curve curve(WeaponCatalog.Entry entry) {
        if (!supports(entry)) throw new IllegalArgumentException("Canonical supported Firmly Planted entry required");
        return DATA.curves.get(entry.id());
    }
    static int effectiveStat(int base, int totalBonus) { return (int)Math.clamp((long)base+totalBonus,0L,100L); }
    private static int quantize(double seconds) {
        check(Double.isFinite(seconds) && seconds > 0 && seconds <= 60, "safe seconds");
        return Math.max(1,(int)Math.ceil(seconds * 20));
    }
    /** TOTALbonus already includes FP. Scalar includes any legal ready-only Quickdraw .95.
     * Caller owns selected companion authority; never pass a previously rounded duration.
     */
    public static int handlingTicks(WeaponCatalog.Entry entry, int totalBonus, double scalar, boolean ready) {
        var c=curve(entry);
        if (!Double.isFinite(scalar) || scalar <= 0 || scalar > 1) throw new IllegalArgumentException("Scalar must be finite in (0,1]");
        int stat=effectiveStat(c.baseHandlingStat,totalBonus);
        return quantize((ready ? c.ready.seconds(stat) : Math.max(c.stow.seconds(stat),c.stow.seconds(100))) * scalar);
    }
    /** Snapshot affects entering only; false is also used for exit. No handling scalar affects ADS. */
    public static int adsTicks(WeaponCatalog.Entry entry, int totalBonus, boolean snapshotEntering) {
        var c=curve(entry);
        if (snapshotEntering && c.snapshotScalar==null) throw new IllegalArgumentException("No distinct Snapshot pair");
        double seconds=c.ads.seconds(effectiveStat(c.baseHandlingStat,totalBonus));
        if (snapshotEntering) seconds*=c.snapshotScalar;
        return Math.clamp(quantize(seconds),snapshotEntering ? 1 : 2,20);
    }
    static void validateResource(String json) {
        try { check(JsonParser.parseString(json).equals(DATA.document), "mutated resource"); }
        catch (RuntimeException e) { throw new IllegalStateException("Invalid W189 JSON",e); }
    }
}
