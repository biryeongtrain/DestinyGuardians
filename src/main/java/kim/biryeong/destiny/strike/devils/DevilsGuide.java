package kim.biryeong.destiny.strike.devils;

import kim.biryeong.destiny.activity.presentation.GuideRoute;
import kim.biryeong.destiny.activity.presentation.ObjectiveGuide;
import kim.biryeong.destiny.activity.presentation.ObjectiveGuide.Mode;
import kim.biryeong.destiny.strike.devils.DevilsPlan.Zone;
import net.minecraft.world.phys.Vec3;

import java.util.EnumMap;
import java.util.List;
import java.util.Map;
import java.util.function.BiFunction;

/**
 * Devils' Lair adapter for the shared {@link ObjectiveGuide}: which marker each phase points at and the walkable
 * marker chain per zone. Clear phases lead to the zone exit, the refinery device step to the Ghost console; the
 * Rocketyard approach is a fight, so its marker only appears for players who are lost.
 */
final class DevilsGuide {
    /** Marker chain the trail follows, entrance to exit. */
    static final Map<Zone, List<String>> PATHS = new EnumMap<>(Map.of(
            Zone.RY, List.of("RY.IN", "RY.C1", "RY.C2", "RY.OUT"),
            Zone.RF, List.of("RF.IN", "RF.G", "RF.D", "RF.EXIT"),
            Zone.BL, List.of("BL.IN", "BL.H", "BL.B2", "BL.EXIT"),
            Zone.SP, List.of("SP.IN", "SP.C")));

    private DevilsGuide() { }

    /** Step for a phase as {marker id, mode}, or null when no guidance applies. Pure. */
    static Object[] step(DevilsDirector.Phase phase) {
        return switch (phase) {
            case RY_APPROACH -> new Object[]{"RY.C2", Mode.COMBAT};
            case RY_CLEAR -> new Object[]{"RY.OUT", Mode.TRAVEL};
            case RF_DEVICE -> new Object[]{"RF.G", Mode.TRAVEL};
            case RF_CLEAR -> new Object[]{"RF.EXIT", Mode.TRAVEL};
            case BL_BATTLE -> new Object[]{"BL.EXIT", Mode.COMBAT};
            case BL_CLEAR -> new Object[]{"BL.EXIT", Mode.TRAVEL};
            default -> null;
        };
    }

    /** @param anchor resolves (zone, marker id) to its world feet position. */
    static ObjectiveGuide.Target target(DevilsDirector.Phase phase, BiFunction<Zone, String, Vec3> anchor) {
        var step = step(phase);
        if (step == null) return null;
        Zone zone = phase.zone();
        var points = PATHS.getOrDefault(zone, List.of()).stream().map(id -> anchor.apply(zone, id)).toList();
        return new ObjectiveGuide.Target(phase.name(), anchor.apply(zone, (String) step[0]),
                points.size() >= 2 ? GuideRoute.of(points) : null, (Mode) step[1]);
    }
}
