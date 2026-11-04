package kim.biryeong.destiny.weapon;

import com.google.gson.*;
import com.google.gson.stream.JsonReader;
import com.google.gson.stream.JsonToken;
import java.io.*;
import java.math.BigDecimal;
import java.nio.charset.StandardCharsets;
import java.util.*;

/** Exact base sockets; Measured-table adaptation for PvE, NOT a verified Destiny integer formula.
 * Clarity supplies endpoints/half-magazine threshold only; current DDC adds7.5% maximum. See owned SOURCE.md for limitations.
 * Pure catalog arithmetic: no Java entities, stacks, ammo reads or selection/session mutation.
 */
public final class HighImpactReservesProfile {
    public static final String ID = "high_impact_reserves";
    public static final long HASH = 2213355989L;
    private static final String SOURCE = "art/weapons/w182/high_impact_reserves/clarity-source.json";
    private static final String RESOURCE = "/destiny/weapons/w182-high_impact_reserves.json";
    public static final String MAPPING = "MEASURED_2019_40ROUND_QUANTIZED_ENDPOINT_NORMALIZATION_W182_NOT_CURRENT_EXACT_FORMULA";
    // Dated firsthand40-round body damage: index = rounds AFTER the shot. Preserve all rungs.
    private static final int[] MEASURED = {595,595,595,595,595,582,570,568,556,555,544,
            543,542,541,531,531,531,531,531,530,530};
    private static final Set<WeaponPerks.Roll> EXPECTED = Set.of(
        roll("seventh_seraph_officer_revolver", 3037520408L, 4, 3527094473L),
        roll("bygones", 2712244741L, 3, 1760176771L),
        roll("chattering_bone", 568515759L, 4, 423791138L),
        roll("blast_furnace", 3843477312L, 4, 169306153L),
        roll("claws_of_the_wolf", 1280933460L, 4, 753756428L),
        roll("long_arm", 8293111L, 4, 619833418L),
        roll("bug_out_bag", 2744715540L, 4, 575371383L),
        roll("high_albedo", 1197486957L, 4, 718633408L),
        roll("dream_breaker", 2931957300L, 4, 1206254527L),
        roll("hammerhead", 603242241L, 4, 2479293397L));
    private static final List<WeaponPerks.Roll> ROLLS = load();
    private HighImpactReservesProfile() {}

    private static WeaponPerks.Roll roll(String id, long hash, int socket, long pool) {
        return new WeaponPerks.Roll(id, hash, socket, HASH, pool);
    }

    private static IllegalStateException invalid(String detail) {
        return new IllegalStateException("Invalid W182 High-Impact Reserves profile: " + detail);
    }
    private static void check(boolean condition, String detail) { if (!condition) throw invalid(detail); }

    private static List<WeaponPerks.Roll> load() {
        var stream = HighImpactReservesProfile.class.getResourceAsStream(RESOURCE);
        if (stream == null) throw invalid("missing resource");
        try (var reader = new InputStreamReader(stream, StandardCharsets.UTF_8)) {
            return parse(reader);
        } catch (IOException e) { throw new IllegalStateException("Cannot read W182 High-Impact Reserves", e); }
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
            check("W182".equals(string(data.get("stage"))), "stage");
            var perk = object(data.get("perk"), "id", "hash", "normalMinimum", "normalMaximum",
                    "fusionMinimum", "fusionMaximum", "mapping", "damageSource");
            check(ID.equals(string(perk.get("id"))) && HASH == integer(perk.get("hash"))
                    && SOURCE.equals(string(perk.get("damageSource")))
                    && MAPPING.equals(string(perk.get("mapping"))), "base trait/source/measured adaptation policy");
            exact(perk.get("normalMinimum"), "1.121");
            exact(perk.get("normalMaximum"), "1.256");
            exact(perk.get("fusionMinimum"), "1.103");
            exact(perk.get("fusionMaximum"), "1.229");
            check(data.get("weapons") instanceof JsonArray, "weapon array");
            var rows = data.getAsJsonArray("weapons");
            check(rows.size() == EXPECTED.size(), "ten exact sockets");
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
            throw new IllegalStateException("Invalid W182 High-Impact Reserves resource", e);
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

    public static List<WeaponPerks.Roll> rolls() { return ROLLS; }
    public static boolean supports(WeaponCatalog.Entry entry) {
        return entry != null && WeaponCatalog.find(entry.id()).filter(entry::equals).isPresent()
                && EXPECTED.stream().anyMatch(r -> r.id().equals(entry.id()));
    }
    /** Pure arithmetic on TRUE rounds before the paid cartridge, never rounds after consumption.
     * Reject inconsistent capacities (including overflow magazine sizes); canonical base only.
     * Invalid inputs throw here; the runtime capture boundary converts them to NONE.
     */
    public static float multiplier(WeaponCatalog.Entry entry, int roundsBefore, int baseCapacity) {
        if (!supports(entry)) throw new IllegalArgumentException("No base HIR socket for entry");
        if (baseCapacity != WeaponProfile.forEntry(entry).magazine()
                || roundsBefore < 1 || roundsBefore > baseCapacity)
            throw new IllegalArgumentException("HIR requires valid true pre-rounds and canonical base capacity");
        int after = roundsBefore - 1;
        if (2L * after > baseCapacity) return 1f;
        // Source2019 evaluates shot20/40 at after20 (50%). Project conservatively via ceiling:
        // never advance to a lower measured ammo index before crossing its rational boundary.
        int referenceAfter = (int)((40L * after + baseCapacity - 1) / baseCapacity);
        boolean reduced = entry.family().equals("fusion_rifle")
                || entry.family().equals("linear_fusion_rifle") && entry.frame().equals("aggressive_burst");
        double minimum = reduced ? 1.103 : 1.121;
        double maximum = reduced ? 1.229 : 1.256;
        return (float)(minimum + (MEASURED[referenceAfter] - 530) * (maximum - minimum) / 65);

    }
}
