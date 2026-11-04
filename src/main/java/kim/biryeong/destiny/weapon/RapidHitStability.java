package kim.biryeong.destiny.weapon;

/** W44's local Minecraft stability-to-kick/bloom curve, not an exact Destiny recoil simulation. */
public final class RapidHitStability {
    private RapidHitStability() {}
    public static float effective(float base, int bonus) {
        if (!Float.isFinite(base) || base < 0 || base > 100 || bonus < 0 || bonus > 100)
            throw new IllegalArgumentException("Unsafe stability");
        return Math.min(100, base + bonus);
    }
    /** Preserve the exact existing rounded/clamped idle values at zero bonus. */
    public static float kick(WeaponAimProfile base, int bonus) {
        float stat = effective(base.stability(), bonus);
        return bonus == 0 ? base.kick() : Math.clamp(base.kick()
                * (1 - .006f * stat) / (1 - .006f * base.stability()), .1f, 2);
    }
    public static float bloom(WeaponAimProfile base, int bonus) {
        return bonus == 0 ? base.bloomPerShot() : .02f + .18f * (1 - effective(base.stability(), bonus) / 100);
    }

    /** Signed aggregate for stat penalties such as Iron Reach. Keep the older positive-only API. */
    public static float effectiveSigned(float base, int delta) {
        if (!Float.isFinite(base) || base < 0 || base > 100)
            throw new IllegalArgumentException("Unsafe base stability");
        return (float)Math.clamp((double)base + delta,0,100);
    }
    public static float kickSigned(WeaponAimProfile base, int delta) {
        float stat = effectiveSigned(base.stability(),delta);
        return delta == 0 ? base.kick() : Math.clamp(base.kick()
            * (1-.006f*stat)/(1-.006f*base.stability()),.1f,2);
    }
    public static float bloomSigned(WeaponAimProfile base, int delta) {
        return delta == 0 ? base.bloomPerShot() : .02f+.18f*(1-effectiveSigned(base.stability(),delta)/100);
    }
}
