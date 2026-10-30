package kim.biryeong.destiny.crucible;

import kim.biryeong.destiny.DestinyGuardians;
import kim.biryeong.destiny.fx.PlayerAnimations;
import kim.biryeong.minigamelib.cinematic.CameraViews;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.phys.Vec3;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.phys.shapes.CollisionContext;
import net.minecraft.core.Direction;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.HashSet;
import java.util.Set;
import java.util.Objects;
import java.util.UUID;

/**
 * One INTRO phase, owned and ticked by CrucibleRuntime on the server thread.
 * begin once per match, start each viewer, tick once per server tick, close on
 * phase exit. Call cancel(player) BEFORE leaving the match or teleporting away.
 * Runtime freezes participants and rejects gameplay actions for the entire phase.
 *
 * These are six Trials-scene candidate motions, NOT a recovered general 6v6
 * cinematic. Shots, stage locations, spacing and clip-to-player assignment are
 * authored. Runtime places up to three representatives per team from actorPlacements(),
 * BEFORE starting cameras, and restores them on exit. ALL roster entries remain
 * available. This class never changes player position, game mode or inventory.
 */
public final class CrucibleIntro implements AutoCloseable {
    public static final int MAP_TICKS = 100;
    public static final double BODY_SECONDS = 445.0 / 30.0;
    public static final int BODY_TICKS = 298; // ceil(14.83333 * 20) + one entry tick
    public static final int RECOMMENDED_PHASE_TICKS = 400;
    public static final int REPRESENTATIVES_PER_TEAM = 3;
    public static final List<String> CLIPS = List.of(
            "h15_intro_80b7bbc8", "h15_intro_80b7bbca", "h15_intro_80b7bbcc",
            "h15_intro_80b7bbd0", "h15_intro_80b7bbd4", "h15_intro_80b7bbdb");
    private static final Map<UUID, CrucibleIntro> ACTOR_OWNERS = new HashMap<>();

    public record Shot(Vec3 from, Vec3 to, Vec3 lookAt, int ticks) {
        public Shot {
            finite(from); finite(to); finite(lookAt);
            if (ticks < 1) throw new IllegalArgumentException("Shot ticks must be positive");
        }
    }

    public record Stage(Vec3 alphaOrigin, Vec3 bravoOrigin, float alphaYaw, float bravoYaw) {
        public Stage {
            finite(alphaOrigin); finite(bravoOrigin);
            if (!Float.isFinite(alphaYaw) || !Float.isFinite(bravoYaw))
                throw new IllegalArgumentException("Stage yaw must be finite");
        }
    }

    /** Compact, grounded rows on the inspected Javelin-4 courtyard. Y is resolved from real collision. */
    public static Stage confrontationStage(ServerLevel level) {
        Vec3 alpha = grounded(level, new Vec3(33.5, 85, 85.5));
        Vec3 bravo = grounded(level, new Vec3(39.5, 85, 85.5));
        return new Stage(alpha, bravo, facing(alpha, bravo), facing(bravo, alpha));
    }

    public static List<Shot> confrontationShots(ServerLevel level, Stage stage) {
        Vec3 center = stage.alphaOrigin().add(stage.bravoOrigin()).scale(.5);
        Vec3 target = center.add(0, 0.6, 0);
        Vec3 wide = center.add(0, 3.4, 10);
        Vec3 alphaEye = stage.alphaOrigin().add(0, 0.7, 0), bravoEye = stage.bravoOrigin().add(0, 0.7, 0);
        // Destiny-style reveal: high establishing crane that descends into the face-off, then slow push-ins on each
        // side and a final pull-back to the wide. Moves fall back to a static frame when an endpoint is blocked.
        List<Shot> result = List.of(
                safe(level, center.add(0, 9, 22), wide, target, 130),
                safe(level, center.add(5, 3.0, 9), center.add(3, 3.4, 6.5), alphaEye, 50),
                safe(level, center.add(-5, 3.0, 9), center.add(-3, 3.4, 6.5), bravoEye, 50),
                safe(level, wide, center.add(0, 4.2, 13), target, 70));
        for (Shot shot : result) {
            if (!level.noBlockCollision(null, new AABB(shot.from(), shot.from()).inflate(.4))
                    || !level.noBlockCollision(null, new AABB(shot.to(), shot.to()).inflate(.4)))
                throw new IllegalStateException("Intro camera near plane intersects terrain");
            if (level.clip(new ClipContext(shot.from(), shot.lookAt(), ClipContext.Block.COLLIDER,
                    ClipContext.Fluid.NONE, CollisionContext.empty())).getType() != HitResult.Type.MISS)
                throw new IllegalStateException("Intro camera sightline intersects terrain");
        }
        return result;
    }

