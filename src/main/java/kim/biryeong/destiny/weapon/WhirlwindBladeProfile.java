package kim.biryeong.destiny.weapon;

import com.google.gson.Gson;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.*;

/** W195 base WhirlwindBlade, DDC row 248. JSON-only initialization avoids registry cycles. */
public final class WhirlwindBladeProfile {
    public static final String ID = "whirlwind_blade";
    public static final long HASH = 3913600130L;
    private static final String SHA256 = "2fe06b87881b48de4afc16bee70bbbccb59d0b5571324c044f323349ed7b07a0";
    private static final Gson GSON = new Gson();
    private static final List<WeaponPerks.Roll> EXPECTED = List.of(
        new WeaponPerks.Roll("abide_the_return", 1644160541L, 4, HASH, 2761485963L),
        new WeaponPerks.Roll("goldtusk", 3371413057L, 4, HASH, 700250835L),
        new WeaponPerks.Roll("crown_splitter", 2782325302L, 4, HASH, 99092784L),
        new WeaponPerks.Roll("falling_guillotine", 614426548L, 4, HASH, 66521752L),
        new WeaponPerks.Roll("temptation_s_hook", 35794111L, 4, HASH, 2147541212L));
    private record Perk(String id, long hash, float step, int maxStacks, int durationTicks) {}
    private record Data(String stage, Perk perk, List<WeaponPerks.Roll> weapons) {}
    private static final Map<String, WeaponCatalog.Entry> CATALOG = catalog();
    private static final Data DATA = load();
    private WhirlwindBladeProfile() {}

    private static byte[] bytes(String path) {
        var stream = WhirlwindBladeProfile.class.getResourceAsStream(path);
        if (stream == null) throw new IllegalStateException("Missing WhirlwindBladeProfile resource " + path);
        try (stream) { return stream.readAllBytes(); }
        catch (IOException e) { throw new IllegalStateException(e); }
    }
    private static void check(boolean valid, String reason) {
        if (!valid) throw new IllegalStateException("Invalid W195 WhirlwindBlade: " + reason);
    }
    private static Map<String, WeaponCatalog.Entry> catalog() {
        var entries = GSON.fromJson(new String(bytes("/destiny/weapons/w30.json"), StandardCharsets.UTF_8),
            WeaponCatalog.Entry[].class);
        var map = new HashMap<String, WeaponCatalog.Entry>();
        for (var e : entries) check(map.putIfAbsent(e.id(), e) == null, "unique canonical catalog");
        return Map.copyOf(map);
    }
    private static Data load() {
        var raw = bytes("/destiny/weapons/w195-whirlwind-blade.json");
        try { check(HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw)).equals(SHA256),
                    "resource checksum"); }
        catch (NoSuchAlgorithmException e) { throw new IllegalStateException(e); }
        var d = GSON.fromJson(new String(raw, StandardCharsets.UTF_8), Data.class);
        check(d != null && "W195".equals(d.stage) && d.perk != null && ID.equals(d.perk.id)
            && d.perk.hash == HASH && d.perk.step == .03f && d.perk.maxStacks == 10 && d.perk.durationTicks == 70, "base perk values");
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
    public static int maxStacks() { return DATA.perk.maxStacks; }
    public static float multiplier(int stacks) { return 1f + DATA.perk.step * Math.clamp(stacks, 0, maxStacks()); }
}
