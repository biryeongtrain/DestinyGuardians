package kim.biryeong.destiny.campaign.presentation;

import kim.biryeong.destiny.activity.presentation.ModelTransport;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;
import java.util.ArrayList;
import java.util.List;

/** Activity-authored flight choices; the reusable transport owns admission and lifecycle. */
public final class DevilsTransportPaths {
    public static final String MODEL = "rg_skiff";
    private DevilsTransportPaths() { }
    public static List<ModelTransport.Route> candidates(Vec3 pad) {
        // Tutorial skiff: 5 x 4.85 x 15.74 block body, padded for idle sway and opening clamps.
        var hull = new AABB(-5, -5, -10, 5, 5, 10);
        var routes = new ArrayList<ModelTransport.Route>();
        for (int height : new int[]{12, 18, 30, 48, 64, 80, 96}) {
            var hover = pad.add(0, height, 0);
            for (int yaw : new int[]{0, 180, 90, 270}) {
                double radians = Math.toRadians(yaw);
                var forward = new Vec3(-Math.sin(radians), 0, Math.cos(radians));
                routes.add(new ModelTransport.Route(hover.add(forward.scale(-8)).add(0, 16, 0),
                        hover, hover.add(forward.scale(12)).add(0, 24, 0), yaw, hull));
            }
        }
        return List.copyOf(routes);
    }
}