    private static Shot safe(ServerLevel level, Vec3 from, Vec3 to, Vec3 lookAt, int ticks) {
        Vec3 mid = from.add(to).scale(.5);
        for (Vec3 p : new Vec3[]{from, mid, to}) {
            if (!level.noBlockCollision(null, new AABB(p, p).inflate(.4))
                    || level.clip(new ClipContext(p, lookAt, ClipContext.Block.COLLIDER, ClipContext.Fluid.NONE,
                    CollisionContext.empty())).getType() != HitResult.Type.MISS)
                return new Shot(to, to, lookAt, ticks);
        }
        return new Shot(from, to, lookAt, ticks);
    }

    private static float facing(Vec3 from, Vec3 to) {
        Vec3 direction = to.subtract(from);
        return (float) Math.toDegrees(Math.atan2(-direction.x, direction.z));
    }

    private static Vec3 grounded(ServerLevel level, Vec3 point) {
        var hit = level.clip(new ClipContext(point.add(0, .75, 0), point.add(0, -1, 0),
                ClipContext.Block.COLLIDER, ClipContext.Fluid.NONE, CollisionContext.empty()));
        if (hit.getType() != HitResult.Type.BLOCK || hit.getDirection() != Direction.UP)
            throw new IllegalStateException("Intro actor has no supporting floor");
        Vec3 feet = new Vec3(point.x, hit.getLocation().y + .02, point.z);
        if (!level.noBlockCollision(null, new AABB(feet.x - .4, feet.y, feet.z - .4,
                feet.x + .4, feet.y + 2.2, feet.z + .4)))
            throw new IllegalStateException("Intro actor intersects terrain");
        return feet;
    }

    /** Complete participant snapshot for Runtime HUD/roster, independent of actor budget. */
    public record Participant(UUID id, String name) { }

    /** Runtime adapter must preserve real game mode/inventory and restore its own camera.
     * If using CameraViews, Runtime must also route BetterModel packets through the
     * cinematic filter. An ordinary CameraViews.open alone does NOT do that.
     * close must be idempotent and must not close a newer foreign camera session.
     */
    public interface Camera extends AutoCloseable {
        void move(Vec3 position, float yaw, float pitch, boolean cut);
        boolean closed();
        /** Chunk readiness, not just a successful open/respawn packet. */
        default boolean ready() { return !closed(); }
        /** Carrier must be paired before its BetterModel passenger displays are resent. */
        default boolean tracksActor(ServerPlayer actor) { return ready(); }
        @Override void close();
    }

    @FunctionalInterface
    public interface CameraFactory {
        Camera open(ServerPlayer viewer, ServerLevel level, Vec3 position, float yaw, float pitch);
    }

    /** PlayerAnimations owns the exact tracker; this class owns WHEN each audience
     * pair needs a snapshot. Implementations must not call play/animate/prime or
     * advance the clock. sync returns true only after a current-pose spawn/resend
     * was submitted; it is NOT a client acknowledgement. Both methods run inside
     * CameraViews.sending. remove must affect only this actor's owned intro tracker.
     */
    public interface ActorAudience {
        boolean sync(ServerPlayer actor, ServerPlayer viewer, String expectedClip);
        void remove(ServerPlayer actor, ServerPlayer viewer, String expectedClip);
    }

