package kim.biryeong.destiny.weapon;

import com.google.gson.*;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.*;

/** Additive weapon identities. Presentation reuse never replaces gameplay statistics or socket pools. */
public final class LegendaryWeapons {
    private static final Map<String, JsonObject> ROWS = load();
    private LegendaryWeapons() {}
    private static Map<String, JsonObject> load() {
        var in = LegendaryWeapons.class.getResourceAsStream("/destiny/weapons/w327-legendary.json");
        if (in == null) throw new IllegalStateException("Missing legendary weapon definitions");
        try (var reader = new InputStreamReader(in, StandardCharsets.UTF_8)) {
            var out = new LinkedHashMap<String, JsonObject>();
            for (var el : JsonParser.parseReader(reader).getAsJsonArray()) {
                var row = el.getAsJsonObject();
                String id = row.get("id").getAsString();
                if (!id.matches("[a-z0-9_]+") || id.equals(row.get("base").getAsString())
                        || out.putIfAbsent(id, row) != null) throw new IllegalStateException("Invalid legendary identity " + id);
            }
            return Collections.unmodifiableMap(out);
        } catch (java.io.IOException e) { throw new IllegalStateException(e); }
    }
    public static boolean contains(String id) { return ROWS.containsKey(id); }
    public static Set<String> ids() { return ROWS.keySet(); }
    public static String baseId(String id) { var r = ROWS.get(id); return r == null ? id : r.get("base").getAsString(); }
    /** Visual route only. Never pass this result into damage, perk, magazine or stat calculations. */
    public static WeaponCatalog.Entry base(WeaponCatalog.Entry entry) {
        return entry == null || !contains(entry.id()) ? entry : WeaponCatalog.find(baseId(entry.id())).orElseThrow();
    }
    public static String name(String id) { var r = ROWS.get(id); return r == null ? null : r.get("nameKo").getAsString(); }
    static boolean exactRoll(WeaponPerks.Roll roll) {
        var row = ROWS.get(roll.id());
        if (row == null || row.getAsJsonObject("characteristics").get("bungieHash").getAsLong() != roll.hash()) return false;
        for (var value : row.getAsJsonArray("officialTraits")) {
            var socket = value.getAsJsonObject();
            if (socket.get("socket").getAsInt() != roll.socket() || socket.get("plugSetHash").getAsLong() != roll.plugSetHash()) continue;
            for (var perk : socket.getAsJsonArray("perks")) {
                var p = perk.getAsJsonObject();
                if (p.get("hash").getAsLong() == roll.perkHash() && "Trait".equals(p.get("type").getAsString())) return true;
            }
        }
        return false;
    }
    public static <T> List<T> append(List<T> legacy, String field, Class<T> type) {
        var out = new ArrayList<>(legacy); var gson = new Gson();
        for (var row : ROWS.values()) {
            var value = row.get(field);
            if (value == null) throw new IllegalStateException("Missing legendary field " + field);
            if (value.isJsonArray()) for (var item : value.getAsJsonArray()) out.add(gson.fromJson(item, type));
            else out.add(gson.fromJson(value, type));
        }
        return List.copyOf(out);
    }
    public static JsonObject field(String id, String key) {
        var row = ROWS.get(id);
        return row == null || !row.has(key) ? null : row.getAsJsonObject(key).deepCopy();
    }
}
