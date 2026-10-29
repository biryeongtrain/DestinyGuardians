package kim.biryeong.destiny.weapon;

import net.minecraft.world.phys.Vec3;

/** Pure shot dispersion math; angles are local Minecraft tuning, not exact Destiny 2 values. */
public final class ShotDispersion {
    private ShotDispersion() {}

    /** Combines independent hip/bloom and airborne half-angles in degrees. */
    public static double coneDegrees(double hipDegrees, double airDegrees, double adsProgress,
                                     boolean airborne, double airborneEffectiveness,
                                     double bloomDegrees, double accuracyScalar) {
        double hipTerm = (nonNegative(hipDegrees) + nonNegative(bloomDegrees))
                * (1 - unit(adsProgress)) * unit(accuracyScalar);
        double airTerm = airborne
                ? nonNegative(airDegrees) * (1 - unit(airborneEffectiveness / 100)) : 0;
        return Math.hypot(hipTerm, airTerm);
    }

    /**
     * Samples a uniform disk in the tangent plane, then normalizes the ray.
     * Samples are clamped to [0, 1]; malformed angles disable spread and invalid
     * directions return zero. Half-angles at or above 90 are limited below 90
     * so the tangent projection stays in the forward hemisphere.
     */
    public static Vec3 sample(Vec3 forward, double halfAngleDegrees,
                              double radialSample, double azimuthSample) {
        if (forward == null || !Double.isFinite(forward.x)
                || !Double.isFinite(forward.y) || !Double.isFinite(forward.z)) {
            return Vec3.ZERO;
        }
        Vec3 direction = forward.normalize();
        if (direction.lengthSqr() == 0 || !Double.isFinite(direction.lengthSqr())) {
            return Vec3.ZERO;
        }
        double angle = nonNegative(halfAngleDegrees);
        if (angle == 0) return direction;
        double radius = Math.sqrt(unit(radialSample))
                * Math.tan(Math.toRadians(Math.min(angle, Math.nextDown(90.0))));
        if (radius == 0) return direction;

        // Switch reference axes near vertical aim to avoid a degenerate cross product.
        Vec3 reference = Math.abs(direction.y) > 0.999
                ? new Vec3(1, 0, 0) : new Vec3(0, 1, 0);
        Vec3 right = direction.cross(reference).normalize();
        Vec3 up = right.cross(direction);
        double azimuth = unit(azimuthSample) * (2 * Math.PI);
        return direction.add(right.scale(radius * Math.cos(azimuth)))
                .add(up.scale(radius * Math.sin(azimuth))).normalize();
    }

    private static double nonNegative(double value) {
        return Double.isFinite(value) ? Math.max(0, value) : 0;
    }

    private static double unit(double value) {
        return Double.isFinite(value) ? Math.clamp(value, 0, 1) : 0;
    }
}
