package kim.biryeong.destiny.weapon;

/** Minecraft health/blocks adaptation. Identity, cartridge counts and timing come from pinned data;
 * these local damage and projectile budgets are not Destiny damage units. Intrinsics live elsewhere. */
final class ExoticProfilesW350 {
    private ExoticProfilesW350() {}
    static WeaponProfile adjust(WeaponCatalog.Entry entry, WeaponProfile p) {
        if (!WeaponExotics.expanded(entry)) return p;
        var mode = p.mode(); float damage = p.damage(); int pellets = 1;
        double range = p.range(), spread = 0, speed = p.speed(), gravity = p.gravity(), blast = p.blastRadius();
        switch (entry.id()) {
            case "crimson" -> damage = 3;
            case "jotunn" -> { mode = WeaponProfile.Mode.PROJECTILE; damage = 15; speed = 1.1; gravity = 0; blast = 2.5; }
            case "whisper_of_the_worm" -> damage = 24;
            case "tractor_cannon" -> { damage = 16; range = 9; }
            default -> { }
        }
        return new WeaponProfile(mode, damage, p.intervalTicks(), p.magazine(), p.reserve(), p.reloadTicks(),
                range, p.chargeTicks(), p.burst(), pellets, spread, speed, gravity, blast, p.automatic(),
                p.infiniteReserve(), p.cadenceTicks(), p.burstSpacingTicks(), p.sharedBurstAmmo(),
                false, p.reloadTicks(), 0);
    }
}
