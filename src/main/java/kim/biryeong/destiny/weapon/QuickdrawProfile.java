package kim.biryeong.destiny.weapon;

import com.google.gson.*;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.security.*;
import java.util.*;

/** Base Quickdraw only. JSON-only initialization avoids catalog/perk registry recursion.
 * Current official sockets and historical raw curves have separate pinned provenance.
 * Handling is capped at 100; ready-only .95 and legal TD scalar precede one ceil.
 */
public final class QuickdrawProfile {
    public static final String ID = "quickdraw";
    public static final long HASH = 706527188L;
    public static final int DURATION_TICKS = 20;
    public static final double READY_SCALAR = .95;
    private static final Gson GSON = new Gson();
    private static final List<WeaponPerks.Roll> EXPECTED = List.of(
        new WeaponPerks.Roll("blast_furnace",3843477312L,3,HASH,1976101165L),
        new WeaponPerks.Roll("dead_man_walking_xx7463",3751622019L,3,HASH,3268663985L),
        new WeaponPerks.Roll("biting_winds",1621657423L,3,HASH,3968704963L),
        new WeaponPerks.Roll("whispering_slab",211938782L,3,HASH,1885424927L),
        new WeaponPerks.Roll("beloved",3107853529L,4,HASH,887157889L),
        new WeaponPerks.Roll("apostate",2164448701L,4,HASH,2826016044L),
        new WeaponPerks.Roll("parcel_of_stardust_fell_to_earth",2217366863L,4,HASH,3424940310L),
        new WeaponPerks.Roll("hollow_words",607191995L,3,HASH,637298592L),
        new WeaponPerks.Roll("dream_breaker",2931957300L,4,HASH,1206254527L),
        new WeaponPerks.Roll("edge_transit",218335759L,4,HASH,2535579724L),
        new WeaponPerks.Roll("bad_omens",991314988L,4,HASH,2955928741L),
        new WeaponPerks.Roll("bellowing_giant",2186258845L,3,HASH,2605036073L),
        new WeaponPerks.Roll("code_duello",2496242052L,3,HASH,3719628667L),
        new WeaponPerks.Roll("pyroclastic_flow",1289324202L,3,HASH,528513254L),
        new WeaponPerks.Roll("fixed_odds",2194955522L,3,HASH,4227334000L),
        new WeaponPerks.Roll("hammerhead",603242241L,3,HASH,2515290473L));
    private record Quadratic(double evpp, double vpp, double offset) {
        double seconds(int stat) { return evpp * stat * stat + vpp * stat + offset; }
    }
    private record Curve(String id, int baseHandlingStat, Quadratic ready, Quadratic stow) {}
    private record Companion(String id, String perk, WeaponPerks.Roll roll) {}
    private record Data(JsonObject document, List<WeaponPerks.Roll> rolls, Map<String, Curve> curves, List<Companion> companions) {}
    private static final Map<String, JsonObject> CATALOG = byId("/destiny/weapons/w30.json");
    private static final Data DATA = load();
    private QuickdrawProfile() {}
    private static void check(boolean ok, String detail) {
        if (!ok) throw new IllegalStateException("Invalid W185 Quickdraw: " + detail);
    }
    private static byte[] bytes(String path) {
        var input = QuickdrawProfile.class.getResourceAsStream(path);
        check(input != null, "missing " + path);
        try (input) { return input.readAllBytes(); }
        catch (IOException e) { throw new IllegalStateException(e); }
    }
    private static Map<String, JsonObject> byId(String path) {
        var map = new HashMap<String, JsonObject>();
        for (var row : JsonParser.parseString(new String(bytes(path), StandardCharsets.UTF_8)).getAsJsonArray()) {
            var obj = row.getAsJsonObject();check(map.putIfAbsent(obj.get("id").getAsString(), obj) == null, "duplicate ID");
        }
        return Map.copyOf(map);
    }
    private static Data load() {
        var raw = bytes("/destiny/weapons/w185-quickdraw.json");
        try { check(HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw)).equals("c172eaef26e83b16f81586f4dd1e57cd5048600d019d08364e45e59103da94da"), "checksum"); }
        catch (NoSuchAlgorithmException e) { throw new IllegalStateException(e); }
        var root = JsonParser.parseString(new String(raw, StandardCharsets.UTF_8)).getAsJsonObject();
        check(root.keySet().equals(Set.of("stage","perk","weapons","curves","coSelections")) && root.get("stage").getAsString().equals("W185"), "schema");
        var rolls = new ArrayList<WeaponPerks.Roll>();
        for (var row : root.getAsJsonArray("weapons")) {
            var roll = GSON.fromJson(row, WeaponPerks.Roll.class);
            check(EXPECTED.contains(roll) && !rolls.contains(roll) && row.equals(GSON.toJsonTree(roll)), "exact unique base roll");rolls.add(roll);
        }
        check(rolls.size() == 16, "complete16");
        var stats = byId("/destiny/weapons/w40-characteristics.json");
        var handling = byId("/destiny/weapons/w58-handling.json");
        var curves = new HashMap<String, Curve>();
        for (var row : root.getAsJsonArray("curves")) {
            var c = GSON.fromJson(row, Curve.class);
            var roll = EXPECTED.stream().filter(r -> r.id().equals(c.id)).findFirst().orElseThrow();
            check(curves.putIfAbsent(c.id,c) == null && CATALOG.containsKey(c.id), "unique curve");
            var st = stats.get(c.id);var h = handling.get(c.id).getAsJsonObject("profile");
            check(st.get("bungieHash").getAsLong() == roll.hash() && !st.get("exotic").getAsBoolean()
                && st.getAsJsonObject("stats").get("943549884").getAsInt() == c.baseHandlingStat, "official stats");
            check(h.get("supported").getAsBoolean() && quantize(c.ready.seconds(c.baseHandlingStat)) == h.get("readyTicks").getAsInt()
                && quantize(Math.max(c.stow.seconds(c.baseHandlingStat),c.stow.seconds(100))) == h.get("stowTicks").getAsInt(), "raw W58 baseline");
        }
        check(curves.size() == 16, "complete curves");
        var companions = new ArrayList<Companion>();
        for (var row : root.getAsJsonArray("coSelections")) {
            var pair = GSON.fromJson(row,Companion.class);
            var source = EXPECTED.stream().filter(r -> r.id().equals(pair.id)).findFirst().orElseThrow();
            check(source.socket() != pair.roll.socket() && source.hash() == pair.roll.hash() && pair.id.equals(pair.roll.id())
                && !companions.contains(pair), "exact distinct companion");companions.add(pair);
        }
        check(companions.size() == 37 && companions.stream().filter(c -> c.perk.equals("threat_detector")).count() == 4, "companion completeness");
        return new Data(root,List.copyOf(rolls),Map.copyOf(curves),List.copyOf(companions));
    }
    private static int quantize(double seconds) {
        check(Double.isFinite(seconds) && seconds > 0 && seconds <= 60, "safe seconds");
        return Math.max(1,(int)Math.ceil(seconds * 20));
    }
    public static List<WeaponPerks.Roll> rolls() { return DATA.rolls; }
    public static boolean supports(WeaponCatalog.Entry entry) {
        return entry != null && DATA.curves.containsKey(entry.id())
            && Objects.equals(entry,GSON.fromJson(CATALOG.get(entry.id()),WeaponCatalog.Entry.class));
    }
    static boolean compatible(WeaponCatalog.Entry entry, String perk, WeaponPerks.Roll selected) {
        return supports(entry) && DATA.companions.stream().anyMatch(c -> c.id.equals(entry.id()) && c.perk.equals(perk) && c.roll.equals(selected));
    }
    /** Accept only the existing TD scalar table. No multiplication of rounded prior ticks. */
    public static int handlingTicks(WeaponCatalog.Entry entry, double scalar, boolean ready) {
        if (!supports(entry) || !Double.isFinite(scalar) || (scalar != 1 && scalar != .9 && scalar != .81))
            throw new IllegalArgumentException("Canonical Quickdraw entry and sourced TD scalar required");
        if (scalar != 1 && DATA.companions.stream().noneMatch(c -> c.id.equals(entry.id()) && c.perk.equals("threat_detector")))
            throw new IllegalArgumentException("No legal TD pair");
        var c = DATA.curves.get(entry.id());
        return quantize((ready ? c.ready.seconds(100) * READY_SCALAR : c.stow.seconds(100)) * scalar);
    }
    static void validateResource(String json) {
        try { check(JsonParser.parseString(json).equals(DATA.document), "mutated resource"); }
        catch (RuntimeException e) { throw new IllegalStateException("Invalid W185 JSON",e); }
    }
}
