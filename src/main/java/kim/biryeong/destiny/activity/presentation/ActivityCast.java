package kim.biryeong.destiny.activity.presentation;

import kim.biryeong.destiny.DestinyGuardians;
import kim.biryeong.destiny.crucible.CrucibleIntro;
import kim.biryeong.destiny.fx.PlayerAnimations;
import kim.biryeong.minigamelib.cinematic.CameraViews;
import net.minecraft.core.Direction;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;
import net.minecraft.world.phys.shapes.CollisionContext;

import java.util.*;

/**
 * Shared staged player cast for strike/dungeon/raid briefings and intros: each fireteam member plays an
 * authored {@code h15_intro_*} body clip at a placement while every viewer watches through a CameraViews
 * camera. Generalised from the Crucible intro cast; the activity owns placement teleports, freezing,
 * restore and phase timing. One instance per activity scene; there is no global mutable cast.
 */
public final class ActivityCast implements AutoCloseable {
    private static final Set<ActivityCast> LIVE = Collections.newSetFromMap(new IdentityHashMap<>());
    private static final Map<UUID, ActivityCast> ACTOR_OWNERS = new HashMap<>();

    private static final class Actor {
        final CrucibleIntro.ActorPlacement placement; final int revealTick; boolean playing, revealed, hidOwnBody, wasInvisible;
        Actor(CrucibleIntro.ActorPlacement placement, int revealTick) { this.placement = placement; this.revealTick = revealTick; }
        ServerPlayer player() { return placement.player(); }
    }
    private static final class Viewer {
        final ServerPlayer player; final ServerLevel originLevel; final CrucibleIntro.Camera camera;
        int lastShot = -1; final Set<UUID> synced = new HashSet<>();
        Viewer(ServerPlayer player, CrucibleIntro.Camera camera) { this.player = player; originLevel = player.level(); this.camera = camera; }
    }

    private final MinecraftServer server;
    private final ServerLevel level;
    private final List<CrucibleIntro.Shot> shots;
    private final CrucibleIntro.CameraFactory cameras;
    private final CrucibleIntro.ActorAudience audience;
    private final int leadTicks, bodyTicks, startedAt;
    private final Map<UUID, Actor> actors = new LinkedHashMap<>();
    private final Map<UUID, Viewer> viewers = new LinkedHashMap<>();
    private int lastTick = Integer.MIN_VALUE, bodyStartedAt = -1;
    private boolean closed;

    private ActivityCast(ServerLevel level, List<CrucibleIntro.ActorPlacement> placements, List<Integer> reveals, List<CrucibleIntro.Shot> shots,
                         int leadTicks, int bodyTicks, CrucibleIntro.CameraFactory cameras, CrucibleIntro.ActorAudience audience) {
        this.level = Objects.requireNonNull(level); server = level.getServer(); requireThread();
        this.shots = List.copyOf(shots); this.cameras = Objects.requireNonNull(cameras); this.audience = Objects.requireNonNull(audience);
        if (this.shots.isEmpty()) throw new IllegalArgumentException("At least one camera shot required");
        if (leadTicks < 0 || bodyTicks < 1) throw new IllegalArgumentException("Invalid cast timing");
        this.leadTicks = leadTicks; this.bodyTicks = bodyTicks; startedAt = server.getTickCount();
        for (var shot : this.shots) { inWorld(shot.from()); inWorld(shot.to()); }
        if (reveals.size() != placements.size()) throw new IllegalArgumentException("One reveal delay per actor");
        for (int index = 0; index < placements.size(); index++) {
            var placement = placements.get(index); int reveal = reveals.get(index);
            if (reveal < 0) throw new IllegalArgumentException("Negative reveal delay");
            ServerPlayer p = placement.player();
            if (p.level() != level || actors.containsKey(p.getUUID())) throw new IllegalArgumentException("Invalid cast member " + p.getUUID());
            if (placement.animation() == null || !placement.animation().startsWith("h15_intro_"))
                throw new IllegalArgumentException("Cast clips must be staged intro clips: " + placement.animation());
            inWorld(placement.position());
            if (ACTOR_OWNERS.containsKey(p.getUUID()) || PlayerAnimations.isPlaying(p) || CameraViews.get(p) != null) continue;
            var actor = new Actor(placement, leadTicks + reveal);
            // Not yet transmatted in: the ordinary body must not stand on stage before its arrival.
            actor.wasInvisible = p.isInvisible(); p.setInvisible(true); actor.hidOwnBody = true;
            actors.put(p.getUUID(), actor); ACTOR_OWNERS.put(p.getUUID(), this);
        }
        LIVE.add(this);
    }

