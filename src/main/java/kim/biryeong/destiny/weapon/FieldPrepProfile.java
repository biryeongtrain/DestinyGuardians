package kim.biryeong.destiny.weapon;

import java.util.List;

/** W320 batch A. DDC Weapon Perks row95 (PvE base): +20 Ammo Generation; while crouched +50 Reload, x0.8 reload, x0.8 ready/stow.
 * Exact pinned Bungie sockets only; JSON-only static loading (no registry initialization).
 */
public final class FieldPrepProfile {
    public static final String ID = "field_prep";
    public static final long HASH = 2869569095L;
    private static final BatchAPerkData.Data DATA = BatchAPerkData.load("/destiny/weapons/w320-field-prep.json", ID, HASH, 13,
        "ammoGenerationBonus", 20, "crouchReloadBonus", 50, "crouchReloadScalar", 0.8, "crouchHandlingScalar", 0.8);
    private FieldPrepProfile() {}
    public static List<WeaponPerks.Roll> rolls() { return DATA.rolls(); }
    public static int ammoGenerationBonus() { return DATA.i("ammoGenerationBonus"); }
    public static int crouchReloadBonus() { return DATA.i("crouchReloadBonus"); }
    public static double crouchReloadScalar() { return DATA.d("crouchReloadScalar"); }
    public static double crouchHandlingScalar() { return DATA.d("crouchHandlingScalar"); }
}
