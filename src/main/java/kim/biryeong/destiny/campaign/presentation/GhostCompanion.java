package kim.biryeong.destiny.campaign.presentation;

import eu.pb4.polymer.virtualentity.api.ElementHolder;
import eu.pb4.polymer.virtualentity.api.attachment.ManualAttachment;
import eu.pb4.polymer.virtualentity.api.elements.BlockDisplayElement;
import kim.biryeong.destiny.DestinyGuardians;
import kim.biryeong.destiny.campaign.RisingServices;
import kim.biryeong.destiny.tutorial.TutorialGhost;
import kim.biryeong.destiny.weapon.WeaponAiming;
import kr.toxicity.model.api.BetterModel;
import kr.toxicity.model.api.animation.AnimationIterator;
import kr.toxicity.model.api.animation.AnimationModifier;
import kr.toxicity.model.api.mod.platform.ModLocation;
import kr.toxicity.model.api.mod.platform.ModPlayer;
import kr.toxicity.model.api.tracker.DummyTracker;
import net.minecraft.core.particles.DustParticleOptions;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.util.Brightness;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.Vec3;
import org.joml.Quaternionf;
import org.joml.Vector3f;

import java.util.*;

/**
 * The owner-only Ghost that accompanies one Guardian through the mission.
 * Body: BetterModel {@code rg_ghost} (clips idle/scan/speak/shell_open/shell_close/transmat/look);
 * when that model is not loaded it falls back to the existing tutorial Generalist Shell displays.
 *
 * <p>Follow framing: upper-right of the view and slightly ahead, never on the screen centre; during
 * ADS it retreats behind the right shoulder (out of the sight picture). Scans fly the Ghost to the
 * target and sweep a light fan (Polymer block displays + owner-only dust) across it; the fan's sweep
 * phase follows the world game time so it lines up with the {@code rg_scan} screen band.
 */
final class GhostCompanion {
    enum Mode { FOLLOW, HOLD, SCAN }

    private static final Map<UUID, GhostCompanion> ALL = new HashMap<>();
    static final int SWEEP_TICKS = 20; // == post_effect/guardian_rises/scan.json Fx.w (1.0 s)

    private final ServerPlayer owner;
    private final ServerLevel level;
    private Body body;
    private Vec3 pos;
    private Mode mode = Mode.FOLLOW;
    private Vec3 holdPos, holdLook;
    private Vec3 scanTarget;
    private double scanWidth, scanHeight;
    private int scanUntil = -1, scanStart = -1;
    /** W301: >0 = one slow top-to-bottom pass over the whole scan instead of looping 1 s sweeps. */
    private boolean scanOnce;
    private double scanFace = .28;
    private boolean scanVertical = true;
    private int speakingUntil = -1;
    private int followAt = -1;
    private int glideUntil = -1;
    private boolean speakingAnim, scanningAnim, hidden;
    /**
     * W301 (user): like D2 the Ghost lives inside its Guardian and only materialises when it has a job — cinematics
     * (HOLD), scans (SCAN), the shoulder hand-off after a cinematic, and darkness, where it lights the way.
     */
    private boolean materialized = true, dark;
    private int tuckAt = -1, keepUntil = -1, lightCheckAt, dissolveFrom = -1;
    static final int DISSOLVE_TICKS = 28;
    private final Light light;
    private ScanFan fan;

    private GhostCompanion(ServerPlayer owner, Vec3 start) {
        this.owner = owner;
        this.level = owner.level();
        this.pos = start;
        this.body = Body.create(owner, start);
        this.light = new Light(owner);
    }

    /** Existing companion or a new one appearing at {@code start} (or the follow slot when null). */
    static GhostCompanion ensure(ServerPlayer p, Vec3 start) {
        var g = ALL.get(p.getUUID());
        if (g != null && g.owner == p && g.level == p.level()) return g;
        if (g != null) g.destroy();
        g = new GhostCompanion(p, start != null ? start : followSlot(p, 0));
        ALL.put(p.getUUID(), g);
        return g;
    }

    static Optional<GhostCompanion> existing(ServerPlayer p) {
        var g = ALL.get(p.getUUID());
        return g != null && g.owner == p ? Optional.of(g) : Optional.empty();
    }