    /** Authored representative staging plan; Runtime owns applying/restoring it. */
    public record ActorPlacement(ServerPlayer player, Vec3 position, float yaw, String animation) { }
    private static final class Actor {
        final ServerPlayer player;
        final ActorPlacement placement;
        final String clip;
        boolean playing;
        Actor(ActorPlacement placement) {
            this.placement = placement;
            this.player = placement.player();
            this.clip = placement.animation();
        }
    }
    private static final class Viewer {
        final ServerPlayer player;
        final ServerLevel originLevel;
        final Camera camera;
        int lastShot = -1;
        final Set<UUID> syncedActors = new HashSet<>();
        Viewer(ServerPlayer player, Camera camera) {
            this.player = player;
            this.originLevel = player.level();
            this.camera = camera;
        }
    }
    private record ViewPose(Vec3 position, float yaw, float pitch, int shot) { }

    private final MinecraftServer server;
    private final ServerLevel level;
    private final List<Participant> alpha;
    private final List<Participant> bravo;
    private final List<Shot> shots;
    private final CameraFactory cameras;
    private final ActorAudience audience;
    private final Map<UUID, Actor> actors = new LinkedHashMap<>();
    private final Map<UUID, Viewer> viewers = new LinkedHashMap<>();
    private final int startedAt;
    private int lastTick = Integer.MIN_VALUE;
    private int bodyStartedAt = -1;
    private boolean closed;

    private CrucibleIntro(List<ServerPlayer> alpha, List<ServerPlayer> bravo, ServerLevel level,
                          List<Shot> shots, Stage stage, CameraFactory cameras, ActorAudience audience) {
        this.level = Objects.requireNonNull(level);
        this.server = level.getServer();
        requireThread();
        this.shots = List.copyOf(shots);
        this.cameras = Objects.requireNonNull(cameras);
        this.audience = Objects.requireNonNull(audience);
        Objects.requireNonNull(stage);
        if (shots.isEmpty()) throw new IllegalArgumentException("At least one authored camera shot required");
        long total = this.shots.stream().mapToLong(Shot::ticks).sum();
        if (total < MAP_TICKS || total > Integer.MAX_VALUE)
            throw new IllegalArgumentException("Shots must cover at least the 100 tick map lead");
        for (Shot shot : this.shots) {
            inWorld(shot.from()); inWorld(shot.to());
        }
        List<ServerPlayer> a = List.copyOf(alpha), b = List.copyOf(bravo);
        var seen = new java.util.HashSet<UUID>();
        for (ServerPlayer player : concat(a, b)) {
            if (!seen.add(player.getUUID())) throw new IllegalArgumentException("Duplicate participant " + player.getUUID());
            if (player.level().getServer() != server) throw new IllegalArgumentException("Participant belongs to another server");
        }
        this.alpha = roster(a);
        this.bravo = roster(b);
        this.startedAt = server.getTickCount();
        try {
            // Only plan here. Runtime applies these positions BEFORE opening cameras.
            stage(a, stage.alphaOrigin(), stage.alphaYaw(), 0);
            stage(b, stage.bravoOrigin(), stage.bravoYaw(), 3);
        } catch (RuntimeException | LinkageError error) {
            close();
            throw error;
        }
    }

    /** Create one shared cast. Calling begin for each viewer would create competing casts.
     * Runtime must stage actorPlacements() before calling start(viewer).
     */
    public static CrucibleIntro begin(List<ServerPlayer> alpha, List<ServerPlayer> bravo, ServerLevel level,
                                      List<Shot> shots, Stage stage, CameraFactory cameras, ActorAudience audience) {
        return new CrucibleIntro(alpha, bravo, level, shots, stage, cameras, audience);
    }

