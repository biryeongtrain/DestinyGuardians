package kim.biryeong.destiny.weapon;

import com.google.gson.Gson;
import java.io.IOException;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.*;

/** Exact selected base traits; Clarity tier values applied to W62's historical W46 curves.
 * Stow, consumption, refresh scope and expiration mode are explicitly unknown in these sources.
 */
public final class FeedingFrenzyProfile {
    public static final String ID = "feeding_frenzy";
    public static final long HASH = 2779035018L;
    private static final String RESOURCE = "/destiny/weapons/w108-feeding-frenzy.json";
    private static final int[] BONUSES = {8, 50, 60, 75, 100};
    private static final double[] SCALARS = {.975, .9, .87, .84, .8};

    public record Reload(int firstTicks, int intervalTicks, int baseReloadStat, int effectiveReloadStat) {}
    public record Perk(String id, long hash, int durationTicks, int maxStacks,
                       String timingSource, String mechanicsSource) {}
    public record Policies(String stowPersistence, String reloadConsumption, String killRefreshAllStacks,
                           String expirationAllOrOneStack, String reloadSnapshot, int statCap,
                           String rounding, String shellFirstDelay, String combinedOutlaw) {}
    private record Tier(int stacks, int reloadBonus, double durationMultiplier) {}
    private record Curve(String id, double evpp, double vpp, double offset) {
        double seconds(int stat) { return evpp * stat * stat + vpp * stat + offset; }
    }
    private record Row(String id, int stacks, int firstTicks, int intervalTicks,
                       int baseReloadStat, int effectiveReloadStat) {
        Reload reload() { return new Reload(firstTicks, intervalTicks, baseReloadStat, effectiveReloadStat); }
    }
    private record Data(String stage, Perk perk, Policies policies, Tier[] tiers,
                        WeaponPerks.Roll[] weapons, Curve[] curves, Row[] reloads) {}

    private static final Set<WeaponPerks.Roll> EXPECTED = Set.of(
        roll("seventh_seraph_officer_revolver", 3037520408L, 4, 3527094473L),
        roll("steelfeather_repeater", 1251729046L, 3, 473189353L),
        roll("cold_denial", 1216130969L, 3, 330841869L),
        roll("blast_furnace", 3843477312L, 3, 1976101165L),
        roll("the_recluse", 3354242550L, 3, 242L),
        roll("brass_attacks", 2121785039L, 3, 100135553L),
        roll("hollow_words", 607191995L, 3, 637298592L),
        roll("null_composure", 1644680957L, 3, 272L),
        roll("coriolis_force", 3512349612L, 3, 2568674372L),
        roll("retraced_path", 548958835L, 3, 2945646047L),
        roll("fixed_odds", 2194955522L, 3, 4227334000L),
        roll("hammerhead", 603242241L, 3, 2515290473L),
        roll("retrofit_escapade", 3103325054L, 3, 3756086698L));

    private static final Policies EXPECTED_POLICIES = new Policies(
        "UNKNOWN", "UNKNOWN", "UNKNOWN", "UNKNOWN", "AT_RELOAD_START_LOCAL_POLICY", 100,
        "CEIL_SECONDS_TIMES_20_ONCE", "PRESERVE_EXISTING_DISTINCT_FIRST_DELAY_IF_PRESENT",
        "NO_DISTINCT_SELECTED_SOCKET_PAIR");
    private static final Data DATA = load();
    private static final Map<String, Reload> RELOADS = index();

    private FeedingFrenzyProfile() {}

    private static WeaponPerks.Roll roll(String id, long hash, int socket, long pool) {
        return new WeaponPerks.Roll(id, hash, socket, HASH, pool);
    }

    private static Data load() {
        var stream = FeedingFrenzyProfile.class.getResourceAsStream(RESOURCE);
        if (stream == null) throw invalid("Missing resource");
        try (var reader = new InputStreamReader(stream, StandardCharsets.UTF_8)) {
            var data = new Gson().fromJson(reader, Data.class);
            validate(data);
            return data;
        } catch (IOException e) {
            throw new IllegalStateException("Cannot read W108 Feeding Frenzy profile", e);
        }
    }

    /** Package-visible for pure negative resource tests; never changes the loaded profile. */
    static void validateResource(String json) {
        validate(new Gson().fromJson(json, Data.class));
    }

    private static IllegalStateException invalid(String detail) {
        return new IllegalStateException("Invalid W108 Feeding Frenzy profile: " + detail);
    }

    private static void check(boolean condition, String detail) {
        if (!condition) throw invalid(detail);
    }

