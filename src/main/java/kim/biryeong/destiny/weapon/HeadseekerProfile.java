package kim.biryeong.destiny.weapon;

import com.google.gson.*;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.*;

/** Exact base sockets and DDC row113 mechanics. Initialization reads JSON directly and never
 * calls WeaponCatalog, WeaponCharacteristics, WeaponBallistics or WeaponPerks registries.
 * Uncertain AA, enhanced stability and original weakspot/shield distinctions are excluded. */
public final class HeadseekerProfile {
    public static final String ID = "headseeker";
    public static final long HASH = 460017080L;
    public static final int DURATION_TICKS = 11;
    private static final Gson GSON = new Gson();
    private static final List<WeaponPerks.Roll> EXPECTED = List.of(
        new WeaponPerks.Roll("blast_furnace", 3843477312L, 4, HASH, 169306153L),
        new WeaponPerks.Roll("bygones", 2712244741L, 4, HASH, 3060320121L),
        new WeaponPerks.Roll("chattering_bone", 568515759L, 4, HASH, 423791138L),
        new WeaponPerks.Roll("claws_of_the_wolf", 1280933460L, 3, HASH, 206409262L),
        new WeaponPerks.Roll("cold_denial", 1216130969L, 4, HASH, 720537379L),
        new WeaponPerks.Roll("high_albedo", 1197486957L, 4, HASH, 718633408L));
    private static final JsonObject PERK = JsonParser.parseString("""
        {"id":"headseeker","hash":460017080,"durationTicks":11,"precisionBonusMultiplier":1.2}
        """).getAsJsonObject();
    private record Data(List<WeaponPerks.Roll> rolls, Map<String, WeaponCatalog.Entry> entries) {}
    private static final Data DATA = load();
    private HeadseekerProfile() {}
    private static void check(boolean value, String message) {
        if (!value) throw new IllegalStateException("Invalid W202 Headseeker: " + message);
    }
    private static JsonElement json(String path) {
        var stream = HeadseekerProfile.class.getResourceAsStream(path);
        check(stream != null, "missing " + path);
        try (stream) {
            return JsonParser.parseString(new String(stream.readAllBytes(), StandardCharsets.UTF_8));
        } catch (IOException e) { throw new IllegalStateException(e); }
    }
    private static Data load() {
        var root = json("/destiny/weapons/w202-headseeker.json").getAsJsonObject();
        validate(root);
        var entries = new HashMap<String, WeaponCatalog.Entry>();
        for (var row : json("/destiny/weapons/w30.json").getAsJsonArray()) {
            var entry = GSON.fromJson(row, WeaponCatalog.Entry.class);
            if (EXPECTED.stream().anyMatch(r -> r.id().equals(entry.id())))
                check(entries.putIfAbsent(entry.id(), entry) == null, "duplicate canonical entry");
        }
        check(entries.size() == EXPECTED.size(), "six canonical entries");
        var seen = new HashSet<String>();
        for (var row : json("/destiny/weapons/w40-characteristics.json").getAsJsonArray()) {
            var stat = row.getAsJsonObject(); String id = stat.get("id").getAsString();
            if (!entries.containsKey(id)) continue;
            var roll = EXPECTED.stream().filter(r -> r.id().equals(id)).findFirst().orElseThrow();
            check(seen.add(id) && !stat.get("exotic").getAsBoolean()
                    && stat.get("bungieHash").getAsLong() == roll.hash(), "exact legendary item identity");
            String family = entries.get(id).family();
            check(family.equals("pulse_rifle") || family.equals("sidearm"), "direct ranged sources only");
        }
        check(seen.size() == EXPECTED.size(), "complete characteristics");
        return new Data(EXPECTED, Map.copyOf(entries));
    }
    private static void validate(JsonObject root) {
        check(root.keySet().equals(Set.of("stage", "perk", "weapons"))
                && root.get("stage").getAsString().equals("W202") && PERK.equals(root.get("perk")), "schema/mechanics");
        var seen = new HashSet<WeaponPerks.Roll>();
        for (var row : root.getAsJsonArray("weapons")) {
            var roll = GSON.fromJson(row, WeaponPerks.Roll.class);
            check(roll != null && EXPECTED.contains(roll) && seen.add(roll)
                    && row.equals(GSON.toJsonTree(roll)), "exact unique base socket");
        }
        check(seen.size() == EXPECTED.size(), "complete six sockets");
    }
    static void validateResource(String value) {
        try { validate(JsonParser.parseString(value).getAsJsonObject()); }
        catch (RuntimeException e) { throw new IllegalStateException("Invalid W202 Headseeker resource", e); }
    }
    public static List<WeaponPerks.Roll> rolls() { return DATA.rolls; }
    public static boolean supports(String id) { return id != null && DATA.entries.containsKey(id); }
    public static boolean supports(WeaponCatalog.Entry entry) {
        return entry != null && entry.equals(DATA.entries.get(entry.id()));
    }
    public static int durationTicks() { return DURATION_TICKS; }
    public static float precisionBonusMultiplier() { return 1.2f; }
}
