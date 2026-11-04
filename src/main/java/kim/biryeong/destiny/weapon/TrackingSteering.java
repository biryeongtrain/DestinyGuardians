package kim.biryeong.destiny.weapon;

/** Bounded angular steering only: never increases speed, teleports or chooses an enemy.
 * Turn-rate is caller-authored Minecraft tuning, not a recovered Destiny flight equation. */
public final class TrackingSteering {
    public record Vector(double x, double y, double z) {
        public double length() { return Math.hypot(Math.hypot(x,y),z); }
        private boolean finite() { return Double.isFinite(x)&&Double.isFinite(y)&&Double.isFinite(z); }
        private Vector scale(double s) { return new Vector(x*s,y*s,z*s); }
        private Vector cross(Vector b) { return new Vector(y*b.z-z*b.y,z*b.x-x*b.z,x*b.y-y*b.x); }
        private double dot(Vector b) { return x*b.x+y*b.y+z*b.z; }
    }
    private static final Vector ZERO=new Vector(0,0,0);
    private TrackingSteering() {}
    /** Invalid desired/angle cannot steer. Invalid velocity fails closed to zero, never NaN flight. */
    public static Vector turn(Vector velocity, Vector desired, double maxRadians) {
        if (velocity==null || !velocity.finite()) return ZERO;
        double speed=velocity.length();
        if (!Double.isFinite(speed) || speed<1e-12) return ZERO;
        if (desired==null || !desired.finite() || !Double.isFinite(maxRadians) || maxRadians<=0) return velocity;
        double distance=desired.length();
        if (!Double.isFinite(distance) || distance<1e-12) return velocity;
        Vector from=velocity.scale(1/speed),to=desired.scale(1/distance);
        double angle=Math.acos(Math.clamp(from.dot(to),-1,1));
        double step=Math.min(Math.PI,maxRadians);
        if (angle<=step) return to.scale(speed);
        Vector axis=from.cross(to);double norm=axis.length();
        if (norm<1e-12) {
            // Opposite vectors have no unique shortest arc. Pick a stable perpendicular axis.
            Vector basis=Math.abs(from.x)<=Math.abs(from.y)&&Math.abs(from.x)<=Math.abs(from.z)
                    ?new Vector(1,0,0):Math.abs(from.y)<=Math.abs(from.z)?new Vector(0,1,0):new Vector(0,0,1);
            axis=from.cross(basis);norm=axis.length();
        }
        axis=axis.scale(1/norm);
        double c=Math.cos(step),s=Math.sin(step);Vector side=axis.cross(from);
        Vector next=new Vector(from.x*c+side.x*s,from.y*c+side.y*s,from.z*c+side.z*s);
        double nextNorm=next.length();
        return Double.isFinite(nextNorm)&&nextNorm>0?next.scale(speed/nextNorm):velocity;
    }
}
