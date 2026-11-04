package kim.biryeong.destiny.campaign.fallen;

import kim.biryeong.destiny.DestinyGuardians;
import kim.biryeong.destiny.campaign.RisingEncounters.Slot;
import kim.biryeong.destiny.campaign.RisingServices;
import kim.biryeong.destiny.campaign.RisingServices.FallenKind;
import kim.biryeong.destiny.campaign.RisingServices.Zone;
import kr.toxicity.model.api.BetterModel;
import kr.toxicity.model.api.animation.AnimationIterator;
import kr.toxicity.model.api.animation.AnimationModifier;
import kr.toxicity.model.api.mod.platform.ModLocation;
import kr.toxicity.model.api.mod.platform.ModPlayer;
import kr.toxicity.model.api.tracker.DummyTracker;
import kr.toxicity.model.api.tracker.TrackerModifier;
import kr.toxicity.model.api.tracker.TrackerUpdateAction;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;

import java.util.*;

/**
 * Fallen Skiff reinforcement drop (W300 r7, original presentation). Presentation only: the encounter's spawn
 * timing stays authoritative. {@code incoming} (sent when the previous wave thins, {@code WAVE_DELAY} ticks before
 * the spawn) starts the Skiff's {@code arrive} clip sped up to fit that lead; {@code spawned} (right after the wave's
 * entities exist) plays {@code drop}, lifts the dropped Fallen into the Skiff's belly so they fall the last few
 * blocks (inside FallenBrain's spawn grace), then {@code depart} and removal. A missing cue never blocks anything:
 * a Skiff with no drop leaves after {@link Timing#HOVER_TIMEOUT}. Without BetterModel/rg_skiff the drop falls back
 * to a teleport-in column of particles and the Skiff sounds.
 */
public final class SkiffDrop {
    private SkiffDrop() {}

    /** Pure timing (ticks), unit tested. Clip lengths come from rg_skiff.bbmodel (arrive 4 s, drop 2.6 s, depart 4 s). */
    public static final class Timing {
        public static final int ARRIVE_CLIP = 80, DROP_CLIP = 52, DEPART_CLIP = 80;
        /** Fastest acceptable arrive playback. A skiff covering ~90 m in 1.5 s still reads as a swoop. */
        public static final float MAX_SPEED = 3f;
        /** DEPART_DELAY: the Skiff holds station after the drop (drop clip 52 t + ~3 s) so a player can find it. */
        public static final int HOVER_TIMEOUT = 240, DEPART_DELAY = 110, LIFT_HEIGHT = 5, HOVER_HEIGHT = 9;
        private Timing() {}
        /** Playback speed so the arrive clip ends by {@code lead}; 1 when there is time, capped at MAX_SPEED. */
        public static float arriveSpeed(int lead) {
            if (lead <= 0) return MAX_SPEED;
            return Math.max(1f, Math.min(MAX_SPEED, ARRIVE_CLIP / (float) lead));
        }
        public static int arriveTicks(int lead) { return (int) Math.ceil(ARRIVE_CLIP / arriveSpeed(lead)); }
        /** Total Skiff lifetime from the drop cue. */
        public static int afterDrop() { return DEPART_DELAY + DEPART_CLIP; }
    }

