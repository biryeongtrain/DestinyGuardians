package kim.biryeong.destiny.weapon;

/** Reference-informed incremental overrides, separate from W46's historical whole-magazine curves.
 * Long Arm timing is an authored baseline, NOT an official/unmodified-game measurement.
 * See art/weapons/w48/README-reload.md for the observed two-cartridge HUD and uncertainty.
 */
public final class WeaponReloadPolicy {
    private WeaponReloadPolicy() {}

    public record Plan(int firstTicks, int intervalTicks, int roundsPerInsert) {
        public Plan {
            if (firstTicks < 1 || intervalTicks < 1 || roundsPerInsert < 0 || roundsPerInsert > 3)
                throw new IllegalArgumentException("Unsafe reload plan");
        }
        public boolean incremental() { return roundsPerInsert > 0; }
    }

    /** Only the selected canonical Long Arm (8293111), not every aggressive scout or a reissue. */
    public static Plan forEntry(WeaponCatalog.Entry entry, int fallbackTicks, boolean shellReload) {
        if (entry != null && entry.id().equals("long_arm")
                && WeaponCatalog.find(entry.id()).filter(entry::equals).isPresent())
            return new Plan(20, 13, 2);
        return new Plan(fallbackTicks, fallbackTicks, shellReload ? 1 : 0);
    }
}
