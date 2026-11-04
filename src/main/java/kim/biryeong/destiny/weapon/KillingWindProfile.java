package kim.biryeong.destiny.weapon;

import java.util.List;

/** W320 batch A. DDC row136: weapon kill +20 Range, +50 Mobility, +40 Handling, 5% falloff for 5s; +5s per kill up to 8s; removed on stow.
 * Exact pinned Bungie sockets only; JSON-only static loading (no registry initialization).
 */
public final class KillingWindProfile {
    public static final String ID = "killing_wind";
    public static final long HASH = 2450788523L;
    private static final BatchAPerkData.Data DATA = BatchAPerkData.load("/destiny/weapons/w320-killing-wind.json", ID, HASH, 11,
        "rangeBonus", 20, "mobilityBonus", 50, "handlingBonus", 40, "falloffScalar", 1.05, "durationTicks", 100, "extendTicks", 100, "maxTicks", 160, "removedOnStow", true);
    private KillingWindProfile() {}
    public static List<WeaponPerks.Roll> rolls() { return DATA.rolls(); }
    public static int rangeBonus() { return DATA.i("rangeBonus"); }
    public static int mobilityBonus() { return DATA.i("mobilityBonus"); }
    public static int handlingBonus() { return DATA.i("handlingBonus"); }
    public static double falloffScalar() { return DATA.d("falloffScalar"); }
    public static int durationTicks() { return DATA.i("durationTicks"); }
    public static int extendTicks() { return DATA.i("extendTicks"); }
    public static int maxTicks() { return DATA.i("maxTicks"); }
    public static boolean removedOnStow() { return DATA.b("removedOnStow"); }
}
