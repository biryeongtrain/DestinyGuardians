package kim.biryeong.destiny.strike.devils;

import kim.biryeong.destiny.campaign.RisingServices;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;
import net.minecraft.world.phys.shapes.CollisionContext;
import java.util.*;

/** Live-world spatial admission. Call on the server thread, immediately before spawning/teleporting.
 * No result means defer/retry; this helper never fabricates a fallback or counts a death.
 * All returned coordinates are world-space entity FEET (including flying actors).
 */
public final class DevilsSpatial {
    public static final double MIN_SPAWN_DISTANCE = 12;
    public record Point(String marker, Vec3 pos, float yaw, boolean visible) { }
    private DevilsSpatial() { }
    /** One bounded, resumable placement search. Owned by a session slot, never shared across generations. */
    public static final class Search {
        private int nextCandidate;
        private long rotation;
        private boolean pending, waiting, transientBlocked;
        public boolean pending() { return pending; }
        public boolean waiting() { return waiting; }
        private void clear() { nextCandidate = 0; pending = waiting = transientBlocked = false; }
    }

    public static boolean flying(DevilsPlan.Kind kind) {
        return switch (kind) { case SHANK, WIZARD, SERVITOR, SEPIKS -> true; default -> false; };
    }

    /** Actual entity dimensions include boss footprints; reservations protect other pending spawns. */
    public static Optional<Point> spawn(ServerLevel level, DevilsPlan.Slot slot, BlockPos origin,
                                        Mob mob, List<ServerPlayer> players, List<AABB> reservations) {
        return spawn(level, slot, origin, mob, players, reservations, ignored -> {});
    }
    public static Optional<Point> spawn(ServerLevel level, DevilsPlan.Slot slot, BlockPos origin,
                                        Mob mob, List<ServerPlayer> players, List<AABB> reservations,
                                        java.util.function.Consumer<String> failure) {
        return spawn(level, slot, origin, mob, players, reservations, new Search(), failure);
    }
    public static Optional<Point> spawn(ServerLevel level, DevilsPlan.Slot slot, BlockPos origin,
                                        Mob mob, List<ServerPlayer> players, List<AABB> reservations,
                                        Search search, java.util.function.Consumer<String> failure) {
        thread(level);
        var targets = players.stream().filter(p -> p.level() == level && p.isAlive() && !p.isSpectator()).toList();
        if (targets.isEmpty()) { search.clear(); failure.accept("no eligible targets"); return Optional.empty(); }
        var positions = targets.stream().map(Entity::position).toList();
        int pathProbes = 0;
        int distanceRejected = 0, collisionRejected = 0, supportRejected = 0, routeRejected = 0;
        var candidates = new ArrayList<>(DevilsMaps.candidates(slot.zone(), slot.anchor(), origin));
        if (candidates.isEmpty()) candidates.add(DevilsMaps.anchor(slot.zone(), slot.anchor(), origin));
        // Spread an eight-member pack across authored candidates; only probe a bounded apron around those platforms.
        if (!search.pending) {
            search.clear();
            search.rotation = slot.index() + level.getGameTime() / 40;
        }
        Collections.rotate(candidates, -Math.floorMod(search.rotation, candidates.size()));
        int candidateIndex = 0;
        var valid = new ArrayList<Point>();
        boolean flying = flying(slot.kind());
        boolean mobileFlyer = slot.kind() == DevilsPlan.Kind.SHANK || slot.kind() == DevilsPlan.Kind.WIZARD;
        // Try distinct authored pads before nearby offsets. Otherwise four blocked
        // offsets at one pad consume the whole navigation budget and starve valid lanes.
        for (double[] offset : slot.ordinary() ? new double[][]{{0,0},{1.5,0},{-1.5,0},{0,1.5},{0,-1.5},{1.5,1.5},{-1.5,-1.5},{1.5,-1.5},{-1.5,1.5}} : new double[][]{{0,0}}) {
          for (var marker : candidates) {
            Vec3 base = marker.pos().add(offset[0], 0, offset[1]);
            boolean groundFlightPad = flying && !"flying".equals(marker.tags().get("role"));
            if (groundFlightPad) base = base.add(0, 2.5, 0);
            // Indoor mobile flyers may hover lower when the ceiling prevents the outdoor height.
            // Explicit flying anchors (including bosses) retain their authored elevation.
            double[] heights = groundFlightPad && slot.ordinary()
                    ? new double[]{0, -.5, -1, -1.5, -2, -2.5}
                    : flying ? new double[]{0} : new double[]{0, .5, 1, -.5, -1};
            for (double dy : heights) {
                int currentCandidate = candidateIndex++;
                if (currentCandidate < search.nextCandidate) continue;
                Vec3 pos = base.add(0, dy, 0);
                AABB body = bodyAt(mob, pos);
                if (!clearTerrain(level, slot.zone(), origin, mob, body)) { collisionRejected++; continue; }
                if (!flying && !supported(level, body)) { supportRejected++; continue; }
                if (mobileFlyer && !flightSupported(level, pos)) { supportRejected++; continue; }
                // Only a geometrically valid pad can wait on transient proximity/occupancy.
                if (!farEnough(pos, positions, MIN_SPAWN_DISTANCE)) {
                    distanceRejected++; search.transientBlocked = true; continue;
                }
                if (occupied(level, mob, body, reservations)) {
                    collisionRejected++; search.transientBlocked = true; continue;
                }
                // Each director tick accepts at most two actors. Bound expensive navigation work too.
                if (pathProbes++ >= 4) {
                    if (!valid.isEmpty()) { search.clear(); return preferHidden(valid); }
                    search.nextCandidate = currentCandidate;
                    search.pending = true;
                    return Optional.empty();
                }
                if (!reachable(level, mob, pos, targets, flying, mobileFlyer)) {
                    routeRejected++;
                    // Stationary flyers test a firing line to current targets, not map connectivity.
                    // Guardians taking cover must not consume placement failures and reset the encounter.
                    if (flying && !mobileFlyer) search.transientBlocked = true;
                    continue;
                }
                boolean visible = targets.stream().anyMatch(p -> line(level, p.getEyePosition(), body.getCenter()));
                Point accepted = new Point(marker.id(), pos, marker.yaw(), visible);
                if (!visible) { search.clear(); return Optional.of(accepted); }
                valid.add(accepted);
                break;
            }
        }
        }
        boolean waiting = valid.isEmpty() && search.transientBlocked;
        search.clear();
        search.waiting = waiting;
        if (valid.isEmpty() && !waiting) failure.accept("candidates exhausted; distance=" + distanceRejected
                + ", collision=" + collisionRejected + ", support=" + supportRejected + ", route=" + routeRejected);
        return preferHidden(valid);
    }

