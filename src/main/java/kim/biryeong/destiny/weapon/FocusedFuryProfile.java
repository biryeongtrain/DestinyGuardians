package kim.biryeong.destiny.weapon;

import com.google.gson.*;
import java.io.IOException;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.*;

/** Exact selected65 base Focused Fury sockets and immutable official magazine thresholds.
 * Initialization reads resource JSON only; it never calls the outer catalog/perk/timing registries.
 * Clarity supplies 35%, +25%, 11s, reload/stow progress reset and stowed buff persistence.
 * Counter consumption, repeated-threshold refresh and deadline/lifecycle rules are master-owned
 * local policy, documented separately in art/weapons/w174/focused-fury/clarity-source.json.
 */
public final class FocusedFuryProfile {
    public static final String ID = "focused_fury";
    public static final long HASH = 2896038713L;
    private static final String RESOURCE = "/destiny/weapons/w174-focused-fury.json";
    private static final Gson GSON = new Gson();
    private static final Set<WeaponPerks.Roll> EXPECTED = Set.of(
        new WeaponPerks.Roll("aishas_embrace", 2638190703L, 4, HASH, 4211351701L),
        new WeaponPerks.Roll("retraced_path", 548958835L, 4, HASH, 398391969L),
        new WeaponPerks.Roll("fixed_odds", 2194955522L, 4, HASH, 1686775256L));
    private static final Map<String, Integer> MAGAZINES = Map.of(
        "aishas_embrace", 17, "retraced_path", 94, "fixed_odds", 44);
    private static final JsonObject PERK = JsonParser.parseString("""
        {"id":"focused_fury","hash":2896038713,"durationTicks":220,
         "damageMultiplier":1.25,"precisionFraction":0.35}
        """).getAsJsonObject();
    private static final JsonObject POLICIES = JsonParser.parseString("""
        {"threshold":"CEIL_35_PERCENT_OFFICIAL_BASE_MAGAZINE",
         "progressReset":"STOW_OR_RELOAD",
         "buffWhileStowed":"REMAINS_ACTIVE_CLARITY",
         "refresh":"LOCAL_CONSUME_THRESHOLD_RESET_COUNTER_ZERO_REFRESH_220_TICKS",
         "deadline":"LOCAL_STOW_RELOAD_PRESERVE_DEADLINE_NO_PAUSE",
         "damageAttribution":"MASTER_PAID_DIRECT_ONLY_NO_OTHER_PERK_SPLASH",
         "lifecycle":"MASTER_OWNED_LOCAL_POLICY"}
        """).getAsJsonObject();
    private record Source(WeaponCatalog.Entry entry, int baseMagazine) {}
    private record Magazine(String id, int baseMagazine, int threshold) {}
    private static final Map<String, Source> SOURCES = selectedJson();
    private static final List<WeaponPerks.Roll> ROLLS = load();
    private FocusedFuryProfile() {}