    /** Standard packet-only view adapter. Runtime must still integrate BetterModel packet
     * routing and owner visibility as documented above; this never sets real spectator mode.
     */
    public static CameraFactory cameraViews() {
        return (viewer, level, position, yaw, pitch) -> {
            var owned = CameraViews.open(viewer, level, position, yaw, pitch);
            return new Camera() {
                @Override public void move(Vec3 next, float nextYaw, float nextPitch, boolean cut) {
                    if (closed()) throw new IllegalStateException("Intro camera ownership lost");
                    owned.move(level, next, nextYaw, nextPitch, cut);
                }
                @Override public boolean closed() {
                    return owned.closed() || CameraViews.get(viewer) != owned;
                }
                @Override public boolean ready() { return !closed() && owned.ready(); }
                @Override public boolean tracksActor(ServerPlayer actor) {
                    return ready() && actor.level() == level && owned.tracks(actor.chunkPosition());
                }
                @Override public void close() {
                    if (CameraViews.get(viewer) == owned) owned.close();
                }
            };
        };
    }

    /** All participants/observers may join or rejoin at the current time; the cast never restarts. */
    public boolean start(ServerPlayer viewer) {
        requireThread();
        if (closed || !valid(viewer) || viewer.level() != level) return false;
        Viewer existing = viewers.get(viewer.getUUID());
        if (existing != null) return existing.player == viewer && !existing.camera.closed();
        if (CameraViews.get(viewer) != null || viewer.getCamera() != viewer) return false;
        ViewPose pose = cameraPose(elapsedTicks());
        Camera camera = null;
        try {
            camera = Objects.requireNonNull(cameras.open(viewer, level, pose.position(), pose.yaw(), pose.pitch()));
            if (camera.closed()) { camera.close(); return false; }
            Viewer state = new Viewer(viewer, camera);
            state.lastShot = pose.shot();
            // Register FIRST: Runtime.viewingIntro must be true when the audience
            // bridge refreshes owner visibility and the per-viewer sight filter.
            viewers.put(viewer.getUUID(), state);
            syncAudience(state);
            return true;
        } catch (RuntimeException | LinkageError error) {
            Viewer registered = viewers.get(viewer.getUUID());
            if (registered != null && registered.player == viewer && registered.camera == camera)
                dropViewer(registered);
            else if (camera != null) closeCamera(camera);
            warn("camera open", error);
            return false;
        }
    }

    /** Does not tick PlayerAnimations or CameraViews; their existing global clocks remain sole owners. */
    public void tick() {
        requireThread();
        if (closed || lastTick == server.getTickCount()) return;
        lastTick = server.getTickCount();
        for (Viewer viewer : List.copyOf(viewers.values())) {
            if (!valid(viewer.player) || viewer.player.level() != viewer.originLevel || viewer.camera.closed()) {
                cancel(viewer.player);
                continue;
            }
            try {
                ViewPose pose = cameraPose(elapsedTicks());
                boolean cut = pose.shot() != viewer.lastShot;
                if (cut) viewer.syncedActors.clear();
                viewer.camera.move(pose.position(), pose.yaw(), pose.pitch(), cut);
                viewer.lastShot = pose.shot();
            } catch (RuntimeException | LinkageError error) {
                warn("camera tick", error);
                cancel(viewer.player);
            }
        }
        for (Actor actor : List.copyOf(actors.values())) {
            if (!valid(actor.player) || actor.player.level() != level || actor.player.isSpectator())
                cancel(actor.player);
            else if (actor.playing && !actor.clip.equals(PlayerAnimations.activeClip(actor.player)))
                releaseActor(actor); // A foreign replacement is never stopped/restarted.
        }
        if (bodyStartedAt < 0 && elapsedTicks() >= MAP_TICKS) {
            bodyStartedAt = server.getTickCount();
            for (Actor actor : List.copyOf(actors.values())) {
                try {
                    // A foreign animation acquired during map lead must never be stopped.
                    if (!PlayerAnimations.isPlaying(actor.player)) {
                        // Tracker creation and initial animation packets must reach viewers
                        // whose CameraViews session filters ordinary world packets.
                        CameraViews.sending(() -> actor.playing = PlayerAnimations.playIntroInPlace(actor.player, actor.clip));
                    }
                    if (!actor.playing) releaseActor(actor);
                } catch (RuntimeException | LinkageError error) {
                    warn("body start", error);
                    releaseActor(actor);
                }
            }
        }
        if (bodyStartedAt >= 0 && server.getTickCount() - bodyStartedAt >= BODY_TICKS) {
            close();
            return;
        }
        // Covers initial cast, camera cuts/chunk reload, and every late viewer.
        // Every viewer gets all ready actor carriers; no audience-count cap.
        for (Viewer viewer : List.copyOf(viewers.values())) syncAudience(viewer);
    }

