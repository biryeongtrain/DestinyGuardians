package kim.biryeong.destiny.weapon;

import com.google.gson.*;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.*;

/** Base Osmosis only. Static loading reads pinned JSON, never calls catalog/trait registries. */
public final class OsmosisProfile {
    public static final String ID = "osmosis";
    public static final long HASH = 1774574192L;
    private static final Gson GSON = new Gson();
    private static final List<WeaponPerks.Roll> EXPECTED = List.of(
        new WeaponPerks.Roll("patron_of_lost_causes", 2723241847L, 4, HASH, 120674550L),
        new WeaponPerks.Roll("seventh_seraph_officer_revolver", 3037520408L, 4, HASH, 3527094473L),
        new WeaponPerks.Roll("steelfeather_repeater", 1251729046L, 4, HASH, 2645685327L));
    private static final JsonObject PERK = JsonParser.parseString("""
        {"id":"osmosis","hash":1774574192,"refillPercent":50,
         "trigger":"successful_grenade_ability_activate","refillsPerStowEpisode":1,
         "element":"equipped_grenade_until_stowed","rounding":"ceiling_tick_free"}
        """).getAsJsonObject();
    private record Data(List<WeaponPerks.Roll> rolls, Map<String, WeaponCatalog.Entry> entries) {}
    private static final Data DATA = load();
    private OsmosisProfile() {}
    private static void check(boolean value, String message) {
        if (!value) throw new IllegalStateException("Invalid W203 Osmosis: " + message);
    }
    private static JsonElement json(String path) {
        var stream = OsmosisProfile.class.getResourceAsStream(path);
        check(stream != null, "missing " + path);
        try (stream) {
            return JsonParser.parseString(new String(stream.readAllBytes(), StandardCharsets.UTF_8));
        } catch (IOException e) { throw new IllegalStateException(e); }
    }
    private static Data load() {
        validate(json("/destiny/weapons/w203-osmosis.json").getAsJsonObject());
        var entries = new HashMap<String, WeaponCatalog.Entry>();
        for (var row : json("/destiny/weapons/w30.json").getAsJsonArray()) {
            var entry = GSON.fromJson(row, WeaponCatalog.Entry.class);
            if (EXPECTED.stream().anyMatch(r -> r.id().equals(entry.id())))
                check(entries.putIfAbsent(entry.id(), entry) == null, "duplicate canonical entry");
        }
        check(entries.size() == EXPECTED.size(), "three canonical entries");
        var seen = new HashSet<String>();
        for (var row : json("/destiny/weapons/w40-characteristics.json").getAsJsonArray()) {
            var stat = row.getAsJsonObject(); String id = stat.get("id").getAsString();
            if (!entries.containsKey(id)) continue;
            var roll = EXPECTED.stream().filter(r -> r.id().equals(id)).findFirst().orElseThrow();
            check(seen.add(id) && !stat.get("exotic").getAsBoolean()
                    && stat.get("bungieHash").getAsLong() == roll.hash()
                    && stat.get("ammo").getAsString().equals("PRIMARY")
                    && stat.get("damage").getAsString().equals("KINETIC"), "exact primary legendary identity");
            check(Set.of("scout_rifle", "hand_cannon", "auto_rifle").contains(entries.get(id).family()),
                    "direct primary sources only");
        }
        check(seen.size() == EXPECTED.size(), "complete characteristics");
        return new Data(EXPECTED, Map.copyOf(entries));
    }
    private static void validate(JsonObject root) {
        check(root.keySet().equals(Set.of("stage", "perk", "weapons"))
                && root.get("stage").getAsString().equals("W203") && PERK.equals(root.get("perk")), "schema/mechanics");
        var seen = new HashSet<WeaponPerks.Roll>();
        for (var row : root.getAsJsonArray("weapons")) {
            var roll = GSON.fromJson(row, WeaponPerks.Roll.class);
            check(roll != null && EXPECTED.contains(roll) && seen.add(roll)
                    && row.equals(GSON.toJsonTree(roll)), "exact unique base trait socket");
        }
        check(seen.size() == EXPECTED.size(), "complete three sockets");
    }
    static void validateResource(String value) {
        try { validate(JsonParser.parseString(value).getAsJsonObject()); }
        catch (RuntimeException e) { throw new IllegalStateException("Invalid W203 Osmosis resource", e); }
    }
    public static List<WeaponPerks.Roll> rolls() { return DATA.rolls; }
    public static boolean supports(String id) { return id != null && DATA.entries.containsKey(id); }
    public static boolean supports(WeaponCatalog.Entry entry) {
        return entry != null && entry.equals(DATA.entries.get(entry.id()));
    }
    /** Local integer-cartridge policy, not a sourced rounding claim: ceil(50% capacity), no ticks. */
    public static int refillRounds(int capacity) { return capacity <= 0 ? 0 : capacity / 2 + capacity % 2; }
}
