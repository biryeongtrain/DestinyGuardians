package kim.biryeong.destiny.weapon;

import com.google.gson.Gson;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.List;

/** Base Adagio, DDC Weapon Perks row7. Initialization only reads the pinned resource. */
public final class AdagioProfile {
    public static final String ID = "adagio";
    public static final long HASH = 3673922083L;
    private static final List<WeaponPerks.Roll> EXPECTED = List.of(
        new WeaponPerks.Roll("aishas_embrace", 2638190703L, 4, HASH, 4211351701L),
        new WeaponPerks.Roll("canis_major", 2066434718L, 4, HASH, 2791121719L));
    private record Perk(String id, long hash, double damageMultiplier, int rangeBonus,
                        double cadenceMultiplier, int durationTicks, boolean refresh,
                        boolean persistsStow) {}
    /** Null Range stat means absent in the official definition (Canis, whose slopes are zero).
     * Sum legal bonuses before one 0..100 stat cap, evaluate hip endpoints, then apply ADS.
     */
    public record RangeCurve(String id, Integer baseRangeStat, double offsetStart, double vppStart,
                             double offsetEnd, double vppEnd, double floor, double precision) {}
    private record Data(String stage, Perk perk, List<WeaponPerks.Roll> weapons,
                        List<RangeCurve> rangeCurves) {}
    private static final Data DATA = load();
    private AdagioProfile() {}

    private static Data load() {
        var stream = AdagioProfile.class.getResourceAsStream("/destiny/weapons/w193-adagio.json");
        if (stream == null) throw new IllegalStateException("Missing W193 Adagio");
        try (var reader = new InputStreamReader(stream, StandardCharsets.UTF_8)) {
            var d = new Gson().fromJson(reader, Data.class);
            if (d == null || !"W193".equals(d.stage)
                || !new Perk(ID, HASH, 1.3, 10, 1.2, AdagioCycle.DURATION_TICKS, true, false).equals(d.perk)
                || !EXPECTED.equals(d.weapons)
                || !List.of(new RangeCurve("aishas_embrace", 34, 30.25, .1568, 60.75, 0, .5,
                        1.696078431372549),
                    new RangeCurve("canis_major", null, 999, 0, 999.9, 0, .999, 1)).equals(d.rangeCurves))
                throw new IllegalStateException("Invalid W193 Adagio definition/socket/curve");
            return new Data(d.stage, d.perk, List.copyOf(d.weapons), List.copyOf(d.rangeCurves));
        } catch (java.io.IOException e) { throw new IllegalStateException(e); }
    }
    public static List<WeaponPerks.Roll> rolls() { return DATA.weapons; }
    public static boolean supports(WeaponCatalog.Entry entry) {
        return entry != null && WeaponCatalog.find(entry.id()).filter(entry::equals).isPresent()
            && EXPECTED.stream().anyMatch(r -> r.id().equals(entry.id())
                && r.hash() == WeaponCharacteristics.of(entry).bungieHash())
            && !WeaponCharacteristics.of(entry).exotic();
    }
    public static int durationTicks() { return DATA.perk.durationTicks; }
    public static int rangeBonus() { return DATA.perk.rangeBonus; }
    public static RangeCurve rangeCurve(WeaponCatalog.Entry entry) {
        if (!supports(entry)) throw new IllegalArgumentException("Unsupported Adagio weapon");
        return DATA.rangeCurves.stream().filter(c -> c.id.equals(entry.id())).findFirst().orElseThrow();
    }
    /** Once per accepted firing decision, from a profile that has not yet received Adagio.
     * RAW damage is unchanged: only the paid token supplies damage to direct AND splash.
     * Return a snapshot; never rewrite a WeaponCycle deadline after accepting its shot.
     */
    public static WeaponProfile firingProfile(WeaponCatalog.Entry entry, WeaponProfile base) {
        if (!supports(entry)) return base;
        double cadence = base.cadenceTicks() * DATA.perk.cadenceMultiplier;
        return new WeaponProfile(base.mode(), base.damage(), (int)Math.ceil(cadence), base.magazine(),
            base.reserve(), base.reloadTicks(), base.range(), base.chargeTicks(), base.burst(),
            base.pellets(), base.spread(), base.speed(), base.gravity(), base.blastRadius(),
            base.automatic(), base.infiniteReserve(), cadence, base.burstSpacingTicks(),
            base.sharedBurstAmmo(), base.shellReload(), base.firstReloadTicks(), base.roundsPerInsert());
    }
}