    /** Revalidate the exact warned pad at activation; selecting a different pad needs a new warning. */
    public static boolean recheck(ServerLevel level, DevilsPlan.Slot slot, BlockPos origin, Mob mob,
                                  Vec3 pos, List<ServerPlayer> players, List<AABB> reservations) {
        thread(level);
        var targets = players.stream().filter(p -> p.level()==level && p.isAlive() && !p.isSpectator()).toList();
        var body = bodyAt(mob, pos); boolean flying = flying(slot.kind());
        return !targets.isEmpty() && farEnough(pos, targets.stream().map(Entity::position).toList(), MIN_SPAWN_DISTANCE)
                && clear(level, slot.zone(), origin, mob, body, reservations) && (flying || supported(level, body))
                && (!(slot.kind()==DevilsPlan.Kind.SHANK || slot.kind()==DevilsPlan.Kind.WIZARD) || flightSupported(level, pos))
                && reachable(level, mob, pos, targets, flying,
                    slot.kind()==DevilsPlan.Kind.SHANK || slot.kind()==DevilsPlan.Kind.WIZARD);
    }

    /** Three authored seats; occupied or obstructed seats are refused, never teleported blindly. */
    public static Optional<Point> seat(ServerLevel level, DevilsPlan.Zone zone, BlockPos origin,
                                      Entity player, int seat, List<AABB> reservations) {
        thread(level);
        if (seat < 0 || seat >= DevilsPlan.PLAYERS) throw new IllegalArgumentException("seat must be 0..2");
        var marker = DevilsMaps.anchor(zone, zone.name() + ".IN." + seat, origin);
        for (double dy : new double[]{0, .5, 1, -.5, -1}) {
            Vec3 pos = marker.pos().add(0, dy, 0); AABB box = bodyAt(player, pos);
            if (clear(level, zone, origin, player, box, reservations) && supported(level, box))
                return Optional.of(new Point(marker.id(), pos, marker.yaw(), false));
        }
        return Optional.empty();
    }

    /** Only the four source-derived Sepiks anchors. Caller owns cooldown and telegraph, and rechecks at commit. */
    public static Optional<Point> warp(ServerLevel level, BlockPos origin, Mob sepiks,
                                      List<ServerPlayer> players, List<AABB> reservations) {
        thread(level);
        var valid = new ArrayList<Point>();
        for (int i = 1; i <= 4; i++) {
            var marker = DevilsMaps.anchor(DevilsPlan.Zone.SP, "SP.WARP." + i, origin);
            Vec3 pos = marker.pos();
            if (!warpClear(level, origin, sepiks, pos, players, reservations)) continue;
            valid.add(new Point(marker.id(), pos, marker.yaw(), true));
        }
        return valid.stream().max(Comparator.comparingDouble(p -> p.pos().distanceToSqr(sepiks.position())));
    }

