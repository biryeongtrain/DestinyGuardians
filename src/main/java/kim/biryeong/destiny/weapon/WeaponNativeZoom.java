package kim.biryeong.destiny.weapon;

/**
 * Pure Minecraft movement adaptation for native speed-based FOV.
 * This does not change DDC base ADS profiles or damage falloff.
 */
public final class WeaponNativeZoom {
    private WeaponNativeZoom() {}

    /**
     * Returns lerp(1, baseAdsScalar / max(1, effectiveZoom), clamp(progress, 0, 1)).
     * The caller applies Moving Target once, after this scalar.
     *
     * @param baseAdsScalar base ADS movement scalar in (0, 1]
     * @param effectiveZoom finite zoom; values below one use one
     * @param progress finite ADS transition progress, clamped to [0, 1]
     * @return a finite movement scalar in (0, 1]; underflow saturates at Double.MIN_VALUE
     * @throws IllegalArgumentException if any input is non-finite or the base is outside (0, 1]
     */
    public static double movementScalar(double baseAdsScalar, double effectiveZoom, double progress) {
        if (!Double.isFinite(baseAdsScalar) || baseAdsScalar <= 0 || baseAdsScalar > 1) {
            throw new IllegalArgumentException("baseAdsScalar must be finite and in (0, 1]");
        }
        if (!Double.isFinite(effectiveZoom) || !Double.isFinite(progress)) {
            throw new IllegalArgumentException("effectiveZoom and progress must be finite");
        }
        double target = Math.max(Double.MIN_VALUE, baseAdsScalar / Math.max(1, effectiveZoom));
        double t = Math.clamp(progress, 0, 1);
        // Weighted endpoints avoid cancellation to zero near full ADS.
        return (1 - t) + t * target;
    }
}
