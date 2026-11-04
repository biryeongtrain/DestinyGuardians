package kim.biryeong.destiny.weapon;

import java.util.Set;

/**
 * Pure W48 base/intrinsic held-trigger policy, not the global accessibility
 * full-auto setting or a roll/perk simulator. No ammo, cadence or input mutation.
 * Existing AR/SMG/trace/MG automatic families are retained. The only additional
 * selected weapons have explicit "full auto" in their actual official intrinsic
 * socket plug description; see art/weapons/w48/fire-policy-evidence.json.
 * A Rapid-Fire label, burst, or non-intrinsic Full Auto Trigger System trait is
 * insufficient. False means this scoped policy requires a fresh trigger cycle,
 * not that the original game can never make the weapon automatic with a perk.
 */
public final class WeaponFirePolicy {
    private static final Set<String> BASE_AUTOMATIC_FAMILIES = Set.of(
            "auto_rifle", "submachine_gun", "trace_rifle", "machine_gun");
    private static final Set<String> INTRINSIC_AUTOMATIC_IDS = Set.of(
            "aishas_embrace",             // Intrinsic 3920852688: Fires full auto...
            "dead_man_walking_xx7463",   // Intrinsic 806997698: Full auto...
            "ikelos_sg_v1_0_1");         // Intrinsic 996573084: Fires full auto...

    private WeaponFirePolicy() {}

    /** Known, canonical selected entries only; null/unknown/mismatched entries return false. */
    public static boolean supportsAutomatic(WeaponCatalog.Entry entry) {
        if (entry == null || !WeaponCatalog.find(entry.id()).filter(entry::equals).isPresent()) return false;
        return BASE_AUTOMATIC_FAMILIES.contains(entry.family()) || INTRINSIC_AUTOMATIC_IDS.contains(entry.id());
    }
}
