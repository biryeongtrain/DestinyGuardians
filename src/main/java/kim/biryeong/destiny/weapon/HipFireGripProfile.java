package kim.biryeong.destiny.weapon;

import com.google.gson.*;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.*;

/** Pinned base trait sockets and DDC row120. Static load reads JSON only; it never calls
 * WeaponCatalog, WeaponCharacteristics or WeaponPerks registries (including indirectly).
 * AA, stickiness and precision-angle fields are source evidence, not simulated effects. */
public final class HipFireGripProfile {
    public static final String ID = "hip_fire_grip";
    public static final long HASH = 1866048759L;
    private static final Gson GSON = new Gson();
    private static final List<WeaponPerks.Roll> EXPECTED = List.of(
        new WeaponPerks.Roll("duke_mk_44", 2112909414L, 4, HASH, 3815727680L),
        new WeaponPerks.Roll("first_in_last_out", 3616586446L, 3, HASH, 267999755L),
        new WeaponPerks.Roll("long_arm", 8293111L, 3, HASH, 3056706286L),
        new WeaponPerks.Roll("whispering_slab", 211938782L, 3, HASH, 1885424927L));
    private static final JsonObject PERK = JsonParser.parseString("""
        {"id":"hip_fire_grip","hash":1866048759,"stabilityBonus":25,"accuracyScalar":0.7,
         "falloffScalar":1.2,"falloffExcludedFamilies":["shotgun","sniper_rifle","fusion_rifle"],
         "falloffExcludedIds":["the_last_word"],"unsimulated":{"aimAssistBonus":15,
         "precisionAngleThresholdDegreesBonus":2.7,"aimAssistFalloffDistanceScalar":1.2,
         "reticleStickinessFalloffDistanceScalar":1.2}}
        """).getAsJsonObject();
    private record Data(List<WeaponPerks.Roll> rolls, Map<String, WeaponCatalog.Entry> entries) {}
    private static final Data DATA = load();
    private HipFireGripProfile() {}

    private static void check(boolean value, String message) {
        if (!value) throw new IllegalStateException("Invalid W203 Hip-Fire Grip: " + message);
    }
    private static JsonElement json(String path) {
        var stream = HipFireGripProfile.class.getResourceAsStream(path);
        check(stream != null, "missing " + path);
        try (stream) {
            return JsonParser.parseString(new String(stream.readAllBytes(), StandardCharsets.UTF_8));
        } catch (IOException e) { throw new IllegalStateException(e); }
    }
    private static Data load() {
        validate(json("/destiny/weapons/w203-hip-fire-grip.json").getAsJsonObject());
        var entries = new HashMap<String, WeaponCatalog.Entry>();
        for (var row : json("/destiny/weapons/w30.json").getAsJsonArray()) {
            var entry = GSON.fromJson(row, WeaponCatalog.Entry.class);
            if (EXPECTED.stream().anyMatch(r -> r.id().equals(entry.id()))) {
                check(entries.putIfAbsent(entry.id(), entry) == null, "duplicate canonical entry");
                String family = switch (entry.id()) {
                    case "duke_mk_44" -> "hand_cannon";
                    case "first_in_last_out" -> "shotgun";
                    case "long_arm" -> "scout_rifle";
                    case "whispering_slab" -> "bow";
                    default -> throw new IllegalStateException("Unexpected Hip-Fire Grip source");
                };
                check(family.equals(entry.family()), "canonical family");
            }
        }
        check(entries.size() == EXPECTED.size(), "four canonical entries");
        var seen = new HashSet<String>();
        for (var row : json("/destiny/weapons/w40-characteristics.json").getAsJsonArray()) {
            var stat = row.getAsJsonObject();
            String id = stat.get("id").getAsString();
            if (!entries.containsKey(id)) continue;
            var roll = EXPECTED.stream().filter(r -> r.id().equals(id)).findFirst().orElseThrow();
            check(seen.add(id) && !stat.get("exotic").getAsBoolean()
                    && stat.get("bungieHash").getAsLong() == roll.hash(), "exact legendary item identity");
        }
        check(seen.size() == EXPECTED.size(), "complete characteristics");
        return new Data(EXPECTED, Map.copyOf(entries));
    }
    private static void validate(JsonObject root) {
        check(root.keySet().equals(Set.of("stage", "perk", "weapons"))
                && root.get("stage").getAsString().equals("W203") && PERK.equals(root.get("perk")),
                "schema/base mechanics");
        var seen = new HashSet<WeaponPerks.Roll>();
        for (var row : root.getAsJsonArray("weapons")) {
            var roll = GSON.fromJson(row, WeaponPerks.Roll.class);
            check(roll != null && EXPECTED.contains(roll) && seen.add(roll)
                    && row.equals(GSON.toJsonTree(roll)), "exact unique base socket");
        }
        check(seen.size() == EXPECTED.size(), "complete four sockets");
    }
    static void validateResource(String value) {
        try { validate(JsonParser.parseString(value).getAsJsonObject()); }
        catch (RuntimeException e) { throw new IllegalStateException("Invalid W203 Hip-Fire Grip resource", e); }
    }
    public static List<WeaponPerks.Roll> rolls() { return DATA.rolls; }
    public static boolean supports(String id) { return id != null && DATA.entries.containsKey(id); }
    public static boolean supports(WeaponCatalog.Entry entry) {
        return entry != null && entry.equals(DATA.entries.get(entry.id()));
    }
    public static int stabilityBonus() { return 25; }
    public static double accuracyScalar() { return 0.7; }
    /** Distance-threshold multiplier only; the shotgun source keeps ordinary damage falloff. */
    public static double falloffScalar(WeaponCatalog.Entry entry) {
        if (!supports(entry) || entry.id().equals("the_last_word")) return 1;
        return switch (entry.family()) {
            case "shotgun", "sniper_rifle", "fusion_rifle" -> 1;
            default -> 1.2;
        };
    }
}
