package kim.biryeong.destiny.weapon;

import com.google.gson.*;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.*;

/** BASIC DDC Weapon Perks row110. Static initialization reads JSON only, never registries.
 * The AA cone scalar0.85 remains source-only; no engine mapping is invented. */
public final class GutshotProfile {
    public static final String ID = "gutshot_straight";
    public static final long HASH = 1365187766L;
    private static final Gson GSON = new Gson();
    private static final List<WeaponPerks.Roll> EXPECTED = List.of(
            new WeaponPerks.Roll("allied_demand", 1532276803L, 4, HASH, 703779397L),
            new WeaponPerks.Roll("ammit_ar2", 2119346509L, 4, HASH, 560115158L));
    private static final JsonObject PERK = JsonParser.parseString("""
            {"id":"gutshot_straight","hash":1365187766,
             "autoRifleBodyMultiplier":1.2,"sidearmBodyMultiplier":1.1}
            """).getAsJsonObject();
    private record Data(Map<String, WeaponCatalog.Entry> entries) {}
    private static final Data DATA = load();
    private GutshotProfile() {}

    private static void require(boolean value, String message) {
        if (!value) throw new IllegalStateException("Invalid W226 Gutshot: " + message);
    }
    private static JsonElement json(String path) {
        var input = GutshotProfile.class.getResourceAsStream(path);
        require(input != null, "missing " + path);
        try (input) {
            return JsonParser.parseString(new String(input.readAllBytes(), StandardCharsets.UTF_8));
        } catch (IOException e) { throw new IllegalStateException(e); }
    }
    private static void validate(JsonObject root) {
        require(root.keySet().equals(Set.of("stage", "perk", "weapons"))
                && "W226".equals(root.get("stage").getAsString())
                && PERK.equals(root.get("perk")), "exact BASIC mechanics/schema");
        var seen = new HashSet<WeaponPerks.Roll>();
        for (var row : root.getAsJsonArray("weapons")) {
            var roll = GSON.fromJson(row, WeaponPerks.Roll.class);
            require(EXPECTED.contains(roll) && seen.add(roll) && row.equals(GSON.toJsonTree(roll)),
                    "exact unique BASIC socket");
        }
        require(seen.size() == EXPECTED.size(), "complete two sockets");
    }
    static void validateResource(String value) {
        try { validate(JsonParser.parseString(value).getAsJsonObject()); }
        catch (RuntimeException e) { throw new IllegalStateException("Invalid W226 Gutshot resource", e); }
    }
    private static Data load() {
        validate(json("/destiny/weapons/w226-gutshot.json").getAsJsonObject());
        var entries = new HashMap<String, WeaponCatalog.Entry>();
        for (var raw : json("/destiny/weapons/w30.json").getAsJsonArray()) {
            var entry = GSON.fromJson(raw, WeaponCatalog.Entry.class);
            if (EXPECTED.stream().anyMatch(r -> r.id().equals(entry.id())))
                require(entries.putIfAbsent(entry.id(), entry) == null, "duplicate canonical entry");
        }
        require(entries.size() == 2, "two canonical entries");
        var seen = new HashSet<String>();
        for (var raw : json("/destiny/weapons/w40-characteristics.json").getAsJsonArray()) {
            var row = raw.getAsJsonObject();
            String id = row.get("id").getAsString();
            if (!entries.containsKey(id)) continue;
            var roll = EXPECTED.stream().filter(r -> r.id().equals(id)).findFirst().orElseThrow();
            String family = id.equals("ammit_ar2") ? "auto_rifle" : "sidearm";
            require(seen.add(id) && !row.get("exotic").getAsBoolean()
                    && row.get("bungieHash").getAsLong() == roll.hash()
                    && family.equals(entries.get(id).family()), "exact legendary identity/family");
        }
        require(seen.size() == 2, "complete characteristics");
        return new Data(Map.copyOf(entries));
    }
    public static List<WeaponPerks.Roll> rolls() { return EXPECTED; }
    public static boolean supports(WeaponCatalog.Entry entry) {
        return entry != null && entry.equals(DATA.entries.get(entry.id()));
    }
    public static float bodyMultiplier(WeaponCatalog.Entry entry) {
        if (!supports(entry)) throw new IllegalArgumentException("Noncanonical Gutshot source");
        return entry.family().equals("auto_rifle") ? 1.2f : 1.1f;
    }
}
