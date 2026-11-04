package kim.biryeong.destiny.weapon;

import com.google.gson.*;
import com.google.gson.stream.JsonReader;
import com.google.gson.stream.JsonToken;
import java.io.*;
import java.math.BigDecimal;
import java.nio.charset.StandardCharsets;
import java.util.*;

/** Exact W181 base Vorpal sockets and pinned Clarity PvE multipliers by ammunition type. */
public final class VorpalProfile {
    public static final String ID = "vorpal_weapon";
    public static final long HASH = 1546637391L;
    private static final String SOURCE = "art/weapons/w181/vorpal/clarity-source.json";
    private static final String RESOURCE = "/destiny/weapons/w181-vorpal.json";
    public record Perk(String id, long hash, float primaryMultiplier, float specialMultiplier,
                       float heavyMultiplier, String damageSource) {}
    private static final Perk PERK = new Perk(ID, HASH, 1.20f, 1.15f, 1.10f, SOURCE);
    private static final Set<WeaponPerks.Roll> EXPECTED = Set.of(
        roll("seventh_seraph_officer_revolver", 3037520408L, 3527094473L),
        roll("steelfeather_repeater", 1251729046L, 2645685327L),
        roll("patron_of_lost_causes", 2723241847L, 120674550L),
        roll("aishas_embrace", 2638190703L, 4211351701L),
        roll("farewell", 541188001L, 3819615926L),
        roll("whispering_slab", 211938782L, 967526625L),
        roll("bite_of_the_fox", 1403800851L, 2442672691L),
        roll("first_in_last_out", 3616586446L, 1439234589L),
        roll("hollow_words", 607191995L, 1485010760L),
        roll("stormchaser", 3652506829L, 4213354588L),
        roll("canis_major", 2066434718L, 2791121719L),
        roll("dimensional_hypotrochoid", 1311684613L, 1092097342L),
        roll("salvager_s_salvo", 2060863616L, 254L), // curated fixed-roll legendary socket4
        roll("retrofit_escapade", 3103325054L, 2461260598L),
        roll("crown_splitter", 2782325302L, 99092784L),
        roll("temptation_s_hook", 35794111L, 2147541212L),
        roll("nezarec_s_whisper", 254636484L, 699056095L));
    private static final List<WeaponPerks.Roll> ROLLS = load();
    private VorpalProfile() {}

    private static WeaponPerks.Roll roll(String id, long hash, long pool) {
        return new WeaponPerks.Roll(id, hash, 4, HASH, pool);
    }

    private static IllegalStateException invalid(String detail) {
        return new IllegalStateException("Invalid W181 Vorpal profile: " + detail);
    }
    private static void check(boolean condition, String detail) { if (!condition) throw invalid(detail); }

    private static List<WeaponPerks.Roll> load() {
        var stream = VorpalProfile.class.getResourceAsStream(RESOURCE);
        if (stream == null) throw invalid("missing resource");
        try (var reader = new InputStreamReader(stream, StandardCharsets.UTF_8)) {
            return parse(reader);
        } catch (IOException e) { throw new IllegalStateException("Cannot read W181 Vorpal", e); }
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
            check("W181".equals(string(data.get("stage"))), "stage");
            var perk = object(data.get("perk"), "id", "hash", "primaryMultiplier", "specialMultiplier",
                    "heavyMultiplier", "damageSource");
            check(ID.equals(string(perk.get("id"))) && HASH == integer(perk.get("hash"))
                    && SOURCE.equals(string(perk.get("damageSource"))), "base trait/source");
            exact(perk.get("primaryMultiplier"), "1.20");
            exact(perk.get("specialMultiplier"), "1.15");
            exact(perk.get("heavyMultiplier"), "1.10");
            check(data.get("weapons") instanceof JsonArray, "weapon array");
            var rows = data.getAsJsonArray("weapons");
            check(rows.size() == EXPECTED.size(), "seventeen exact sockets");
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
                check(meta.ammo() == expectedAmmo(roll.id()), "official ammunition type");
                result.add(roll);
            }
            check(seen.equals(EXPECTED), "complete socket allowlist");
            return List.copyOf(result);
        } catch (IOException | RuntimeException e) {
            throw new IllegalStateException("Invalid W181 Vorpal resource", e);
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
                while (reader.hasNext()) { check(array.size() < 32, "excess rows"); array.add(read(reader, depth + 1)); }
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

    private static WeaponAmmoType expectedAmmo(String id) {
        return switch (id) {
            case "seventh_seraph_officer_revolver", "steelfeather_repeater", "patron_of_lost_causes",
                 "aishas_embrace", "farewell", "whispering_slab" -> WeaponAmmoType.PRIMARY;
            case "bite_of_the_fox", "first_in_last_out", "hollow_words", "nezarec_s_whisper", "salvager_s_salvo" -> WeaponAmmoType.SPECIAL;
            default -> WeaponAmmoType.HEAVY; // Only the exact allowlisted remaining six reach this branch.
        };
    }
    public static Perk perk() { return PERK; }
    public static List<WeaponPerks.Roll> rolls() { return ROLLS; }
    public static boolean supports(WeaponCatalog.Entry entry) {
        return entry != null && WeaponCatalog.find(entry.id()).filter(entry::equals).isPresent()
                && EXPECTED.stream().anyMatch(r -> r.id().equals(entry.id()));
    }
    /** Pure source scalar. Target eligibility is checked independently for each impact. */
    public static float multiplier(WeaponCatalog.Entry entry) {
        if (!supports(entry)) throw new IllegalArgumentException("No Vorpal socket for entry");
        return switch (WeaponCharacteristics.of(entry).ammo()) {
            case PRIMARY -> PERK.primaryMultiplier;
            case SPECIAL -> PERK.specialMultiplier;
            case HEAVY -> PERK.heavyMultiplier;
        };
    }
}
