package kim.biryeong.destiny.fx;

import java.util.Comparator;
import java.util.List;
import java.util.Optional;

/** Server-side approximation of the private vanilla CENTER-billboard text plane.
 * Units are a logical image plane seven blocks ahead, not framebuffer pixels.
 * Font metrics, gap and stacking are authored presentation, not measured Destiny constants.
 * No Minecraft state, damage, clock, ownership or persistent reservations live here. */
public final class DamageNumberLayout {
    public static final double PLANE = 7;
    public static final double SCALE = .65;
    public static final double BASE_Y = .12;
    public static final double RISE = .025;
    public static final double GAP = .035;
    private static final double FONT_PIXEL = 1d / 40;
    private DamageNumberLayout() {}

    public record Point(double x, double y, double z) {
        public Point {
            if (!finite(x, y, z)) throw new IllegalArgumentException("Nonfinite point");
        }
    }
    public record View(Point eye, double yaw, double pitch) {
        public View {
            if (eye == null || !finite(yaw, pitch) || Math.abs(pitch) > 90)
                throw new IllegalArgumentException("Invalid view");
        }
    }
    public record Box(double x, double y, double halfWidth, double halfHeight) {
        public Box {
            if (!finite(x, y, halfWidth, halfHeight) || halfWidth <= 0 || halfHeight <= 0
                    || !finite(x-halfWidth, x+halfWidth, y-halfHeight, y+halfHeight))
                throw new IllegalArgumentException("Invalid box");
        }
    }
    public record Projected(Box box, double angularScale) {}

    private static boolean finite(double... values) {
        for (double value : values) if (!Double.isFinite(value)) return false;
        return true;
    }

    /** Matches the existing distance-scaled billboard, including the 4..96 distance clamp.
     * Behind/near-eye or overflowed projections have no useful visible reservation.
     * At steep pitch the yaw-defined screen-right remains well-defined. */
    public static Optional<Projected> project(View view, Point impact, boolean precision,
                                               int age, double lift, int digits) {
        if (view == null || impact == null || age < 0 || age >= 16 || !Double.isFinite(lift)
                || lift < 0 || digits < 1 || digits > 10) return Optional.empty();
        double yaw = Math.toRadians(view.yaw), pitch = Math.toRadians(view.pitch);
        double sy = Math.sin(yaw), cy = Math.cos(yaw), sp = Math.sin(pitch), cp = Math.cos(pitch);
        double dx = impact.x-view.eye.x, dy = impact.y-view.eye.y, dz = impact.z-view.eye.z;
        double depth = -sy*cp*dx-sp*dy+cy*cp*dz;
        double distance = Math.hypot(Math.hypot(dx,dy),dz);
        if (!finite(depth,distance) || depth <= .05) return Optional.empty();
        double angular = Math.clamp(distance,4,96)/depth;
        double x = (-cy*dx-sy*dz)/depth*PLANE+((precision?.18:-.18)+FONT_PIXEL*SCALE)*angular;
        double y = (-sy*sp*dx+cp*dy+cy*sp*dz)/depth*PLANE+(BASE_Y+age*RISE+lift+4*FONT_PIXEL*SCALE)*angular;
        // Native renderer scales by -1/40 and translates by (1-width/2,-lineHeight).
        // Reserve a conservative numeric advance box plus shadow margin, not just its anchor.
        // Ten-pixel vertical envelope [-1,9] has center +4; horizontal center is +1.
        double hw = (digits*6+2)*FONT_PIXEL*SCALE/2*angular;
        double hh = 10*FONT_PIXEL*SCALE/2*angular;
        if (!finite(angular,x,y,hw,hh,x-hw,x+hw,y-hh,y+hh)) return Optional.empty();
        return Optional.of(new Projected(new Box(x,y,hw,hh),angular));
    }

    /** Occupancy in a newly born label's moving frame until the older label expires.
     * Different distance clamps/off-axis depths have different projected rise velocities.
     * Reserving the full relative sweep prevents later collisions without moving old holders.
     * Static owner view/anchors assumed; camera or player motion remains an approximation. */
    public static Box relativeSweep(Projected existing, int age, double newAngularScale) {
        if (existing == null || existing.box == null || age < 0 || age >= 16
                || !finite(existing.angularScale,newAngularScale) || existing.angularScale <= 0 || newAngularScale <= 0)
            throw new IllegalArgumentException("Invalid sweep inputs");
        var b=existing.box;
        double delta=(existing.angularScale-newAngularScale)*RISE*(15-age);
        return new Box(b.x,b.y+delta/2,b.halfWidth,b.halfHeight+Math.abs(delta)/2);
    }

    /** Smallest upward-only placement outside all horizontally intersecting live boxes.
     * One sorted sweep, bounded by the caller's existing 24-owner scene budget. Never changes
     * or retains the input; expired/evicted holders therefore need no second reservation map. */
    public static Box packUp(Box desired, List<Box> occupied, double gap) {
        if (desired == null || occupied == null || !Double.isFinite(gap) || gap < 0)
            throw new IllegalArgumentException("Invalid layout inputs");
        double y = desired.y;
        var collisions = occupied.stream().filter(b -> b != null
                && Math.abs(desired.x-b.x) < desired.halfWidth+b.halfWidth+gap)
                .sorted(Comparator.<Box>comparingDouble(b -> b.y-b.halfHeight)
                        .thenComparingDouble(b -> b.y+b.halfHeight).thenComparingDouble(Box::x)
                        .thenComparingDouble(Box::halfWidth)).toList();
        for (var box : collisions) {
            if (y+desired.halfHeight <= box.y-box.halfHeight-gap) break;
            if (y-desired.halfHeight < box.y+box.halfHeight+gap)
                y = Math.nextUp(box.y+box.halfHeight+gap+desired.halfHeight);
        }
        return new Box(desired.x,y,desired.halfWidth,desired.halfHeight);
    }
}
