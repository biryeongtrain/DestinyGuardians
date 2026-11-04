package kim.biryeong.destiny.weapon;

import com.google.gson.*;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.security.*;
import java.util.*;

/** Base Lead from Gold only; static initialization reads JSON without entering the perk registry.
 * Capacity basis and one final integer ceiling are authored port policy, not proven Destiny rounding.
 */
public final class LeadFromGoldProfile {
    public static final String ID = "lead_from_gold";
    public static final long HASH = 1556840489L;
    private static final Gson GSON = new Gson();
    private static final List<WeaponPerks.Roll> EXPECTED = List.of(
        new WeaponPerks.Roll("apostate",2164448701L,3,HASH,1306932196L),
        new WeaponPerks.Roll("mindbender_s_ambition_adept",912150785L,3,HASH,1732284294L),
        new WeaponPerks.Roll("hollow_words",607191995L,3,HASH,637298592L),
        new WeaponPerks.Roll("dream_breaker",2931957300L,3,HASH,3785896921L),
        new WeaponPerks.Roll("deafening_whisper",981718087L,3,HASH,3110206796L),
        new WeaponPerks.Roll("nezarec_s_whisper",254636484L,3,HASH,210449465L));
    private record Data(JsonObject document, List<WeaponPerks.Roll> rolls,
                        Map<String, WeaponCatalog.Entry> entries) {}
    private static final Data DATA = load();
    private LeadFromGoldProfile() {}

    private static void check(boolean valid, String reason) {
        if (!valid) throw new IllegalStateException("Invalid W187 Lead from Gold: " + reason);
    }
    private static byte[] bytes(String path) {
        var input = LeadFromGoldProfile.class.getResourceAsStream(path);
        check(input != null, "missing " + path);
        try (input) { return input.readAllBytes(); }
        catch (IOException error) { throw new IllegalStateException(error); }
    }
    private static JsonElement json(String path) {
        return JsonParser.parseString(new String(bytes(path), StandardCharsets.UTF_8));
    }
    private static Data load() {
        byte[] raw = bytes("/destiny/weapons/w187-lead_from_gold.json");
        try {
            check(HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw))
                    .equals("a643fb9241fe75dbed6dc8b786409f14ac9749bbe08b940343397b20970b9442"), "checksum");
        } catch (NoSuchAlgorithmException error) { throw new IllegalStateException(error); }
        var root = JsonParser.parseString(new String(raw, StandardCharsets.UTF_8)).getAsJsonObject();
        check(root.keySet().equals(Set.of("stage", "perk", "weapons"))
                && root.get("stage").getAsString().equals("W187"), "schema");
        var rolls = new ArrayList<WeaponPerks.Roll>();
        for (var row : root.getAsJsonArray("weapons")) {
            var roll = GSON.fromJson(row, WeaponPerks.Roll.class);
            check(row.equals(GSON.toJsonTree(roll)) && EXPECTED.contains(roll)
                    && !rolls.contains(roll), "exact unique base roll");
            rolls.add(roll);
        }
        check(rolls.size() == EXPECTED.size(), "complete six sockets");
        Map<String, WeaponCatalog.Entry> entries = new HashMap<>();
        for (var row : json("/destiny/weapons/w30.json").getAsJsonArray()) {
            var entry = GSON.fromJson(row, WeaponCatalog.Entry.class);
            if (rolls.stream().anyMatch(roll -> roll.id().equals(entry.id())))
                check(entries.putIfAbsent(entry.id(), entry) == null, "unique catalog entry");
        }
        check(entries.size() == EXPECTED.size(), "canonical entries");
        int characteristics = 0;
        for (var row : json("/destiny/weapons/w40-characteristics.json").getAsJsonArray()) {
            var c = row.getAsJsonObject();
            String id = c.get("id").getAsString();
            if (!entries.containsKey(id)) continue;
            var roll = rolls.stream().filter(r -> r.id().equals(id)).findFirst().orElseThrow();
            check(c.get("bungieHash").getAsLong() == roll.hash()
                    && !c.get("exotic").getAsBoolean()
                    && c.get("ammo").getAsString().equals("SPECIAL"), "legendary Special identity");
            characteristics++;
        }
        check(characteristics == EXPECTED.size(), "complete characteristics");
        return new Data(root, List.copyOf(rolls), Map.copyOf(entries));
    }

    public static List<WeaponPerks.Roll> rolls() { return DATA.rolls; }
    public static boolean supports(WeaponCatalog.Entry entry) {
        return entry != null && entry.equals(DATA.entries.get(entry.id()));
    }
    /** Pure capacity query. Invalid input is inert; current ammo never changes the grant amount.
     * Uses local bounded reserve capacity, excluding magazine/legacy overflow. 1 Special: ceil(R/4),
     * 2 Specials: ceil(R/8). No intermediate rounding, no unsupported third Special count.
     */
    public static int amount(WeaponCatalog.Entry entry, int equippedSpecialCount) {
        if (!supports(entry) || equippedSpecialCount < 1 || equippedSpecialCount > 2) return 0;
        return reserveGrant(WeaponProfile.forEntry(entry).reserve(), equippedSpecialCount);
    }
    static int reserveGrant(int reserveCapacity, int equippedSpecialCount) {
        if (reserveCapacity <= 0 || equippedSpecialCount < 1 || equippedSpecialCount > 2) return 0;
        return (int)Math.ceilDiv((long)reserveCapacity, 4L * equippedSpecialCount);
    }
    static void validateResource(String value) {
        try { check(JsonParser.parseString(value).equals(DATA.document), "mutated resource"); }
        catch (RuntimeException error) { throw new IllegalStateException("Invalid W187 JSON", error); }
    }
}
