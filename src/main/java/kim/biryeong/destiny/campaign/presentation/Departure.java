package kim.biryeong.destiny.campaign.presentation;

import kim.biryeong.destiny.DestinyGuardians;
import kim.biryeong.destiny.campaign.RisingServices;
import kr.toxicity.model.api.BetterModel;
import kr.toxicity.model.api.animation.AnimationIterator;
import kr.toxicity.model.api.animation.AnimationModifier;
import kr.toxicity.model.api.mod.platform.ModLocation;
import kr.toxicity.model.api.mod.platform.ModPlayer;
import kr.toxicity.model.api.tracker.DummyTracker;
import net.minecraft.core.particles.DustParticleOptions;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;

/**
 * Dock 13 departure — original W300 staging (no extracted takeoff animation/camera).
 *
 * <pre>
 *  t   0  cinematic: movement locked, vanilla + combat HUD + first-person weapon hidden; a 6-tick black cut
 *         moves the view to a 3/4 front vantage ~11 blocks from the hull (ship fills >= 1/3 of the frame,
 *         line of sight checked); Ghost sweeps the hull (2.8 s), scan_loop at the hull
 *  t  56  ship power_up clip + ship_power; engine glow particles
 *  t 100  Ghost transmat: revive flash; under the flash the HUD hides and the player becomes the camera
 *         at a low wide vantage beside the ship (original spot restored on early close)
 *  t 116  takeoff (W301): one code-driven path — vertical lift 6.5 blocks (1.7 s, ground wash), a short hover
 *         with the nose rising, then a cubic boost 140 blocks along the nose; exhaust is emitted every tick and
 *         filled along the nozzle's motion so it stays attached; the camera leads the ship with a capped turn rate
 *  t 206  ship_flash (jump); t 212 fade to black, done(). The black is kept through stopAll()/the Tower
 *         teleport; after the level change an arrival Curtain holds black 1.5 s and fades in over 1.5 s.
 * </pre>
 * The ship is the open {@link ShipProp}'s tracker when one exists (taken over, never two ships), otherwise
 * a private rg_ship spawned at shipPos/shipYaw. Offsets scale with {@link ShipProp#SCALE}.
 */
final class Departure extends RisingPresentation.Scene {
    static final int SCAN_TICKS = 56, POWER = 56, TRANSMAT = 100, FLASH_END = 112, TAKEOFF = 116, FLIGHT = 90,
            JUMP = 206, BLACK = 212;
    /** W301: flight timing measured from the hangar roof (see {@link #measureLift}); JUMP/BLACK are the defaults. */
    private Flight flight = Flight.of(6.5);
    private int jumpAt = JUMP, blackAt = BLACK;

    private final Vec3 shipPos;
    private final float shipYaw;
    private final Vec3 forward, right;
    private RisingPresentation.Lock lock;
    private DummyTracker ship;
    private Vec3 shipNow;
    private boolean ghostHidden, black;
    private Vec3 framed;
    static final int CUT_END = 6;
    /** rg_ship bounding box centre is ~2.6 blocks (x SCALE/1.35) above its origin. */
    private Vec3 centre() { return shipPos.add(0, 2.6 * ShipProp.SCALE, 0); }

    Departure(ServerPlayer player, Vec3 shipPos, float shipYaw, Runnable done) {
        super(player, done);
        this.shipPos = shipPos;
        this.shipYaw = shipYaw;
        double r = Math.toRadians(shipYaw);
        forward = new Vec3(-Math.sin(r), 0, Math.cos(r));
        right = new Vec3(-Math.cos(r), 0, -Math.sin(r));
        shipNow = shipPos;
    }

    @Override void begin() {
        RisingPresentation.clearArrival(player);
        RisingPresentation.closeCurtains(player);
        lock = RisingPresentation.lock(player);
        lock.hideHud(true);
        kim.biryeong.destiny.hud.CombatHud.remove(player);
        for (var prop : RisingPresentation.scenes(player, ShipProp.class)) {
            var taken = prop.takeOver();
            if (ship == null) ship = taken;
            else if (taken != null) taken.close();
        }
        if (ship != null) ship.location(ModLocation.of(player.level(), shipPos, 0, shipYaw));
        else ship = ShipProp.spawn(player, shipPos, shipYaw);
        if (ship != null) ship.animate("idle", new AnimationModifier(0, 0, AnimationIterator.Type.LOOP));
        RisingPresentation.post(player, RisingPresentation.FADE);
        var g = GhostCompanion.ensure(player, null);
        float k = ShipProp.SCALE;
        g.scan(shipPos.add(0, 1.4 * k, 0), null, SCAN_TICKS, 6.0 * k, 2.6 * k, false);
        RisingAudio.sfxAt(player, "scan_loop", shipPos, 1f, .9f, 32f);
    }

