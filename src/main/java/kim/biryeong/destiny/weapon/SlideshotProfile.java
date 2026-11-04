package kim.biryeong.destiny.weapon;

import java.util.List;

/** W320 batch A. DDC row202: slide refills 15% magazine, +20 Range/+20? Stability 2.5s for the first shot, 0.3s cooldown, removed on stow.
 * Exact pinned Bungie sockets only; JSON-only static loading (no registry initialization).
 */
public final class SlideshotProfile {
    public static final String ID = "slideshot";
    public static final long HASH = 3161816588L;
    private static final BatchAPerkData.Data DATA = BatchAPerkData.load("/destiny/weapons/w320-slideshot.json", ID, HASH, 7,
        "refillFraction", 0.15, "rangeBonus", 20, "stabilityBonus", 20, "durationTicks", 50, "cooldownTicks", 6, "firstShotOnly", true, "removedOnStow", true);
    private SlideshotProfile() {}
    public static List<WeaponPerks.Roll> rolls() { return DATA.rolls(); }
    public static double refillFraction() { return DATA.d("refillFraction"); }
    public static int rangeBonus() { return DATA.i("rangeBonus"); }
    public static int stabilityBonus() { return DATA.i("stabilityBonus"); }
    public static int durationTicks() { return DATA.i("durationTicks"); }
    public static int cooldownTicks() { return DATA.i("cooldownTicks"); }
    public static boolean firstShotOnly() { return DATA.b("firstShotOnly"); }
    public static boolean removedOnStow() { return DATA.b("removedOnStow"); }
}