    private static void validate(Data data) {
        check(data != null && "W108".equals(data.stage) && data.perk != null, "stage/perk");
        check(new Perk(ID, HASH, 70, 5, "art/weapons/w108/references/reload-timings.json",
                "art/weapons/w108/references/mechanics.json").equals(data.perk), "exact sourced perk constants");
        check(EXPECTED_POLICIES.equals(data.policies), "source unknowns and local policies");
        check(data.tiers != null && data.tiers.length == 5, "five complete tiers");
        var tierNumbers = new HashSet<Integer>();
        for (var tier : data.tiers) {
            check(tier != null && tier.stacks >= 1 && tier.stacks <= 5 && tierNumbers.add(tier.stacks), "unique tier");
            check(tier.reloadBonus == BONUSES[tier.stacks - 1]
                    && Double.compare(tier.durationMultiplier, SCALARS[tier.stacks - 1]) == 0, "sourced tier values");
        }
        check(data.weapons != null && data.weapons.length == EXPECTED.size(), "exact selected socket count");
        var rolls = new HashSet<WeaponPerks.Roll>();
        var ids = new HashSet<String>();
        for (var roll : data.weapons) {
            check(roll != null && EXPECTED.contains(roll) && rolls.add(roll) && ids.add(roll.id()), "exact selected socket");
            var entry = WeaponCatalog.find(roll.id()).orElseThrow(() -> invalid("unknown selected ID"));
            var meta = WeaponCharacteristics.of(entry);
            check(meta.bungieHash() == roll.hash() && !meta.exotic(), "official selected item");
        }
        check(rolls.equals(EXPECTED), "complete selected socket allowlist");
        check(data.curves != null && data.curves.length == ids.size(), "complete historical curves");
        var curves = new HashMap<String, Curve>();
        for (var curve : data.curves) {
            check(curve != null && ids.contains(curve.id) && curves.putIfAbsent(curve.id, curve) == null,
                    "unique selected curve");
            var entry = WeaponCatalog.find(curve.id).orElseThrow(() -> invalid("unknown curve ID"));
            check(expectedCurve(curve.id, entry.family()).equals(curve), "pinned W46 coefficients");
        }
        check(data.reloads != null && data.reloads.length == ids.size() * 5, "complete reload Cartesian product");
        var plans = new HashSet<String>();
        for (var row : data.reloads) {
            check(row != null && ids.contains(row.id) && row.stacks >= 1 && row.stacks <= 5
                    && plans.add(key(row.id, row.stacks)), "unique selected weapon/tier plan");
            var entry = WeaponCatalog.find(row.id).orElseThrow(() -> invalid("unknown reload ID"));
            var stat = WeaponCharacteristics.of(entry).stats().get("4188031367");
            check(stat != null && stat >= 0 && stat <= 100 && stat == row.baseReloadStat, "official base reload stat");
            int effective = Math.min(100, stat + BONUSES[row.stacks - 1]);
            double seconds = curves.get(row.id).seconds(effective) * SCALARS[row.stacks - 1];
            check(Double.isFinite(seconds) && seconds > 0 && seconds <= 60, "finite reload duration");
            int ticks = (int) Math.ceil(seconds * 20);
            check(row.effectiveReloadStat == effective && row.firstTicks == ticks && row.intervalTicks == ticks,
                    "exact stat/scalar/rounding math");
            check(row.firstTicks >= 1 && row.firstTicks <= (int) Math.ceil(curves.get(row.id).seconds(stat) * 20),
                    "reload cannot slow baseline");
            var baseline = WeaponTiming.forEntry(entry);
            check(baseline.supported() && !baseline.shellReload(), "selected whole-magazine timing");
        }
        check(plans.size() == ids.size() * 5, "complete five tiers per selected weapon");
    }

    /** Same coefficient literals as pinned W46; a changed file cannot silently redefine the curve. */
    private static Curve expectedCurve(String id, String family) {
        return switch (family) {
            case "hand_cannon" -> new Curve(id, 6.137590643e-05, -.02385522011, 3.600042253);
            case "auto_rifle" -> new Curve(id, 8.55689e-05, -.0242021, 2.80673006666667);
            case "pulse_rifle" -> new Curve(id, 9.26208e-05, -.0256877, 2.92627266666667);
            case "submachine_gun" -> new Curve(id, 6.08642e-05, -.0191345, 2.62769);
            case "sidearm" -> new Curve(id, 2.38311e-05, -.0124553, 2.14667245);
            case "fusion_rifle" -> new Curve(id, 6.15281e-05, -.0198054, 2.8285704);
            case "trace_rifle" -> new Curve(id, 5e-05, -.0155, 2.65);
            case "machine_gun" -> new Curve(id, 9.05351e-05, -.0305819, 6.1219905);
            default -> throw invalid("unreviewed curve family " + family);
        };
    }

    private static String key(String id, int stacks) { return id + ":" + stacks; }

    private static Map<String, Reload> index() {
        var result = new HashMap<String, Reload>();
        for (var row : DATA.reloads) result.put(key(row.id, row.stacks), row.reload());
        return Map.copyOf(result);
    }

    /** Already validated sourced scalar; used before the final tick rounding in combined stat buffs. */
    public static double durationMultiplier(int stacks) {
        if (stacks < 1 || stacks > 5) throw new IllegalArgumentException("Invalid active reload tier");
        return SCALARS[stacks-1];
    }
    public static int durationTicks() { return DATA.perk.durationTicks; }
    public static int maxStacks() { return DATA.perk.maxStacks; }
    public static Perk perk() { return DATA.perk; }
    public static Policies policies() { return DATA.policies; }
    public static List<WeaponPerks.Roll> rolls() { return List.of(DATA.weapons); }

    /** Active tiers only. Zero/invalid stacks and noncanonical/unsupported entries fail closed. */
    public static Reload reload(WeaponCatalog.Entry entry, int stacks) {
        if (entry == null || stacks < 1 || stacks > 5
                || WeaponCatalog.find(entry.id()).filter(entry::equals).isEmpty())
            throw new IllegalArgumentException("Invalid Feeding Frenzy entry/stacks");
        var result = RELOADS.get(key(entry.id(), stacks));
        if (result == null) throw new IllegalArgumentException("No Feeding Frenzy reload for " + entry.id());
        return result;
    }
}