    /** Waves that should arrive by Skiff (pure, unit tested). */
    public static final class Choice {
        static final double DROP_RADIUS = 10;
        private Choice() {}
        /**
         * Reinforcement waves only: never the opening wave (it spawns with no lead time and opens the fight), never a
         * Walker wave (it lands on its own), never Gateway. Needs at least two ground units; Shanks fly in by themselves.
         * Breach is mostly interior; there the runtime open-sky check decides (Graveyard reinforcements qualify).
         */
        public static boolean skiffWave(Zone zone, int index, List<Slot> wave) {
            if (zone == null || zone == Zone.GATEWAY || wave == null) return false;
            if (index <= 0 && !openingByShip(zone)) return false;
            if (wave.stream().anyMatch(s -> s.kind() == FallenKind.WALKER)) return false;
            return dropped(wave).size() >= 2;
        }
        /**
         * W300 r6 map: Dock 13 is three ordered waves (dock_defense, dock_ship_west, dock_ship_east); waves 2-3 drop by
         * Skiff from prop.skiff_* hints under the roof hole. Every zone's opening wave is already on site.
         */
        public static boolean openingByShip(Zone zone) { return false; }
        /**
         * Ground units within DROP_RADIUS of the densest ground unit (most neighbours in range, first on ties) ride
         * the Skiff; far outliers and Shanks spawn as usual. Anchoring on a unit, not the mean, keeps one distant
         * marker from dragging the drop point away from the squad.
         */
        public static List<Slot> dropped(List<Slot> wave) {
            var ground = wave.stream().filter(s -> s.kind() != FallenKind.SHANK && s.kind() != FallenKind.WALKER).toList();
            if (ground.isEmpty()) return List.of();
            Slot anchor = ground.get(0);
            long best = -1;
            for (var a : ground) {
                long n = ground.stream().filter(b -> horizontal(a.pos(), b.pos()) <= DROP_RADIUS).count();
                if (n > best) { best = n; anchor = a; }
            }
            Vec3 c = anchor.pos();
            return ground.stream().filter(s -> horizontal(s.pos(), c) <= DROP_RADIUS).toList();
        }
        /** All ground units of the wave, riders first: the eyes for the sky search and the beam targets off-centre. */
        public static List<Slot> ground(List<Slot> wave, List<Slot> riders) {
            var out = new ArrayList<>(riders);
            for (var s : wave) if (s.kind() != FallenKind.SHANK && s.kind() != FallenKind.WALKER && !out.contains(s)) out.add(s);
            return out;
        }
        public static Vec3 centroid(List<Slot> slots) {
            double x = 0, y = Double.MAX_VALUE, z = 0;
            for (var s : slots) { x += s.pos().x; z += s.pos().z; y = Math.min(y, s.pos().y); }
            return new Vec3(x / slots.size(), y, z / slots.size());
        }
        /** Yaw whose forward (-sin, cos) points from the player to the drop: the Skiff comes in from behind it. */
        public static float approachYaw(Vec3 drop, Vec3 player) {
            double ax = drop.x - (player == null ? drop.x : player.x), az = drop.z - (player == null ? drop.z - 1 : player.z);
            if (ax * ax + az * az < 1e-6) az = 1;
            return (float) Math.toDegrees(Math.atan2(-ax, az));
        }
        static double horizontal(Vec3 a, Vec3 b) { return Math.hypot(a.x - b.x, a.z - b.z); }
    }

    /**
     * Where the Skiff can hover (pure, unit tested; the offline zone scan uses the same code on the bundled templates).
     * Preferred: straight above the riders. When a roof is in the way, the nearest column within {@link #RADIUS} whose
     * sky is open, whose hull box is clear and that the riders' spawn area can see (a hangar door, a roof hole) — the
     * Skiff hovers there and beams the riders in at their own spawns. Empty when there is no such column.
     */
    public static final class Sky {
        /** Search rings: the usual drop radius, then a wider one for enclosed halls (Dock 13's ship-bay roof hole). */
        public static final int RADIUS = 24, FAR_RADIUS = 40, HULL_XZ = 3, HULL_DOWN = 2, HULL_UP = 2, MAX_EYES = 8, ACCEPT_EYES = 3;
        /**
         * rg_skiff hull extent around its origin, in blocks (bbmodel elements x +/-40 px, y -44.5..33 px,
         * z -120..131.8 px; plus the idle bob +/-3 px and the drop dip -6 px). Checked along the chosen yaw.
         */
        public static final double HULL_BACK = 8, HULL_FRONT = 8.5, HULL_HALF_WIDTH = 2.75, HULL_BELOW = 3.2, HULL_ABOVE = 2.4;
        /** Yaw offsets tried from the preferred approach yaw. */
        static final float[] YAW_STEPS = {0, 45, -45, 90, -90, 135, -135, 180};
        /** Hover heights above the riders' floor, best first. */
        static final int[] HEIGHTS = {Timing.HOVER_HEIGHT, 7, 11, 5, 13, 15, 18, 22, 26, 30};
        /** Blocks a ray/hull; {@code sky(x,y,z)}: nothing solid at or above y in that column. */
        public interface Grid {
            boolean solid(int x, int y, int z);
            boolean sky(int x, int y, int z);
        }
        public enum Kind { DIRECT, OFFSET, HINT }
        /** {@code seenBy}: how many ground units' eyes see the Skiff's belly. */
        /** {@code yaw}: hull heading that fits; {@code viewerSees}: the watching player's eye has a clear ray to the hull. */
        public record Spot(Vec3 hover, Kind kind, double offset, int seenBy, float yaw, boolean viewerSees) { }
        private Sky() {}

        /** Unique block reads allowed per decision (server-thread cost cap); past it the best spot so far wins. */
        public static final int BUDGET = 80_000;
        /** Extra reads spent looking for a spot the watching player can see once a rider-only spot is in hand. */
        public static final int VIEWER_BUDGET = 15_000;

        public static Optional<Spot> find(Grid grid, List<Vec3> ground, Vec3 anchor, Vec3 hint) {
            return find(grid, ground, anchor, hint, 0, null);
        }