    static void remove(ServerPlayer p) {
        var g = ALL.remove(p.getUUID());
        if (g != null) g.destroy0();
    }

    static void tickAll(int now) {
        for (var g : List.copyOf(ALL.values())) {
            if (g.owner.hasDisconnected() || g.owner.isRemoved() || g.owner.level() != g.level) {
                ALL.remove(g.owner.getUUID(), g);
                g.destroy0();
                continue;
            }
            g.tick(now);
        }
    }

    static void clearAll() {
        for (var g : List.copyOf(ALL.values())) g.destroy0();
        ALL.clear();
    }

    boolean modelBacked() { return body instanceof ModelBody; }
    Vec3 position() { return pos; }
    Vec3 eye() { return pos.add(0, .02, 0); }

    void follow() {
        if (mode != Mode.FOLLOW) body.play("shell_close", AnimationIterator.Type.PLAY_ONCE);
        mode = Mode.FOLLOW; followAt = -1; stopScanVisuals();
    }

    /** Hovers at a fixed point, facing {@code look}. */
    void hold(Vec3 at, Vec3 look) { mode = Mode.HOLD; holdPos = at; holdLook = look; followAt = -1; stopScanVisuals(); }

    /** Returns to the shoulder slot with a slow ease (cinematic hand-off) over about {@code ticks}. */
    /**
     * W301 (user): "사라진 거 아니니까 걱정하지 마세요" — the Ghost dematerialises where it hovers: the petals part,
     * cyan motes peel off and drift toward its Guardian, the shell shrinks away and a last spark pops. It then stays
     * inside the Guardian until it is needed (darkness, scans, cinematics).
     */
    void dissolve() {
        mode = Mode.FOLLOW;
        followAt = -1;
        glideUntil = keepUntil = -1;
        stopScanVisuals();
        if (!materialized || hidden) return;
        int now = now();
        dissolveFrom = now;
        tuckAt = now + DISSOLVE_TICKS;
        body.play("dissolve", AnimationIterator.Type.PLAY_ONCE);
        RisingAudio.sfxAt(owner, "transmat", pos, .8f, 1.35f, 16f);
        RisingAudio.vanilla(owner, "block.amethyst_block.resonate", .35f, 1.6f);
    }

    private float yawTo(Vec3 t) { Vec3 d = t.subtract(pos); return (float) Math.toDegrees(-Math.atan2(d.x, d.z)); }
    private float pitchTo(Vec3 t) { Vec3 d = t.subtract(pos); return (float) Math.toDegrees(-Math.atan2(d.y, Math.sqrt(d.x * d.x + d.z * d.z))); }

    boolean dissolving() { return dissolveFrom >= 0; }

    private void dissolveFx(int now) {
        int age = now - dissolveFrom;
        Vec3 chest = owner.position().add(0, owner.getBbHeight() * .62, 0);
        Vec3 toward = chest.subtract(pos);
        double dist = toward.length();
        toward = dist < 1e-3 ? Vec3.ZERO : toward.scale(1 / dist);
        var rnd = level.getRandom();
        var cyan = new DustParticleOptions(0x5FE8FF, .28f);
        var white = new DustParticleOptions(0xD8F8FF, .2f);
        // Motes peel off the shell surface and drift a short way toward the Guardian (never into the lens).
        int motes = age < 8 ? 1 : age < 22 ? 2 : 1; // a light veil of motes, not a cloud (Vision r22)
        for (int i = 0; i < motes; i++) {
            Vec3 n = new Vec3(rnd.nextGaussian(), rnd.nextGaussian(), rnd.nextGaussian()).normalize();
            Vec3 at = pos.add(n.scale(.22 + .12 * rnd.nextDouble()));
            if (at.distanceToSqr(owner.getEyePosition()) < NEAR_EYE * NEAR_EYE) continue;
            level.sendParticles(owner, (i & 1) == 0 ? cyan : white, true, false, at.x, at.y, at.z, 1, .01, .01, .01, 0);
            Vec3 v = toward.scale(.035).add(n.scale(.012));
            if ((age + i) % 3 == 0) level.sendParticles(owner, ParticleTypes.END_ROD, true, false, at.x, at.y, at.z, 0, v.x, v.y, v.z, 1);
        }
        if (age % 4 == 0) level.sendParticles(owner, ParticleTypes.ELECTRIC_SPARK, true, false,
                pos.x, pos.y, pos.z, 2, .18, .18, .18, .02);
        if (age == DISSOLVE_TICKS - 2) {
            // The last pinpoint of light pops as the shell vanishes.
            level.sendParticles(owner, ParticleTypes.END_ROD, true, false, pos.x, pos.y, pos.z, 4, .03, .03, .03, .03);
            level.sendParticles(owner, ParticleTypes.ELECTRIC_SPARK, true, false, pos.x, pos.y, pos.z, 8, .1, .1, .1, .08);
            RisingAudio.vanilla(owner, "block.beacon.deactivate", .25f, 1.9f);
        }
    }

