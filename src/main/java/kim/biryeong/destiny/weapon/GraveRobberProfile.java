package kim.biryeong.destiny.weapon;

import com.google.gson.*;
import com.google.gson.stream.JsonReader;
import com.google.gson.stream.JsonToken;
import java.io.*;
import java.math.BigDecimal;
import java.nio.charset.StandardCharsets;
import java.util.*;

/** Exact nine W110 base sockets and pinned Clarity three-second refill clock. */
public final class GraveRobberProfile {
    public static final String ID = "grave_robber";
    public static final long HASH = 1631667848L;
    private static final String SOURCE = "art/weapons/w110/references/clarity-source.json";
    private static final String RESOURCE = "/destiny/weapons/w110-grave-robber.json";
    public record Perk(String id, long hash, String timingSource, int cooldownTicks) {}
    private static final Perk PERK = new Perk(ID, HASH, SOURCE, 60);
    private static final Set<WeaponPerks.Roll> EXPECTED = Set.of(
        roll("steelfeather_repeater", 1251729046L, 3, 473189353L),
        roll("cold_denial", 1216130969L, 3, 330841869L),
        roll("claws_of_the_wolf", 1280933460L, 4, 753756428L),
        roll("patron_of_lost_causes", 2723241847L, 3, 2564227946L),
        roll("bug_out_bag", 2744715540L, 3, 907333373L),
        roll("ikelos_smg_v1_0_1", 1723472487L, 4, 1329L),
        roll("lonesome", 2199171672L, 3, 3612808001L),
        roll("dead_man_walking_xx7463", 3751622019L, 4, 1210839935L),
        roll("dust_rock_blues", 636912560L, 4, 1624251370L));
    private static final List<WeaponPerks.Roll> ROLLS = load();
    private GraveRobberProfile() {}

    private static WeaponPerks.Roll roll(String id, long hash, int socket, long pool) {
        return new WeaponPerks.Roll(id, hash, socket, HASH, pool);
    }

    private static IllegalStateException invalid(String detail) {
        return new IllegalStateException("Invalid W110 Grave Robber profile: " + detail);
    }
    private static void check(boolean condition, String detail) { if (!condition) throw invalid(detail); }

    private static List<WeaponPerks.Roll> load() {
        var stream = GraveRobberProfile.class.getResourceAsStream(RESOURCE);
        if (stream == null) throw invalid("missing resource");
        try (var reader = new InputStreamReader(stream, StandardCharsets.UTF_8)) {
            return parse(reader);
        } catch (IOException e) { throw new IllegalStateException("Cannot read W110 Grave Robber", e); }
    }

    /** Negative resource tests exercise the same strict parser as production. */
    static void validateResource(String json) {
        if (json == null) throw invalid("null input");
        parse(new StringReader(json));
    }

    private static List<WeaponPerks.Roll> parse(Reader input) {
        try (var reader = new JsonReader(input)) {
            reader.setStrictness(Strictness.STRICT);
            var data = object(read(reader, 0), "stage", "perk", "weapons");
            check(reader.peek() == JsonToken.END_DOCUMENT, "trailing content");
            check("W110".equals(string(data.get("stage"))), "stage");
            var perk = object(data.get("perk"), "id", "hash", "timingSource", "cooldownTicks");
            check(ID.equals(string(perk.get("id"))) && HASH == integer(perk.get("hash"))
                    && SOURCE.equals(string(perk.get("timingSource"))), "base trait/source");
            exact(perk.get("cooldownTicks"), "60");
            check(data.get("weapons") instanceof JsonArray, "weapon array");
            var rows = data.getAsJsonArray("weapons");
            check(rows.size() == EXPECTED.size(), "nine exact sockets");
            var result = new ArrayList<WeaponPerks.Roll>();
            var seen = new HashSet<WeaponPerks.Roll>();
            for (var value : rows) {
                var row = object(value, "id", "hash", "socket", "perkHash", "plugSetHash");
                var roll = new WeaponPerks.Roll(string(row.get("id")), integer(row.get("hash")),
                        Math.toIntExact(integer(row.get("socket"))), integer(row.get("perkHash")), integer(row.get("plugSetHash")));
                check(EXPECTED.contains(roll) && seen.add(roll), "exact unique base socket");
                var entry = WeaponCatalog.find(roll.id()).orElseThrow(() -> invalid("unknown weapon"));
                var meta = WeaponCharacteristics.of(entry);
                check(meta.bungieHash() == roll.hash() && !meta.exotic(), "official item identity");
                result.add(roll);
            }
            check(seen.equals(EXPECTED), "complete socket allowlist");
            return List.copyOf(result);
        } catch (IOException | RuntimeException e) {
            throw new IllegalStateException("Invalid W110 Grave Robber resource", e);
        }
    }

    // Gson's ordinary record adapter accepts numeric strings and truncates fractional integers.
    // Read a bounded strict tree first, rejecting duplicate members before they can be overwritten.
    private static JsonElement read(JsonReader reader, int depth) throws IOException {
        check(depth <= 5, "excess nesting");
        return switch (reader.peek()) {
            case BEGIN_OBJECT -> {
                reader.beginObject(); var object = new JsonObject();
                while (reader.hasNext()) {
                    String key = reader.nextName();
                    check(!object.has(key) && object.size() < 16, "duplicate/excess member");
                    object.add(key, read(reader, depth + 1));
                }
                reader.endObject(); yield object;
            }
            case BEGIN_ARRAY -> {
                reader.beginArray(); var array = new JsonArray();
                while (reader.hasNext()) { check(array.size() < 16, "excess rows"); array.add(read(reader, depth + 1)); }
                reader.endArray(); yield array;
            }
            case STRING -> new JsonPrimitive(reader.nextString());
            case NUMBER -> new JsonPrimitive(new BigDecimal(reader.nextString()));
            default -> throw invalid("unexpected JSON value");
        };
    }

    private static JsonObject object(JsonElement value, String... fields) {
        check(value instanceof JsonObject, "object required");
        var object = value.getAsJsonObject();
        check(object.keySet().equals(Set.of(fields)), "exact required fields");
        return object;
    }
    private static String string(JsonElement value) {
        check(value instanceof JsonPrimitive p && p.isString(), "string required");
        return value.getAsString();
    }
    private static BigDecimal number(JsonElement value) {
        check(value instanceof JsonPrimitive p && p.isNumber(), "number required");
        return value.getAsBigDecimal();
    }
    private static long integer(JsonElement value) { return number(value).longValueExact(); }
    private static void exact(JsonElement value, String expected) {
        check(number(value).compareTo(new BigDecimal(expected)) == 0, "exact sourced setting");
    }

    public static Perk perk() { return PERK; }
    public static int cooldownTicks() { return PERK.cooldownTicks; }
    public static List<WeaponPerks.Roll> rolls() { return ROLLS; }
    /** Forged catalog records and unsupported/exotic weapons cannot capture a source. */
    public static boolean supports(WeaponCatalog.Entry entry) {
        return entry != null && WeaponCatalog.find(entry.id()).filter(entry::equals).isPresent()
                && ROLLS.stream().anyMatch(r -> r.id().equals(entry.id()));
    }
}