        /**
         * @param ground the wave's ground units' feet (riders first); the first {@link #MAX_EYES} are used as eyes
         * @param anchor drop centroid; a DIRECT spot is one right above it
         * @param yaw preferred hull heading (approach from behind the player); other headings are tried if it clips
         * @param viewer eye of the player watching the fight (or null). Order of preference: hint, straight above,
         *     columns within {@link #RADIUS} that this player can see; then the first spot only the riders see
         *     (hint, above, any column up to {@link #FAR_RADIUS}).
         */
        public static Optional<Spot> find(Grid grid, List<Vec3> ground, Vec3 anchor, Vec3 hint, float yaw, Vec3 viewer) {
            if (ground.isEmpty()) return Optional.empty();
            var g = new Cached(grid);
            var q = new Query(g, ground.stream().limit(MAX_EYES).map(p -> p.add(0, 1.6, 0)).toList(), anchor, yaw, viewer);
            try {
                return Optional.ofNullable(search(q, ground, hint));
            } catch (Budget e) {
                return Optional.ofNullable(q.fallback);
            } finally {
                LAST_READS.set(g.reads);
            }
        }

        /** Unique solid reads of the last {@link #find} on this thread (for logs/tests). */
        public static int lastReads() { return LAST_READS.get(); }
        private static final ThreadLocal<Integer> LAST_READS = ThreadLocal.withInitial(() -> 0);

        private static final class Query {
            final Cached g; final List<Vec3> eyes; final Vec3 anchor; final float yaw; final Vec3 viewer;
            Spot fallback;
            int fallbackReads;
            /** Out of time to improve on the rider-only spot. */
            boolean exhausted() { return fallback != null && g.reads - fallbackReads > VIEWER_BUDGET; }
            Query(Cached g, List<Vec3> eyes, Vec3 anchor, float yaw, Vec3 viewer) {
                this.g = g; this.eyes = eyes; this.anchor = anchor; this.yaw = yaw; this.viewer = viewer;
            }
            /** True when {@code s} is good enough to stop: no viewer to please, or the viewer sees it. */
            boolean accept(Spot s) {
                if (s == null) return false;
                if (viewer == null || s.viewerSees()) return true;
                if (fallback == null) { fallback = s; fallbackReads = g.reads; }
                return false;
            }
        }

        private static Spot search(Query q, List<Vec3> ground, Vec3 hint) {
            var g = q.g;
            int ax = floor(q.anchor.x), ay = floor(q.anchor.y), az = floor(q.anchor.z);
            if (hint != null) {
                // the marker's column: its own height first, then lower (into view of the dock floor), then higher
                int hx = floor(hint.x), hy = floor(hint.y), hz = floor(hint.z);
                List<Integer> ys = new ArrayList<>(List.of(hy));
                for (int y = hy - 2; y >= ay + 5; y -= 2) ys.add(y);
                for (int y = hy + 2; y <= hy + 8; y += 2) ys.add(y);
                for (int y : ys) {
                    Spot s = evaluate(q, hx, y, hz, Kind.HINT);
                    if (q.accept(s)) return s;
                    if (q.exhausted()) return q.fallback;
                }
            }
            for (int h : HEIGHTS) {
                Spot s = evaluate(q, ax, ay + h, az, Kind.DIRECT);
                if (q.accept(s)) return s;
            }
            double minX = Double.MAX_VALUE, maxX = -Double.MAX_VALUE, minZ = Double.MAX_VALUE, maxZ = -Double.MAX_VALUE;
            for (Vec3 p : ground) { minX = Math.min(minX, p.x); maxX = Math.max(maxX, p.x); minZ = Math.min(minZ, p.z); maxZ = Math.max(maxZ, p.z); }
            List<double[]> cols = new ArrayList<>();
            for (int x = floor(minX) - FAR_RADIUS; x <= floor(maxX) + FAR_RADIUS; x++)
                for (int z = floor(minZ) - FAR_RADIUS; z <= floor(maxZ) + FAR_RADIUS; z++) {
                    double d = Double.MAX_VALUE;
                    for (Vec3 p : ground) d = Math.min(d, Math.hypot(x + .5 - p.x, z + .5 - p.z));
                    // 2-block lattice: neighbouring hover spots look the same and it quarters the work
                    if (d <= FAR_RADIUS && ((x - floor(q.anchor.x)) & 1) == 0 && ((z - floor(q.anchor.z)) & 1) == 0)
                        cols.add(new double[]{d, x, z});
                }
            cols.sort(Comparator.<double[]>comparingDouble(c -> c[0]).thenComparingDouble(c -> c[1]).thenComparingDouble(c -> c[2]));
            int top = ay + HEIGHTS[HEIGHTS.length - 1] + HULL_UP + 1;
            for (double[] c : cols) {
                // past RADIUS a spot only the riders see is still better than nothing, but a nearer one wins
                if ((c[0] > RADIUS || q.exhausted()) && q.fallback != null) return q.fallback;
                int x = (int) c[1], z = (int) c[2];
                if (!g.sky(x, top, z)) continue; // roofed even at the highest hover
                for (int h : HEIGHTS) {
                    Spot s = evaluate(q, x, ay + h, z, Kind.OFFSET);
                    if (s == null) continue;
                    if (q.accept(s) || c[0] > RADIUS) return s;
                    break; // this column only reaches the riders; try the next column for the viewer
                }
            }
            return q.fallback;
        }