    void glide(int ticks) { follow(); glideUntil = now() + ticks; keepUntil = glideUntil + 30; }

    /** Keeps the current hold until server tick {@code tick}, then returns to the shoulder. */
    void followAt(int tick) { followAt = tick; }

    /**
     * Flies near {@code target} and sweeps it for {@code ticks}. width/height size the swept area;
     * {@code vertical} sweeps top to bottom (bodies, doors), otherwise left to right (hulls).
     * {@code from} is where the Ghost hovers, null to pick a point between the owner and the target.
     */
    void scan(Vec3 target, Vec3 from, int ticks, double width, double height, boolean vertical) {
        scanOnce = false;
        scanFace = .28;
        startScan(target, from, ticks, width, height, vertical);
    }

    /**
     * W301 opening: a single head-to-toe pass lasting the whole scan; the sweep plane sits {@code face}
     * blocks in front of the body so the light stays on screen while the camera follows it down.
     */
    void scanOnce(Vec3 target, Vec3 from, int ticks, double width, double height, double face) {
        scanOnce = true;
        scanFace = face;
        startScan(target, from, ticks, width, height, true);
    }

    /** 0..1 progress of a {@link #scanOnce} pass (eased: lingers a moment at the head and the feet). */
    double scanProgress(int now) {
        if (scanUntil <= scanStart) return 1;
        double u = Math.clamp((now - scanStart) / (double) (scanUntil - scanStart), 0, 1);
        return u * u * (3 - 2 * u);
    }

    private void startScan(Vec3 target, Vec3 from, int ticks, double width, double height, boolean vertical) {
        mode = Mode.SCAN;
        scanStart = now();
        followAt = -1;
        scanTarget = target;
        scanWidth = width;
        scanHeight = height;
        scanVertical = vertical;
        scanUntil = now() + ticks;
        Vec3 toOwner = owner.getEyePosition().subtract(target);
        Vec3 flat = new Vec3(toOwner.x, 0, toOwner.z);
        if (flat.lengthSqr() < 1e-4) flat = new Vec3(0, 0, 1);
        double stand = Math.min(Math.max(1.6, width * .9 + 1.2), Math.max(1.6, flat.length() - .6));
        holdPos = from != null ? from : target.add(flat.normalize().scale(stand)).add(0, height * .5 + .55, 0);
        if (fan != null) fan.destroy();
        fan = new ScanFan(owner, level, holdPos);
        if (!hidden) body.play("scan", AnimationIterator.Type.LOOP);
        scanningAnim = true;
    }

    boolean scanning() { return mode == Mode.SCAN && now() < scanUntil; }

    void speak(int untilTick) {
        speakingUntil = untilTick;
        if (!speakingAnim && !hidden) { body.play("speak", AnimationIterator.Type.LOOP); speakingAnim = true; }
    }

    void play(String clip, AnimationIterator.Type type) { if (!hidden) body.play(clip, type); }
    void stop(String clip) { body.stop(clip); }

    /** Hidden while transmatted (departure). Showing again re-spawns at the follow slot. */
    void hidden(boolean value) {
        if (hidden == value) return;
        hidden = value;
        stopScanVisuals();
        light.clear();
        body.close();
        body = value ? Body.NONE : Body.create(owner, pos = followSlot(owner, now()));
        materialized = !value;
        tuckAt = -1;
        speakingAnim = scanningAnim = false;
    }

