package kim.biryeong.destiny.weapon;

import java.util.List;

/** W320 batch A. DDC row133: slide after 1.5s sprint: 15% damage and x0.8 charge time for ?s (local 2s).
 * Exact pinned Bungie sockets only; JSON-only static loading (no registry initialization).
 */
public final class KickstartProfile {
    public static final String ID = "kickstart";
    public static final long HASH = 1754714824L;
    private static final BatchAPerkData.Data DATA = BatchAPerkData.load("/destiny/weapons/w320-kickstart.json", ID, HASH, 1,
        "sprintTicks", 30, "damageMultiplier", 1.15, "chargeScalar", 0.8, "durationTicks", 40);
    private KickstartProfile() {}
    public static List<WeaponPerks.Roll> rolls() { return DATA.rolls(); }
    public static int sprintTicks() { return DATA.i("sprintTicks"); }
    public static double damageMultiplier() { return DATA.d("damageMultiplier"); }
    public static double chargeScalar() { return DATA.d("chargeScalar"); }
    public static int durationTicks() { return DATA.i("durationTicks"); }
}
