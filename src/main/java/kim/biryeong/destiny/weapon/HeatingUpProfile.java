package kim.biryeong.destiny.weapon;

import com.google.gson.*;
import java.io.IOException;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.*;

/** Base Heating Up only. JSON-only loading avoids catalog/perk initialization cycles. */
public final class HeatingUpProfile {
    public static final String ID = "heating_up";
    public static final long HASH = 1570042021L;
    private static final Gson GSON = new Gson();
    private static final List<WeaponPerks.Roll> EXPECTED = List.of(
        new WeaponPerks.Roll("farewell", 541188001L, 3, HASH, 284168234L),
        new WeaponPerks.Roll("dream_breaker", 2931957300L, 3, HASH, 3785896921L),
        new WeaponPerks.Roll("retrofit_escapade", 3103325054L, 3, HASH, 3756086698L));
    private static final JsonObject PERK = JsonParser.parseString("""
        {"id":"heating_up","hash":1570042021,"durationTicks":110,"maxStacks":2,
         "remainsWhileStowed":true,"stabilityBonus":[0,15,30],
         "recoilDirectionBonus":[0,20,40],"accuracyScalar":[1.0,0.85,0.75]}
        """).getAsJsonObject();
    private static final Map<String, WeaponCatalog.Entry> CANONICAL = canonical();
    private static final List<WeaponPerks.Roll> ROLLS = validate(read("w177-heating-up.json").getAsJsonObject());

    private HeatingUpProfile() {}

    private static void check(boolean valid, String reason) {
        if (!valid) throw new IllegalStateException("Invalid W177 Heating Up: " + reason);
    }

    private static JsonElement read(String file) {
        var stream = HeatingUpProfile.class.getResourceAsStream("/destiny/weapons/" + file);
        check(stream != null, "missing " + file);
        try (var reader = new InputStreamReader(stream, StandardCharsets.UTF_8)) {
            return JsonParser.parseReader(reader);
        } catch (IOException | JsonParseException e) {
            throw new IllegalStateException("Cannot read W177 source " + file, e);
        }
    }

    private static Map<String, WeaponCatalog.Entry> canonical() {
        var entries = new HashMap<String, WeaponCatalog.Entry>();
        for (var row : read("w30.json").getAsJsonArray()) {
            var entry = GSON.fromJson(row, WeaponCatalog.Entry.class);
            check(entries.putIfAbsent(entry.id(), entry) == null, "duplicate catalog ID");
        }
        var selected = new HashMap<String, JsonObject>();
        for (var row : read("w40-characteristics.json").getAsJsonArray()) {
            var source = row.getAsJsonObject();
            check(selected.putIfAbsent(source.get("id").getAsString(), source) == null, "duplicate selected ID");
        }
        var result = new HashMap<String, WeaponCatalog.Entry>();
        for (var roll : EXPECTED) {
            var source = selected.get(roll.id());
            check(source != null && source.get("bungieHash").equals(new JsonPrimitive(roll.hash()))
                && source.get("exotic").equals(new JsonPrimitive(false)) && entries.containsKey(roll.id()),
                "nonexotic selected identity " + roll.id());
            result.put(roll.id(), entries.get(roll.id()));
        }
        return Map.copyOf(result);
    }

    private static List<WeaponPerks.Roll> validate(JsonObject root) {
        check(root.keySet().equals(Set.of("stage", "perk", "weapons"))
            && new JsonPrimitive("W177").equals(root.get("stage")) && PERK.equals(root.get("perk")),
            "schema/mechanics");
        var rows = root.getAsJsonArray("weapons");
        check(rows.size() == EXPECTED.size(), "roll coverage");
        var result = new ArrayList<WeaponPerks.Roll>();
        for (var row : rows) {
            var roll = GSON.fromJson(row, WeaponPerks.Roll.class);
            check(EXPECTED.contains(roll) && row.equals(GSON.toJsonTree(roll)) && !result.contains(roll),
                "exact unique base socket");
            result.add(roll);
        }
        return List.copyOf(result);
    }

    /** Same fail-closed validator as loading, without mutating the loaded profile. */
    static void validateResource(String json) {
        try { validate(JsonParser.parseString(json).getAsJsonObject()); }
        catch (RuntimeException e) { throw new IllegalStateException("Invalid W177 Heating Up JSON", e); }
    }

    public static List<WeaponPerks.Roll> rolls() { return ROLLS; }
    public static boolean supports(WeaponCatalog.Entry entry) {
        return entry != null && entry.id() != null && entry.equals(CANONICAL.get(entry.id()));
    }
    public static int durationTicks() { return 110; }

    /** Clamp callers to the sourced 0..2 tiers; nonpositive stacks are neutral. */
    public static int stabilityBonus(int stacks) { return Math.clamp(stacks, 0, 2) * 15; }
    public static int recoilDirectionBonus(int stacks) { return Math.clamp(stacks, 0, 2) * 20; }
    /** Applies equally to accuracy cone size and cone growth, once per calculation. */
    public static double accuracyScalar(int stacks) { return stacks <= 0 ? 1.0 : stacks == 1 ? .85 : .75; }
}