        /** A hover spot at block (x,y,z), or null: sky above, hull fits at some heading, a rider sees the belly. */
        static Spot evaluate(Query q, int x, int y, int z, Kind kind) {
            var g = q.g;
            if (!g.sky(x, y + HULL_UP + 1, z)) return null;
            Vec3 hover = new Vec3(x + .5, y, z + .5);
            // cheapest first: hull footprint under open sky (heightmap only, no block reads), then rays
            Float heading = null, clipped = null;
            for (float d : YAW_STEPS) {
                float h = q.yaw + d;
                if (!hullFits(g, hover, h)) continue;
                if (approachClear(g, hover, h)) { heading = h; break; }
                if (clipped == null) clipped = h; // fits, but flies in through a wall; last resort heading
            }
            if (heading == null) heading = clipped;
            if (heading == null || !anySees(g, q.eyes, hover)) return null;
            boolean viewerSees = q.viewer != null && viewerSees(g, q.viewer, hover);
            double off = kind == Kind.DIRECT ? 0 : horizontal(hover, q.anchor);
            return new Spot(hover, kind, off, seen(g, q.eyes, hover), heading, viewerSees);
        }

        /**
         * The whole 16-block hull at heading {@code yaw} (forward = (-sin, cos)) is under open sky: nothing solid from
         * the hull's bottom upward anywhere in its footprint. That keeps it out of walls and roofs, and a Skiff tucked
         * under the roof beside a hole would be hidden and could not have flown in anyway.
         */
        public static boolean hullFits(Grid g, Vec3 hover, float yaw) {
            double r = Math.toRadians(yaw), fx = -Math.sin(r), fz = Math.cos(r), sx = Math.cos(r), sz = Math.sin(r);
            int bottom = floor(hover.y - HULL_BELOW);
            for (double a = -HULL_BACK; a <= HULL_FRONT + 1e-9; a += .5)
                for (double b = -HULL_HALF_WIDTH; b <= HULL_HALF_WIDTH + 1e-9; b += HULL_HALF_WIDTH / 2)
                    if (!g.sky(floor(hover.x + fx * a + sx * b), bottom, floor(hover.z + fz * a + sz * b))) return false;
            return true;
        }

        /**
         * The last stretch of the arrive clip (keyframes 1.6 s: 26 blocks out and 7.5 up, 2.8 s: 3.75 out and 1.9 up,
         * along the hull's forward axis) runs under open sky, so the player sees it fly in rather than pop out of a roof.
         */
        public static boolean approachClear(Grid g, Vec3 hover, float yaw) {
            double r = Math.toRadians(yaw), fx = -Math.sin(r), fz = Math.cos(r);
            for (double t = 0; t <= 1.0001; t += 1 / 24.0) {
                double out = 3.75 + t * (26.25 - 3.75), up = 1.9 + t * (7.5 - 1.9);
                double px = hover.x + fx * out, pz = hover.z + fz * out, py = hover.y + up;
                if (!g.sky(floor(px), floor(py - HULL_BELOW), floor(pz))) return false;
            }
            return true;
        }

        /** Viewer's eye sees the hull's belly, centre or top (any of three points). */
        public static boolean viewerSees(Grid g, Vec3 eye, Vec3 hover) {
            return visible(g, eye, hover.add(0, -HULL_DOWN, 0)) || visible(g, eye, hover) || visible(g, eye, hover.add(0, HULL_UP, 0));
        }

        /** Whether a unit standing at {@code feet} sees the Skiff's belly (beam targets off-centre). */
        public static boolean sees(Grid g, Vec3 feet, Vec3 hover) {
            return visible(g, feet.add(0, 1.6, 0), hover.add(0, -HULL_DOWN, 0));
        }

        /** Acceptance uses the first {@link #ACCEPT_EYES} eyes (riders first); {@link #seen} counts them all for the log. */
        private static boolean anySees(Grid g, List<Vec3> eyes, Vec3 hover) {
            Vec3 belly = hover.add(0, -HULL_DOWN, 0);
            for (int i = 0; i < Math.min(ACCEPT_EYES, eyes.size()); i++) if (visible(g, eyes.get(i), belly)) return true;
            return false;
        }

