package kim.biryeong.destiny.weapon;

/**
 * Shapes: pinned intrinsic descriptions. Vortex cost4: Bungie9.7.0 (2026-06-09).
 * Other charged costs are explicitly authored choices, NOT certified current Destiny values.
 * HP, cadence, weak multiplier, movement and physics are authored local PvE tuning.
 */
public record SwordProfile(Shape shape, int heavyCost, int heavyTicks, float heavyMultiplier) {
    public enum Shape { UPPERCUT, DASH, SLAM, VORTEX, CASTER }
    public static SwordProfile of(WeaponCatalog.Entry entry) {
        if (!entry.family().equals("sword")) throw new IllegalArgumentException("Not a sword");
        return switch (entry.frame()) {
            case "lightweight" -> new SwordProfile(Shape.DASH, 3, 16, 1.8f);
            case "aggressive" -> new SwordProfile(Shape.SLAM, 4, 30, 3.5f);
            case "vortex" -> new SwordProfile(Shape.VORTEX, 4, 26, 2.9f);
            case "caster" -> new SwordProfile(Shape.CASTER, 4, 24, 2.4f);
            case "adaptive" -> new SwordProfile(Shape.UPPERCUT, 4, 22, 2.4f);
            default -> throw new IllegalArgumentException("Unknown sword frame: "+entry.frame());
        };
    }
    /** 2024 unpowered heavy costs one; other charged costs are documented above. */
    public int heavyCost(int energy) { return energy>0?heavyCost:1; }
    /** 2023 full power at any nonzero energy; 0.35 weak damage is authored, not measured. */
    public float power(double energy) { return energy>0?1:.35f; }
    public WeaponProfile attack(WeaponProfile base, float damage, boolean heavy) {
        int ticks = heavy ? heavyTicks : base.intervalTicks();
        return new WeaponProfile(WeaponProfile.Mode.MELEE,damage,ticks,base.magazine(),0,
                base.reloadTicks(),heavy?4:base.range(),0,1,1,0,0,0,0,false);
    }
    public WeaponProfile caster(WeaponProfile base, float damage) {
        return new WeaponProfile(WeaponProfile.Mode.PROJECTILE,damage,heavyTicks,base.magazine(),0,
                base.reloadTicks(),24,0,1,1,0,1.4,0,1.75,false);
    }
}