    /** Viewer death/disconnect/leave also relinquishes that player's representative slot. */
    public void cancel(ServerPlayer player) {
        requireThread();
        Viewer viewer = viewers.get(player.getUUID());
        Actor actor = actors.get(player.getUUID());
        if ((viewer != null && viewer.player != player) || (actor != null && actor.player != player)) return;
        if (viewer != null) dropViewer(viewer);
        if (actor != null) releaseActor(actor);
    }

    @Override public void close() {
        requireThread();
        if (closed) return;
        closed = true;
        // Restore camera routing before Runtime teleports participants to spawn.
        for (Viewer viewer : List.copyOf(viewers.values())) dropViewer(viewer);
        for (Actor actor : List.copyOf(actors.values())) releaseActor(actor);
    }

    /** Runtime phase transition alias. Idempotent; never resets a live phase. */
    public void cancelAll() { close(); }

    public boolean closed() { return closed; }
    public int elapsedTicks() { return Math.max(0, server.getTickCount() - startedAt); }
    public List<Participant> alpha() { return alpha; }
    public List<Participant> bravo() { return bravo; }
    public List<UUID> representatives() { return List.copyOf(actors.keySet()); }
    public int viewerCount() { return viewers.size(); }
    /** Runtime can expose this to PlayerAnimations owner-visibility/packet routing hooks. */
    public boolean viewing(ServerPlayer player) {
        Viewer view = viewers.get(player.getUUID());
        return !closed && view != null && view.player == player && !view.camera.closed();
    }
    public List<ActorPlacement> actorPlacements() {
        return actors.values().stream().map(a -> a.placement).toList();
    }

    private void stage(List<ServerPlayer> team, Vec3 origin, float yaw, int clipOffset) {
        List<ServerPlayer> selected = team.stream().filter(p -> valid(p) && p.level() == level && !p.isSpectator()
                && !p.isPassenger() && !p.isSleeping() && !PlayerAnimations.isPlaying(p)
                && CameraViews.get(p) == null && p.getCamera() == p && !ACTOR_OWNERS.containsKey(p.getUUID()))
                .limit(REPRESENTATIVES_PER_TEAM).toList();
        double radians = Math.toRadians(yaw);
        Vec3 right = new Vec3(Math.cos(radians), 0, Math.sin(radians));
        for (int i = 0; i < selected.size(); i++) {
            ServerPlayer player = selected.get(i);
            // First participant stays in the centre even in 1v1 or with an uneven roster.
            int lane = i == 0 ? 0 : i == 1 ? -1 : 1;
            Vec3 position = grounded(level, origin.add(right.scale(lane * 3.2)));
            inWorld(position);
            // Pair matching source motions across the gap, rather than unrelated first clips.
            int clip = clipOffset == 0 ? new int[]{1, 0, 2}[i] : new int[]{4, 5, 3}[i];
            Actor actor = new Actor(new ActorPlacement(player, position, yaw, CLIPS.get(clip)));
            actors.put(player.getUUID(), actor);
            ACTOR_OWNERS.put(player.getUUID(), this);
        }
    }

    private void syncAudience(Viewer viewer) {
        if (closed || viewers.get(viewer.player.getUUID()) != viewer) return;
        if (!viewer.camera.ready()) {
            viewer.syncedActors.clear();
            return;
        }
        for (Actor actor : List.copyOf(actors.values())) {
            UUID actorId = actor.player.getUUID();
            if (!actor.playing || !actor.clip.equals(PlayerAnimations.activeClip(actor.player))) continue;
            if (!viewer.camera.tracksActor(actor.player)) {
                viewer.syncedActors.remove(actorId);
                continue;
            }
            if (viewer.syncedActors.contains(actorId)) continue;
            try {
                boolean[] submitted = {false};
                CameraViews.sending(() -> submitted[0] = audience.sync(actor.player, viewer.player, actor.clip));
                if (submitted[0]) viewer.syncedActors.add(actorId);
            } catch (RuntimeException | LinkageError error) {
                warn("audience snapshot", error);
                // Per-pair failure never restarts/stops the shared cast or denies other viewers.
            }
        }
    }

