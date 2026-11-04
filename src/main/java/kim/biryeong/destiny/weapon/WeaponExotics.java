package kim.biryeong.destiny.weapon;

import com.google.gson.Gson;
import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

/** Additive exact exotic definitions. Legacy pinned 63-weapon resources stay byte-identical.
 * JSON-only initialization avoids cycles between catalog/characteristics/timing/aim loaders.
 * Each consumer retains its own duplicate/coverage/value validation.
 */
public final class WeaponExotics {
    private static final List<JsonObject> ROWS = load();
    private WeaponExotics() {}
    private static List<JsonObject> load() {
        var rows = new ArrayList<JsonObject>();
        for(String path:List.of("/destiny/weapons/w83-exotics.json","/destiny/weapons/w84-exotics.json")) {
            var in = WeaponExotics.class.getResourceAsStream(path);
            if (in == null) throw new IllegalStateException("Missing exotic definitions " + path);
            try (var reader = new InputStreamReader(in, StandardCharsets.UTF_8)) {
                JsonArray data = JsonParser.parseReader(reader).getAsJsonArray();
                if(data.isEmpty())throw new IllegalStateException("Empty exotic definitions " + path);
                for (var value : data) rows.add(value.getAsJsonObject());
            } catch (java.io.IOException e) { throw new IllegalStateException(e); }
        }
        return List.copyOf(rows);
    }
    public static <T> List<T> append(T[] legacy, String field, Class<T> type) {
        var result = new ArrayList<>(Arrays.asList(legacy));
        var gson = new Gson();
        for (var row : ROWS) {
            if (!row.has(field)) throw new IllegalStateException("Missing exotic field " + field);
            var value = row.get(field);
            if (value.isJsonArray()) for (var item : value.getAsJsonArray()) result.add(gson.fromJson(item, type));
            else result.add(gson.fromJson(value, type));
        }
        return List.copyOf(result);
    }
    public static boolean ace(WeaponCatalog.Entry entry) {
        return entry != null && entry.id().equals("ace_of_spades")
                && WeaponCatalog.find(entry.id()).filter(entry::equals).isPresent()
                && WeaponCharacteristics.of(entry).bungieHash() == 347366834L
                && WeaponCharacteristics.of(entry).exotic();
    }
    public static boolean izanagi(WeaponCatalog.Entry entry) {
        return entry != null && entry.id().equals("izanagis_burden")
                && WeaponCatalog.find(entry.id()).filter(entry::equals).isPresent()
                && WeaponCharacteristics.of(entry).bungieHash() == 3211806999L
                && WeaponCharacteristics.of(entry).exotic();
    }
}
