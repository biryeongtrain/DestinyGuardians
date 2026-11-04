package kim.biryeong.destiny.activity.presentation;

import kim.biryeong.destiny.fx.Fx;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.phys.Vec3;

import java.util.ArrayList;
import java.util.List;

/**
 * Shared Ghost breadcrumb trail (owner-only particles): runs along a {@link GuideRoute} from the point nearest
 * the player toward the target, 0.3 m above the floor and drifting forward; rising sparks mark jump spots.
 * Without a route (or already on the target's point) it falls back to a short straight line. Stateless.
 */
public final class GuideTrail {
    public static final double SOFT_SPACING = 1.3, STRONG_SPACING = 0.6;
    public static final int POINTS = 5;
    public static final double LENGTH = 22, FLOOR_LIFT = 0.3, STRAIGHT = 14;
    public static final int GHOST = 0x8FE3FF;

    private GuideTrail() { }

    /** Polyline the trail follows (starts at the player's feet); empty when nothing should be drawn. Pure. */
    public static List<Vec3> path(GuideRoute route, Vec3 feet, Vec3 target, List<Vec3> jumpsOut) {
        var path = new ArrayList<Vec3>();
        if (target == null) return path;
        var section = route == null ? List.<GuideRoute.Point>of() : route.section(feet, target, POINTS, LENGTH);
        if (!section.isEmpty()) {
            path.add(feet);
            for (var w : section) {
                path.add(w.pos());
                if (w.jump() && jumpsOut != null) jumpsOut.add(w.pos());
            }
        } else if (route == null || route.nearest(target) == route.nearest(feet)) {
            Vec3 dir = target.subtract(feet);
            double len = Math.min(STRAIGHT, dir.length());
            if (len < 1) return path;
            path.add(feet);
            path.add(feet.add(dir.normalize().scale(len)));
        }
        return path;
    }

    public static void draw(ServerPlayer p, GuideRoute route, Vec3 target, int now, boolean strong) {
        if (!(p.level() instanceof ServerLevel level)) return;
        var jumps = new ArrayList<Vec3>();
        var path = path(route, p.position(), target, jumps);
        if (path.size() < 2) return;
        double spacing = strong ? STRONG_SPACING : SOFT_SPACING;
        float size = strong ? 1.2f : 0.75f;
        double phase = (now * 0.08) % spacing;
        double travelled = 0, next = phase;
        for (int i = 1; i < path.size(); i++) {
            Vec3 a = path.get(i - 1), b = path.get(i);
            double seg = a.distanceTo(b);
            for (; seg > 1e-3 && next < travelled + seg; next += spacing) {
                if (next < 1.2) continue; // keep the first metre clear of the camera
                Vec3 at = a.add(b.subtract(a).scale((next - travelled) / seg));
                level.sendParticles(p, Fx.dust(GHOST, size), true, true, at.x, at.y + FLOOR_LIFT, at.z, 1, 0, 0, 0, 0);
            }
            travelled += seg;
        }
        for (Vec3 j : jumps)
            for (int k = 0; k < (strong ? 3 : 1); k++)
                level.sendParticles(p, ParticleTypes.END_ROD, true, false, j.x, j.y + FLOOR_LIFT + k * 0.35, j.z, 0, 0, 1, 0, 0.12);
        if (strong) level.sendParticles(p, ParticleTypes.END_ROD, true, false, target.x, target.y + 1.2, target.z, 4, .3, .6, .3, .01);
    }
}
