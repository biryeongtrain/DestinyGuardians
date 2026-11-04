package kim.biryeong.destiny.weapon;

/** Historical official 2022 family endpoints, not an exhaustive current-2026 sandbox table.
 * Local interpolation lives separately in WeaponFlinchState. No invented Glaive/Sword row,
 * Resilience stat, armor mod or universal application of the 2024 Crucible-only multiplier. */
public final class WeaponFlinchProfile {
    private WeaponFlinchProfile() {}
    public static float maxResistance(WeaponCatalog.Entry entry) {
        if(entry==null)return 0;
        return switch(entry.family()) {
            case "auto_rifle", "submachine_gun", "bow" -> .25f;
            case "pulse_rifle", "scout_rifle", "sidearm", "machine_gun" -> .20f;
            case "hand_cannon", "trace_rifle" -> .15f;
            case "fusion_rifle", "shotgun", "sniper_rifle", "grenade_launcher", "heavy_grenade_launcher",
                    "linear_fusion_rifle", "rocket_launcher" -> .10f;
            default -> 0;
        };
    }
}
