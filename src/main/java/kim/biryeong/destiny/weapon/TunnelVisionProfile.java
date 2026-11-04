package kim.biryeong.destiny.weapon;

import java.util.List;

/** W320 batch A. DDC row238: reload finished within 3.6s of a weapon kill: +20 Aim Assist, -?% growth, +? ADS for 5s. '?' values are local placeholders.
 * Exact pinned Bungie sockets only; JSON-only static loading (no registry initialization).
 */
public final class TunnelVisionProfile {
    public static final String ID = "tunnel_vision";
    public static final long HASH = 2946784966L;
    private static final BatchAPerkData.Data DATA = BatchAPerkData.load("/destiny/weapons/w320-tunnel-vision.json", ID, HASH, 3,
        "killWindowTicks", 72, "durationTicks", 100, "aimAssistBonus", 20, "growthScalar", 0.85, "adsScalar", 0.8);
    private TunnelVisionProfile() {}
    public static List<WeaponPerks.Roll> rolls() { return DATA.rolls(); }
    public static int killWindowTicks() { return DATA.i("killWindowTicks"); }
    public static int durationTicks() { return DATA.i("durationTicks"); }
    public static int aimAssistBonus() { return DATA.i("aimAssistBonus"); }
    public static double growthScalar() { return DATA.d("growthScalar"); }
    public static double adsScalar() { return DATA.d("adsScalar"); }
}
