package kim.biryeong.destiny.weapon;

import com.google.gson.Gson;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.HashSet;
import java.util.List;
import java.util.OptionalDouble;

/** W193 base Trait, DDC row124. Initialization reads only its own JSON, never live registries. */
public final class ImpulseAmplifierProfile {
    public static final String ID = "impulse_amplifier";
    public static final long HASH = 951095735L;
    public enum VelocityStatus { DDC_CONFIRMED, OMITTED_UNKNOWN }
    private record Perk(String id, long hash, int reloadBonus, double durationMultiplier,
                        double rocketDurationMultiplier) {}
    private record Quadratic(double evpp, double vpp, double offset) {
        double seconds(int stat) { return evpp * stat * stat + vpp * stat + offset; }
    }
    private record Curve(String id, int baseReloadStat, Quadratic reload) {}
    private record Companion(String id, String perk, WeaponPerks.Roll roll) {}
    private record Velocity(String id, String family, VelocityStatus status, Double scalar) {}
    private record Data(String stage, Perk perk, List<WeaponPerks.Roll> weapons, List<Curve> curves,
                        List<Companion> coSelections, List<Velocity> projectileVelocity) {}
    private static final Data DATA = load();
    private ImpulseAmplifierProfile() {}

    private static void check(boolean valid, String detail) {
        if (!valid) throw new IllegalStateException("Invalid W193 Impulse Amplifier: " + detail);
    }
    private static Data load() {
        var stream = ImpulseAmplifierProfile.class.getResourceAsStream("/destiny/weapons/w193-impulse-amplifier.json");
        check(stream != null, "missing resource");
        try (var reader = new InputStreamReader(stream, StandardCharsets.UTF_8)) {
            var data = new Gson().fromJson(reader, Data.class);
            var expected = List.of(
                new WeaponPerks.Roll("canis_major", 2066434718L, 3, HASH, 4037911937L),
                new WeaponPerks.Roll("code_duello", 2496242052L, 3, HASH, 3719628667L),
                new WeaponPerks.Roll("nezarec_s_whisper", 254636484L, 3, HASH, 210449465L));
            check(data != null && "W193".equals(data.stage) && data.perk != null
                && ID.equals(data.perk.id) && data.perk.hash == HASH && data.perk.reloadBonus == 20
                && data.perk.durationMultiplier == .85 && data.perk.rocketDurationMultiplier == .8
                && expected.equals(data.weapons) && data.curves != null && data.curves.size() == 3
                && data.projectileVelocity != null && data.projectileVelocity.size() == 3,
                "base mechanics/exact three sockets");
            var ids = new HashSet<String>();
            for (var c : data.curves) {
                check(c != null && ids.add(c.id) && expected.stream().anyMatch(r -> r.id().equals(c.id))
                    && c.baseReloadStat >= 0 && c.baseReloadStat <= 100 && c.reload != null
                    && Double.isFinite(c.reload.evpp) && Double.isFinite(c.reload.vpp)
                    && Double.isFinite(c.reload.offset), "unique finite raw curve");
                for (int stat = 0; stat <= 100; stat++) quantize(c.reload.seconds(stat));
            }
            ids.clear();
            for (var v : data.projectileVelocity) {
                check(v != null && ids.add(v.id), "unique velocity");
                String family = switch (v.id) {
                    case "canis_major" -> "heavy_grenade_launcher";
                    case "code_duello" -> "rocket_launcher";
                    case "nezarec_s_whisper" -> "glaive";
                    default -> throw new IllegalStateException("Foreign Impulse Amplifier velocity");
                };
                check(family.equals(v.family) && (v.id.equals("code_duello")
                    ? v.status == VelocityStatus.DDC_CONFIRMED && Double.valueOf(1.1).equals(v.scalar)
                    : v.status == VelocityStatus.OMITTED_UNKNOWN && v.scalar == null), "sourced vs unknown velocity");
            }
            var companions = List.of(
                new Companion("code_duello", "frenzy", new WeaponPerks.Roll("code_duello", 2496242052L, 4, 4104185692L, 147528717L)),
                new Companion("nezarec_s_whisper", "frenzy", new WeaponPerks.Roll("nezarec_s_whisper", 254636484L, 4, 4104185692L, 699056095L)));
            check(companions.equals(data.coSelections), "exact distinct reload partners");
            return new Data(data.stage, data.perk, List.copyOf(data.weapons), List.copyOf(data.curves),
                List.copyOf(data.coSelections), List.copyOf(data.projectileVelocity));
        } catch (java.io.IOException e) { throw new IllegalStateException(e); }
    }

