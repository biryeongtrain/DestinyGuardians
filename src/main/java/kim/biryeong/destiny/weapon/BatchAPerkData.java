package kim.biryeong.destiny.weapon;

import com.google.gson.*;
import java.io.IOException;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.*;

/** W320 batch A resource loader. Reads JSON only (never the catalog/perk registries) and pins
 * stage, perk identity, exact Bungie sockets and the DDC-sourced numeric parameters.
 */
final class BatchAPerkData {
    record Data(String id, long hash, JsonObject perk, List<WeaponPerks.Roll> rolls) {
        int i(String key) { return perk.get(key).getAsInt(); }
        double d(String key) { return perk.get(key).getAsDouble(); }
        boolean b(String key) { return perk.get(key).getAsBoolean(); }
    }
    private static final Map<String, JsonObject> BASE = byId("/destiny/weapons/w40-characteristics.json");
    private BatchAPerkData() {}

    static JsonElement read(String path) {
        var stream = BatchAPerkData.class.getResourceAsStream(path);
        if (stream == null) throw new IllegalStateException("Missing W320 resource " + path);
        try (var reader = new InputStreamReader(stream, StandardCharsets.UTF_8)) {
            return JsonParser.parseReader(reader);
        } catch (IOException | JsonParseException e) {
            throw new IllegalStateException("Cannot read W320 resource " + path, e);
        }
    }
    private static Map<String, JsonObject> byId(String path) {
        var result = new HashMap<String, JsonObject>();
        for (var e : read(path).getAsJsonArray()) result.put(e.getAsJsonObject().get("id").getAsString(), e.getAsJsonObject());
        return Map.copyOf(result);
    }
    private static void check(boolean ok, String resource, String detail) {
        if (!ok) throw new IllegalStateException("Invalid W320 " + resource + ": " + detail);
    }
    /** expected = alternating key/value pairs pinning every numeric/boolean perk parameter. */
    static Data load(String resource, String id, long hash, int rollCount, Object... expected) {
        var root = read(resource).getAsJsonObject();
        check(root.keySet().equals(Set.of("stage", "perk", "policies", "source", "weapons"))
            && "W320".equals(root.get("stage").getAsString()), resource, "schema/stage");
        var perk = root.getAsJsonObject("perk");
        check(id.equals(perk.get("id").getAsString()) && perk.get("hash").getAsLong() == hash, resource, "identity");
        check(expected.length % 2 == 0 && perk.keySet().size() == 2 + expected.length / 2, resource, "parameter set");
        for (int i = 0; i < expected.length; i += 2) {
            var value = perk.get((String) expected[i]);
            var want = expected[i + 1];
            check(value != null && (want instanceof Boolean flag ? value.getAsBoolean() == flag
                : Math.abs(value.getAsDouble() - ((Number) want).doubleValue()) < 1e-9), resource, "DDC/local value " + expected[i]);
        }
        var source = root.getAsJsonObject("source");
        check(source.has("ddcText") && !source.get("ddcText").getAsString().isBlank()
            && root.getAsJsonObject("policies").size() > 0, resource, "source/policies");
        var rolls = new ArrayList<WeaponPerks.Roll>();
        var keys = new HashSet<String>();
        for (var e : root.getAsJsonArray("weapons")) {
            var roll = new Gson().fromJson(e, WeaponPerks.Roll.class);
            var base = BASE.get(roll.id());
            check(base != null && base.get("bungieHash").getAsLong() == roll.hash() && !base.get("exotic").getAsBoolean()
                && roll.perkHash() == hash && roll.socket() >= 0 && roll.socket() <= 63 && roll.plugSetHash() > 0
                && keys.add(roll.id() + ":" + roll.socket()), resource, "exact socket " + roll);
            rolls.add(roll);
        }
        check(rolls.size() == rollCount, resource, "complete pinned pool");
        return new Data(id, hash, perk, List.copyOf(rolls));
    }
}
