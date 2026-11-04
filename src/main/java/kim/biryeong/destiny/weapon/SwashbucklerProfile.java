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

/** Exact base-trait settings and eight pinned official sockets, no sword or glaive sockets. */
public final class SwashbucklerProfile {
    public static final String ID = "swashbuckler";
    public static final long HASH = 4082225868L;
    private static final String RESOURCE = "/destiny/weapons/w110-swashbuckler.json";
    public record Perk(String id, long hash, int durationTicks,
                       List<Float> multipliers, String timingSource) {
        public Perk { multipliers = List.copyOf(multipliers); }
    }
    private record Data(String stage, Perk perk, WeaponPerks.Roll[] weapons) {}
    private static final Set<WeaponPerks.Roll> EXPECTED = Set.of(
        roll("gnawing_hunger", 821154603L, 594510568L),
        roll("steelfeather_repeater", 1251729046L, 2645685327L),
        roll("cold_denial", 1216130969L, 720537379L),
        roll("bug_out_bag", 2744715540L, 575371383L),
        roll("lonesome", 2199171672L, 167712635L),
        roll("biting_winds", 1621657423L, 2763203653L),
        roll("whispering_slab", 211938782L, 967526625L),
        roll("mindbender_s_ambition_adept", 912150785L, 4054654930L));
    private static final Data DATA = load();
    private SwashbucklerProfile() {}

    private static WeaponPerks.Roll roll(String id, long hash, long pool) {
        return new WeaponPerks.Roll(id, hash, 4, HASH, pool);
    }
    private static IllegalStateException invalid() {
        return new IllegalStateException("Invalid W110 Swashbuckler profile");
    }
    private static void check(boolean condition) { if (!condition) throw invalid(); }

    private static Data load() {
        var stream = SwashbucklerProfile.class.getResourceAsStream(RESOURCE);
        if (stream == null) throw invalid();
        try (var reader = new InputStreamReader(stream, StandardCharsets.UTF_8)) {
            var text = new StringBuilder();
            var buffer = new char[4096];
            for (int n; (n = reader.read(buffer)) != -1;) text.append(buffer, 0, n);
            return parse(text.toString());
        } catch (IOException e) { throw new IllegalStateException("Cannot read W110 Swashbuckler", e); }
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
        number(object.get(key), expected);
    }
    private static void number(JsonElement value, String expected) {
        check(value != null && value.isJsonPrimitive() && value.getAsJsonPrimitive().isNumber()
                && value.getAsBigDecimal().compareTo(new BigDecimal(expected)) == 0);
    }
    private static Data parse(String json) {
        try (var reader = new JsonReader(new StringReader(Objects.requireNonNull(json)))) {
            reader.setStrictness(Strictness.STRICT);
            var root = read(reader, 0).getAsJsonObject();
            check(reader.peek() == JsonToken.END_DOCUMENT);
            fields(root, "stage", "perk", "weapons");
            string(root, "stage", "W110");
            var perk = root.getAsJsonObject("perk");
            fields(perk, "id", "hash", "durationTicks", "multipliers", "timingSource");
            string(perk, "id", ID);
            number(perk, "hash", Long.toString(HASH));
            number(perk, "durationTicks", "90");
            var multipliers = perk.getAsJsonArray("multipliers");
            String[] values = {"1", "1.067", "1.133", "1.2", "1.266", "1.333"};
            check(multipliers.size() == values.length);
            for (int i = 0; i < values.length; i++) number(multipliers.get(i), values[i]);
            string(perk, "timingSource", "art/weapons/w110/references/clarity-source.json");
            var weapons = root.getAsJsonArray("weapons");
            check(weapons.size() == EXPECTED.size());
            var found = new HashSet<WeaponPerks.Roll>();
            for (var element : weapons) {
                var row = element.getAsJsonObject();
                fields(row, "id", "hash", "socket", "perkHash", "plugSetHash");
                var expected = EXPECTED.stream().filter(r -> r.id().equals(row.get("id").getAsString()))
                    .findFirst().orElseThrow(SwashbucklerProfile::invalid);
                string(row, "id", expected.id());
                number(row, "hash", Long.toString(expected.hash()));
                number(row, "socket", Integer.toString(expected.socket()));
                number(row, "perkHash", Long.toString(HASH));
                number(row, "plugSetHash", Long.toString(expected.plugSetHash()));
                check(found.add(expected));
                var entry = WeaponCatalog.find(expected.id()).orElseThrow(SwashbucklerProfile::invalid);
                var meta = WeaponCharacteristics.of(entry);
                check(meta.bungieHash() == expected.hash() && !meta.exotic());
            }
            check(found.equals(EXPECTED));
            return new Gson().fromJson(root, Data.class);
        } catch (IOException | RuntimeException e) {
            throw new IllegalStateException("Invalid W110 Swashbuckler profile", e);
        }
    }
    static void validateResource(String json) { parse(json); }
    public static Perk perk() { return DATA.perk; }
    public static int durationTicks() { return DATA.perk.durationTicks; }
    public static List<Float> multipliers() { return DATA.perk.multipliers; }
    public static float multiplier(int stacks) {
        if (stacks < 0 || stacks > 5) throw new IllegalArgumentException("Invalid Swashbuckler stack count");
        return multipliers().get(stacks);
    }
    public static List<WeaponPerks.Roll> rolls() { return List.of(DATA.weapons); }

    /** Canonical catalog membership rejects forged records sharing only an ID. */
    public static boolean supports(WeaponCatalog.Entry entry) {
        return entry != null && WeaponCatalog.find(entry.id()).filter(entry::equals).isPresent()
                && EXPECTED.stream().anyMatch(r -> r.id().equals(entry.id()));
    }
}
