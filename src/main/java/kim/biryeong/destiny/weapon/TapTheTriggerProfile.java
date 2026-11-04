package kim.biryeong.destiny.weapon;

import com.google.gson.*;
import java.io.IOException;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.*;

/** Exact base trait sockets and sourced bonuses. Runtime cycles and adapters are master-owned.
 * Static initialization reads only this profile, never the catalog or outer perk registry.
 */
public final class TapTheTriggerProfile {
    public static final String ID = "tap_the_trigger";
    public static final long HASH = 1890422124L;
    private static final String RESOURCE = "/destiny/weapons/w171-tap-the-trigger.json";
    public record Bonuses(int stabilityBonus, float recoilScalar, float accuracyScalar) {}
    public record Perk(String id, long hash, double durationSeconds, int durationTicks,
                       Bonuses ordinary, Bonuses fusion) {}
    private record Data(String stage, Perk perk, JsonObject policies, WeaponPerks.Roll[] weapons) {}
    private static final Set<WeaponPerks.Roll> EXPECTED = Set.of(
        new WeaponPerks.Roll("ammit_ar2", 2119346509L, 4, HASH, 560115158L),
        new WeaponPerks.Roll("gnawing_hunger", 821154603L, 3, HASH, 1144396384L),
        new WeaponPerks.Roll("dead_man_walking_xx7463", 3751622019L, 4, HASH, 1210839935L),
        new WeaponPerks.Roll("dream_breaker", 2931957300L, 4, HASH, 1206254527L),
        new WeaponPerks.Roll("hammerhead", 603242241L, 3, HASH, 2515290473L),
        new WeaponPerks.Roll("retrofit_escapade", 3103325054L, 4, HASH, 2461260598L));
    private static final JsonObject POLICIES = JsonParser.parseString("""
        {
          "refresh": "AFTER_AUTOMATIC_STOPS_FIRING_OR_NEXT_BURST",
          "cycleIntegration": "MASTER_OWNED_LOCAL_POLICY",
          "stabilityRecoilSpreadAdapters": "MASTER_OWNED_LOCAL_POLICY",
          "controllerPressure": "CONTROLLER_ONLY_OUTSIDE_JAVA_KEYBOARD_IMPLEMENTATION",
          "tickConversion": "0.6_SECONDS_TIMES_20_EQUALS_12"
        }
        """).getAsJsonObject();
    private static final Data DATA = load();
    private static final Set<String> IDS = Set.of("ammit_ar2", "gnawing_hunger", "dead_man_walking_xx7463",
        "dream_breaker", "hammerhead", "retrofit_escapade");
    private TapTheTriggerProfile() {}

    private static void check(boolean condition, String detail) {
        if (!condition) throw new IllegalStateException("Invalid W171 Tap the Trigger profile: " + detail);
    }
    private static Data load() {
        var stream = TapTheTriggerProfile.class.getResourceAsStream(RESOURCE);
        check(stream != null, "missing resource");
        try (var reader = new InputStreamReader(stream, StandardCharsets.UTF_8)) {
            var data = new Gson().fromJson(reader, Data.class);
            validate(data);
            return data;
        } catch (IOException | JsonParseException e) {
            throw new IllegalStateException("Cannot read W171 Tap the Trigger profile", e);
        }
    }
    static void validateResource(String json) {
        try {
            validate(new Gson().fromJson(json, Data.class));
        } catch (JsonParseException e) {
            throw new IllegalStateException("Invalid W171 Tap the Trigger JSON", e);
        }
    }
    private static void validate(Data data) {
        check(data != null && "W171".equals(data.stage), "stage");
        check(new Perk(ID, HASH, .6, 12, new Bonuses(40, .5f, .9f),
            new Bonuses(10, .875f, .975f)).equals(data.perk), "exact base mechanics");
        check(POLICIES.equals(data.policies), "refresh and master-owned integration policy");
        check(data.weapons != null && data.weapons.length == 6, "six base sockets");
        var rolls = new HashSet<WeaponPerks.Roll>();
        for (var roll : data.weapons)
            check(roll != null && EXPECTED.contains(roll) && rolls.add(roll), "exact unique base socket");
        check(rolls.equals(EXPECTED), "complete membership");
    }
    public static List<WeaponPerks.Roll> rolls() { return List.of(DATA.weapons); }
    public static Perk perk() { return DATA.perk; }
    public static int durationTicks() { return DATA.perk.durationTicks; }

    /** Equality with the full canonical catalog entry prevents same-ID forged family substitutions. */
    public static boolean supports(WeaponCatalog.Entry entry) {
        return entry != null && IDS.contains(entry.id())
            && WeaponCatalog.find(entry.id()).filter(entry::equals).isPresent();
    }
    private static Bonuses bonuses(WeaponCatalog.Entry entry) {
        if (!supports(entry)) throw new IllegalArgumentException("Unsupported Tap the Trigger entry: " + entry);
        return "fusion_rifle".equals(entry.family()) ? DATA.perk.fusion : DATA.perk.ordinary;
    }
    public static int stabilityBonus(WeaponCatalog.Entry entry) { return bonuses(entry).stabilityBonus; }
    public static float recoilScalar(WeaponCatalog.Entry entry) { return bonuses(entry).recoilScalar; }
    public static float accuracyScalar(WeaponCatalog.Entry entry) { return bonuses(entry).accuracyScalar; }
}