    void destroy() { ALL.remove(owner.getUUID(), this); destroy0(); }

    private void destroy0() { stopScanVisuals(); light.clear(); body.close(); body = Body.NONE; }

    /** Raw light at the Guardian's eye (block or sky), with hysteresis so the Ghost does not flicker in and out. */
    private boolean dark() {
        var at = net.minecraft.core.BlockPos.containing(owner.getEyePosition());
        int lit = Math.max(level.getBrightness(net.minecraft.world.level.LightLayer.BLOCK, at),
                level.getBrightness(net.minecraft.world.level.LightLayer.SKY, at) - level.getSkyDarken());
        return dark ? lit < 9 : lit <= 5;
    }

    /**
     * W301 dynamic Ghost light: owner-only fake light blocks (client lighting only; the server world is untouched).
     * A strong light where the Guardian is looking (up to 28 blocks) and a softer glow at the shell. Moved at most
     * every 2 ticks; the real block state is re-sent whenever a light moves away or the Ghost tucks in.
     */
    static final class Light {
        static final double REACH = 28;
        private final ServerPlayer owner;
        private net.minecraft.core.BlockPos beam, glow;
        private int movedAt;

        Light(ServerPlayer owner) { this.owner = owner; }

        void update(ServerPlayer p, Vec3 shell, int now) {
            if (now - movedAt < 2) return;
            movedAt = now;
            var level = p.level();
            Vec3 eye = p.getEyePosition();
            Vec3 end = eye.add(p.getLookAngle().scale(REACH));
            var hit = level.clip(new net.minecraft.world.level.ClipContext(eye, end,
                    net.minecraft.world.level.ClipContext.Block.COLLIDER, net.minecraft.world.level.ClipContext.Fluid.NONE, p));
            net.minecraft.core.BlockPos target = hit.getType() == net.minecraft.world.phys.HitResult.Type.BLOCK
                    ? hit.getBlockPos().relative(hit.getDirection()) : net.minecraft.core.BlockPos.containing(end);
            beam = place(level, beam, air(level, target, eye), 15);
            glow = place(level, glow, air(level, net.minecraft.core.BlockPos.containing(shell), eye), 11);
        }

        /** First air block on the way back from {@code at} toward the eye (never inside geometry). */
        private static net.minecraft.core.BlockPos air(ServerLevel level, net.minecraft.core.BlockPos at, Vec3 eye) {
            Vec3 c = net.minecraft.world.phys.Vec3.atCenterOf(at);
            Vec3 step = eye.subtract(c);
            double len = step.length();
            if (len < 1e-3) return at;
            step = step.scale(1 / len);
            for (int i = 0; i < 4; i++) {
                var pos = net.minecraft.core.BlockPos.containing(c.add(step.scale(i)));
                if (level.isLoaded(pos) && level.getBlockState(pos).isAir()) return pos;
            }
            return null;
        }

        private net.minecraft.core.BlockPos place(ServerLevel level, net.minecraft.core.BlockPos old,
                                                   net.minecraft.core.BlockPos next, int brightness) {
            if (java.util.Objects.equals(old, next)) return old;
            if (owner.hasDisconnected()) return null;
            if (old != null && !old.equals(beam == old ? glow : beam))
                owner.connection.send(new net.minecraft.network.protocol.game.ClientboundBlockUpdatePacket(level, old));
            if (next != null) owner.connection.send(new net.minecraft.network.protocol.game.ClientboundBlockUpdatePacket(next,
                    Blocks.LIGHT.defaultBlockState().setValue(net.minecraft.world.level.block.LightBlock.LEVEL, brightness)));
            return next;
        }

        void clear() {
            if (beam == null && glow == null) return;
            if (!owner.hasDisconnected()) {
                var level = owner.level();
                for (var pos : new net.minecraft.core.BlockPos[]{beam, glow})
                    if (pos != null && level.isLoaded(pos))
                        owner.connection.send(new net.minecraft.network.protocol.game.ClientboundBlockUpdatePacket(level, pos));
            }
            beam = glow = null;
        }
    }

    private int now() { return owner.level().getServer().getTickCount(); }

