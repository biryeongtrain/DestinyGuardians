package kim.biryeong.destiny.weapon;

import net.minecraft.world.phys.Vec3;
import org.junit.jupiter.api.Test;

import java.util.Random;

import static org.junit.jupiter.api.Assertions.*;

class ShotDispersionW241Test {
    private static final double EPS = 1e-12;

    @Test
    void airborneEffectivenessHasAnExactFullAdsCutoffAt100() {
        assertEquals(0.08, ShotDispersion.coneDegrees(4, 8, 1, true, 99, 3, 0.5), EPS);
        Vec3 forward = new Vec3(2, -3, 7);
        for (double ae : new double[]{100, 101, 250}) {
            double angle = ShotDispersion.coneDegrees(4, 8, 1, true, ae, 3, 0.5);
            assertEquals(0.0, angle);
            assertEquals(forward.normalize(), ShotDispersion.sample(forward, angle, 1, 0.37));
        }
    }

    @Test
    void groundedFullAdsRemovesHipAndBloomRegardlessOfAirborneEffectiveness() {
        for (double ae : new double[]{0, 99, 100, 150}) {
            assertEquals(0.0, ShotDispersion.coneDegrees(5, 12, 1, false, ae, 4, 1));
        }
    }

    @Test
    void airPenaltySurvivesZeroAccuracyScalarAndHipSurvives100Ae() {
        assertEquals(6, ShotDispersion.coneDegrees(20, 8, 0.3, true, 25, 5, 0), EPS);
        for (double ae : new double[]{100, 150}) {
            assertEquals(7.5, ShotDispersion.coneDegrees(10, 8, 0, true, ae, 5, 0.5), EPS);
            assertEquals(3.75, ShotDispersion.coneDegrees(10, 8, 0.5, true, ae, 5, 0.5), EPS);
        }
    }

    @Test
    void partialAdsCombinesIndependentTermsInQuadratureAndClampsControls() {
        assertEquals(Math.sqrt(38.25),
                ShotDispersion.coneDegrees(4, 8, 0.5, true, 25, 2, 0.5), EPS);
        assertEquals(10, ShotDispersion.coneDegrees(4, 8, -1, true, -50, 2, 2), EPS);
        assertEquals(0.0, ShotDispersion.coneDegrees(4, 8, 2, true, 120, 2, 1));
        assertEquals(8, ShotDispersion.coneDegrees(4, 8, 0, true, 0, 2, -1), EPS);
        assertEquals(0.0, ShotDispersion.coneDegrees(-4, -8, 0, true, 0, -2, 1));
        assertEquals(0.0, ShotDispersion.coneDegrees(Double.NaN, Double.POSITIVE_INFINITY,
                Double.NaN, true, Double.NaN, Double.NEGATIVE_INFINITY, Double.NaN));
    }

    @Test
    void zeroSpreadAndCenterSamplesReturnTheExactNormalizedForward() {
        Vec3 forward = new Vec3(2, -3, 7);
        assertEquals(forward.normalize(), ShotDispersion.sample(forward, 0, 1, 0.7));
        assertEquals(forward.normalize(), ShotDispersion.sample(forward, 35, 0, 0.7));
        double angle = ShotDispersion.coneDegrees(10, 20, 1, true, 100, 8, 1);
        assertEquals(forward.normalize(), ShotDispersion.sample(forward, angle, 0.8, 0.1));
    }

    @Test
    void samplesStayFiniteUnitAndInsideTheConeAcrossAllAimOrientations() {
        for (double yaw : new double[]{-180, -90, 0, 45, 180}) {
            for (double pitch : new double[]{-90, -89.999999, -45, 0, 45, 89.999999, 90}) {
                double y = Math.toRadians(yaw), p = Math.toRadians(pitch);
                Vec3 forward = new Vec3(-Math.sin(y) * Math.cos(p), -Math.sin(p),
                        Math.cos(y) * Math.cos(p)).scale(7);
                Vec3 axis = forward.normalize();
                for (double degrees : new double[]{0, 0.1, 12, 80}) {
                    for (double radial : new double[]{0, 0.01, 0.25, 1}) {
                        for (double azimuth : new double[]{0, 0.125, 0.5, 0.875, 1}) {
                            Vec3 ray = ShotDispersion.sample(forward, degrees, radial, azimuth);
                            assertFiniteUnit(ray);
                            double along = ray.dot(axis);
                            assertTrue(along > 0);
                            double actual = Math.atan2(ray.cross(axis).length(), along);
                            assertTrue(actual <= Math.toRadians(degrees) + EPS);
                            // Projection onto the tangent plane must preserve the disk area CDF.
                            double tangentRadius = ray.cross(axis).length() / along;
                            assertEquals(Math.sqrt(radial) * Math.tan(Math.toRadians(degrees)),
                                    tangentRadius, EPS);
                        }
                    }
                }
            }
        }
        // Exact vertical vectors, independent of trigonometric near-zero components.
        for (Vec3 forward : new Vec3[]{new Vec3(0, 1, 0), new Vec3(0, -1, 0)}) {
            Vec3 ray = ShotDispersion.sample(forward, 12, 1, 0.3);
            assertFiniteUnit(ray);
            assertEquals(Math.toRadians(12), Math.acos(ray.dot(forward)), EPS);
        }
    }

