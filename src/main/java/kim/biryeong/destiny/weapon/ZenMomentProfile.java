package kim.biryeong.destiny.weapon;

import com.google.gson.*;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.security.*;
import java.util.*;

/** Exact official base sockets. Numeric flinch, tentative cap and refresh-all expiry are
 * explicitly authored port policies, not measurements of the original game. No stability bonus.
 * Initialization reads canonical JSON directly and never enters the WeaponPerks registry. */
public final class ZenMomentProfile {
    public static final String ID = "zen_moment";
    public static final long HASH = 2387244414L;
    public static final int DURATION_TICKS = 20, MAX_STACK_UNITS = 10, UNITS_PER_STACK = 2;
    private static final Gson GSON = new Gson();
    private static final List<WeaponPerks.Roll> EXPECTED = List.of(
        new WeaponPerks.Roll("duke_mk_44",2112909414L,2,HASH,3744182842L),
        new WeaponPerks.Roll("austringer",3055790362L,4,HASH,785215120L),
        new WeaponPerks.Roll("gnawing_hunger",821154603L,3,HASH,1144396384L),
        new WeaponPerks.Roll("cold_denial",1216130969L,3,HASH,330841869L),
        new WeaponPerks.Roll("blast_furnace",3843477312L,3,HASH,1976101165L),
        new WeaponPerks.Roll("frontier_justice",273396910L,3,HASH,174L), // curated fixed-roll legendary
        new WeaponPerks.Roll("distant_relation",2034817450L,3,HASH,1131958073L),
        new WeaponPerks.Roll("bug_out_bag",2744715540L,3,HASH,907333373L),
        new WeaponPerks.Roll("lonesome",2199171672L,3,HASH,3612808001L),
        new WeaponPerks.Roll("dead_man_walking_xx7463",3751622019L,4,HASH,1210839935L),
        new WeaponPerks.Roll("retrofit_escapade",3103325054L,3,HASH,3756086698L));
    private record Data(JsonObject document, List<WeaponPerks.Roll> rolls,
                        Map<String, WeaponCatalog.Entry> entries) {}
    private static final Data DATA = load();
    private ZenMomentProfile() {}
    private static void check(boolean valid, String reason) {
        if (!valid) throw new IllegalStateException("Invalid W188 Zen Moment: " + reason);
    }
    private static byte[] bytes(String path) {
        var input = ZenMomentProfile.class.getResourceAsStream(path);
        check(input != null, "missing " + path);
        try (input) { return input.readAllBytes(); }
        catch (IOException error) { throw new IllegalStateException(error); }
    }
    private static JsonElement json(String path) {
        return JsonParser.parseString(new String(bytes(path), StandardCharsets.UTF_8));
    }
    private static Data load() {
        byte[] raw = bytes("/destiny/weapons/w188-zen_moment.json");
        try {
            check(HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw))
                    .equals("e7cfd735995a8710dce0a0ed46f7f9bfb14f11df8c0ab05f970da03329f326fc"), "checksum");
        } catch (NoSuchAlgorithmException error) { throw new IllegalStateException(error); }
        var root = JsonParser.parseString(new String(raw, StandardCharsets.UTF_8)).getAsJsonObject();
        check(root.keySet().equals(Set.of("stage", "perk", "weapons"))
                && root.get("stage").getAsString().equals("W188"), "schema");
        var rolls = new ArrayList<WeaponPerks.Roll>();
        for (var row : root.getAsJsonArray("weapons")) {
            var roll = GSON.fromJson(row, WeaponPerks.Roll.class);
            check(row.equals(GSON.toJsonTree(roll)) && EXPECTED.contains(roll)
                    && !rolls.contains(roll), "exact unique base roll");
            rolls.add(roll);
        }
        check(rolls.size() == EXPECTED.size(), "complete eleven sockets");
        Map<String, WeaponCatalog.Entry> entries = new HashMap<>();
        for (var row : json("/destiny/weapons/w30.json").getAsJsonArray()) {
            var entry = GSON.fromJson(row, WeaponCatalog.Entry.class);
            if (rolls.stream().anyMatch(roll -> roll.id().equals(entry.id())))
                check(entries.putIfAbsent(entry.id(), entry) == null, "unique canonical entry");
        }
        check(entries.size() == EXPECTED.size(), "canonical entries");
        int characteristics = 0;
        for (var row : json("/destiny/weapons/w40-characteristics.json").getAsJsonArray()) {
            var c = row.getAsJsonObject(); String id = c.get("id").getAsString();
            if (!entries.containsKey(id)) continue;
            var roll = rolls.stream().filter(v -> v.id().equals(id)).findFirst().orElseThrow();
            check(c.get("bungieHash").getAsLong() == roll.hash()
                    && !c.get("exotic").getAsBoolean(), "legendary identity");
            characteristics++;
        }
        check(characteristics == EXPECTED.size(), "complete characteristics");
        return new Data(root, List.copyOf(rolls), Map.copyOf(entries));
    }
    public static List<WeaponPerks.Roll> rolls() { return DATA.rolls; }
    public static boolean supports(WeaponCatalog.Entry entry) {
        return entry != null && entry.equals(DATA.entries.get(entry.id()));
    }
    /** Half-stack units preserve exact pulse/sidearm 1.5 stacks; no integer truncation. */
    public static int hitUnits(WeaponCatalog.Entry entry) {
        if (!supports(entry)) return 0;
        return switch (entry.family()) {
            case "hand_cannon", "scout_rifle" -> 4;
            case "pulse_rifle", "sidearm" -> 3;
            default -> 2;
        };
    }
    /** AUTHORED linear ten percent per stack, maximum 50%; source numeric flinch is unknown. */
    public static float flinchScalar(int stackUnits) {
        return stackUnits < 0 || stackUnits > MAX_STACK_UNITS ? 1f : 1f - .05f * stackUnits;
    }
    static void validateResource(String value) {
        // Exact lexical JSON bytes also reject numeric type coercion, duplicate keys and unknown fields.
        check(Arrays.equals(value.getBytes(StandardCharsets.UTF_8),
                bytes("/destiny/weapons/w188-zen_moment.json")), "mutated resource");
    }
}
