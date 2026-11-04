package kim.biryeong.destiny.weapon;

import java.util.List;

/** W320 batch A. DDC row25: damage with every equipped weapon, each within 7s of the last: +30% damage for 10s, no refresh while active, persists through stow.
 * Exact pinned Bungie sockets only; JSON-only static loading (no registry initialization).
 */
public final class BaitAndSwitchProfile {
    public static final String ID = "bait_and_switch";
    public static final long HASH = 3078487919L;
    private static final BatchAPerkData.Data DATA = BatchAPerkData.load("/destiny/weapons/w320-bait-and-switch.json", ID, HASH, 1,
        "chainTicks", 140, "damageMultiplier", 1.3, "durationTicks", 200, "persistsThroughStow", true);
    private BaitAndSwitchProfile() {}
    public static List<WeaponPerks.Roll> rolls() { return DATA.rolls(); }
    public static int chainTicks() { return DATA.i("chainTicks"); }
    public static double damageMultiplier() { return DATA.d("damageMultiplier"); }
    public static int durationTicks() { return DATA.i("durationTicks"); }
    public static boolean persistsThroughStow() { return DATA.b("persistsThroughStow"); }
}
