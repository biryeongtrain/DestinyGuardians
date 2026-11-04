package kim.biryeong.destiny.weapon;

import java.util.List;

/** W320 batch A. DDC row102: +20 Range while shields are active; off at critical health; back 1s after shields are full.
 * Exact pinned Bungie sockets only; JSON-only static loading (no registry initialization).
 */
public final class FragileFocusProfile {
    public static final String ID = "fragile_focus";
    public static final long HASH = 2451262963L;
    private static final BatchAPerkData.Data DATA = BatchAPerkData.load("/destiny/weapons/w320-fragile-focus.json", ID, HASH, 1,
        "rangeBonus", 20, "reactivateTicks", 20);
    private FragileFocusProfile() {}
    public static List<WeaponPerks.Roll> rolls() { return DATA.rolls(); }
    public static int rangeBonus() { return DATA.i("rangeBonus"); }
    public static int reactivateTicks() { return DATA.i("reactivateTicks"); }
}
