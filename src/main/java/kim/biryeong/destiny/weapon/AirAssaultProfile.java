package kim.biryeong.destiny.weapon;

import java.util.List;

/** W320 batch A. DDC row12: passive +10 AE; weapon kill +30 AE/stack for 5s, max 2, airborne kills grant 2; kills refresh; removed on stow.
 * Exact pinned Bungie sockets only; JSON-only static loading (no registry initialization).
 */
public final class AirAssaultProfile {
    public static final String ID = "air_assault";
    public static final long HASH = 3722653512L;
    private static final BatchAPerkData.Data DATA = BatchAPerkData.load("/destiny/weapons/w320-air-assault.json", ID, HASH, 3,
        "passiveAirborne", 10, "airbornePerStack", 30, "maxStacks", 2, "airborneKillStacks", 2, "durationTicks", 100, "removedOnStow", true);
    private AirAssaultProfile() {}
    public static List<WeaponPerks.Roll> rolls() { return DATA.rolls(); }
    public static int passiveAirborne() { return DATA.i("passiveAirborne"); }
    public static int airbornePerStack() { return DATA.i("airbornePerStack"); }
    public static int maxStacks() { return DATA.i("maxStacks"); }
    public static int airborneKillStacks() { return DATA.i("airborneKillStacks"); }
    public static int durationTicks() { return DATA.i("durationTicks"); }
    public static boolean removedOnStow() { return DATA.b("removedOnStow"); }
}