    private void dropViewer(Viewer viewer) {
        if (!viewers.remove(viewer.player.getUUID(), viewer)) return;
        // Detach before restoring ordinary camera routing. A failed sync may still
        // have registered a partial pair, so remove all currently owned actor pairs.
        for (Actor actor : List.copyOf(actors.values())) {
            try { CameraViews.sending(() -> audience.remove(actor.player, viewer.player, actor.clip)); }
            catch (RuntimeException | LinkageError error) { warn("audience detach", error); }
        }
        viewer.syncedActors.clear();
        closeCamera(viewer.camera);
    }

    private void releaseActor(Actor actor) {
        UUID id = actor.player.getUUID();
        if (!actors.remove(id, actor) || !ACTOR_OWNERS.remove(id, this)) return;
        for (Viewer viewer : viewers.values()) viewer.syncedActors.remove(id);
        try {
            if (actor.playing && actor.clip.equals(PlayerAnimations.activeClip(actor.player)))
                CameraViews.sending(() -> PlayerAnimations.stop(actor.player));
        } catch (RuntimeException | LinkageError error) { warn("body close", error); }
    }

    private ViewPose cameraPose(int tick) {
        int remaining = tick;
        for (int i = 0; i < shots.size(); i++) {
            Shot shot = shots.get(i);
            if (remaining < shot.ticks() || i == shots.size() - 1) {
                double t = Math.clamp(remaining / (double) Math.max(1, shot.ticks() - 1), 0, 1);
                Vec3 position = shot.from().add(shot.to().subtract(shot.from()).scale(t));
                Vec3 direction = shot.lookAt().subtract(position);
                float yaw = (float) Math.toDegrees(Math.atan2(-direction.x, direction.z));
                float pitch = (float) -Math.toDegrees(Math.atan2(direction.y, Math.hypot(direction.x, direction.z)));
                return new ViewPose(position, yaw, pitch, i);
            }
            remaining -= shot.ticks();
        }
        throw new IllegalStateException("No shots");
    }

    private void inWorld(Vec3 position) {
        finite(position);
        if (position.y < level.getMinY() || position.y >= level.getMaxY()
                || !level.getWorldBorder().isWithinBounds(position))
            throw new IllegalArgumentException("Authored stage/camera position outside world");
    }
    private static void finite(Vec3 position) {
        Objects.requireNonNull(position);
        if (!Double.isFinite(position.x) || !Double.isFinite(position.y) || !Double.isFinite(position.z))
            throw new IllegalArgumentException("Position must be finite");
    }
    private static boolean valid(ServerPlayer player) {
        return !player.hasDisconnected() && !player.isRemoved() && player.isAlive();
    }
    private void requireThread() {
        if (!server.isSameThread()) throw new IllegalStateException("CrucibleIntro requires server thread");
    }
    private static List<Participant> roster(List<ServerPlayer> players) {
        return players.stream().map(p -> new Participant(p.getUUID(), p.getGameProfile().name())).toList();
    }
    private static List<ServerPlayer> concat(List<ServerPlayer> alpha, List<ServerPlayer> bravo) {
        List<ServerPlayer> result = new ArrayList<>(alpha); result.addAll(bravo); return result;
    }
    private static void closeCamera(Camera camera) {
        try { camera.close(); }
        catch (RuntimeException | LinkageError error) { warn("camera close", error); }
    }
    private static void warn(String operation, Throwable error) {
        DestinyGuardians.LOGGER.warn("Crucible intro {} failed: {}", operation, error.toString());
    }
}
