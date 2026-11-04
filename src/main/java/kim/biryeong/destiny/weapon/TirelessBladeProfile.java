package kim.biryeong.destiny.weapon;

import com.google.gson.Gson;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.*;

/** W194 base TirelessBlade, DDC row 230. JSON-only initialization avoids registry cycles. */
public final class TirelessBladeProfile {
    public static final String ID = "tireless_blade";
    public static final long HASH = 2590710093L;
    private static final String SHA256 = "6b2f2a0146d9950a7b2edbb7cdb35db93ec98b601d2e8a3347f484f5b1309782";
    private static final Gson GSON = new Gson();
    private static final List<WeaponPerks.Roll> EXPECTED = List.of(
        new WeaponPerks.Roll("abide_the_return", 1644160541L, 3, HASH, 211008653L),
        new WeaponPerks.Roll("abide_the_return", 1644160541L, 4, HASH, 2761485963L),
        new WeaponPerks.Roll("goldtusk", 3371413057L, 3, HASH, 1162279549L),
        new WeaponPerks.Roll("crown_splitter", 2782325302L, 3, HASH, 427353656L),
        new WeaponPerks.Roll("falling_guillotine", 614426548L, 3, HASH, 2228304432L),
        new WeaponPerks.Roll("temptation_s_hook", 35794111L, 3, HASH, 4018960212L));
    private record Perk(String id, long hash, int kills, int returnRounds, boolean firstKillOnSpawn, boolean persistsThroughStow) {}
    private record Data(String stage, Perk perk, List<WeaponPerks.Roll> weapons) {}
    private static final Map<String, WeaponCatalog.Entry> CATALOG = catalog();
    private static final Data DATA = load();
    private TirelessBladeProfile() {}

    private static byte[] bytes(String path) {
        var stream = TirelessBladeProfile.class.getResourceAsStream(path);
        if (stream == null) throw new IllegalStateException("Missing TirelessBladeProfile resource " + path);
        try (stream) { return stream.readAllBytes(); }
        catch (IOException e) { throw new IllegalStateException(e); }
    }
    private static void check(boolean valid, String reason) {
        if (!valid) throw new IllegalStateException("Invalid W194 TirelessBlade: " + reason);
    }
    private static Map<String, WeaponCatalog.Entry> catalog() {
        var entries = GSON.fromJson(new String(bytes("/destiny/weapons/w30.json"), StandardCharsets.UTF_8),
            WeaponCatalog.Entry[].class);
        var map = new HashMap<String, WeaponCatalog.Entry>();
        for (var e : entries) check(map.putIfAbsent(e.id(), e) == null, "unique canonical catalog");
        return Map.copyOf(map);
    }
    private static Data load() {
        var raw = bytes("/destiny/weapons/w194-tireless-blade.json");
        try { check(HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw)).equals(SHA256),
                    "resource checksum"); }
        catch (NoSuchAlgorithmException e) { throw new IllegalStateException(e); }
        var d = GSON.fromJson(new String(raw, StandardCharsets.UTF_8), Data.class);
        check(d != null && "W194".equals(d.stage) && d.perk != null && ID.equals(d.perk.id)
            && d.perk.hash == HASH && d.perk.kills == 2 && d.perk.returnRounds == 1 && d.perk.firstKillOnSpawn == true && d.perk.persistsThroughStow == true, "base perk values");
        check(EXPECTED.equals(d.weapons), "exact base Trait socket tuples");
        for (var r : d.weapons) check(CATALOG.containsKey(r.id()), "canonical catalog source");
        return new Data(d.stage, d.perk, List.copyOf(d.weapons));
    }
    public static List<WeaponPerks.Roll> rolls() { return DATA.weapons; }
    public static boolean supports(WeaponCatalog.Entry entry) {
        return entry != null && "sword".equals(entry.family()) && entry.equals(CATALOG.get(entry.id()))
            && DATA.weapons.stream().anyMatch(r -> r.id().equals(entry.id()));
    }
    public static int kills() { return DATA.perk.kills; }
    public static int returnRounds() { return DATA.perk.returnRounds; }
    public static boolean firstKillOnSpawn() { return DATA.perk.firstKillOnSpawn; }
    public static boolean persistsThroughStow() { return DATA.perk.persistsThroughStow; }
}
