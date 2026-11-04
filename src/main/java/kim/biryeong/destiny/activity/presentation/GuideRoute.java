package kim.biryeong.destiny.activity.presentation;

import net.minecraft.world.phys.Vec3;

import java.util.ArrayList;
import java.util.List;
import java.util.Objects;

/**
 * Shared walkable guide route: world (or zone-local) feet positions on the floor, a {@code jump} flag where the
 * floor rises before the next point. Activity-neutral; campaign routes.json and strike marker paths both build
 * one. Pure: nearest-point and trail-section selection are unit tested.
 */
public record GuideRoute(List<Point> points) {
    /** Vertical distance counts double so stacked stairs/tunnel segments are not confused with the floor above. */
    public static final double Y_WEIGHT = 2.0;

    public record Point(Vec3 pos, boolean jump, String objective) {
        public Point { Objects.requireNonNull(pos); }
        public Point(Vec3 pos) { this(pos, false, null); }
    }

    public GuideRoute { points = List.copyOf(points); }

    public static GuideRoute of(List<Vec3> positions) {
        return new GuideRoute(positions.stream().map(Point::new).toList());
    }

    public boolean usable() { return points.size() >= 2; }

    public GuideRoute offset(Vec3 origin) {
        var moved = new ArrayList<Point>(points.size());
        for (var w : points) moved.add(new Point(w.pos().add(origin), w.jump(), w.objective()));
        return new GuideRoute(moved);
    }

    /** Index of the point closest to {@code at} (vertical distance weighted), or -1 if empty. */
    public int nearest(Vec3 at) {
        int best = -1;
        double bestD = Double.MAX_VALUE;
        for (int i = 0; i < points.size(); i++) {
            Vec3 p = points.get(i).pos();
            double dx = p.x - at.x, dy = (p.y - at.y) * Y_WEIGHT, dz = p.z - at.z;
            double d = dx * dx + dy * dy + dz * dz;
            if (d < bestD) { bestD = d; best = i; }
        }
        return best;
    }

    /**
     * The next part of the route from the player toward the objective: starts at the point nearest the player
     * (dropped if the player is already past it), walks toward the point nearest the target and stops after
     * {@code maxPoints} further points or {@code maxLength} metres. Empty when there is nothing to walk.
     */
    public List<Point> section(Vec3 player, Vec3 target, int maxPoints, double maxLength) {
        if (!usable() || target == null) return List.of();
        int from = nearest(player), to = nearest(target);
        if (from < 0 || to < 0 || from == to) return List.of();
        int step = to > from ? 1 : -1;
        var out = new ArrayList<Point>();
        Point first = points.get(from), next = points.get(from + step);
        if (player.distanceToSqr(next.pos()) >= first.pos().distanceToSqr(next.pos())) out.add(first);
        double length = 0;
        Vec3 last = out.isEmpty() ? player : first.pos();
        for (int i = from + step; ; i += step) {
            Point w = points.get(i);
            length += last.distanceTo(w.pos());
            out.add(w);
            last = w.pos();
            if (i == to || out.size() >= maxPoints + 1 || length >= maxLength) break;
        }
        return out;
    }
}
