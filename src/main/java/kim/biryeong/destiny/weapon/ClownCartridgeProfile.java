package kim.biryeong.destiny.weapon;

import com.google.gson.Gson;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.*;

/** W193 base Clown Cartridge, DDC row 48. JSON-only initialization avoids registry cycles. */
public final class ClownCartridgeProfile {
    public static final String ID = "clown_cartridge";
    public static final long HASH = 2284787283L;
    private static final String SHA256 = "067b387162883830199e37519a3bc40a7616aed9820f170f7ed4058ef1ed8698";
    private static final Gson GSON = new Gson();
    private static final List<WeaponPerks.Roll> EXPECTED = List.of(
        new WeaponPerks.Roll("line_in_the_sand", 946443267L, 4, HASH, 3257645194L),
        new WeaponPerks.Roll("stormchaser", 3652506829L, 3, HASH, 897699284L),
        new WeaponPerks.Roll("canis_major", 2066434718L, 3, HASH, 4037911937L));
    private record Perk(String id, long hash, int minimumBonusPercent, int maximumBonusPercent, String sampling) {}
    private record Data(String stage, Perk perk, List<WeaponPerks.Roll> weapons) {}
    private static final Map<String, WeaponCatalog.Entry> CATALOG = catalog();
    private static final Data DATA = load();
    private ClownCartridgeProfile() {}

    private static byte[] bytes(String path) {
        var stream = ClownCartridgeProfile.class.getResourceAsStream(path);
        if (stream == null) throw new IllegalStateException("Missing ClownCartridgeProfile resource " + path);
        try (stream) { return stream.readAllBytes(); }
        catch (IOException e) { throw new IllegalStateException(e); }
    }
    private static void check(boolean valid, String reason) {
        if (!valid) throw new IllegalStateException("Invalid W193 Clown Cartridge: " + reason);
    }
    private static Map<String, WeaponCatalog.Entry> catalog() {
        var entries = GSON.fromJson(new String(bytes("/destiny/weapons/w30.json"), StandardCharsets.UTF_8),
            WeaponCatalog.Entry[].class);
        var map = new HashMap<String, WeaponCatalog.Entry>();
        for (var e : entries) check(map.putIfAbsent(e.id(), e) == null, "unique canonical catalog");
        return Map.copyOf(map);
    }
    private static Data load() {
        var raw = bytes("/destiny/weapons/w193-clown-cartridge.json");
        try { check(HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw)).equals(SHA256),
                    "resource checksum"); }
        catch (NoSuchAlgorithmException e) { throw new IllegalStateException(e); }
        var d = GSON.fromJson(new String(raw, StandardCharsets.UTF_8), Data.class);
        check(d != null && "W193".equals(d.stage) && d.perk != null && ID.equals(d.perk.id)
            && d.perk.hash == HASH && d.perk.minimumBonusPercent == 10 && d.perk.maximumBonusPercent == 50
                && "uniform_integer_inclusive".equals(d.perk.sampling), "base perk values");
        check(EXPECTED.equals(d.weapons), "exact three base Trait socket tuples");
        for (var r : d.weapons) check(CATALOG.containsKey(r.id()), "canonical catalog source");
        return new Data(d.stage, d.perk, List.copyOf(d.weapons));
    }
    public static List<WeaponPerks.Roll> rolls() { return DATA.weapons; }
    public static boolean supports(WeaponCatalog.Entry entry) {
        return entry != null && entry.equals(CATALOG.get(entry.id()))
            && DATA.weapons.stream().anyMatch(r -> r.id().equals(entry.id()));
    }
    public static int minimumBonusPercent() { return DATA.perk.minimumBonusPercent; }
    public static int maximumBonusPercent() { return DATA.perk.maximumBonusPercent; }
    /** Exact integer ceil(base * (1 + bonus/100)); sampling belongs to the completion event. */
    public static int target(WeaponCatalog.Entry entry, int bonusPercent) {
        if (!supports(entry) || bonusPercent < minimumBonusPercent() || bonusPercent > maximumBonusPercent()) return 0;
        long scaled = (long)WeaponProfile.forEntry(entry).magazine() * (100 + bonusPercent);
        return Math.toIntExact((scaled + 99) / 100);
    }
    public static int maximumTarget(WeaponCatalog.Entry entry) { return target(entry, maximumBonusPercent()); }
}
