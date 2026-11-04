package kim.biryeong.destiny.weapon;

import com.google.gson.Gson;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.HashSet;
import java.util.List;

/** W192 base Rangefinder, DDC row 174. Enhanced passive +5 Handling is excluded. */
public final class RangefinderProfile {
    public static final String ID = "rangefinder";
    public static final long HASH = 2846385770L;
    private record Perk(String id, long hash, int rangeBonus, float zoomScalar,
                        double projectileSpeedScalar, float minAdsProgress) {}
    private record Range(String id, Integer baseRange, double offsetStart, double vppStart,
                         double offsetEnd, double vppEnd, double floor, double precision) {
        WeaponBallistics.Profile evaluate(int totalBonus) {
            int stat = (int)Math.clamp((long)(baseRange == null ? 0 : baseRange) + totalBonus, 0, 100);
            return new WeaponBallistics.Profile(offsetStart + vppStart * stat,
                offsetEnd + vppEnd * stat, floor, precision);
        }
    }
    private record Data(String stage, Perk perk, List<WeaponPerks.Roll> weapons, List<Range> ranges) {}
    private static final Data DATA = load();
    private RangefinderProfile() {}

    private static Data load() {
        var stream = RangefinderProfile.class.getResourceAsStream("/destiny/weapons/w192-rangefinder.json");
        if (stream == null) throw new IllegalStateException("Missing W192 Rangefinder");
        try (var reader = new InputStreamReader(stream, StandardCharsets.UTF_8)) {
            var data = new Gson().fromJson(reader, Data.class);
            var expected = List.of(
                new WeaponPerks.Roll("duke_mk_44", 2112909414L, 2, HASH, 3744182842L),
                new WeaponPerks.Roll("austringer", 3055790362L, 4, HASH, 785215120L),
                new WeaponPerks.Roll("bygones", 2712244741L, 3, HASH, 1760176771L),
                new WeaponPerks.Roll("chattering_bone", 568515759L, 3, HASH, 216806616L),
                new WeaponPerks.Roll("claws_of_the_wolf", 1280933460L, 4, HASH, 753756428L),
                new WeaponPerks.Roll("allied_demand", 1532276803L, 3, HASH, 3275836355L),
                new WeaponPerks.Roll("farewell", 541188001L, 3, HASH, 284168234L),
                new WeaponPerks.Roll("dead_man_walking_xx7463", 3751622019L, 4, HASH, 1210839935L),
                new WeaponPerks.Roll("biting_winds", 1621657423L, 4, HASH, 2763203653L),
                new WeaponPerks.Roll("whispering_slab", 211938782L, 3, HASH, 1885424927L),
                new WeaponPerks.Roll("apostate", 2164448701L, 3, HASH, 1306932196L),
                new WeaponPerks.Roll("dream_breaker", 2931957300L, 3, HASH, 3785896921L),
                new WeaponPerks.Roll("coriolis_force", 3512349612L, 4, HASH, 753624012L),
                new WeaponPerks.Roll("line_in_the_sand", 946443267L, 3, HASH, 1503774254L),
                new WeaponPerks.Roll("stormchaser", 3652506829L, 3, HASH, 897699284L),
                new WeaponPerks.Roll("edge_transit", 218335759L, 3, HASH, 447678063L),
                new WeaponPerks.Roll("bellowing_giant", 2186258845L, 3, HASH, 2605036073L),
                new WeaponPerks.Roll("fixed_odds", 2194955522L, 4, HASH, 1686775256L));
            if (data == null || !"W192".equals(data.stage) || data.perk == null
                    || !ID.equals(data.perk.id) || data.perk.hash != HASH || data.perk.rangeBonus != 10
                    || data.perk.zoomScalar != 1.1f || data.perk.projectileSpeedScalar != 1.05
                    || data.perk.minAdsProgress != .5f || data.weapons == null
                    || !data.weapons.equals(expected) || data.ranges == null || data.ranges.size() != expected.size())
                throw new IllegalStateException("Invalid W192 Rangefinder definition/socket pool");
            var ids = new HashSet<String>();
            for (var range : data.ranges) {
                if (range == null || !ids.add(range.id)
                        || expected.stream().noneMatch(r -> r.id().equals(range.id))
                        || (range.baseRange == null && (range.vppStart != 0 || range.vppEnd != 0))
                        || (range.baseRange != null && (range.baseRange < 0 || range.baseRange > 100))
                        || !Double.isFinite(range.vppStart) || !Double.isFinite(range.vppEnd)
                        || range.vppStart < 0 || range.vppEnd < 0)
                    throw new IllegalStateException("Invalid Rangefinder raw range curve");
                range.evaluate(0);
                range.evaluate(100);
            }
            // WeaponPerks may be loading this profile: never query its registry here.
            return new Data(data.stage, data.perk, List.copyOf(data.weapons), List.copyOf(data.ranges));
        } catch (java.io.IOException e) { throw new IllegalStateException(e); }
    }

    public static List<WeaponPerks.Roll> rolls() { return DATA.weapons; }
    public static int rangeBonus() { return DATA.perk.rangeBonus; }
    public static float zoomScalar() { return DATA.perk.zoomScalar; }
    public static double projectileSpeedScalar() { return DATA.perk.projectileSpeedScalar; }
    public static float minAdsProgress() { return DATA.perk.minAdsProgress; }
    public static boolean supports(WeaponCatalog.Entry entry) {
        return entry != null && WeaponCatalog.find(entry.id()).filter(entry::equals).isPresent()
            && DATA.weapons.stream().anyMatch(r -> r.id().equals(entry.id())
                && r.hash() == WeaponCharacteristics.of(entry).bungieHash());
    }

    /** MASTER: sum all legally co-selected Range bonuses before this single clamp/evaluation.
     * This is a HIP profile. Apply existing ADS falloff scaling afterward, independently of zoom.
     * Zero-slope W43 sentinel curves remain range-independent; no new curve is invented.
     */
    public static WeaponBallistics.Profile ballistics(WeaponCatalog.Entry entry, int totalRangeBonus) {
        if (!supports(entry)) throw new IllegalArgumentException("Unsupported Rangefinder entry");
        return DATA.ranges.stream().filter(r -> r.id.equals(entry.id())).findFirst().orElseThrow()
            .evaluate(totalRangeBonus);
    }
}