        private static final class Budget extends RuntimeException {
            Budget() { super(null, null, false, false); }
        }

        /** Memoises block reads (rays from the same eyes overlap) and enforces {@link #BUDGET}. */
        private static final class Cached implements Grid {
            final Grid g;
            final HashMap<Long, Boolean> solid = new HashMap<>();
            final HashMap<Long, Boolean> sky = new HashMap<>();
            int reads;
            Cached(Grid g) { this.g = g; }
            static long key(int x, int y, int z) { return ((long) (x & 0x3FFFFFF) << 38) | ((long) (z & 0x3FFFFFF) << 12) | (y & 0xFFF); }
            @Override public boolean solid(int x, int y, int z) {
                return solid.computeIfAbsent(key(x, y, z), k -> {
                    if (reads >= BUDGET) throw new Budget();
                    reads++;
                    return g.solid(x, y, z);
                });
            }
            @Override public boolean sky(int x, int y, int z) { return sky.computeIfAbsent(key(x, y, z), k -> g.sky(x, y, z)); }
        }

        /** Number of eyes with a clear ray to the Skiff's belly; stops counting at the first when only presence matters. */
        static int seen(Grid g, List<Vec3> eyes, Vec3 hover) {
            Vec3 belly = hover.add(0, -HULL_DOWN, 0);
            int n = 0;
            for (Vec3 e : eyes) if (visible(g, e, belly)) n++;
            return n;
        }

        /**
         * Hull box clear and open sky above its centre: the Skiff may hover in a roof hole or above the roof line,
         * provided a rider can see its belly (checked separately).
         */
        static boolean open(Grid g, int x, int y, int z) {
            if (!g.sky(x, y + HULL_UP + 1, z)) return false;
            for (int yy = y - HULL_DOWN; yy <= y + HULL_UP; yy++)
                for (int xx = x - HULL_XZ; xx <= x + HULL_XZ; xx++)
                    for (int zz = z - HULL_XZ; zz <= z + HULL_XZ; zz++)
                        if (g.solid(xx, yy, zz)) return false;
            return true;
        }

        /** Voxel ray (quarter-block steps) from an eye to the Skiff's belly. */
        static boolean visible(Grid g, Vec3 from, Vec3 to) {
            double len = from.distanceTo(to);
            int steps = Math.max(1, (int) Math.ceil(len * 4));
            int lx = Integer.MIN_VALUE, ly = 0, lz = 0;
            for (int i = 1; i < steps; i++) {
                Vec3 p = from.lerp(to, i / (double) steps);
                int x = floor(p.x), y = floor(p.y), z = floor(p.z);
                if (x == lx && y == ly && z == lz) continue;
                lx = x; ly = y; lz = z;
                if (g.solid(x, y, z)) return false;
            }
            return true;
        }
        private static int floor(double v) { return (int) Math.floor(v); }
        private static double horizontal(Vec3 a, Vec3 b) { return Math.hypot(a.x - b.x, a.z - b.z); }
    }

    // ------------------------------------------------------------------------------------------ runtime

    private enum State { ARRIVING, HOVER, DROPPING, DEPARTING }
    private record Key(ServerLevel level, Zone zone, int index) {}

    private static final class Skiff {
        final ServerLevel level;
        final Vec3 at;
        final float yaw;
        final List<Slot> riders;
        final Sky.Kind kind;
        final Set<Slot> beamed = new HashSet<>();
        DummyTracker tracker;
        State state = State.ARRIVING;
        int age, stateAge, arriveTicks;
        Skiff(ServerLevel level, Vec3 at, float yaw, List<Slot> riders, Sky.Kind kind) {
            this.level = level; this.at = at; this.yaw = yaw; this.riders = riders; this.kind = kind;
        }
    }

    private static final Map<Key, Skiff> ACTIVE = new HashMap<>();
    private static final Set<String> WARNED = new HashSet<>();
    /** One decision (and one INFO line) per wave; a checkpoint retry of the same wave decides again after this. */
    private static final Map<Key, Long> DECIDED = new HashMap<>();
    private static final long REDECIDE_TICKS = 400;

    /** Wave about to arrive in {@code lead} ticks. Repeated cues for the same wave are ignored. */
    public static void incoming(ServerLevel level, Zone zone, int index, List<Slot> wave, int lead) {
        incoming(level, zone, index, wave, lead, null);
    }

    /** Marker id of the optional hover hint for an encounter (map lane; {@code prop.*} already passes the id grammar). */
    public static String hintMarker(String encounter) { return "prop.skiff_" + encounter; }

