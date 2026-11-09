package kim.biryeong.destiny.weapon;

import com.google.gson.Gson;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.*;

/** W193 base Overflow, DDC row 161. JSON-only initialization avoids registry cycles. */
public final class OverflowProfile {
    public static final String ID = "overflow";
    public static final long HASH = 3643424744L;
    private static final String SHA256 = "8cd3a8a034557bc79cd83ec801edf105eff66870900689fdd09edfce3dd17cb6";
    private static final Gson GSON = new Gson();
    private static final List<WeaponPerks.Roll> EXPECTED = List.of(
        new WeaponPerks.Roll("gnawing_hunger", 821154603L, 3, HASH, 1144396384L),
        new WeaponPerks.Roll("lonesome", 2199171672L, 3, HASH, 3612808001L),
        new WeaponPerks.Roll("brass_attacks", 2121785039L, 3, HASH, 100135553L));
    private record Perk(String id, long hash, int magazineMultiplier) {}
    private record Data(String stage, Perk perk, List<WeaponPerks.Roll> weapons) {}
    private static final Map<String, WeaponCatalog.Entry> CATALOG = catalog();
    private static final Data DATA = load();
    private OverflowProfile() {}

    private static byte[] bytes(String path) {
        var stream = OverflowProfile.class.getResourceAsStream(path);
        if (stream == null) throw new IllegalStateException("Missing OverflowProfile resource " + path);
        try (stream) { return stream.readAllBytes(); }
        catch (IOException e) { throw new IllegalStateException(e); }
    }
    private static void check(boolean valid, String reason) {
        if (!valid) throw new IllegalStateException("Invalid W193 Overflow: " + reason);
    }
    private static Map<String, WeaponCatalog.Entry> catalog() {
        var entries = GSON.fromJson(new String(bytes("/destiny/weapons/w30.json"), StandardCharsets.UTF_8),
            WeaponCatalog.Entry[].class);
        var map = new HashMap<String, WeaponCatalog.Entry>();
        for (var e : entries) check(map.putIfAbsent(e.id(), e) == null, "unique canonical catalog");
        return Map.copyOf(map);
    }
    private static Data load() {
        var raw = bytes("/destiny/weapons/w193-overflow.json");
        try { check(HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw)).equals(SHA256),
                    "resource checksum"); }
        catch (NoSuchAlgorithmException e) { throw new IllegalStateException(e); }
        var d = GSON.fromJson(new String(raw, StandardCharsets.UTF_8), Data.class);
        check(d != null && "W193".equals(d.stage) && d.perk != null && ID.equals(d.perk.id)
            && d.perk.hash == HASH && d.perk.magazineMultiplier == 2, "base perk values");
        check(EXPECTED.equals(d.weapons), "exact three base Trait socket tuples");
        for (var r : d.weapons) check(CATALOG.containsKey(r.id()), "canonical catalog source");
        return new Data(d.stage, d.perk, List.copyOf(d.weapons));
    }
    public static List<WeaponPerks.Roll> rolls() { return LegendaryPerks.expandRolls(ID, DATA.weapons); }
    public static boolean supports(WeaponCatalog.Entry entry) {
        return entry != null && (entry.equals(CATALOG.get(entry.id())) || LegendaryWeapons.contains(entry.id())
                && WeaponCatalog.find(entry.id()).filter(entry::equals).isPresent())
            && rolls().stream().anyMatch(r -> r.id().equals(entry.id()));
    }
    /** Pure capacity target; no pickup, magazine, reserve or item mutation. */
    public static int target(WeaponCatalog.Entry entry) {
        if (!supports(entry)) return 0;
        return Math.multiplyExact(WeaponProfile.forEntry(entry).magazine(), DATA.perk.magazineMultiplier);
    }
}
