package kim.biryeong.destiny.weapon;

import com.google.gson.Gson;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.*;

/** W195 base EnGarde, DDC row 82. JSON-only initialization avoids registry cycles. */
public final class EnGardeProfile {
    public static final String ID = "en_garde";
    public static final long HASH = 1685431615L;
    private static final String SHA256 = "ff29a848c771552062e4f40fe2028075a25fe3c5597d755fd6c3daa0e01ee815";
    private static final Gson GSON = new Gson();
    private static final List<WeaponPerks.Roll> EXPECTED = List.of(
        new WeaponPerks.Roll("abide_the_return", 1644160541L, 4, HASH, 2761485963L),
        new WeaponPerks.Roll("falling_guillotine", 614426548L, 4, HASH, 66521752L),
        new WeaponPerks.Roll("temptation_s_hook", 35794111L, 4, HASH, 2147541212L));
    private record Perk(String id, long hash, float damageMultiplier, int durationTicks, String cooldownSecondsDDC, boolean cooldownConfirmed, int provisionalCooldownTicks) {}
    private record Data(String stage, Perk perk, List<WeaponPerks.Roll> weapons) {}
    private static final Map<String, WeaponCatalog.Entry> CATALOG = catalog();
    private static final Data DATA = load();
    private EnGardeProfile() {}

    private static byte[] bytes(String path) {
        var stream = EnGardeProfile.class.getResourceAsStream(path);
        if (stream == null) throw new IllegalStateException("Missing EnGardeProfile resource " + path);
        try (stream) { return stream.readAllBytes(); }
        catch (IOException e) { throw new IllegalStateException(e); }
    }
    private static void check(boolean valid, String reason) {
        if (!valid) throw new IllegalStateException("Invalid W195 EnGarde: " + reason);
    }
    private static Map<String, WeaponCatalog.Entry> catalog() {
        var entries = GSON.fromJson(new String(bytes("/destiny/weapons/w30.json"), StandardCharsets.UTF_8),
            WeaponCatalog.Entry[].class);
        var map = new HashMap<String, WeaponCatalog.Entry>();
        for (var e : entries) check(map.putIfAbsent(e.id(), e) == null, "unique canonical catalog");
        return Map.copyOf(map);
    }
    private static Data load() {
        var raw = bytes("/destiny/weapons/w195-en-garde.json");
        try { check(HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw)).equals(SHA256),
                    "resource checksum"); }
        catch (NoSuchAlgorithmException e) { throw new IllegalStateException(e); }
        var d = GSON.fromJson(new String(raw, StandardCharsets.UTF_8), Data.class);
        check(d != null && "W195".equals(d.stage) && d.perk != null && ID.equals(d.perk.id)
            && d.perk.hash == HASH && d.perk.damageMultiplier == 1.3f && d.perk.durationTicks == 30 && "2?".equals(d.perk.cooldownSecondsDDC) && !d.perk.cooldownConfirmed && d.perk.provisionalCooldownTicks == 40, "base perk values");
        check(EXPECTED.equals(d.weapons), "exact base Trait socket tuples");
        for (var r : d.weapons) check(CATALOG.containsKey(r.id()), "canonical catalog source");
        return new Data(d.stage, d.perk, List.copyOf(d.weapons));
    }
    public static List<WeaponPerks.Roll> rolls() { return DATA.weapons; }
    public static boolean supports(WeaponCatalog.Entry entry) {
        return entry != null && "sword".equals(entry.family()) && entry.equals(CATALOG.get(entry.id()))
            && DATA.weapons.stream().anyMatch(r -> r.id().equals(entry.id()));
    }
    public static int durationTicks() { return DATA.perk.durationTicks; }
    /** Local provisional mapping; DDC explicitly retains the unknown 2? cooldown. */
    public static int provisionalCooldownTicks() { return DATA.perk.provisionalCooldownTicks; }
    public static float multiplier(boolean active) { return active ? DATA.perk.damageMultiplier : 1f; }
}
