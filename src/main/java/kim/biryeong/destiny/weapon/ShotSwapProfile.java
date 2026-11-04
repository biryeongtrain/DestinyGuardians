package kim.biryeong.destiny.weapon;

import java.util.List;

/** W320 batch A. DDC row198: weapon kill +2 stacks (max 6); ready/stow +100 handling and x0.7 duration; stow consumes one stack.
 * Exact pinned Bungie sockets only; JSON-only static loading (no registry initialization).
 */
public final class ShotSwapProfile {
    public static final String ID = "shot_swap";
    public static final long HASH = 2586829431L;
    private static final BatchAPerkData.Data DATA = BatchAPerkData.load("/destiny/weapons/w320-shot-swap.json", ID, HASH, 1,
        "stacksPerKill", 2, "maxStacks", 6, "handlingBonus", 100, "durationScalar", 0.7);
    private ShotSwapProfile() {}
    public static List<WeaponPerks.Roll> rolls() { return DATA.rolls(); }
    public static int stacksPerKill() { return DATA.i("stacksPerKill"); }
    public static int maxStacks() { return DATA.i("maxStacks"); }
    public static int handlingBonus() { return DATA.i("handlingBonus"); }
    public static double durationScalar() { return DATA.d("durationScalar"); }
}
