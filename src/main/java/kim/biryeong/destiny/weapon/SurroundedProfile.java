package kim.biryeong.destiny.weapon;

import com.google.gson.*;
import com.google.gson.stream.JsonReader;
import com.google.gson.stream.JsonToken;
import java.io.*;
import java.math.BigDecimal;
import java.nio.charset.StandardCharsets;
import java.util.*;

/** Exact W109 base sockets and pinned Clarity settings, including the sword exception. */
public final class SurroundedProfile {
    public static final String ID = "surrounded";
    public static final long HASH = 3708227201L;
    private static final String SOURCE = "art/weapons/w109/references/clarity-source.json";
    private static final String RESOURCE = "/destiny/weapons/w109-surrounded.json";
    public record Perk(String id, long hash, double radius, int minimumEnemies, int lingerTicks,
                       double multiplier, double swordMultiplier, String timingSource) {}
    private static final Perk PERK = new Perk(ID, HASH, 15, 3, 30, 1.4, 1.35, SOURCE);
    private static final Set<WeaponPerks.Roll> EXPECTED = Set.of(
        roll("steelfeather_repeater", 1251729046L, 2645685327L),
        roll("first_in_last_out", 3616586446L, 1439234589L),
        roll("hollow_words", 607191995L, 1485010760L),
        roll("dream_breaker", 2931957300L, 1206254527L),
        roll("hammerhead", 603242241L, 2479293397L),
        roll("crown_splitter", 2782325302L, 99092784L),
        roll("falling_guillotine", 614426548L, 66521752L),
        roll("temptation_s_hook", 35794111L, 2147541212L));
    private static final List<WeaponPerks.Roll> ROLLS = load();
    private SurroundedProfile() {}

    private static WeaponPerks.Roll roll(String id, long hash, long pool) {
        return new WeaponPerks.Roll(id, hash, 4, HASH, pool);
    }

    private static IllegalStateException invalid(String detail) {
        return new IllegalStateException("Invalid W109 Surrounded profile: " + detail);
    }
    private static void check(boolean condition, String detail) { if (!condition) throw invalid(detail); }

    private static List<WeaponPerks.Roll> load() {
        var stream = SurroundedProfile.class.getResourceAsStream(RESOURCE);
        if (stream == null) throw invalid("missing resource");
        try (var reader = new InputStreamReader(stream, StandardCharsets.UTF_8)) {
            return parse(reader);
        } catch (IOException e) { throw new IllegalStateException("Cannot read W109 Surrounded", e); }
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
            check("W109".equals(string(data.get("stage"))), "stage");
            var perk = object(data.get("perk"), "id", "hash", "radius", "minimumEnemies", "lingerTicks",
                    "multiplier", "swordMultiplier", "timingSource");
            check(ID.equals(string(perk.get("id"))) && HASH == integer(perk.get("hash"))
                    && SOURCE.equals(string(perk.get("timingSource"))), "base trait/source");
            exact(perk.get("radius"), "15"); exact(perk.get("minimumEnemies"), "3");
            exact(perk.get("lingerTicks"), "30"); exact(perk.get("multiplier"), "1.4");
            exact(perk.get("swordMultiplier"), "1.35");
            check(data.get("weapons") instanceof JsonArray, "weapon array");
            var rows = data.getAsJsonArray("weapons");
            check(rows.size() == EXPECTED.size(), "eight exact sockets");
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
            throw new IllegalStateException("Invalid W109 Surrounded resource", e);
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
    public static double radius() { return PERK.radius; }
    public static int minimumEnemies() { return PERK.minimumEnemies; }
    public static int lingerTicks() { return PERK.lingerTicks; }
    public static List<WeaponPerks.Roll> rolls() { return ROLLS; }
    /** Unsupported and forged entries cannot request an eligible weapon's multiplier. */
    public static float multiplier(WeaponCatalog.Entry entry) {
        if (entry == null || WeaponCatalog.find(entry.id()).filter(entry::equals).isEmpty()
                || ROLLS.stream().noneMatch(r -> r.id().equals(entry.id())))
            throw new IllegalArgumentException("No Surrounded socket for entry");
        return (float) ("sword".equals(entry.family()) ? PERK.swordMultiplier : PERK.multiplier);
    }
}
