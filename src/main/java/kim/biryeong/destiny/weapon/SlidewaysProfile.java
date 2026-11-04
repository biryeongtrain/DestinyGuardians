package kim.biryeong.destiny.weapon;

import java.util.List;

/** W320 batch A. DDC row203: slide refills 15% magazine, +15? Stability/+30? Handling 3s, 0.5s cooldown, removed on stow. '?' values are local policy.
 * Exact pinned Bungie sockets only; JSON-only static loading (no registry initialization).
 */
public final class SlidewaysProfile {
    public static final String ID = "slideways";
    public static final long HASH = 2039302152L;
    private static final BatchAPerkData.Data DATA = BatchAPerkData.load("/destiny/weapons/w320-slideways.json", ID, HASH, 9,
        "refillFraction", 0.15, "stabilityBonus", 15, "handlingBonus", 30, "durationTicks", 60, "cooldownTicks", 10, "removedOnStow", true);
    private SlidewaysProfile() {}
    public static List<WeaponPerks.Roll> rolls() { return DATA.rolls(); }
    public static double refillFraction() { return DATA.d("refillFraction"); }
    public static int stabilityBonus() { return DATA.i("stabilityBonus"); }
    public static int handlingBonus() { return DATA.i("handlingBonus"); }
    public static int durationTicks() { return DATA.i("durationTicks"); }
    public static int cooldownTicks() { return DATA.i("cooldownTicks"); }
    public static boolean removedOnStow() { return DATA.b("removedOnStow"); }
}
