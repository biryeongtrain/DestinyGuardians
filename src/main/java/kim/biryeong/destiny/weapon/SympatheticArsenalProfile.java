package kim.biryeong.destiny.weapon;

import com.google.gson.Gson;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.*;

/** Exact five base socket4 rolls; raw colegal stat/scalar composition and historical W46 curves. */
public final class SympatheticArsenalProfile {
    public static final String ID = "sympathetic_arsenal";
    public static final long HASH = 3350417888L;
    public record Perk(String id, long hash, int reloadBonus, int windowTicks) {}
    private record Quadratic(double evpp, double vpp, double offset) {
        double seconds(int stat) { return evpp * stat * stat + vpp * stat + offset; }
    }
    private record Curve(String id, int baseReloadStat, int reloadStatCap, Quadratic reload) {}
    private record Companion(String id, String perk, WeaponPerks.Roll roll) {}
    private record Tiers(String id, List<Integer> reloadBonus, List<Double> durationMultiplier) {
        private Tiers { reloadBonus = List.copyOf(reloadBonus); durationMultiplier = List.copyOf(durationMultiplier); }
    }
    private record Data(String stage, Perk perk, List<WeaponPerks.Roll> weapons, List<Curve> curves,
                        List<Companion> coSelections, List<Tiers> companionTiers) {}
    private static final List<String> COMPANIONS = List.of("feeding_frenzy", "rapid_hit", "threat_detector", "surplus");
    private static final Data DATA = load();
    private SympatheticArsenalProfile() {}
    private static void check(boolean ok, String detail) {
        if (!ok) throw new IllegalStateException("Invalid W194 Sympathetic Arsenal: " + detail);
    }
    private static Data load() {
        var stream = SympatheticArsenalProfile.class.getResourceAsStream("/destiny/weapons/w194-sympathetic-arsenal.json");
        check(stream != null, "missing resource");
        try (var reader = new InputStreamReader(stream, StandardCharsets.UTF_8)) {
            var d = new Gson().fromJson(reader, Data.class);
            var expected = List.of(
                new WeaponPerks.Roll("cold_denial", 1216130969L, 4, HASH, 720537379L),
                new WeaponPerks.Roll("brass_attacks", 2121785039L, 4, HASH, 3403850295L),
                new WeaponPerks.Roll("biting_winds", 1621657423L, 4, HASH, 2763203653L),
                new WeaponPerks.Roll("whispering_slab", 211938782L, 4, HASH, 967526625L),
                new WeaponPerks.Roll("hollow_words", 607191995L, 4, HASH, 1485010760L));
            check(d != null && "W194".equals(d.stage) && d.perk != null
                && ID.equals(d.perk.id) && d.perk.hash == HASH && d.perk.reloadBonus == 20 && d.perk.windowTicks == 72
                && expected.equals(d.weapons) && d.curves != null && d.curves.size() == 5
                && d.coSelections != null && d.coSelections.size() == 9
                && d.companionTiers != null && d.companionTiers.size() == 4, "base mechanics/pool");
            var ids = new HashSet<String>();
            for (var c : d.curves) {
                check(c != null && ids.add(c.id) && expected.stream().anyMatch(r -> r.id().equals(c.id))
                    && c.baseReloadStat >= 0 && c.baseReloadStat <= 100
                    && c.reloadStatCap == (Set.of("biting_winds", "whispering_slab").contains(c.id) ? 85 : 100)
                    && c.reload != null && Double.isFinite(c.reload.evpp) && Double.isFinite(c.reload.vpp)
                    && Double.isFinite(c.reload.offset), "unique safe curve");
                for (int stat = 0; stat <= c.reloadStatCap; stat++) quantize(c.reload.seconds(stat));
            }
            ids.clear();
            for (var t : d.companionTiers) {
                int size = switch (t.id) { case "feeding_frenzy", "rapid_hit" -> 6; case "threat_detector" -> 3; case "surplus" -> 4; default -> 0; };
                check(ids.add(t.id) && size > 0 && t.reloadBonus.size() == size && t.durationMultiplier.size() == size,
                    "unique complete tier table");
                check(t.reloadBonus.getFirst() == 0 && t.durationMultiplier.getFirst() == 1, "neutral tier");
                for (int i = 0; i < size; i++) check(t.reloadBonus.get(i) >= 0 && t.reloadBonus.get(i) <= 100
                    && Double.isFinite(t.durationMultiplier.get(i)) && t.durationMultiplier.get(i) > 0
                    && t.durationMultiplier.get(i) <= 1, "raw tier bounds");
            }
            var tuples = new HashSet<String>();
            for (var c : d.coSelections) {
                check(c != null && COMPANIONS.contains(c.perk) && c.roll != null
                    && c.id.equals(c.roll.id()) && c.roll.socket() == 3
                    && expected.stream().anyMatch(r -> r.id().equals(c.id) && r.hash() == c.roll.hash())
                    && tuples.add(c.id + ":" + c.perk), "distinct legal companion");
            }
            check(tuples.equals(Set.of("cold_denial:feeding_frenzy", "cold_denial:threat_detector",
                "brass_attacks:feeding_frenzy", "brass_attacks:rapid_hit", "brass_attacks:threat_detector",
                "brass_attacks:surplus", "biting_winds:rapid_hit", "biting_winds:surplus", "hollow_words:feeding_frenzy")),
                "exact companion matrix");
            return new Data(d.stage, d.perk, List.copyOf(d.weapons), List.copyOf(d.curves),
                List.copyOf(d.coSelections), List.copyOf(d.companionTiers));
        } catch (java.io.IOException e) { throw new IllegalStateException(e); }
    }
    public static Perk perk() { return DATA.perk; }
    public static int reloadBonus() { return DATA.perk.reloadBonus; }
    public static int windowTicks() { return DATA.perk.windowTicks; }
    public static List<WeaponPerks.Roll> rolls() { return DATA.weapons; }
    public static List<String> reloadCompanions() { return COMPANIONS; }
    public static boolean supports(WeaponCatalog.Entry entry) {
        return entry != null && WeaponCatalog.find(entry.id()).filter(entry::equals).isPresent()
            && DATA.weapons.stream().anyMatch(r -> r.id().equals(entry.id())
                && r.hash() == WeaponCharacteristics.of(entry).bungieHash());
    }
    public static boolean compatible(WeaponCatalog.Entry entry, String id, WeaponPerks.Roll roll) {
        return supports(entry) && DATA.coSelections.stream().anyMatch(c -> c.id.equals(entry.id())
            && c.perk.equals(id) && c.roll.equals(roll));
    }
    private static Tiers tiers(String id, int tier) {
        var t = DATA.companionTiers.stream().filter(v -> v.id.equals(id)).findFirst().orElseThrow();
        if (tier < 0 || tier >= t.reloadBonus.size()) throw new IllegalArgumentException("Invalid companion tier");
        return t;
    }
    public static int companionBonus(String id, int tier) { return tiers(id, tier).reloadBonus.get(tier); }
    public static double companionScalar(String id, int tier) { return tiers(id, tier).durationMultiplier.get(tier); }
    /** TOTAL bonus includes SA passive and the actually selected active socket3 companion. */
    public static WeaponReloadPolicy.Plan reloadPlan(WeaponCatalog.Entry entry, int totalBonus,
                                                     double totalScalar, WeaponReloadPolicy.Plan base) {
        if (!supports(entry) || base == null || base.incremental() || !Double.isFinite(totalScalar)
            || totalScalar <= 0 || totalScalar > 1) throw new IllegalArgumentException("Invalid SA raw reload plan");
        var c = DATA.curves.stream().filter(v -> v.id.equals(entry.id())).findFirst().orElseThrow();
        int stat = (int)Math.clamp((long)c.baseReloadStat + totalBonus, 0L, (long)c.reloadStatCap);
        int ticks = quantize(c.reload.seconds(stat) * totalScalar);
        return new WeaponReloadPolicy.Plan(ticks, ticks, 0);
    }
    private static int quantize(double seconds) {
        check(Double.isFinite(seconds) && seconds > 0 && seconds <= 60, "safe seconds");
        return Math.max(1, (int)Math.ceil(seconds * 20));
    }
}
