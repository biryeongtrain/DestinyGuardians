package kim.biryeong.destiny.weapon;

import eu.pb4.polymer.resourcepack.api.PackResource;

/** Read-only final model projection for output-pack reference analysis. */
public final class WeaponSurfaceProjection {
    private WeaponSurfaceProjection() {}

    /** Final converter bytes for reference analysis; the builder and source files remain untouched.
     * Pre-finish snapshots otherwise still contain W30 texture references, even though the
     * output converter replaces them with W123 textures after pruning. */
    public static void projectOutput(java.util.Map<String, PackResource> snapshot) {
        if (!Boolean.parseBoolean(System.getProperty("destiny.weapon.surface.w123", "true"))) return;
        projectOutput(snapshot, Boolean.getBoolean("destiny.weapon.surface.w115"));
    }

    static void projectOutput(java.util.Map<String, PackResource> snapshot, boolean legacyW115) {
        var rules = WeaponSurfaceW123Assets.rules();
        for (String path : WeaponSurfaceW123Assets.TARGETS) {
            if (legacyW115 && WeaponSurfaceAssets.TARGETS.contains(path)) continue;
            snapshot.put(path, WeaponSurfaceW123Assets.convert(path, snapshot.get(path), rules));
        }
    }

}