    /** {@code hint}: optional world position from a {@link #hintMarker} marker, tried first. */
    public static void incoming(ServerLevel level, Zone zone, int index, List<Slot> wave, int lead, Vec3 hint) {
        try {
            if (level == null || wave == null) return;
            var key = new Key(level, zone, index);
            if (ACTIVE.containsKey(key)) return;
            long now = level.getGameTime();
            Long decided = DECIDED.get(key);
            if (decided != null && now - decided < REDECIDE_TICKS) return;
            DECIDED.put(key, now);
            String encounter = wave.isEmpty() ? "?" : wave.get(0).encounter();
            if (!Choice.skiffWave(zone, index, wave)) {
                DestinyGuardians.LOGGER.info("[skiff] {} wave {} ({}): eligible=false (size {}, index {})", zone, index, encounter, wave.size(), index);
                return;
            }
            var riders = Choice.dropped(wave);
            Vec3 ground = Choice.centroid(riders);
            var units = Choice.ground(wave, riders);
            long t0 = System.nanoTime();
            ServerPlayer watcher = nearestPlayerEntity(level, ground);
            Vec3 viewer = watcher == null ? null : watcher.getEyePosition();
            float preferred = Choice.approachYaw(ground, watcher == null ? null : watcher.position());
            var spot = Sky.find(grid(level), units.stream().map(Slot::pos).toList(), ground, hint, preferred, viewer).orElse(null);
            long micros = (System.nanoTime() - t0) / 1000;
            int reads = Sky.lastReads();
            boolean model = BetterModel.model(RisingServices.Models.SKIFF).isPresent();
            if (spot == null) {
                DestinyGuardians.LOGGER.info("[skiff] {} wave {} ({}): eligible=true riders={} ground={} sky=none within {} m{} -> skipped, wave spawns normally ({} us, {} reads{})",
                        zone, index, encounter, riders.size(), fmt(ground), Sky.FAR_RADIUS, hint == null ? "" : " (hint " + fmt(hint) + " blocked)",
                        micros, reads, reads >= Sky.BUDGET ? ", budget hit" : "");
                return;
            }
            Vec3 at = spot.hover();
            // Off-centre Skiffs beam every ground unit in (they spawn where the encounter placed them).
            var skiff = new Skiff(level, at, spot.yaw(), spot.kind() == Sky.Kind.DIRECT ? riders : units, spot.kind());
            skiff.arriveTicks = Timing.arriveTicks(lead);
            attach(skiff, lead);
            FallenSounds.play(level, at, FallenSounds.Ev.SKIFF_FLYOVER);
            if (spot.kind() != Sky.Kind.DIRECT) {
                var g = grid(level);
                for (var u : skiff.riders) if (Sky.sees(g, u.pos(), at)) skiff.beamed.add(u);
            }
            ACTIVE.put(key, skiff);
            DestinyGuardians.LOGGER.info("[skiff] {} wave {} ({}): eligible=true riders={} ground={} sky={} hover={} yaw={} offset={}m seenBy={}/{} viewer={} viewerSees={} lead={}t arrive={}t tracker={} search={}us/{}reads fallback={}",
                    zone, index, encounter, skiff.riders.size(), fmt(ground), spot.kind(), fmt(at), Math.round(spot.yaw()),
                    String.format(Locale.ROOT, "%.1f", spot.offset()), spot.seenBy(), Math.min(units.size(), Sky.MAX_EYES),
                    watcher == null ? "none" : watcher.getScoreboardName() + "@" + fmt(viewer), spot.viewerSees(), lead, skiff.arriveTicks,
                    skiff.tracker == null ? "none" : "viewers=" + skiff.tracker.playerCount(), micros, reads, model ? (spot.kind() == Sky.Kind.DIRECT ? "none" : "beam-in at spawns") : "no rg_skiff model: particles+sound only");
        } catch (RuntimeException e) {
            DestinyGuardians.LOGGER.warn("Skiff arrival failed (presentation only): {}", e.toString());
        }
    }

    /** The wave's entities now exist. Plays the drop even if no arrival was cued (teleport-in, no lead). */
    public static void spawned(ServerLevel level, Zone zone, int index, List<Slot> wave) { spawned(level, zone, index, wave, null); }