    /**
     * Plan only. The activity teleports actors to {@link #actorPlacements()} BEFORE calling {@link #start}.
     * {@code reveals[i]} delays actor i's clip after the lead; until then the camera filter keeps its body
     * unseen, and a {@link TransmatArrival} materialises it on its reveal tick.
     */
    public static ActivityCast begin(ServerLevel level, List<CrucibleIntro.ActorPlacement> placements, List<Integer> reveals,
                                     List<CrucibleIntro.Shot> shots, int leadTicks, int bodyTicks,
                                     CrucibleIntro.CameraFactory cameras, CrucibleIntro.ActorAudience audience) {
        return new ActivityCast(level, placements, reveals, shots, leadTicks, bodyTicks, cameras, audience);
    }
    /** Standard player-animation audience: per-viewer intro tracker snapshots. */
    public static CrucibleIntro.ActorAudience playerAnimations() {
        return new CrucibleIntro.ActorAudience() {
            @Override public boolean sync(ServerPlayer actor, ServerPlayer viewer, String clip) { return PlayerAnimations.syncIntroViewer(actor, viewer, clip); }
            @Override public void remove(ServerPlayer actor, ServerPlayer viewer, String clip) { PlayerAnimations.removeIntroViewer(actor, viewer, clip); }
        };
    }
    /** True while {@code player} watches any live cast; PlayerAnimations routes intro trackers by this. */
    public static boolean viewing(ServerPlayer player) {
        for (var cast : LIVE) if (cast.viewingThis(player)) return true;
        return false;
    }

    public boolean start(ServerPlayer viewer) {
        requireThread();
        if (closed || !valid(viewer) || viewer.level() != level) return false;
        Viewer existing = viewers.get(viewer.getUUID());
        if (existing != null) return existing.player == viewer && !existing.camera.closed();
        if (CameraViews.get(viewer) != null || viewer.getCamera() != viewer) return false;
        var pose = pose(elapsedTicks());
        CrucibleIntro.Camera camera = null;
        try {
            camera = Objects.requireNonNull(cameras.open(viewer, level, pose.position, pose.yaw, pose.pitch));
            if (camera.closed()) { camera.close(); return false; }
            var state = new Viewer(viewer, camera); state.lastShot = pose.shot;
            viewers.put(viewer.getUUID(), state); // register first: viewing() must be true during audience sync
            sync(state);
            return true;
        } catch (RuntimeException | LinkageError error) {
            var registered = viewers.get(viewer.getUUID());
            if (registered != null && registered.camera == camera) drop(registered); else if (camera != null) closeCamera(camera);
            warn("camera open", error); return false;
        }
    }