    @Override void update(int t, int now) {
        if (t == 2) cut(vantage(SCAN_ANGLES, 11 * ShipProp.SCALE / 1.35, 4.5), centre());
        if (t == CUT_END) RisingPresentation.removePosts(player, RisingPresentation.FADE);
        if (t > CUT_END && t < TRANSMAT && framed != null) aim(centre(), .35f);
        if (t == POWER) {
            animate("power_up", AnimationIterator.Type.PLAY_ONCE);
            if (ship != null && !ship.isClosed()) ShipProp.engines(ship, true);
            RisingAudio.sfxAt(player, "ship_power", shipPos, 1.2f, 1f, 48f);
            GhostCompanion.existing(player).ifPresent(g -> g.hold(shipPos.add(right.scale(2.2 * ShipProp.SCALE)).add(0, 2.6 * ShipProp.SCALE, 0), shipPos));
        }
        if (t >= POWER && (t < TAKEOFF ? (t & 1) == 0 : t < jumpAt)) engines(t);
        if (t == TRANSMAT) {
            GhostCompanion.existing(player).ifPresent(g -> g.play("transmat", AnimationIterator.Type.PLAY_ONCE));
            RisingAudio.sfx(player, "transmat", .9f, 1f);
            RisingPresentation.post(player, RisingPresentation.REVIVE);
        }
        if (t == TRANSMAT + 3) {
            // Hidden by the flash: the Guardian is aboard; their view becomes the external camera.
            GhostCompanion.existing(player).ifPresent(g -> g.hidden(true));
            ghostHidden = true;
            lock.hideHud(true);
            cut(vantage(TAKEOFF_ANGLES, 15 * ShipProp.SCALE / 1.35, 1.0), centre());
        }
        if (t == FLASH_END) RisingPresentation.removePosts(player, RisingPresentation.REVIVE);
        if (t == TAKEOFF) {
            flight = Flight.of(measureLift());
            jumpAt = TAKEOFF + flight.total();
            blackAt = jumpAt + (BLACK - JUMP);
            DestinyGuardians.LOGGER.info("[GuardianRises] departure lift {} blocks, flight {} ticks", flight.lift(), flight.total());
            animate("takeoff", AnimationIterator.Type.HOLD_ON_LAST);
            RisingAudio.sfxAt(player, "ship_takeoff", shipPos, 1.2f, .85f, 96f);
        }
        if (t > TAKEOFF && t < jumpAt) fly(t - TAKEOFF);
        if (t == jumpAt) RisingPresentation.post(player, RisingPresentation.SHIP_FLASH);
        if (t == blackAt) {
            RisingPresentation.post(player, RisingPresentation.FADE);
            if (ship != null) { ship.close(); ship = null; }
            black = true;
            RisingPresentation.arrivalPending(player);
            complete(); // screen is black; the director teleports (black kept), then closes this handle
        }
    }

    private void animate(String clip, AnimationIterator.Type type) {
        if (ship != null && !ship.isClosed()) ship.animate(clip, new AnimationModifier(2, 2, type));
    }

    // ---------------------------------------------------------------- W301 flight (user: lift, then fast)
    /** Default lift/hover ends (ticks after TAKEOFF) for the minimum 6.5-block lift. */
    static final int LIFT = 34, HOVER = 46;
    static final double LIFT_HEIGHT = 6.5, BOOST_DISTANCE = 160, BOOST_RISE = 26, MAX_LIFT = 64;
    private Vec3 prevNozzleL, prevNozzleR;
    private float pitchNow;