    private void stopScanVisuals() {
        if (fan != null) { fan.destroy(); fan = null; }
        if (scanningAnim) { body.stop("scan"); scanningAnim = false; }
    }

    private static Vec3 followSlot(ServerPlayer p, int now) {
        double yaw = Math.toRadians(p.getYRot());
        Vec3 right = new Vec3(-Math.cos(yaw), 0, -Math.sin(yaw));
        Vec3 forward = new Vec3(-Math.sin(yaw), 0, Math.cos(yaw));
        boolean ads = WeaponAiming.progress(p) > .05f;
        // ~40 deg right of centre and above the crosshair; behind the shoulder while aiming down sights.
        // The tutorial Generalist Shell is ~0.7 block wide: keep it at the tutorial's own framing (2.1 ahead,
        // 1.25 right) so it reads as a companion instead of filling the corner of the screen.
        boolean shell = Body.TUTORIAL_SHELL;
        Vec3 offset = ads ? right.scale(shell ? 1.3 : .85).add(forward.scale(shell ? -.9 : -.75)).add(0, .65, 0)
                : shell ? right.scale(1.25).add(forward.scale(2.1)).add(0, .42, 0)
                : right.scale(1.05).add(forward.scale(.8)).add(0, .38, 0);
        return p.getEyePosition().add(offset).add(0, Math.sin(now / 14.0) * .045, 0);
    }

    private void tick(int now) {
        if (mode == Mode.SCAN && now >= scanUntil) follow();
        if (mode == Mode.HOLD && followAt >= 0 && now >= followAt) { followAt = -1; follow(); }
        if (speakingAnim && now >= speakingUntil) { body.stop("speak"); speakingAnim = false; }
        if (hidden) { light.clear(); return; }
        if (now >= lightCheckAt) { lightCheckAt = now + 10; dark = dark(); }
        if (dissolveFrom >= 0) {
            if (materialized && now < tuckAt) {
                dissolveFx(now);
                body.place(level, pos, yawTo(owner.getEyePosition()), pitchTo(owner.getEyePosition()), now, true);
                return;
            }
            dissolveFrom = -1;
            if (materialized) { tuckAt = -1; body.close(); body = Body.NONE; materialized = false; speakingAnim = false; }
        }
        boolean want = mode != Mode.FOLLOW || dark || now < glideUntil || now < keepUntil;
        if (want && !materialized) {
            tuckAt = -1;
            pos = clearOfTerrain(followSlot(owner, now));
            body = Body.create(owner, pos);
            body.play("transmat", AnimationIterator.Type.PLAY_ONCE);
            materialized = true;
            speakingAnim = false;
            scanningAnim = mode == Mode.SCAN;
            if (scanningAnim) body.play("scan", AnimationIterator.Type.LOOP);
        } else if (want && tuckAt >= 0) {
            // Needed again mid-tuck (e.g. a scan ends into a cinematic hold): grow back instead of staying shrunk.
            tuckAt = -1;
            body.play("transmat", AnimationIterator.Type.PLAY_ONCE);
        } else if (!want && materialized) {
            if (tuckAt < 0) { tuckAt = now + 12; body.play("transmat_out", AnimationIterator.Type.PLAY_ONCE); }
            else if (now >= tuckAt) {
                tuckAt = -1;
                stopScanVisuals();
                body.close();
                body = Body.NONE;
                materialized = false;
                speakingAnim = false;
            }
        }
        if (materialized && dark && tuckAt < 0) light.update(owner, eye(), now); else light.clear();
        if (!materialized) return;
        Vec3 target = switch (mode) {
            case FOLLOW -> clearOfTerrain(followSlot(owner, now));
            case HOLD, SCAN -> holdPos.add(0, Math.sin(now / 16.0) * .035, 0);
        };
        if (pos.distanceToSqr(target) > 256) pos = target;
        else pos = pos.lerp(target, mode != Mode.FOLLOW ? .14 : now < glideUntil ? .075 : .2);

        Vec3 look;
        if (mode == Mode.SCAN) look = sweepPoint(now, 0);
        else if (mode == Mode.HOLD) look = holdLook;
        else if (now < speakingUntil || Body.TUTORIAL_SHELL) look = owner.getEyePosition(); // the shell's eye faces its Guardian (tutorial framing)
        else look = owner.getEyePosition().add(owner.getLookAngle().scale(10));
        Vec3 d = look.subtract(pos);
        float yaw = (float) Math.toDegrees(-Math.atan2(d.x, d.z));
        float pitch = (float) Math.toDegrees(-Math.atan2(d.y, Math.sqrt(d.x * d.x + d.z * d.z)));
        body.place(level, pos, yaw, pitch, now, mode != Mode.FOLLOW);

        if (mode == Mode.SCAN && fan != null) {
            // The cross line of the fan sits on the camera when the target is the owner; draw rays only then.
            boolean self = scanTarget.distanceToSqr(owner.getEyePosition()) < 4;
            fan.update(eye(), sweepPoint(now, -1), sweepPoint(now, 0), sweepPoint(now, 1), !self);
            if ((now & 1) == 0) particles(now);
        }
    }

