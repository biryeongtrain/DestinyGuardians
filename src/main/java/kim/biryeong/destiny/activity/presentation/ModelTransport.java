package kim.biryeong.destiny.activity.presentation;

import kr.toxicity.model.api.BetterModel;
import kr.toxicity.model.api.animation.AnimationIterator;
import kr.toxicity.model.api.animation.AnimationModifier;
import kr.toxicity.model.api.mod.platform.ModLocation;
import kr.toxicity.model.api.mod.platform.ModPlayer;
import kr.toxicity.model.api.tracker.DummyTracker;
import kr.toxicity.model.api.tracker.TrackerModifier;
import kr.toxicity.model.api.tracker.TrackerUpdateAction;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;
import org.joml.Quaterniond;
import java.util.*;

/** Session-owned, noncombat model transport. Caller-supplied hull must include any played clips.
 * Never loads chunks or mutates combat actors. Unloaded/obstructed movement closes the prop.
 */
public final class ModelTransport implements AutoCloseable {
    public record Route(Vec3 start, Vec3 hover, Vec3 exit, float yaw, AABB hull) {
        public Route {
            Objects.requireNonNull(start); Objects.requireNonNull(hover); Objects.requireNonNull(exit); Objects.requireNonNull(hull);
            if (!Float.isFinite(yaw)) throw new IllegalArgumentException("Invalid heading");
            FlightSweep.corridor(hull, List.of(pose(start, yaw), pose(hover, yaw), pose(exit, yaw)));
        }
    }
    private final ServerLevel level;
    private final Route route;
    private final DeliveryTimeline timeline;
    private final DummyTracker tracker;
    private final Map<UUID, ServerPlayer> viewers = new HashMap<>();
    private Vec3 position;
    private boolean closed;
    private ModelTransport(ServerLevel level, Route route, DeliveryTimeline timeline, DummyTracker tracker) {
        this.level = level; this.route = route; this.timeline = timeline; this.tracker = tracker; position = route.start();
    }
    public static Optional<ModelTransport> create(ServerLevel level, String model, Route route,
                                                   int approach, int maxHold, int settle, int departure) {
        var timeline = new DeliveryTimeline(approach, maxHold, settle, departure);
        if (!clearRoute(level, route)) return Optional.empty();
        var renderer = BetterModel.model(model).orElse(null);
        if (renderer == null) return Optional.empty();
        var tracker = renderer.create(location(level, route.start(), route.yaw()),
                TrackerModifier.DEFAULT.toBuilder().sightTrace(false).build(), t -> t.displays().forEach(d -> d.moveDuration(2)));
        return Optional.of(new ModelTransport(level, route, timeline, tracker));
    }
    /** Read-only feasibility check using the same admission corridor as create(). */
    public static boolean clearRoute(ServerLevel level, Route route) {
        return inspectRoute(level, route) == FlightTerrain.Result.CLEAR;
    }
    public static FlightTerrain.Result inspectRoute(ServerLevel level, Route route) {
        for (var box : FlightSweep.corridor(route.hull(), List.of(pose(route.start(), route.yaw()),
                pose(route.hover(), route.yaw()), pose(route.exit(), route.yaw())))) {
            var result = FlightTerrain.inspect(level, box);
            if (result != FlightTerrain.Result.CLEAR) return result;
        }
        return FlightTerrain.Result.CLEAR;
    }
    public void delivered() { timeline.delivered(); }
    public void animate(String clip, boolean loop) {
        if (!closed()) tracker.animate(clip, new AnimationModifier(2, 2,
                loop ? AnimationIterator.Type.LOOP : AnimationIterator.Type.PLAY_ONCE));
    }
    public void brightness(int block, int sky) {
        if (block < 0 || block > 15 || sky < 0 || sky > 15) throw new IllegalArgumentException("Invalid light level");
        if (!closed()) tracker.update(TrackerUpdateAction.brightness(block, sky));
    }
    public Vec3 position() { return position; }
    public boolean closed() { return closed || tracker.isClosed(); }
    public void tick(boolean paused, List<ServerPlayer> audience) {
        if (closed()) { close(); return; }
        timeline.tick(paused);
        if (timeline.phase() == DeliveryTimeline.Phase.CLOSED) { close(); return; }
        Vec3 next = switch (timeline.phase()) {
            case APPROACH -> route.start().lerp(route.hover(), ease(timeline.fraction()));
            case HOLD -> route.hover();
            case DEPART -> route.hover().lerp(route.exit(), ease(timeline.fraction()));
            case CLOSED -> position;
        };
        if (!paused) {
            var sweep = FlightSweep.between(route.hull(), pose(position, route.yaw()), pose(next, route.yaw()));
            if (FlightTerrain.inspect(level, sweep) != FlightTerrain.Result.CLEAR) { close(); return; }
            tracker.location(location(level, next, route.yaw())); position = next;
        }
        var current = new HashMap<UUID, ServerPlayer>();
        for (var p : audience) if (!p.hasDisconnected() && p.level() == level && p.connection.hasClientLoaded()) current.put(p.getUUID(), p);
        for (var p : List.copyOf(viewers.values())) if (current.get(p.getUUID()) != p) {
            tracker.remove(ModPlayer.of(p.connection)); viewers.remove(p.getUUID());
        }
        for (var p : current.values()) if (!viewers.containsKey(p.getUUID())) {
            tracker.spawn(ModPlayer.of(p.connection)); viewers.put(p.getUUID(), p);
        }
    }
    private static double ease(double t) { return t * t * (3 - 2 * t); }
    private static FlightSweep.Pose pose(Vec3 position, float yaw) {
        return new FlightSweep.Pose(position, new Quaterniond().rotationY(Math.toRadians(-yaw)));
    }
    private static ModLocation location(ServerLevel level, Vec3 at, float yaw) { return ModLocation.of(level, at.x, at.y, at.z, 0, yaw); }
    @Override public void close() {
        if (closed) return; closed = true; timeline.close(); viewers.clear(); tracker.close();
    }
}
