package kim.biryeong.destiny.activity.presentation;

import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;
import org.joml.Quaterniond;
import org.joml.Vector3d;

import java.util.ArrayList;
import java.util.List;
import java.util.Objects;

/** Conservative rigid-hull corridor for linear translation and shortest-arc quaternion interpolation.
 * The caller must provide the evaluated local hull (including all skeletal motion) and every actual
 * interpolation endpoint. Raw animation keys are insufficient for compiled curves with overshoot.
 * Does not authorize a route, load chunks, move a ship, or approximate a source animation. */
public final class FlightSweep {
    private static final double EPSILON = 1e-7;
    private static final int MAX_POSES = 8192;
    private FlightSweep() { }

    public record Pose(Vec3 position, Quaterniond rotation) {
        public Pose {
            Objects.requireNonNull(position); Objects.requireNonNull(rotation);
            finite(position.x, position.y, position.z, rotation.x, rotation.y, rotation.z, rotation.w);
            double norm = rotation.lengthSquared();
            if (!Double.isFinite(norm) || norm < 1e-16) throw new IllegalArgumentException("Invalid rotation norm");
            rotation = new Quaterniond(rotation).normalize();
        }
        /** JOML values are mutable; neither input nor returned values may mutate a validated route. */
        @Override public Quaterniond rotation() { return new Quaterniond(rotation); }
    }

    public static List<AABB> corridor(AABB localHull, List<Pose> poses) {
        hull(localHull); Objects.requireNonNull(poses);
        if (poses.isEmpty() || poses.size() > MAX_POSES) throw new IllegalArgumentException("Invalid flight pose count");
        var result = new ArrayList<AABB>(Math.max(1, poses.size()-1));
        if (poses.size() == 1) result.add(at(localHull, poses.getFirst()).inflate(EPSILON));
        else for (int i=1; i<poses.size(); i++) result.add(between(localHull, poses.get(i-1), poses.get(i)));
        return List.copyOf(result);
    }

    /** Endpoint boxes alone miss a turning ship's nose/tail. Each corner's rotation arc departs from
     * its endpoint chord by at most radius*(1-cos(angle/2)). Linear translation adds no deviation.
     * Inflating their union by this sagitta bounds every intermediate point, without sampling gaps.
     * Radius is measured from the rotation origin, not the box center (off-center hulls matter). */
    public static AABB between(AABB localHull, Pose start, Pose end) {
        hull(localHull); Objects.requireNonNull(start); Objects.requireNonNull(end);
        double dot = Math.abs(start.rotation.dot(end.rotation));
        double cosineHalfAngle = Math.clamp(dot, 0, 1);
        double radius = 0;
        for (Vec3 corner : corners(localHull)) radius = Math.max(radius, corner.length());
        double padding = radius*(1-cosineHalfAngle)+EPSILON;
        return at(localHull, start).minmax(at(localHull, end)).inflate(padding);
    }

    private static AABB at(AABB localHull, Pose pose) {
        Objects.requireNonNull(pose);
        AABB result = null;
        for (Vec3 corner : corners(localHull)) {
            var p = pose.rotation.transform(new Vector3d(corner.x, corner.y, corner.z));
            double x=p.x+pose.position.x, y=p.y+pose.position.y, z=p.z+pose.position.z;
            finite(x,y,z);
            var point = new AABB(x,y,z,x,y,z);
            result = result == null ? point : result.minmax(point);
        }
        return result;
    }

    private static List<Vec3> corners(AABB b) {
        var out = new ArrayList<Vec3>(8);
        for (double x : new double[]{b.minX,b.maxX})
            for (double y : new double[]{b.minY,b.maxY})
                for (double z : new double[]{b.minZ,b.maxZ}) out.add(new Vec3(x,y,z));
        return out;
    }
    private static void hull(AABB b) {
        Objects.requireNonNull(b);
        finite(b.minX,b.minY,b.minZ,b.maxX,b.maxY,b.maxZ);
        if (!(b.maxX>b.minX && b.maxY>b.minY && b.maxZ>b.minZ))
            throw new IllegalArgumentException("Flight hull must have positive volume");
    }
    private static void finite(double... values) {
        for (double value : values) if (!Double.isFinite(value)) throw new IllegalArgumentException("Nonfinite flight geometry");
    }
}
