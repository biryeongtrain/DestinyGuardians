package kim.biryeong.destiny.weapon;

import com.google.gson.Gson;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.List;

/** Base Encore, DDC Weapon Perks row83. Initialization only reads JSON, never perk registries. */
public final class EncoreProfile {
    public static final String ID = "encore";
    public static final long HASH = 1195158366L;
    private static final List<WeaponPerks.Roll> EXPECTED = List.of(
        new WeaponPerks.Roll("fixed_odds", 2194955522L, 3, HASH, 4227334000L));
    private record Perk(String id, long hash, int rangePerStack, int stabilityPerStack,
                        double coneReductionPerStack, int durationTicks, int maxStacks,
                        int precisionKillStacks, boolean refresh, boolean persistsStow) {}
    /** Raw hip curve for master's total-range-stat composition; apply ADS after this curve.
     * Sum legal bonuses, clamp baseRangeStat + totalBonus to 0..100, then evaluate both endpoints.
     */
    public record RangeCurve(String id, int baseRangeStat, double offsetStart, double vppStart,
                             double offsetEnd, double vppEnd, double floor, double precision) {}
    private record Data(String stage, Perk perk, List<WeaponPerks.Roll> weapons, RangeCurve rangeCurve) {}
    private static final Data DATA = load();
    private EncoreProfile() {}

    private static Data load() {
        var stream = EncoreProfile.class.getResourceAsStream("/destiny/weapons/w192-encore.json");
        if (stream == null) throw new IllegalStateException("Missing W192 Encore");
        try (var reader = new InputStreamReader(stream, StandardCharsets.UTF_8)) {
            var d = new Gson().fromJson(reader, Data.class);
            if (d == null || !"W192".equals(d.stage) || d.perk == null
                || !new Perk(ID, HASH, 5, 8, .0125, EncoreCycle.DURATION_TICKS,
                    EncoreCycle.MAX_STACKS, 2, true, true).equals(d.perk)
                || !EXPECTED.equals(d.weapons)
                || !new RangeCurve("fixed_odds", 63, 28.5, .0223, 38.2, 0, .5,
                    1.4607843137254901).equals(d.rangeCurve))
                throw new IllegalStateException("Invalid W192 Encore definition/socket/curve");
            return new Data(d.stage, d.perk, List.copyOf(d.weapons), d.rangeCurve);
        } catch (java.io.IOException e) { throw new IllegalStateException(e); }
    }
    public static List<WeaponPerks.Roll> rolls() { return DATA.weapons; }
    public static boolean supports(WeaponCatalog.Entry entry) {
        return entry != null && WeaponCatalog.find(entry.id()).filter(entry::equals).isPresent()
            && EXPECTED.stream().anyMatch(r -> r.id().equals(entry.id())
                && r.hash() == WeaponCharacteristics.of(entry).bungieHash())
            && !WeaponCharacteristics.of(entry).exotic();
    }
    public static RangeCurve rangeCurve(WeaponCatalog.Entry entry) {
        if (!supports(entry)) throw new IllegalArgumentException("Unsupported Encore weapon");
        return DATA.rangeCurve;
    }
    public static int durationTicks() { return DATA.perk.durationTicks; }
    private static int capped(int stacks) { return Math.clamp(stacks, 0, DATA.perk.maxStacks); }
    public static int rangeBonus(int stacks) { return capped(stacks) * DATA.perk.rangePerStack; }
    public static int stabilityBonus(int stacks) { return capped(stacks) * DATA.perk.stabilityPerStack; }
    public static float coneScalar(int stacks) {
        return (float)(1 - capped(stacks) * DATA.perk.coneReductionPerStack);
    }
}
