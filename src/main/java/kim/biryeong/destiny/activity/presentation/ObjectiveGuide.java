package kim.biryeong.destiny.activity.presentation;

import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.phys.Vec3;

/**
 * Shared per-player path guidance (waypoint marker + Ghost breadcrumb trail) for any activity. The activity owns
 * one instance per participant, feeds it the current {@link Target} every few ticks and calls {@link #clear()} on
 * leave, disconnect and close. Travel targets show the marker shortly after they change and a faint trail from
 * the start; combat targets stay clean until the player has made no progress for {@link #LOST} ticks. Lost
 * players always get the dense trail.
 */
public final class ObjectiveGuide {
    public enum Mode { TRAVEL, COMBAT }

    /** {@code key} identifies the step (a phase name); a new key restarts the timers. */
    public record Target(String key, Vec3 pos, GuideRoute route, Mode mode) { }

    public static final int MARKER_DELAY = 20, SOFT_DELAY = 40, SOFT_PERIOD = 30, STRONG_PERIOD = 10;
    public static final int LOST = 20 * 25;
    /** Getting this much closer counts as progress. */
    public static final double PROGRESS = 3;

    private final ObjectiveWaypoint waypoint;
    private String key;
    private int startedAt, progressAt;
    private double best = Double.MAX_VALUE;

    public ObjectiveGuide(ServerPlayer owner) { this.waypoint = new ObjectiveWaypoint(owner); }

    public ServerPlayer owner() { return waypoint.owner(); }

    /** What to show this tick; pure for tests. Returns {marker, trail, strong}. */
    public static boolean[] decide(Mode mode, int sinceStart, int sinceProgress, int now) {
        boolean lost = sinceProgress >= LOST;
        boolean marker = mode == Mode.TRAVEL ? sinceStart >= MARKER_DELAY : lost;
        boolean trail = lost ? now % STRONG_PERIOD == 0
                : mode == Mode.TRAVEL && sinceStart >= SOFT_DELAY && now % SOFT_PERIOD == 0;
        return new boolean[]{marker, trail, lost};
    }

    /** @param target null or {@code hidden=true} (cinematic, downed, not yet placed) hides everything. */
    public void tick(Target target, boolean hidden, int now) {
        var p = waypoint.owner();
        if (target == null || target.pos() == null) { key = null; waypoint.clear(); return; }
        if (!target.key().equals(key)) { key = target.key(); startedAt = progressAt = now; best = Double.MAX_VALUE; }
        double d = p.position().distanceTo(target.pos());
        if (d < best - PROGRESS) { best = d; progressAt = now; }
        if (hidden) { progressAt = now; waypoint.clear(); return; }
        boolean[] show = decide(target.mode(), now - startedAt, now - progressAt, now);
        waypoint.update(target.pos(), show[0], now);
        if (show[1] && d > ObjectiveWaypoint.ARRIVED) GuideTrail.draw(p, target.route(), target.pos(), now, show[2]);
    }

    public void clear() { key = null; waypoint.clear(); }
}