    /**
     * Keeps the follow slot out of walls/pillars (Vision r13: the shell was cut by a Divide pillar): if the line
     * from the eye to the slot, padded by the shell's radius, hits a block the Ghost slides back toward the eye.
     */
    private Vec3 clearOfTerrain(Vec3 slot) {
        Vec3 eye = owner.getEyePosition();
        Vec3 d = slot.subtract(eye);
        double len = d.length();
        if (len < 1e-3) return slot;
        Vec3 padded = eye.add(d.scale((len + SHELL_RADIUS) / len));
        var hit = level.clip(new net.minecraft.world.level.ClipContext(eye, padded,
                net.minecraft.world.level.ClipContext.Block.VISUAL, net.minecraft.world.level.ClipContext.Fluid.NONE, owner));
        if (hit.getType() == net.minecraft.world.phys.HitResult.Type.MISS) return slot;
        double free = Math.max(.6, hit.getLocation().distanceTo(eye) - SHELL_RADIUS);
        return eye.add(d.scale(Math.min(1, free / len)));
    }

    static final double SHELL_RADIUS = .45;

    /** Point on the current sweep line; side -1..1 across the swept area. */
    Vec3 sweepPoint(int now, double side) {
        long game = RisingPresentation.clientTime(level);
        double phase = scanOnce ? scanProgress(now)
                : Math.floorMod(game, SWEEP_TICKS) / (double) SWEEP_TICKS; // same phase as the rg_scan band
        Vec3 toGhost = pos.subtract(scanTarget);
        Vec3 flat = new Vec3(toGhost.x, 0, toGhost.z);
        flat = flat.lengthSqr() < 1e-4 ? new Vec3(0, 0, 1) : flat.normalize();
        Vec3 across = new Vec3(-flat.z, 0, flat.x);
        Vec3 face = scanTarget.add(flat.scale(scanFace)); // just in front of the surface so the light reads
        if (scanVertical) {
            double y = scanHeight * (.5 - phase);
            return face.add(0, y, 0).add(across.scale(side * scanWidth * .5));
        }
        double x = scanWidth * (phase - .5);
        return face.add(across.scale(x)).add(0, side * scanHeight * .5, 0);
    }

    /**
     * Sweep-line sparks. Vision r2 (o008): when the Ghost scans the owner's own body the sweep line passes
     * through the camera, and particles there fill the screen as huge squares; the dimmer ones fail the
     * blackout's cyan key and read as grey blocks. Nothing is emitted within {@link #NEAR_EYE} of the eye,
     * and only saturated cyan dust is used (no white END_ROD, which the key renders grey).
     */
    private void particles(int now) {
        var a = sweepPoint(now, -1);
        var b = sweepPoint(now, 1);
        var dust = new DustParticleOptions(0x38E6FF, .5f);
        Vec3 eye = owner.getEyePosition();
        for (int i = 0; i <= 8; i++) {
            Vec3 q = a.lerp(b, i / 8.0);
            if (q.distanceToSqr(eye) < NEAR_EYE * NEAR_EYE) continue;
            level.sendParticles(owner, dust, true, false, q.x, q.y, q.z, 1, .01, .01, .01, 0);
        }
    }

    static final double NEAR_EYE = 2.0;