    /** Once per server tick inside {@code CameraViews.sending}; never ticks PlayerAnimations or CameraViews clocks. */
    public void tick() {
        requireThread();
        if (closed || lastTick == server.getTickCount()) return;
        lastTick = server.getTickCount();
        for (var viewer : List.copyOf(viewers.values())) {
            if (!valid(viewer.player) || viewer.player.level() != viewer.originLevel || viewer.camera.closed()) { cancel(viewer.player); continue; }
            try {
                var pose = pose(elapsedTicks()); boolean cut = pose.shot != viewer.lastShot;
                if (cut) viewer.synced.clear();
                viewer.camera.move(pose.position, pose.yaw, pose.pitch, cut); viewer.lastShot = pose.shot;
                if (pose.shot + 1 < shots.size()) viewer.camera.preload(shots.get(pose.shot + 1).from());
            } catch (RuntimeException | LinkageError error) { warn("camera tick", error); cancel(viewer.player); }
        }
        for (var actor : List.copyOf(actors.values())) {
            var p = actor.player();
            if (!valid(p) || p.level() != level || p.isSpectator()) cancel(p);
            else if (actor.playing && !actor.placement.animation().equals(PlayerAnimations.activeClip(p))) release(actor);
        }
        if (bodyStartedAt < 0 && elapsedTicks() >= leadTicks) bodyStartedAt = server.getTickCount() - (elapsedTicks() - leadTicks);
        int elapsed = elapsedTicks();
        var audienceList = viewers.values().stream().map(v -> v.player).toList();
        for (var actor : List.copyOf(actors.values())) {
            if (actor.revealed) continue;
            int until = actor.revealTick - elapsed;
            if (until <= TransmatArrival.LEAD_TICKS) {
                try { TransmatArrival.tick(level, actor.placement.position(), Math.max(0, until), audienceList); }
                catch (RuntimeException | LinkageError error) { warn("transmat", error); }
            }
            if (until > 0) continue;
            actor.revealed = true; unhide(actor);
            try {
                // A foreign animation acquired during the lead is never stopped.
                if (!PlayerAnimations.isPlaying(actor.player()))
                    CameraViews.sending(() -> {
                        actor.playing = PlayerAnimations.playIntroInPlace(actor.player(), actor.placement.animation());
                        // Staged poses hold the Guardian's own weapon model on the rig hand (visual only; the
                        // real slot stays stowed so no first-person/vanilla held item is drawn).
                        if (actor.playing) {
                            var weapon = CinematicHands.heldBeforeStow(actor.player());
                            if (!weapon.isEmpty()) PlayerAnimations.superItem(actor.player(), weapon);
                        }
                    });
                if (!actor.playing) release(actor);
            } catch (RuntimeException | LinkageError error) { warn("body start", error); release(actor); }
        }
        if (bodyStartedAt >= 0 && server.getTickCount() - bodyStartedAt >= bodyTicks) { close(); return; }
        for (var viewer : List.copyOf(viewers.values())) sync(viewer);
    }

    public void cancel(ServerPlayer player) {
        requireThread();
        var viewer = viewers.get(player.getUUID()); var actor = actors.get(player.getUUID());
        if ((viewer != null && viewer.player != player) || (actor != null && actor.player() != player)) return;
        if (viewer != null) drop(viewer);
        if (actor != null) release(actor);
    }
    @Override public void close() {
        requireThread();
        if (closed) return;
        closed = true;
        for (var viewer : List.copyOf(viewers.values())) drop(viewer);
        for (var actor : List.copyOf(actors.values())) release(actor);
        LIVE.remove(this);
    }
    public boolean closed() { return closed; }
    public int elapsedTicks() { return Math.max(0, server.getTickCount() - startedAt); }
    public List<CrucibleIntro.ActorPlacement> actorPlacements() { return actors.values().stream().map(a -> a.placement).toList(); }
    public boolean viewingThis(ServerPlayer player) {
        var v = viewers.get(player.getUUID()); return !closed && v != null && v.player == player && !v.camera.closed();
    }
    public boolean acting(ServerPlayer player) { var a = actors.get(player.getUUID()); return !closed && a != null && a.player() == player; }

    /** Feet on the real collision floor below {@code point}, or empty when unsupported/obstructed. */
    public static Optional<Vec3> grounded(ServerLevel level, Vec3 point) {
        var hit = level.clip(new ClipContext(point.add(0, 1.5, 0), point.add(0, -3, 0), ClipContext.Block.COLLIDER,
                ClipContext.Fluid.NONE, CollisionContext.empty()));
        if (hit.getType() != HitResult.Type.BLOCK || hit.getDirection() != Direction.UP) return Optional.empty();
        Vec3 feet = new Vec3(point.x, hit.getLocation().y + .02, point.z);
        if (!level.noBlockCollision(null, new AABB(feet.x - .35, feet.y, feet.z - .35, feet.x + .35, feet.y + 1.9, feet.z + .35)))
            return Optional.empty();
        return Optional.of(feet);
    }
    /** Camera point clear of terrain with an unobstructed sightline to {@code target}. */
    public static boolean clearShot(ServerLevel level, Vec3 camera, Vec3 target) {
        return level.noBlockCollision(null, new AABB(camera, camera).inflate(.4))
                && level.clip(new ClipContext(camera, target, ClipContext.Block.COLLIDER, ClipContext.Fluid.NONE,
                CollisionContext.empty())).getType() == HitResult.Type.MISS;
    }

