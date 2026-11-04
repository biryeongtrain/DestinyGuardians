package kim.biryeong.destiny.weapon;

/**
 * Scoped full-auto FIRING accessibility policy. Bow trigger cycles and
 * release-to-detonate breach grenades remain deferred; swords are excluded.
 * Glaive ranged fire may repeat. This is not full-auto melee and changes no
 * intrinsic automatic flag, cadence, ammunition, or melee behavior.
 */
public final class WeaponAutoFirePolicy {
    private WeaponAutoFirePolicy() {}

    public static boolean supportsAutomatic(WeaponCatalog.Entry entry, boolean fullAuto) {
        if (!fullAuto) return WeaponFirePolicy.supportsAutomatic(entry);
        if (entry == null || !WeaponCatalog.find(entry.id()).filter(entry::equals).isPresent()) return false;
        return !"bow".equals(entry.family()) && !"sword".equals(entry.family())
                && !BreachGrenade.supports(entry);
    }
}