    @Test
    void fixedSeedDiskHasNoDirectionalBiasAndHasUniformArea() {
        int count = 40_000;
        for (Vec3 forward : new Vec3[]{new Vec3(0, 0, 1), new Vec3(0, 1, 0),
                new Vec3(0, -1, 0), new Vec3(2, -3, 7).normalize()}) {
            Random random = new Random(241);
            Vec3 reference = Math.abs(forward.z) < 0.9 ? new Vec3(0, 0, 1) : new Vec3(1, 0, 0);
            Vec3 first = forward.cross(reference).normalize();
            Vec3 second = forward.cross(first).normalize();
            double sumX = 0, sumY = 0, sumXX = 0, sumYY = 0, sumXY = 0;
            int innerHalfArea = 0;
            double radius = Math.tan(Math.toRadians(20));
            for (int i = 0; i < count; i++) {
                Vec3 ray = ShotDispersion.sample(forward, 20, random.nextDouble(), random.nextDouble());
                double along = ray.dot(forward);
                double x = ray.dot(first) / along / radius;
                double y = ray.dot(second) / along / radius;
                sumX += x;
                sumY += y;
                sumXX += x * x;
                sumYY += y * y;
                sumXY += x * y;
                if (x * x + y * y < 0.5) innerHalfArea++;
            }
            assertEquals(0, sumX / count, 0.01, "No preferred tangent direction");
            assertEquals(0, sumY / count, 0.01, "No preferred tangent direction");
            assertEquals(0.25, sumXX / count, 0.01);
            assertEquals(0.25, sumYY / count, 0.01);
            assertEquals(0, sumXY / count, 0.01);
            assertEquals(0.5, (double) innerHalfArea / count, 0.01, "Uniform area, not uniform radius");
        }
    }

    @Test
    void malformedArgumentsHaveDeterministicFiniteFallbacks() {
        for (Vec3 invalid : new Vec3[]{null, Vec3.ZERO, new Vec3(Double.NaN, 1, 0),
                new Vec3(0, Double.POSITIVE_INFINITY, 0)}) {
            assertEquals(Vec3.ZERO, ShotDispersion.sample(invalid, 10, 0.5, 0.5));
        }
        Vec3 forward = new Vec3(0, 0, 3);
        for (double angle : new double[]{-1, Double.NaN, Double.POSITIVE_INFINITY}) {
            assertEquals(forward.normalize(), ShotDispersion.sample(forward, angle, 1, 0.3));
        }
        assertEquals(forward.normalize(), ShotDispersion.sample(forward, 20, -1, 0.3));
        assertEquals(forward.normalize(), ShotDispersion.sample(forward, 20, Double.NaN, 0.3));
        assertEquals(ShotDispersion.sample(forward, 20, 1, 0),
                ShotDispersion.sample(forward, 20, 2, -1));
        assertEquals(ShotDispersion.sample(forward, 20, 1, 0),
                ShotDispersion.sample(forward, 20, 1, Double.NaN));
        assertFiniteUnit(ShotDispersion.sample(forward, 90, 1, 0.3));
        assertFiniteUnit(ShotDispersion.sample(forward, 180, 1, 0.3));
    }

    private static void assertFiniteUnit(Vec3 vector) {
        assertTrue(Double.isFinite(vector.x) && Double.isFinite(vector.y) && Double.isFinite(vector.z));
        assertEquals(1, vector.length(), EPS);
    }
}