    /**
     * W301 (user: rise out of the hangar, then fly away fast). {@code lift} = blocks to climb before the boost;
     * the lift lasts longer for taller climbs, then a short hover and a 44-tick cubic boost along the nose.
     */
    record Flight(double lift, int liftTicks, int hoverTicks, int total) {
        static Flight of(double lift) {
            lift = Math.clamp(lift, LIFT_HEIGHT, MAX_LIFT);
            int lt = (int) Math.round(LIFT + (lift - LIFT_HEIGHT) * 1.1);
            return new Flight(lift, lt, lt + 12, lt + 12 + 44);
        }
    }

    /** Default flight (6.5-block lift); kept for tests. */
    static double[] path(double t) { return path(Flight.of(LIFT_HEIGHT), t); }

    /**
     * One C1-continuous trajectory for model, exhaust and camera. Lift: vertical ease-in-out with the nose
     * settling up; hover: a short bob while the engines spool; boost: cubic acceleration along the nose (zero
     * start speed, so no jolt) with a climb. Returns {offset along forward, y-offset, pitch}.
     */
    static double[] path(Flight f, double t) {
        double ahead = 0, up, pitch;
        if (t <= f.liftTicks()) {
            double u = t / f.liftTicks(), e = u * u * (3 - 2 * u);
            up = f.lift() * e;
            pitch = -4 * e;
        } else if (t <= f.hoverTicks()) {
            double u = (t - f.liftTicks()) / (double) (f.hoverTicks() - f.liftTicks());
            up = f.lift() + .35 * Math.sin(u * Math.PI);
            pitch = -4 - 6 * (u * u * (3 - 2 * u));
        } else {
            double u = Math.min(1, (t - f.hoverTicks()) / (double) (f.total() - f.hoverTicks()));
            ahead = BOOST_DISTANCE * u * u * u;
            up = f.lift() + BOOST_RISE * u * u;
            pitch = -10 + 2 * u;
        }
        return new double[]{ahead, up, pitch};
    }

    /**
     * Blocks the ship must climb to clear the hangar: the highest solid block above the hull footprint
     * (and the first stretch of the boost lane) plus the hull height and a margin. Open sky gives the minimum.
     */
    private double measureLift() {
        var level = player.level();
        float k = ShipProp.SCALE;
        int base = (int) Math.floor(shipPos.y);
        int top = Integer.MIN_VALUE;
        for (double f = -4.5 * k; f <= 30; f += 1.5) {
            for (double sd = -3.5 * k; sd <= 3.5 * k; sd += 1.5) {
                Vec3 c = shipPos.add(forward.scale(f)).add(right.scale(sd));
                int x = (int) Math.floor(c.x), z = (int) Math.floor(c.z);
                for (int y = base + (int) (MAX_LIFT + 4); y > base + 1; y--) {
                    var pos = new net.minecraft.core.BlockPos(x, y, z);
                    if (!level.isLoaded(pos)) break;
                    if (!level.getBlockState(pos).getCollisionShape(level, pos).isEmpty()) { top = Math.max(top, y); break; }
                }
            }
        }
        if (top == Integer.MIN_VALUE) return LIFT_HEIGHT;
        return top + 1 - shipPos.y + 4.5 * k + 2;
    }

    private Vec3 pathPos(double t) {
        double[] p = path(flight, t);
        return shipPos.add(0, p[1], 0).add(forward.scale(p[0]));
    }

    /** World position of an engine nozzle (bbmodel engine_*_glow at x=+-12, y=40, z=+66 px) for a ship pose. */
    private Vec3 nozzle(Vec3 at, float pitch, int side) {
        float k = ShipProp.SCALE / 16f;
        double a = Math.toRadians(-pitch); // nose-up angle
        Vec3 fwd = forward.scale(Math.cos(a)).add(0, Math.sin(a), 0);
        Vec3 up = new Vec3(0, Math.cos(a), 0).subtract(forward.scale(Math.sin(a)));
        return at.add(right.scale(side * 12 * k)).add(up.scale(40 * k)).subtract(fwd.scale(70 * k));
    }