    private static void check(boolean condition, String detail) {
        if (!condition) throw new IllegalStateException("Invalid W174 Focused Fury profile: " + detail);
    }
    private static JsonElement read(String path) {
        var stream = FocusedFuryProfile.class.getResourceAsStream(path);
        check(stream != null, "missing resource " + path);
        try (var reader = new InputStreamReader(stream, StandardCharsets.UTF_8)) {
            return JsonParser.parseReader(reader);
        } catch (IOException | JsonParseException e) {
            throw new IllegalStateException("Cannot read W174 source " + path, e);
        }
    }
    private static Map<String, JsonObject> byId(String path) {
        var result = new HashMap<String, JsonObject>();
        for (var e : read(path).getAsJsonArray()) {
            var row = e.getAsJsonObject();
            check(result.putIfAbsent(row.get("id").getAsString(), row) == null, "duplicate source ID");
        }
        return result;
    }
    private static Map<String, Source> selectedJson() {
        var catalog = byId("/destiny/weapons/w30.json");
        var stats = byId("/destiny/weapons/w40-characteristics.json");
        var timings = byId("/destiny/weapons/w46-timing.json");
        var result = new HashMap<String, Source>();
        for (var roll : EXPECTED) {
            var stat = stats.get(roll.id());
            check(stat != null && stat.get("bungieHash").getAsLong() == roll.hash()
                && !stat.get("exotic").getAsBoolean(), "selected base identity");
            int magazine = MAGAZINES.get(roll.id());
            check(stat.getAsJsonObject("stats").get("3871231066").getAsInt() == magazine
                && timings.get(roll.id()).getAsJsonObject("timing").get("magazine").getAsInt() == magazine,
                "selected W40 and current W46 magazine must match pinned official base");
            var entry = GSON.fromJson(catalog.get(roll.id()), WeaponCatalog.Entry.class);
            check(entry != null, "selected canonical entry");
            result.put(roll.id(), new Source(entry, magazine));
        }
        return Map.copyOf(result);
    }
    private static List<WeaponPerks.Roll> load() {
        var root = read(RESOURCE).getAsJsonObject();
        validate(root);
        return List.of(GSON.fromJson(root.get("weapons"), WeaponPerks.Roll[].class));
    }
    /** Pure malformed-resource regression entry point. Does not mutate the live profile. */
    static void validateResource(String json) {
        try { validate(JsonParser.parseString(json).getAsJsonObject()); }
        catch (RuntimeException e) { throw new IllegalStateException("Invalid W174 Focused Fury JSON", e); }
    }
    private static void validate(JsonObject root) {
        check(root.keySet().equals(Set.of("stage", "perk", "policies", "weapons", "magazines")), "resource fields");
        check("W174".equals(root.get("stage").getAsString()) && PERK.equals(root.get("perk"))
            && POLICIES.equals(root.get("policies")), "pinned mechanics and explicit local policies");
        var rows = root.getAsJsonArray("weapons");
        check(rows.size() == EXPECTED.size(), "exact three base rolls");
        var found = new HashSet<WeaponPerks.Roll>();
        for (var raw : rows) {
            var roll = GSON.fromJson(raw, WeaponPerks.Roll.class);
            check(roll != null && EXPECTED.contains(roll) && found.add(roll)
                && GSON.toJsonTree(roll).equals(raw), "exact unique base ID/hash/socket/pool");
        }
        var magazines = root.getAsJsonArray("magazines");
        check(magazines.size() == MAGAZINES.size(), "three magazine plans");
        var ids = new HashSet<String>();
        for (var raw : magazines) {
            var plan = GSON.fromJson(raw, Magazine.class);
            check(plan != null && MAGAZINES.containsKey(plan.id) && ids.add(plan.id)
                && plan.baseMagazine == SOURCES.get(plan.id).baseMagazine
                && plan.threshold == thresholdForMagazine(plan.baseMagazine)
                && GSON.toJsonTree(plan).equals(raw), "exact official base and ceil threshold");
        }
    }
    /** Integer ceil(0.35 * baseMagazine), avoiding floating-point or int multiplication overflow. */
    static int thresholdForMagazine(int baseMagazine) {
        if (baseMagazine < 1) throw new IllegalArgumentException("Positive base magazine required");
        return (int) ((35L * baseMagazine + 99L) / 100L);
    }
    public static List<WeaponPerks.Roll> rolls() { return ROLLS; }
    public static int durationTicks() { return 220; }
    public static float multiplier() { return 1.25f; }
    public static boolean supports(String id) { return id != null && SOURCES.containsKey(id); }
    /** All canonical fields must match; a forged same-ID entry is not eligible. */
    public static boolean supports(WeaponCatalog.Entry entry) {
        return entry != null && supports(entry.id()) && SOURCES.get(entry.id()).entry.equals(entry);
    }
    /** Immutable official base capacity, never remaining ammo, overflow or modified magazine size. */
    public static int threshold(WeaponCatalog.Entry entry) {
        if (!supports(entry)) throw new IllegalArgumentException("No Focused Fury threshold for unsupported/noncanonical entry");
        return thresholdForMagazine(SOURCES.get(entry.id()).baseMagazine);
    }
}