    private record Pose(Vec3 position, float yaw, float pitch, int shot) { }
    private Pose pose(int tick) {
        int remaining = tick;
        for (int i = 0; i < shots.size(); i++) {
            var shot = shots.get(i);
            if (remaining < shot.ticks() || i == shots.size() - 1) {
                double t = Math.clamp(remaining / (double) Math.max(1, shot.ticks() - 1), 0, 1);
                t = t * t * (3 - 2 * t);
                Vec3 position = shot.from().lerp(shot.to(), t), d = shot.lookAt().subtract(position);
                return new Pose(position, (float) Math.toDegrees(Math.atan2(-d.x, d.z)),
                        (float) -Math.toDegrees(Math.atan2(d.y, Math.hypot(d.x, d.z))), i);
            }
            remaining -= shot.ticks();
        }
        throw new IllegalStateException("No shots");
    }
    private void sync(Viewer viewer) {
        if (closed || viewers.get(viewer.player.getUUID()) != viewer) return;
        if (!viewer.camera.ready()) { viewer.synced.clear(); return; }
        for (var actor : List.copyOf(actors.values())) {
            var p = actor.player(); UUID id = p.getUUID(); String clip = actor.placement.animation();
            if (!actor.playing || !clip.equals(PlayerAnimations.activeClip(p))) continue;
            if (!viewer.camera.tracksActor(p)) { viewer.synced.remove(id); continue; }
            if (viewer.synced.contains(id)) continue;
            try {
                boolean[] submitted = {false};
                CameraViews.sending(() -> submitted[0] = audience.sync(p, viewer.player, clip));
                if (submitted[0]) viewer.synced.add(id);
            } catch (RuntimeException | LinkageError error) { warn("audience snapshot", error); }
        }
    }
    private void drop(Viewer viewer) {
        if (!viewers.remove(viewer.player.getUUID(), viewer)) return;
        for (var actor : List.copyOf(actors.values())) {
            try { CameraViews.sending(() -> audience.remove(actor.player(), viewer.player, actor.placement.animation())); }
            catch (RuntimeException | LinkageError error) { warn("audience detach", error); }
        }
        viewer.synced.clear(); closeCamera(viewer.camera);
    }
    private static void unhide(Actor actor) {
        if (!actor.hidOwnBody) return;
        actor.hidOwnBody = false; actor.player().setInvisible(actor.wasInvisible);
    }
    private void release(Actor actor) {
        UUID id = actor.player().getUUID();
        if (!actors.remove(id, actor) || !ACTOR_OWNERS.remove(id, this)) return;
        unhide(actor);
        for (var viewer : viewers.values()) viewer.synced.remove(id);
        try {
            if (actor.playing && actor.placement.animation().equals(PlayerAnimations.activeClip(actor.player())))
                CameraViews.sending(() -> PlayerAnimations.stop(actor.player()));
        } catch (RuntimeException | LinkageError error) { warn("body close", error); }
    }
    private void inWorld(Vec3 p) {
        if (!Double.isFinite(p.x) || !Double.isFinite(p.y) || !Double.isFinite(p.z) || p.y < level.getMinY() || p.y >= level.getMaxY()
                || !level.getWorldBorder().isWithinBounds(p)) throw new IllegalArgumentException("Cast position outside world");
    }
    private static boolean valid(ServerPlayer p) { return !p.hasDisconnected() && !p.isRemoved() && p.isAlive(); }
    private void requireThread() { if (!server.isSameThread()) throw new IllegalStateException("ActivityCast requires server thread"); }
    private static void closeCamera(CrucibleIntro.Camera camera) {
        try { camera.close(); } catch (RuntimeException | LinkageError error) { warn("camera close", error); }
    }
    private static void warn(String operation, Throwable error) { DestinyGuardians.LOGGER.warn("Activity cast {} failed: {}", operation, error.toString()); }
}
