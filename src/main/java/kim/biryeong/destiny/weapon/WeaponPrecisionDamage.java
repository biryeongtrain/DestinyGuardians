package kim.biryeong.destiny.weapon;

/** Pure transaction component policy shared by mixed pellets and delayed precision hits.
 * Splash and body damage use their unchanged body component. */
final class WeaponPrecisionDamage {
    private WeaponPrecisionDamage() {}
    static float boost(float precision, double multiplier) {
        if (!Float.isFinite(precision) || precision < 0 || !Double.isFinite(multiplier) || multiplier < 1)
            throw new IllegalArgumentException("Invalid precision transaction");
        return (float)(precision*multiplier);
    }
}