    private void fly(int t) {
        double[] p = path(flight, t);
        shipNow = shipPos.add(0, p[1], 0).add(forward.scale(p[0]));
        pitchNow = (float) p[2];
        if (ship != null && !ship.isClosed()) ship.location(ModLocation.of(player.level(), shipNow, pitchNow, shipYaw));
        // Camera: lead the ship by a quarter second of its own path; angular speed is capped so 20 Hz rotation
        // packets stay smooth (no snap when the boost starts).
        int hover = flight.hoverTicks();
        Vec3 lead = pathPos(Math.min(flight.total(), t + 5)).add(0, 2.6 * ShipProp.SCALE, 0);
        aimCapped(lead, t < hover ? .3f : .35f, t < hover ? 2.6f : 3.2f);
        if (t == hover) RisingAudio.sfxAt(player, "ship_takeoff", shipNow, 1.3f, 1.25f, 128f);
        if (t == 1) groundWash();
    }

    /** Dust blown out across the pad as the ship leaves the ground. */
    private void groundWash() {
        var level = player.level();
        for (int i = 0; i < 28; i++) {
            double a = i / 28.0 * Math.PI * 2;
            Vec3 d = new Vec3(Math.cos(a), 0, Math.sin(a));
            Vec3 at = shipPos.add(d.scale(2.2)).add(0, .2, 0);
            level.sendParticles(player, ParticleTypes.CLOUD, true, false, at.x, at.y, at.z, 0, d.x, .02, d.z, .35);
        }
    }

    /** Engine exhaust: emitted every tick and filled along the nozzle's path since the last tick (no gaps). */
    private void engines(int t) {
        var level = player.level();
        float pitch = t > TAKEOFF ? pitchNow : 0;
        Vec3 l = nozzle(shipNow, pitch, -1), rr = nozzle(shipNow, pitch, 1);
        boolean flying = t > TAKEOFF;
        var core = new DustParticleOptions(0xD6F7FF, flying ? 1.5f : 1.1f);
        var glow = new DustParticleOptions(0x5CC8FF, flying ? 2.4f : 1.6f);
        trail(level, prevNozzleL, l, core, glow, flying, t);
        trail(level, prevNozzleR, rr, core, glow, flying, t);
        prevNozzleL = l;
        prevNozzleR = rr;
    }

    private void trail(net.minecraft.server.level.ServerLevel level, Vec3 from, Vec3 to, DustParticleOptions core,
                       DustParticleOptions glow, boolean flying, int t) {
        Vec3 back = forward.scale(-1);
        if (from == null || !flying) {
            level.sendParticles(player, glow, true, false, to.x, to.y, to.z, 2, .08, .08, .08, 0);
            level.sendParticles(player, core, true, false, to.x, to.y, to.z, 1, .03, .03, .03, 0);
            if ((t & 3) == 0) level.sendParticles(player, ParticleTypes.END_ROD, true, false, to.x, to.y, to.z, 0, back.x, 0, back.z, .04);
            return;
        }
        double len = from.distanceTo(to);
        int n = (int) Math.min(40, Math.max(1, Math.ceil(len / .3)));
        for (int i = 1; i <= n; i++) {
            Vec3 at = from.lerp(to, i / (double) n);
            level.sendParticles(player, core, true, false, at.x, at.y, at.z, 1, .02, .02, .02, 0);
            if ((i & 1) == 0) level.sendParticles(player, glow, true, false, at.x, at.y, at.z, 1, .06, .06, .06, 0);
        }
        // Jet: short-lived streaks blown back out of the nozzle, plus hot sparks.
        level.sendParticles(player, ParticleTypes.END_ROD, true, false, to.x, to.y, to.z, 0, back.x, -.05, back.z, .18);
        if ((t & 1) == 0) level.sendParticles(player, ParticleTypes.FIREWORK, true, false, to.x, to.y, to.z, 0, back.x, 0, back.z, .12);
        if (len < .8) level.sendParticles(player, ParticleTypes.CLOUD, true, false, to.x, to.y - .4, to.z, 1, .15, .05, .15, .01);
    }

    /** {@link #aim} with a per-tick cap on the turn (degrees). */
    private void aimCapped(Vec3 target, float rate, float maxStep) {
        Vec3 eye = player.getEyePosition();
        float yaw = RisingPresentation.yawTo(eye, target), p = RisingPresentation.pitchTo(eye, target);
        float dy = yaw - player.getYRot();
        dy -= 360f * Math.round(dy / 360f);
        float dp = p - player.getXRot();
        dy = Math.clamp(dy * rate, -maxStep, maxStep);
        dp = Math.clamp(dp * rate, -maxStep, maxStep);
        if (Math.abs(dy) < .05f && Math.abs(dp) < .05f) return;
        RisingPresentation.look(player, player.getYRot() + dy, player.getXRot() + dp);
    }

