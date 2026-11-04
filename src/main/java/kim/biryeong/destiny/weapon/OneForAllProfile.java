package kim.biryeong.destiny.weapon;

import com.google.gson.*;
import com.google.gson.stream.JsonReader;
import com.google.gson.stream.JsonToken;
import java.io.IOException;
import java.io.InputStreamReader;
import java.io.StringReader;
import java.math.BigDecimal;
import java.nio.charset.StandardCharsets;
import java.util.*;

/** Exact base-trait settings and eight pinned official sockets, including the paid sword. */
public final class OneForAllProfile {
    public static final String ID = "one_for_all";
    public static final long HASH = 4049631843L;
    private static final String RESOURCE = "/destiny/weapons/w109-one-for-all.json";
    public record Perk(String id, long hash, int hitWindowTicks, int durationTicks,
                       float multiplier, String timingSource) {}
    private record Data(String stage, Perk perk, WeaponPerks.Roll[] weapons) {}
    private static final Set<WeaponPerks.Roll> EXPECTED = Set.of(
        roll("ammit_ar2", 2119346509L, 560115158L),
        roll("aishas_embrace", 2638190703L, 4211351701L),
        roll("brass_attacks", 2121785039L, 3403850295L),
        roll("coriolis_force", 3512349612L, 753624012L),
        roll("retraced_path", 548958835L, 398391969L),
        roll("dimensional_hypotrochoid", 1311684613L, 1092097342L),
        roll("retrofit_escapade", 3103325054L, 2461260598L),
        roll("goldtusk", 3371413057L, 700250835L));
    private static final Data DATA = load();
    private OneForAllProfile() {}

    private static WeaponPerks.Roll roll(String id, long hash, long pool) {
        return new WeaponPerks.Roll(id, hash, 4, HASH, pool);
    }
    private static IllegalStateException invalid() {
        return new IllegalStateException("Invalid W109 One for All profile");
    }
    private static void check(boolean condition) { if (!condition) throw invalid(); }

    private static Data load() {
        var stream = OneForAllProfile.class.getResourceAsStream(RESOURCE);
        if (stream == null) throw invalid();
        try (var reader = new InputStreamReader(stream, StandardCharsets.UTF_8)) {
            var text = new StringBuilder();
            var buffer = new char[4096];
            for (int n; (n = reader.read(buffer)) != -1;) text.append(buffer, 0, n);
            return parse(text.toString());
        } catch (IOException e) { throw new IllegalStateException("Cannot read W109 One for All", e); }
    }

    /** Reject duplicate keys, lenient syntax and trailing data before Gson can coerce/overwrite them. */
    private static JsonElement read(JsonReader reader, int depth) throws IOException {
        check(depth < 8);
        return switch (reader.peek()) {
            case BEGIN_OBJECT -> {
                var object = new JsonObject();
                reader.beginObject();
                while (reader.hasNext()) {
                    String name = reader.nextName();
                    check(!object.has(name));
                    object.add(name, read(reader, depth + 1));
                }
                reader.endObject();
                yield object;
            }
            case BEGIN_ARRAY -> {
                var array = new JsonArray();
                reader.beginArray();
                while (reader.hasNext()) { check(array.size() < 64); array.add(read(reader, depth + 1)); }
                reader.endArray();
                yield array;
            }
            case STRING -> new JsonPrimitive(reader.nextString());
            case NUMBER -> new JsonPrimitive(new BigDecimal(reader.nextString()));
            case BOOLEAN -> new JsonPrimitive(reader.nextBoolean());
            case NULL -> { reader.nextNull(); yield JsonNull.INSTANCE; }
            default -> throw invalid();
        };
    }
    private static void fields(JsonObject object, String... names) {
        check(object.keySet().equals(Set.of(names)));
    }
    private static void string(JsonObject object, String key, String expected) {
        var value = object.get(key);
        check(value != null && value.isJsonPrimitive() && value.getAsJsonPrimitive().isString()
                && expected.equals(value.getAsString()));
    }
    private static void number(JsonObject object, String key, String expected) {
        var value = object.get(key);
        check(value != null && value.isJsonPrimitive() && value.getAsJsonPrimitive().isNumber()
                && value.getAsBigDecimal().compareTo(new BigDecimal(expected)) == 0);
    }
    private static Data parse(String json) {
        try (var reader = new JsonReader(new StringReader(Objects.requireNonNull(json)))) {
            reader.setStrictness(Strictness.STRICT);
            var root = read(reader, 0).getAsJsonObject();
            check(reader.peek() == JsonToken.END_DOCUMENT);
            fields(root, "stage", "perk", "weapons");
            string(root, "stage", "W109");
            var perk = root.getAsJsonObject("perk");
            fields(perk, "id", "hash", "hitWindowTicks", "durationTicks", "multiplier", "timingSource");
            string(perk, "id", ID);
            number(perk, "hash", Long.toString(HASH));
            number(perk, "hitWindowTicks", "60");
            number(perk, "durationTicks", "200");
            number(perk, "multiplier", "1.35");
            string(perk, "timingSource", "art/weapons/w109/references/clarity-source.json");
            var weapons = root.getAsJsonArray("weapons");
            check(weapons.size() == EXPECTED.size());
            var found = new HashSet<WeaponPerks.Roll>();
            for (var element : weapons) {
                var row = element.getAsJsonObject();
                fields(row, "id", "hash", "socket", "perkHash", "plugSetHash");
                var expected = EXPECTED.stream().filter(r -> r.id().equals(row.get("id").getAsString()))
                    .findFirst().orElseThrow(OneForAllProfile::invalid);
                string(row, "id", expected.id());
                number(row, "hash", Long.toString(expected.hash()));
                number(row, "socket", Integer.toString(expected.socket()));
                number(row, "perkHash", Long.toString(HASH));
                number(row, "plugSetHash", Long.toString(expected.plugSetHash()));
                check(found.add(expected));
                var entry = WeaponCatalog.find(expected.id()).orElseThrow(OneForAllProfile::invalid);
                var meta = WeaponCharacteristics.of(entry);
                check(meta.bungieHash() == expected.hash() && !meta.exotic());
            }
            check(found.equals(EXPECTED));
            return new Gson().fromJson(root, Data.class);
        } catch (IOException | RuntimeException e) {
            throw new IllegalStateException("Invalid W109 One for All profile", e);
        }
    }
    static void validateResource(String json) { parse(json); }
    public static Perk perk() { return DATA.perk; }
    public static int hitWindowTicks() { return DATA.perk.hitWindowTicks; }
    public static int durationTicks() { return DATA.perk.durationTicks; }
    public static float multiplier() { return DATA.perk.multiplier; }
    public static List<WeaponPerks.Roll> rolls() { return List.of(DATA.weapons); }

    /** Canonical catalog membership rejects forged records sharing only an ID. */
    public static boolean supports(WeaponCatalog.Entry entry) {
        return entry != null && WeaponCatalog.find(entry.id()).filter(entry::equals).isPresent()
                && EXPECTED.stream().anyMatch(r -> r.id().equals(entry.id()));
    }
}