    /** Owner-only light fan: three rays from the eye to the sweep line plus the line itself. */
    private static final class ScanFan {
        private final ElementHolder holder = new ElementHolder();
        private final Vec3 origin;
        private final List<BlockDisplayElement[]> beams = new ArrayList<>();

        ScanFan(ServerPlayer owner, ServerLevel level, Vec3 origin) {
            this.origin = origin;
            for (int i = 0; i < 4; i++) {
                var glow = element(Blocks.STAINED_GLASS.lightBlue().defaultBlockState());
                var core = element(Blocks.CONCRETE.lightBlue().defaultBlockState());
                beams.add(new BlockDisplayElement[]{glow, core});
                holder.addElement(glow);
                holder.addElement(core);
            }
            new ManualAttachment(holder, level, () -> this.origin);
            holder.startWatching(owner);
        }

        private static BlockDisplayElement element(BlockState state) {
            var e = new BlockDisplayElement(state);
            e.setBrightness(new Brightness(15, 15));
            e.setInterpolationDuration(2);
            e.setViewRange(1.5f);
            e.setScale(new Vector3f(0));
            return e;
        }

        void update(Vec3 eye, Vec3 left, Vec3 middle, Vec3 right, boolean crossLine) {
            beam(0, eye, left, .035f, .006f);
            beam(1, eye, middle, .05f, .008f);
            beam(2, eye, right, .035f, .006f);
            if (crossLine) beam(3, left, right, .06f, .012f);
            else hideBeam(3);
            holder.tick();
        }

        private void hideBeam(int index) {
            for (var e : beams.get(index)) { e.setScale(new Vector3f(0)); e.startInterpolationIfDirty(); }
        }

        private void beam(int index, Vec3 from, Vec3 to, float glowWidth, float coreWidth) {
            var pair = beams.get(index);
            Vec3 d = to.subtract(from);
            float length = (float) d.length();
            if (length < 1e-3) return;
            var dir = new Vector3f((float) d.x, (float) d.y, (float) d.z).normalize();
            var rotation = new Quaternionf().rotationTo(new Vector3f(0, 0, 1), dir);
            Vec3 rel = from.subtract(origin);
            set(pair[0], rotation, rel, glowWidth, length);
            set(pair[1], rotation, rel, coreWidth, length);
        }

        private static void set(BlockDisplayElement e, Quaternionf rotation, Vec3 rel, float width, float length) {
            // Unit block spans [0,1]^3: centre it on the ray in x/y, length along +z.
            var offset = rotation.transform(new Vector3f(-width / 2, -width / 2, 0));
            e.setLeftRotation(new Quaternionf(rotation));
            e.setScale(new Vector3f(width, width, length));
            e.setTranslation(offset.add((float) rel.x, (float) rel.y, (float) rel.z));
            e.startInterpolationIfDirty();
        }

        void destroy() { holder.destroy(); }
    }

    /** The visible Ghost: BetterModel tracker or the tutorial fallback. */
    private interface Body {
        Body NONE = new Body() {
            @Override public void place(ServerLevel l, Vec3 p, float y, float x, int now, boolean open) {}
            @Override public void play(String clip, AnimationIterator.Type type) {}
            @Override public void stop(String clip) {}
            @Override public void close() {}
        };

        void place(ServerLevel level, Vec3 pos, float yaw, float pitch, int now, boolean open);
        void play(String clip, AnimationIterator.Type type);
        void stop(String clip);
        void close();

        /**
         * W300 r13 (user): the campaign uses the original tutorial Generalist Shell Ghost (11 displays from the
         * extracted shell). The BetterModel rg_ghost remains selectable with -Ddestiny.guardianRises.ghostModel=bettermodel.
         */
        boolean TUTORIAL_SHELL = !"bettermodel".equalsIgnoreCase(System.getProperty("destiny.guardianRises.ghostModel"));