    public static void spawned(ServerLevel level, Zone zone, int index, List<Slot> wave, Vec3 hint) {
        try {
            if (level == null || wave == null) return;
            var key = new Key(level, zone, index);
            var skiff = ACTIVE.get(key);
            if (skiff == null) {
                incoming(level, zone, index, wave, 0, hint);
                skiff = ACTIVE.get(key);
                if (skiff == null) return;
            }
            if (skiff.state == State.DROPPING || skiff.state == State.DEPARTING) return;
            skiff.state = State.DROPPING;
            skiff.stateAge = 0;
            if (skiff.tracker != null) skiff.tracker.animate("drop", new AnimationModifier(2, 2, AnimationIterator.Type.PLAY_ONCE));
            FallenSounds.play(level, skiff.at, FallenSounds.Ev.SKIFF_ENEMY_SPAWNER);
            for (var slot : skiff.riders)
                lift(level, slot, skiff.at, skiff.kind == Sky.Kind.DIRECT, skiff.kind == Sky.Kind.DIRECT || skiff.beamed.contains(slot));
        } catch (RuntimeException e) {
            DestinyGuardians.LOGGER.warn("Skiff drop failed (presentation only): {}", e.toString());
        }
    }

    /**
     * DIRECT: move the freshly spawned rider up under the hull so it falls into place. OFFSET/HINT (Skiff hovers at an
     * opening): the rider stays at its spawn and a tractor beam runs from the hull to it. Never moves an old or busy mob.
     */
    private static void lift(ServerLevel level, Slot slot, Vec3 hull, boolean raise, boolean beam) {
        var box = AABB.ofSize(slot.pos(), 3, 3, 3);
        for (var mob : level.getEntitiesOfClass(FallenMob.class, box, m -> m.tickCount <= 2 && !m.isWalkerPart()
                && m.fallenKind() == slot.kind() && m.position().distanceToSqr(slot.pos()) < 1)) {
            Vec3 up = slot.pos().add(0, Timing.LIFT_HEIGHT, 0);
            boolean clear = raise && level.noCollision(mob, mob.getBoundingBox().move(0, Timing.LIFT_HEIGHT, 0))
                    && FallenBrain.clearPath(level, slot.pos().add(0, .5, 0), up.add(0, mob.getBbHeight(), 0));
            if (clear) mob.teleportTo(up.x, up.y, up.z);
            Vec3 from = raise ? new Vec3(slot.pos().x, hull.y - 2.5, slot.pos().z) : hull.add(0, -2.5, 0);
            Vec3 to = clear ? up : slot.pos().add(0, 1, 0);
            // Riders out of the Skiff's sight (behind a wall) only materialise; no beam through geometry.
            if (beam) beam(level, from, to);
            else level.sendParticles(ParticleTypes.REVERSE_PORTAL, to.x, to.y, to.z, 14, .3, .6, .3, .03);
            break;
        }
    }

    private static void beam(ServerLevel level, Vec3 from, Vec3 to) {
        double len = Math.max(.1, from.distanceTo(to));
        for (double d = 0; d <= len; d += .6) {
            Vec3 p = from.lerp(to, d / len);
            level.sendParticles(FallenWeapons.dust(0x9FE8FF, 1.2f), p.x, p.y, p.z, 1, .15, .05, .15, 0);
        }
        level.sendParticles(ParticleTypes.REVERSE_PORTAL, to.x, to.y, to.z, 14, .3, .6, .3, .03);
    }

    /** Tracker settings: sight-trace off (see {@link #attach}); package-visible for the test. */
    static final TrackerModifier TRACKER = TrackerModifier.DEFAULT.toBuilder().sightTrace(false).build();

    private static void attach(Skiff skiff, int lead) {
        var renderer = BetterModel.model(RisingServices.Models.SKIFF).orElse(null);
        if (renderer == null) {
            if (WARNED.add(RisingServices.Models.SKIFF))
                DestinyGuardians.LOGGER.warn("Skiff model '{}' unavailable; drops use the teleport-in fallback", RisingServices.Models.SKIFF);
            return;
        }
        // No sight-trace: BetterModel's FOV culling withholds animation frames from players looking elsewhere, which
        // left the Skiff parked at the first arrive keyframe (~90 blocks out) for anyone who turned around late.
        skiff.tracker = renderer.create(ModLocation.of(skiff.level, skiff.at, 0, skiff.yaw), TRACKER, t -> skiff.tracker = t);
        skiff.tracker.update(TrackerUpdateAction.brightness(15, 15));
        float speed = Timing.arriveSpeed(lead);
        skiff.tracker.animate("idle", new AnimationModifier(0, 0, AnimationIterator.Type.LOOP));
        skiff.tracker.animate("arrive", new AnimationModifier(0, 3, AnimationIterator.Type.PLAY_ONCE, () -> speed));
        viewers(skiff);
    }

    private static void viewers(Skiff skiff) {
        if (skiff.tracker == null || skiff.tracker.isClosed()) return;
        for (ServerPlayer p : skiff.level.players()) {
            if (p.position().distanceToSqr(skiff.at) > 160 * 160) continue;
            var pp = ModPlayer.of(p.connection);
            if (!skiff.tracker.isSpawned(pp)) skiff.tracker.spawn(pp);
        }
    }