    /** Angles (deg) from the ship's right axis toward its nose: 3/4 front views first, then sides. */
    static final double[] SCAN_ANGLES = {40, -40, 65, -65, 15, -15, 90, -90, 120, -120};
    /** Rear/side quarter for takeoff so the climb and forward run stay in frame. */
    static final double[] TAKEOFF_ANGLES = {-130, 130, -100, 100, -155, 155, -70, 70};

    /**
     * First collision-free spot on a ring around the ship with a clear line of sight to the hull centre.
     * Tries the preferred radius, then closer/further rings. Falls back to the player's own position.
     */
    private Vec3 vantage(double[] angles, double radius, double lift) {
        var level = player.level();
        float w = player.getBbWidth() / 2f, h = player.getBbHeight();
        Vec3 aim = centre();
        Vec3 fallback = null;
        for (double r : new double[]{radius, radius * .8, radius * 1.25, radius * .62}) {
            for (double a : angles) {
                double rad = Math.toRadians(a);
                Vec3 dir = right.scale(Math.cos(rad)).add(forward.scale(Math.sin(rad)));
                for (double up : new double[]{lift, lift + 1, lift + 2.5, lift - .8}) {
                    Vec3 feet = shipPos.add(dir.scale(r)).add(0, up, 0);
                    if (!level.noCollision(new AABB(feet.x - w, feet.y, feet.z - w, feet.x + w, feet.y + h, feet.z + w))) continue;
                    Vec3 eye = feet.add(0, player.getEyeHeight(), 0);
                    var hit = level.clip(new ClipContext(eye, aim, ClipContext.Block.COLLIDER, ClipContext.Fluid.NONE, player));
                    if (hit.getType() == HitResult.Type.MISS || hit.getLocation().distanceTo(aim) < 1.5) return feet;
                    if (fallback == null) fallback = feet;
                }
            }
        }
        return fallback != null ? fallback : player.position();
    }

    /** Hard cut (under black or a flash) to a camera spot looking at {@code aim}. */
    private void cut(Vec3 feet, Vec3 aim) {
        framed = feet;
        Vec3 eye = feet.add(0, player.getEyeHeight(), 0);
        lock.relocate(feet, RisingPresentation.yawTo(eye, aim), RisingPresentation.pitchTo(eye, aim));
    }

    /** Turns the view toward {@code target} by {@code rate} of the remaining angle (20 Hz rotation packets). */
    private void aim(Vec3 target, float rate) {
        Vec3 eye = player.getEyePosition();
        float yaw = RisingPresentation.yawTo(eye, target), p = RisingPresentation.pitchTo(eye, target);
        float dy = yaw - player.getYRot();
        dy -= 360f * Math.round(dy / 360f);
        if (Math.abs(dy) < .2f && Math.abs(p - player.getXRot()) < .2f) return;
        RisingPresentation.look(player, player.getYRot() + dy * rate, player.getXRot() + (p - player.getXRot()) * rate);
    }

    @Override boolean holdsBlack() { return black && !closed; }

    @Override void restore() {
        if (ship != null) { ship.close(); ship = null; }
        RisingPresentation.removePosts(player, RisingPresentation.REVIVE, RisingPresentation.SHIP_FLASH);
        if (!RisingPresentation.wantsBlack(player, this)) RisingPresentation.removePosts(player, RisingPresentation.FADE);
        RisingPresentation.holdHud(player, 10); // vanilla HUD first, combat HUD half a second later
        if (ghostHidden) GhostCompanion.existing(player).ifPresent(g -> g.hidden(false));
        if (lock != null) { RisingPresentation.unlock(lock); lock = null; }
        if (!player.hasDisconnected())
            for (String s : new String[]{"scan_loop", "ship_power", "ship_takeoff"})
                player.connection.send(new net.minecraft.network.protocol.game.ClientboundStopSoundPacket(RisingAudio.sfxId(s), null));
    }
}
