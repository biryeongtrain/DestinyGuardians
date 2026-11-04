package kim.biryeong.destiny.weapon;

import java.util.List;

/** W320 batch A. DDC row93: from 40 shield HP, linear 0..100% between 80 and 0 shield HP: +30 Handling, -40% cone, -17% growth; ends at 80.
 * Exact pinned Bungie sockets only; JSON-only static loading (no registry initialization).
 */
public final class EyeOfTheStormProfile {
    public static final String ID = "eye_of_the_storm";
    public static final long HASH = 699525795L;
    private static final BatchAPerkData.Data DATA = BatchAPerkData.load("/destiny/weapons/w320-eye-of-the-storm.json", ID, HASH, 7,
        "triggerShield", 40, "fullShield", 80, "handlingBonus", 30, "coneScalar", 0.6, "growthScalar", 0.83);
    private EyeOfTheStormProfile() {}
    public static List<WeaponPerks.Roll> rolls() { return DATA.rolls(); }
    public static int triggerShield() { return DATA.i("triggerShield"); }
    public static int fullShield() { return DATA.i("fullShield"); }
    public static int handlingBonus() { return DATA.i("handlingBonus"); }
    public static double coneScalar() { return DATA.d("coneScalar"); }
    public static double growthScalar() { return DATA.d("growthScalar"); }
}