    /** Commit-time validation of the exact authored destination, including newly reserved spawn bodies. */
    public static boolean recheckWarp(ServerLevel level, BlockPos origin, Mob sepiks, Vec3 destination,
                                      List<ServerPlayer> players, List<AABB> reservations) {
        thread(level);
        for (int i=1;i<=4;i++) {
            if (DevilsMaps.anchor(DevilsPlan.Zone.SP, "SP.WARP."+i, origin).pos().equals(destination))
                return warpClear(level, origin, sepiks, destination, players, reservations);
        }
        return false;
    }
    private static boolean warpClear(ServerLevel level, BlockPos origin, Mob sepiks, Vec3 pos,
                                     List<ServerPlayer> players, List<AABB> reservations) {
        var targets = players.stream().filter(p -> p.level()==level && p.isAlive() && !p.isSpectator()).toList();
        var box = bodyAt(sepiks, pos);
        return !targets.isEmpty() && pos.distanceToSqr(sepiks.position()) >= 4
                && clear(level, DevilsPlan.Zone.SP, origin, sepiks, box, reservations)
                && farEnough(pos, targets.stream().map(Entity::position).toList(), MIN_SPAWN_DISTANCE)
                && targets.stream().noneMatch(p -> box.inflate(1).intersects(p.getBoundingBox()))
                && targets.stream().anyMatch(p -> line(level, box.getCenter(), p.getEyePosition()));
    }