    public static List<WeaponPerks.Roll> rolls() { return DATA.weapons; }
    public static int reloadBonus() { return DATA.perk.reloadBonus; }
    public static boolean supports(WeaponCatalog.Entry entry) {
        return entry != null && WeaponCatalog.find(entry.id()).filter(entry::equals).isPresent()
            && DATA.weapons.stream().anyMatch(r -> r.id().equals(entry.id())
                && r.hash() == WeaponCharacteristics.of(entry).bungieHash());
    }
    public static boolean compatible(WeaponCatalog.Entry entry, String perk, WeaponPerks.Roll selected) {
        return supports(entry) && DATA.coSelections.stream().anyMatch(c -> c.id.equals(entry.id())
            && c.perk.equals(perk) && c.roll.equals(selected));
    }
    private static Curve curve(WeaponCatalog.Entry entry) {
        if (!supports(entry)) throw new IllegalArgumentException("Unsupported/noncanonical Impulse Amplifier entry");
        return DATA.curves.stream().filter(c -> c.id.equals(entry.id())).findFirst().orElseThrow();
    }
    public static double durationMultiplier(WeaponCatalog.Entry entry) {
        curve(entry);
        return entry.family().equals("rocket_launcher") ? DATA.perk.rocketDurationMultiplier : DATA.perk.durationMultiplier;
    }
    /** TOTAL includes this trait and every actually active, legal other-socket bonus/scalar.
     * Raw W46 seconds, one total-stat clamp, no baseline tick ratios or intermediate rounding.
     */
    public static double reloadSeconds(WeaponCatalog.Entry entry, int totalReloadBonus, double totalScalar) {
        var c = curve(entry);
        if (!Double.isFinite(totalScalar) || totalScalar <= 0 || totalScalar > 1)
            throw new IllegalArgumentException("Reload scalar must be finite in (0,1]");
        int stat = (int)Math.clamp((long)c.baseReloadStat + totalReloadBonus, 0L, 100L);
        return c.reload.seconds(stat) * totalScalar;
    }
    private static int quantize(double seconds) {
        check(Double.isFinite(seconds) && seconds > 0 && seconds <= 60, "safe raw seconds");
        return Math.max(1, (int)Math.ceil(seconds * 20));
    }
    public static WeaponReloadPolicy.Plan reloadPlan(WeaponCatalog.Entry entry, int totalReloadBonus,
                                                     double totalScalar, WeaponReloadPolicy.Plan base) {
        if (base == null || base.incremental()) throw new IllegalArgumentException("Whole-magazine reload required");
        int ticks = quantize(reloadSeconds(entry, totalReloadBonus, totalScalar));
        return new WeaponReloadPolicy.Plan(ticks, ticks, 0);
    }
    public static VelocityStatus projectileVelocityStatus(WeaponCatalog.Entry entry) {
        curve(entry);
        return DATA.projectileVelocity.stream().filter(v -> v.id.equals(entry.id())).findFirst().orElseThrow().status;
    }
    /** Empty means omitted/unknown, never an assertion that Destiny grants no speed bonus. */
    public static OptionalDouble projectileSpeedScalar(WeaponCatalog.Entry entry) {
        curve(entry);
        var v = DATA.projectileVelocity.stream().filter(p -> p.id.equals(entry.id())).findFirst().orElseThrow();
        return v.scalar == null ? OptionalDouble.empty() : OptionalDouble.of(v.scalar);
    }
}