    public static void tick(MinecraftServer server) {
        if (ACTIVE.isEmpty()) return;
        var it = ACTIVE.values().iterator();
        while (it.hasNext()) {
            var s = it.next();
            if (s.level.getServer() != server) continue;
            boolean done;
            try { done = step(s); }
            catch (RuntimeException e) { done = true; }
            if (done) { close(s); it.remove(); }
        }
    }

    private static boolean step(Skiff s) {
        s.age++; s.stateAge++;
        if (s.age % 20 == 0) viewers(s);
        switch (s.state) {
            case ARRIVING -> {
                if (s.stateAge >= s.arriveTicks) { s.state = State.HOVER; s.stateAge = 0; }
            }
            case HOVER -> {
                if (s.stateAge % 30 == 0) s.level.sendParticles(ParticleTypes.CLOUD, s.at.x, s.at.y - 3, s.at.z, 3, 1.5, .2, 1.5, .01);
                if (s.stateAge >= Timing.HOVER_TIMEOUT) depart(s);
            }
            case DROPPING -> {
                if (s.tracker == null && s.stateAge <= 20 && s.stateAge % 2 == 0)
                    for (var r : s.riders) s.level.sendParticles(ParticleTypes.REVERSE_PORTAL, r.pos().x, r.pos().y + 1, r.pos().z, 4, .3, .7, .3, .02);
                if (s.kind != Sky.Kind.DIRECT && s.stateAge > 0 && s.stateAge <= 30 && s.stateAge % 10 == 0)
                    for (var r : s.beamed) beam(s.level, s.at.add(0, -2.5, 0), r.pos().add(0, 1, 0));
                if (s.stateAge >= Timing.DEPART_DELAY) depart(s);
            }
            case DEPARTING -> { return s.stateAge >= Timing.DEPART_CLIP || s.tracker == null; }
        }
        return false;
    }

    private static void depart(Skiff s) {
        s.state = State.DEPARTING;
        s.stateAge = 0;
        if (s.tracker != null && !s.tracker.isClosed()) {
            s.tracker.stopAnimation("idle");
            s.tracker.animate("depart", new AnimationModifier(2, 0, AnimationIterator.Type.HOLD_ON_LAST));
        }
        FallenSounds.play(s.level, s.at, FallenSounds.Ev.SKIFF_FLYOVER, .8f, 1.05f);
    }

    private static void close(Skiff s) {
        if (s.tracker != null && !s.tracker.isClosed()) {
            try { s.tracker.close(); } catch (RuntimeException ignored) { }
        }
        s.tracker = null;
    }

    public static void clear(ServerLevel level) {
        ACTIVE.entrySet().removeIf(e -> { if (e.getKey().level() == level) { close(e.getValue()); return true; } return false; });
        DECIDED.keySet().removeIf(k -> k.level() == level);
    }

    public static void clearAll() { ACTIVE.values().forEach(SkiffDrop::close); ACTIVE.clear(); DECIDED.clear(); }

    static int active() { return ACTIVE.size(); }

    /**
     * Runtime grid: collision shapes for the hull/ray, the MOTION_BLOCKING heightmap for "sky" (works in instance
     * dimensions without sky light, where {@code canSeeSky} is always false). Unloaded columns count as blocked.
     */
    private static Sky.Grid grid(ServerLevel level) {
        return new Sky.Grid() {
            final BlockPos.MutableBlockPos pos = new BlockPos.MutableBlockPos();
            @Override public boolean solid(int x, int y, int z) {
                pos.set(x, y, z);
                if (!level.isLoaded(pos)) return true;
                return !level.getBlockState(pos).getCollisionShape(level, pos).isEmpty();
            }
            @Override public boolean sky(int x, int y, int z) {
                pos.set(x, y, z);
                if (!level.isLoaded(pos)) return false;
                return y >= level.getHeight(Heightmap.Types.MOTION_BLOCKING, x, z);
            }
        };
    }

    private static String fmt(Vec3 v) { return String.format(Locale.ROOT, "(%.1f, %.1f, %.1f)", v.x, v.y, v.z); }

    private static ServerPlayer nearestPlayerEntity(ServerLevel level, Vec3 at) {
        ServerPlayer best = null;
        for (ServerPlayer p : level.players())
            if (!p.isSpectator() && (best == null || p.distanceToSqr(at) < best.distanceToSqr(at))) best = p;
        return best;
    }

    private static Vec3 nearestPlayer(ServerLevel level, Vec3 at) {
        ServerPlayer best = null;
        for (ServerPlayer p : level.players()) if (best == null || p.distanceToSqr(at) < best.distanceToSqr(at)) best = p;
        return best == null ? null : best.position();
    }
}