    public static AABB bodyAt(Entity entity, Vec3 feet) {
        return entity.getBoundingBox().move(feet.subtract(entity.position()));
    }
    private static void thread(ServerLevel level) {
        if (!level.getServer().isSameThread()) throw new IllegalStateException("Spatial validation requires server thread");
    }
    static boolean farEnough(Vec3 at, List<Vec3> players, double distance) {
        return players.stream().allMatch(p -> at.distanceToSqr(p) >= distance * distance);
    }
    static Optional<Point> preferHidden(List<Point> points) {
        return points.stream().filter(p -> !p.visible()).findFirst().or(() -> points.stream().findFirst());
    }
    static boolean within(AABB body, AABB bounds) {
        return Double.isFinite(body.minX) && Double.isFinite(body.minY) && Double.isFinite(body.minZ)
                && Double.isFinite(body.maxX) && Double.isFinite(body.maxY) && Double.isFinite(body.maxZ)
                && body.minX >= bounds.minX && body.minY >= bounds.minY && body.minZ >= bounds.minZ
                && body.maxX <= bounds.maxX && body.maxY <= bounds.maxY && body.maxZ <= bounds.maxZ;
    }
    private static boolean clear(ServerLevel level, DevilsPlan.Zone zone, BlockPos origin,
                                 Entity entity, AABB body, List<AABB> reservations) {
        return clearTerrain(level, zone, origin, entity, body) && !occupied(level, entity, body, reservations);
    }
    private static boolean occupied(ServerLevel level, Entity entity, AABB body, List<AABB> reservations) {
        return reservations.stream().anyMatch(r -> r.inflate(.15).intersects(body))
                || !level.getEntities(entity, body, e -> e.isAlive() && !e.isSpectator()).isEmpty();
    }
    private static boolean clearTerrain(ServerLevel level, DevilsPlan.Zone zone, BlockPos origin, Entity entity, AABB body) {
        var t = DevilsMaps.dimensions(zone);
        AABB bounds = new AABB(origin.getX(), origin.getY(), origin.getZ(),
                origin.getX() + t.getX(), origin.getY() + t.getY(), origin.getZ() + t.getZ());
        if (!within(body, bounds) || !level.getWorldBorder().isWithinBounds(body)) return false;
        for (BlockPos at : BlockPos.betweenClosed(BlockPos.containing(body.minX, body.minY - 1, body.minZ),
                BlockPos.containing(body.maxX, body.maxY, body.maxZ))) {
            if (!level.isLoaded(at) || !level.getFluidState(at).isEmpty()) return false;
            var state = level.getBlockState(at);
            if (state.is(net.minecraft.world.level.block.Blocks.FIRE) || state.is(net.minecraft.world.level.block.Blocks.SOUL_FIRE)
                    || state.is(net.minecraft.world.level.block.Blocks.MAGMA_BLOCK) || state.is(net.minecraft.world.level.block.Blocks.CAMPFIRE)
                    || state.is(net.minecraft.world.level.block.Blocks.SOUL_CAMPFIRE) || state.is(net.minecraft.world.level.block.Blocks.CACTUS)
                    || state.is(net.minecraft.world.level.block.Blocks.WITHER_ROSE) || state.is(net.minecraft.world.level.block.Blocks.SWEET_BERRY_BUSH)) return false;
        }
        return !level.getBlockCollisions(entity, body).iterator().hasNext();
    }
    /** Player feet may rest on fractional slabs/stairs or partly overhang a step. */
    public static boolean groundedPlayer(ServerLevel level, Entity player, Vec3 feet) {
        thread(level);
        var pos = BlockPos.containing(feet);
        var body = bodyAt(player, feet);
        if (!level.hasChunkAt(pos) || !level.getFluidState(pos).isEmpty() || !level.noCollision(player, body)) return false;
        var contact = new AABB(body.minX, body.minY - .08, body.minZ, body.maxX, body.minY, body.maxZ);
        return level.getBlockCollisions(player, contact).iterator().hasNext();
    }
    /** Deepest drop below a mobile flyer that still counts as "over the playable map" (blocks). */
    static final int FLIGHT_SUPPORT_DEPTH = 14;
    /**
     * A mobile flyer (shank, wizard) may only hover where solid ground lies within {@link #FLIGHT_SUPPORT_DEPTH} blocks
     * below it. The zone box is larger than the built map, so bounds alone let a flyer drift over the rim into empty air.
     */
    public static boolean flightSupported(ServerLevel level, Vec3 at) {
        var column = BlockPos.containing(at.x, at.y, at.z);
        for (int dy = 0; dy <= FLIGHT_SUPPORT_DEPTH; dy++) {
            var pos = column.below(dy);
            if (!level.isLoaded(pos)) return false;
            if (!level.getBlockState(pos).getCollisionShape(level, pos).isEmpty()) return true;
        }
        return false;
    }
    static boolean supported(ServerLevel level, AABB box) {
        // Collision-shape ray tests support slabs/stairs; require center and footprint corners, not a full-block guess.
        double inset = Math.min(.1, Math.min(box.getXsize(), box.getZsize()) / 4);
        double[][] samples = {{box.getCenter().x, box.getCenter().z}, {box.minX+inset,box.minZ+inset},
                {box.minX+inset,box.maxZ-inset}, {box.maxX-inset,box.minZ+inset}, {box.maxX-inset,box.maxZ-inset}};
        for (double[] p : samples) {
            Vec3 start = new Vec3(p[0], box.minY + .05, p[1]);
            var hit = level.clip(new ClipContext(start, start.add(0, -.2, 0), ClipContext.Block.COLLIDER,
                    ClipContext.Fluid.NONE, CollisionContext.empty()));
            if (hit.getType() != HitResult.Type.BLOCK) return false;
        }
        return true;
    }
    private static boolean reachable(ServerLevel level, Mob mob, Vec3 pos, List<ServerPlayer> players, boolean flying, boolean mobileFlyer) {
        if (flying && !mobileFlyer) {
            AABB box = bodyAt(mob, pos);
            return players.stream().anyMatch(p -> line(level, box.getCenter(), p.getEyePosition()));
        }
        // Use a fresh navigation probe so a running actor cannot return a cached path from its OLD position.
        // The body was already support-checked; an unspawned mob need not have its onGround flag set.
        Vec3 previous = mob.position(); AABB previousBox = mob.getBoundingBox();
        try {
            mob.setPos(pos);
            net.minecraft.world.entity.ai.navigation.PathNavigation navigation = mobileFlyer
                    ? new net.minecraft.world.entity.ai.navigation.FlyingPathNavigation(mob, level)
                    : new net.minecraft.world.entity.ai.navigation.GroundPathNavigation(mob, level) {
                @Override protected boolean canUpdatePath() { return true; }
            };
            for (var player : players) {
                var path = navigation.createPath(mobileFlyer ? BlockPos.containing(player.position().add(0, 1, 0)) : player.blockPosition(), 1);
                if (path != null && path.canReach()) return true;
            }
            return false;
        } finally { mob.setPos(previous); mob.setBoundingBox(previousBox); }
    }
    private static boolean line(ServerLevel level, Vec3 from, Vec3 to) {
        return level.clip(new ClipContext(from, to, ClipContext.Block.COLLIDER, ClipContext.Fluid.NONE,
                CollisionContext.empty())).getType() == HitResult.Type.MISS;
    }
}
