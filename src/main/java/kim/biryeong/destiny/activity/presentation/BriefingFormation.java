package kim.biryeong.destiny.activity.presentation;

import kim.biryeong.destiny.crucible.CrucibleIntro;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.phys.Vec3;

import java.util.ArrayList;
import java.util.List;
import java.util.Optional;

/**
 * Shared raid-style fireteam briefing: up to three members land in a line facing {@code yaw} while the camera
 * dollies in from the front. Roles follow the Crota's End landing (cin_728_rai) slots chosen for briefings:
 * centre {@code pla01}, screen-left {@code pla03} (hand raise), screen-right {@code pla06}. Lane spacing and the
 * slight depth stagger come from the delivered briefing timeline (+-1.38 m, centre 0.22 m forward).
 */
public final class BriefingFormation {
    public static final List<String> CLIPS = List.of("h15_intro_brief_pla01", "h15_intro_brief_pla03", "h15_intro_brief_pla06");
    /** Source motion 265 frames at 30 fps, then the authored final pose holds. */
    public static final int MOTION_TICKS = 177;
    /** Per-slot reveal delay: source frame (pla01 1, pla03 141, pla06 81) at 30 fps, in server ticks. */
    public static final List<Integer> REVEAL_TICKS = List.of(0, 93, 53);
    /** Camera establishing time before the first transmat completes. */
    public static final int LEAD_TICKS = 20;
    static final double LANE = 1.65;
    private static final double[][] SLOTS = {{0, .22}, {-LANE, -.36}, {LANE, -.35}};

    public record Plan(List<CrucibleIntro.ActorPlacement> placements, List<Integer> reveals, List<CrucibleIntro.Shot> shots) { }
    private BriefingFormation() { }

    /** World offset of formation slot {@code i}: x = screen right (seen from the camera), z = toward the camera. */
    static Vec3 slot(int i, float yaw) {
        double r = Math.toRadians(yaw);
        Vec3 forward = new Vec3(-Math.sin(r), 0, Math.cos(r)), screenRight = new Vec3(Math.cos(r), 0, Math.sin(r));
        // The camera looks back at the team, so its screen-right is the team's own left (+cos, +sin).
        return screenRight.scale(SLOTS[i][0]).add(forward.scale(SLOTS[i][1]));
    }

    /** Grounded placements and a collision-checked camera, or empty when the stage cannot host the shot. */
    public static Optional<Plan> plan(ServerLevel level, List<ServerPlayer> members, Vec3 centre, float yaw) {
        var placements = new ArrayList<CrucibleIntro.ActorPlacement>();
        for (int i = 0; i < Math.min(3, members.size()); i++) {
            var feet = ActivityCast.grounded(level, centre.add(slot(i, yaw)));
            if (feet.isEmpty()) return Optional.empty();
            placements.add(new CrucibleIntro.ActorPlacement(members.get(i), feet.get(), yaw, CLIPS.get(i)));
        }
        if (placements.isEmpty()) return Optional.empty();
        double r = Math.toRadians(yaw);
        Vec3 forward = new Vec3(-Math.sin(r), 0, Math.cos(r)), side = new Vec3(Math.cos(r), 0, Math.sin(r));
        Vec3 base = placements.getFirst().position();
        Vec3 chest = base.add(0, 1.15, 0), face = base.add(0, 1.45, 0);
        Vec3 wide = base.add(forward.scale(8.5)).add(0, 2.4, 0), mid = base.add(forward.scale(5.2)).add(0, 1.65, 0);
        Vec3 close = base.add(forward.scale(4.1)).add(side.scale(.6)).add(0, 1.55, 0);
        for (var p : new Vec3[]{wide, mid, close}) if (!ActivityCast.clearShot(level, p, chest)) {
            // Narrow stages keep the slow push-in but start closer.
            if (!ActivityCast.clearShot(level, mid, chest) || !ActivityCast.clearShot(level, close, face)) return Optional.empty();
            return Optional.of(new Plan(placements, REVEAL_TICKS.subList(0, placements.size()), List.of(new CrucibleIntro.Shot(mid, close, face, MOTION_TICKS + 20),
                    new CrucibleIntro.Shot(close, close, face, 400))));
        }
        return Optional.of(new Plan(placements, REVEAL_TICKS.subList(0, placements.size()), List.of(
                new CrucibleIntro.Shot(wide, mid, chest, LEAD_TICKS + MOTION_TICKS),
                new CrucibleIntro.Shot(mid, close, face, 260),
                new CrucibleIntro.Shot(close, close, face, 200))));
    }
}
