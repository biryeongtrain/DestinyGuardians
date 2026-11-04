package kim.biryeong.destiny.fx;

import java.util.ArrayList;
import java.util.List;

/** H20's original sparse accent choreography, in a right/up/forward basis (blocks). No mesh data. */
final class H20VfxGeometry {
    record Point(double right, double up, double forward, boolean bright) { }

    private H20VfxGeometry() { }

    static double progress(double value) {
        return Double.isFinite(value) ? Math.clamp(value, 0, 1) : 0;
    }

    /** Two broken limb edges; never a filled disc or a cloud around the owner's face. */
    static List<Point> bow(int age, double charge, boolean forming) {
        double q = progress(charge);
        List<Point> points = new ArrayList<>();
        int count = forming ? Math.min(5, 1 + Math.max(0, age) / 2) : 3;
        for (int side : new int[]{-1, 1}) {
            for (int i = 0; i < count; i++) {
                double t = (i + 1) / 5.0;
                points.add(new Point(.04 * Math.sin(age * .5 + i), side * (.18 + .5 * t),
                        .24 * t * t, i == count - 1));
            }
            if (q > 0) {
                // A pair of inward-moving motes and a nock sparkle, not a solid replacement string.
                points.add(new Point(.08, side * (.58 - .42 * q), -.18 * q, true));
                points.add(new Point(-.06, side * .1, -.24 * q, false));
            }
        }
        return List.copyOf(points);
    }

    static List<Point> staff(int age) {
        List<Point> points = new ArrayList<>();
        for (int side : new int[]{-1, 1}) {
            points.add(new Point(0, side * .72, 0, true));
            points.add(new Point(.09, side * .85, .04, false));
            points.add(new Point(-.09, side * .85, -.04, false));
            points.add(new Point(.025 * Math.sin(age), side * .45, 0, false));
        }
        return List.copyOf(points);
    }

    static List<Point> gun(int age) {
        double shimmer = .025 * Math.sin(age * .7);
        return List.of(new Point(-.08, -.04, -.18, false), new Point(.08, -.04, -.18, false),
                new Point(-.08, .03, .05, true), new Point(.08, .03, .05, true),
                new Point(shimmer, .05, .32, true), new Point(0, -.12, -.26, false));
    }

    /** Broken expanding shock edges, with an intentionally empty central aiming lane. */
    static List<Point> release(int age) {
        List<Point> points = new ArrayList<>();
        double radius = .16 + Math.clamp(age, 0, 6) * .045;
        for (int side : new int[]{-1, 1}) for (int i = 0; i < 4; i++) {
            double a = -.85 + i * .55;
            points.add(new Point(side * (.15 + radius * Math.cos(a)), radius * Math.sin(a),
                    age * .035, i == 1));
        }
        return List.copyOf(points);
    }

    /** A compact three-pronged rune and orbit beads; radius stays below .82 block. */
    static List<Point> anchor(int age, int remaining) {
        List<Point> points = new ArrayList<>();
        double envelope = Math.min(1, Math.min((age + 1) / 6.0, Math.max(0, remaining) / 10.0));
        for (int arm = 0; arm < 3; arm++) {
            double a = arm * Math.PI * 2 / 3 + age * .035;
            for (int i = 0; i < 3; i++) {
                double radius = (.28 + i * .23) * envelope;
                points.add(new Point(Math.cos(a) * radius, .08 + i * .035,
                        Math.sin(a) * radius, i == 2));
            }
            double orbit = a + .45;
            points.add(new Point(Math.cos(orbit) * .52 * envelope,
                    .24 + .08 * Math.sin(age * .2 + arm), Math.sin(orbit) * .52 * envelope, true));
        }
        return List.copyOf(points);
    }
}
