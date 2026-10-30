package kim.biryeong.destiny.fx;

import kim.biryeong.minigamelib.cinematic.CameraViews;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.phys.Vec3;

/** Ordinary bow trail only. Does not move the shot/trace or mutate any gameplay state.
 * Retains Fx.line's original sample lattice and native recipient visibility/camera hook.
 * An emission-time owner exclusion cannot erase old particles or infer vanilla F5 view.
 */
public final class BowTrailFx {
    private BowTrailFx() { }

    public static void line(ServerPlayer owner, ServerLevel level, Vec3 from, Vec3 to,
                            int rgb, double step, float size) {
        Vec3 delta = to.subtract(from);
        double length = delta.length();
        if (length < 1.0E-4) return;
        Vec3 dir = delta.scale(1.0 / length);
        var dust = Fx.dust(rgb, size);
        boolean selfView = owner.level() == level && owner.getCamera() == owner
                && CameraViews.get(owner) == null;
        Vec3 eye = owner.getEyePosition();
        // Same d=0,+step lattice as Fx.line: never restart at a clipped point or add an endpoint.
        for (double d = 0; d <= length; d += step) {
            Vec3 point = from.add(dir.scale(d));
            for (var recipient : level.players()) {
                if (recipient == owner && selfView
                        && BowTrailVisibility.hidesOwnerSample(point.distanceToSqr(eye))) continue;
                // false/false + default randomization, native distance and CameraViews routing.
                // Fx.line's simple broadcast overload reaches the same private recipient seam.
                AbilityParticles.sendTo(owner, level, recipient, dust, false, false,
                        point.x, point.y, point.z, 1, 0, 0, 0, 0);
            }
        }
    }
}