        static Body create(ServerPlayer owner, Vec3 start) {
            if (TUTORIAL_SHELL) return new FallbackBody(new TutorialGhost(owner, start), owner);
            var renderer = BetterModel.model(RisingServices.Models.GHOST).orElse(null);
            if (renderer != null) {
                try {
                    var tracker = renderer.create(ModLocation.of(owner.level(), start, 0, owner.getYRot()));
                    tracker.spawn(ModPlayer.of(owner.connection));
                    RisingPresentation.light(tracker, 12);
                    tracker.animate("idle", new AnimationModifier(0, 0, AnimationIterator.Type.LOOP));
                    return new ModelBody(tracker);
                } catch (RuntimeException e) {
                    DestinyGuardians.LOGGER.warn("Guardian Rises: rg_ghost spawn failed, using tutorial Ghost", e);
                }
            } else {
                DestinyGuardians.LOGGER.warn("Guardian Rises: BetterModel rg_ghost not loaded, using tutorial Ghost displays");
            }
            return new FallbackBody(new TutorialGhost(owner, start), owner);
        }
    }

    private static final class ModelBody implements Body {
        private final DummyTracker tracker;
        private Vec3 last = Vec3.ZERO;
        private float lastYaw = Float.NaN, lastPitch;

        ModelBody(DummyTracker tracker) { this.tracker = tracker; }

        @Override public void place(ServerLevel level, Vec3 pos, float yaw, float pitch, int now, boolean open) {
            if (tracker.isClosed()) return;
            if (pos.distanceToSqr(last) < 1e-5 && Math.abs(yaw - lastYaw) < .5f && Math.abs(pitch - lastPitch) < .5f) return;
            last = pos; lastYaw = yaw; lastPitch = pitch;
            tracker.location(ModLocation.of(level, pos, pitch, yaw));
        }

        @Override public void play(String clip, AnimationIterator.Type type) {
            if (!tracker.isClosed()) tracker.animate(clip, new AnimationModifier(3, 3, type));
        }

        @Override public void stop(String clip) { if (!tracker.isClosed()) tracker.stopAnimation(clip); }

        @Override public void close() { tracker.close(); }
    }

    /**
     * Tutorial Generalist Shell. Clip names map onto the shell's own motion: shell_open/scan/transmat open the
     * petals (scan wide, shell_open fully), speak flutters them slightly, transmat grows the shell in; the eye
     * follows the companion's gaze (scan sweep, hold target, owner).
     */
    private static final class FallbackBody implements Body {
        private final TutorialGhost ghost;
        private final ServerPlayer owner;
        private boolean open, scanning, speaking, dissolving;
        private int lookOnce = -1;

        FallbackBody(TutorialGhost ghost, ServerPlayer owner) { this.ghost = ghost; this.owner = owner; }

        @Override public void place(ServerLevel level, Vec3 pos, float yaw, float pitch, int now, boolean hold) {
            ghost.anchor(pos);
            double y = Math.toRadians(yaw), x = Math.toRadians(pitch);
            Vec3 dir = new Vec3(-Math.sin(y) * Math.cos(x), -Math.sin(x), Math.cos(y) * Math.cos(x));
            ghost.look(lookOnce > now ? owner.getEyePosition() : pos.add(dir.scale(4)));
            // W301 (user): at rest the shell stays closed — also while talking on the shoulder; it only parts while
            // scanning, when staged open in a cinematic, or flutters slightly when speaking during a cinematic hold.
            ghost.open(dissolving ? .7f : scanning ? .95f : open ? 1.15f : speaking && hold ? .14f : 0f);
            ghost.tick(now & ~1);
        }

        @Override public void play(String clip, AnimationIterator.Type type) {
            switch (clip) {
                case "shell_open" -> open = true;
                case "shell_close" -> open = false;
                case "scan" -> scanning = true;
                case "speak" -> speaking = true;
                case "transmat" -> ghost.transmat(18);
                case "transmat_out" -> ghost.vanish(10);
                case "dissolve" -> { open = false; dissolving = true; ghost.vanish(GhostCompanion.DISSOLVE_TICKS - 2); }
                case "look" -> lookOnce = owner.level().getServer().getTickCount() + 30;
                default -> { }
            }
        }

        @Override public void stop(String clip) {
            if (clip.equals("scan")) scanning = false;
            if (clip.equals("speak")) speaking = false;
            if (clip.equals("shell_open")) open = false;
        }

        @Override public void close() { ghost.destroy(); }
    }
}
