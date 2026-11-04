package kim.biryeong.destiny.campaign.fallen;

import kim.biryeong.destiny.DestinyGuardians;
import kim.biryeong.destiny.campaign.RisingServices;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;

import java.util.ArrayList;
import java.util.EnumMap;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * Walker boss (W300, original encounter design). One boss state ({@link Machine}) fed by a handful of
 * hit-region entities (four legs, a weakpoint and an armored hull) that never run AI. Cycle:
 * ARMORED (shoot any leg) -> LEG_BREAK -> STAGGER -> EXPOSED (weakpoint takes core damage) -> RECOVER -> ARMORED.
 * Core reaching zero kills the Walker. Each shot (attacker, direct entity, tick) is credited once.
 */
public final class WalkerBoss {
    private WalkerBoss() {}

    public enum Region {
        LEG_FL, LEG_FR, LEG_BL, LEG_BR, WEAKPOINT, HULL;
        public boolean leg() { return ordinal() <= LEG_BR.ordinal(); }
    }

    public enum Phase { ARMORED, LEG_BREAK, STAGGER, EXPOSED, RECOVER, DEAD }

    /**
     * All values original. legArmor/core scale with mission Difficulty.health. Durations are ticks.
     * weakpointMultiplier rewards accuracy (the weakpoint is a small box) without being required.
     */
    public record Tuning(double legArmor, double core, double weakpointMultiplier, double legRestore,
                         int legBreakTicks, int staggerTicks, int exposedTicks, int recoverTicks) {
        /**
         * W300 r3 calibration against the real first-mission rifle (halfdan_d: 3.45 per hit every 3 ticks, 33-round
         * magazine, 44-tick reload, full damage to 20.75 m, 76% at 30 m). Engaged player model: 55% of shots on a leg,
         * 45% on the weakpoint, reloads in lulls. Simulated: ~63 s over 2-3 windows at <=20 m, ~95 s at 30 m, perfect
         * aim still needs 2 windows (~28 s). Sweep in w300-evidence/fallen/r3/sweep; enforced by WalkerBossTest.
         */
        // W302: re-tuned (150/230 -> 215/330) for the mission's real Khvostov 7G-02 row (adaptive 600 RPM,
        // RisingLoadout.RIFLE), keeping the same 60-90 s / 2-3 window target in WalkerBossTest.
        public static final Tuning BASE = new Tuning(215, 330, 1.5, .6, 24, 22, 170, 38);
        public Tuning {
            if (legArmor <= 0 || core <= 0 || weakpointMultiplier < 1 || legRestore <= 0 || legRestore > 1)
                throw new IllegalArgumentException("walker pools");
            if (legBreakTicks <= 0 || staggerTicks <= 0 || exposedTicks <= 0 || recoverTicks <= 0)
                throw new IllegalArgumentException("walker timing");
        }
        public Tuning scaled(double health) {
            double h = FallenArchetypes.positive(health);
            return new Tuning(legArmor * h, core * h, weakpointMultiplier, legRestore,
                    legBreakTicks, staggerTicks, exposedTicks, recoverTicks);
        }
    }

    public enum Outcome { LEG_DAMAGE, LEG_BROKEN, CORE_DAMAGE, KILLED, DEFLECTED, DUPLICATE }

    /** applied is the pool damage actually credited (0 for deflect/duplicate). */
    public record Hit(Outcome outcome, double applied, Phase phase) {
        public boolean accepted() { return applied > 0; }
    }

    /** Pure boss state. No Minecraft types; unit tested. */
    public static final class Machine {
        private final Tuning tuning;
        private final double[] legs = new double[4];
        private double core;
        private Phase phase = Phase.ARMORED;
        private int phaseTicks, cycles;
        private long now;
        private Region brokenLeg;
        private final Map<Object, Long> credited = new HashMap<>();

        public Machine(Tuning tuning) {
            this.tuning = tuning;
            java.util.Arrays.fill(legs, tuning.legArmor());
            core = tuning.core();
        }

        public Phase phase() { return phase; }
        public double core() { return core; }
        public double coreFraction() { return core / tuning.core(); }
        public double leg(Region r) { return r.leg() ? legs[r.ordinal()] : 0; }
        public double legArmorTotal() { double t = 0; for (double v : legs) t += v; return t; }
        public int cycles() { return cycles; }
        public int phaseTicks() { return phaseTicks; }
        public Region brokenLeg() { return brokenLeg; }
        public Tuning tuning() { return tuning; }
        public long now() { return now; }

        /** Which region can currently take damage (for UI hints / AI). */
        public boolean vulnerable(Region region) {
            return switch (phase) {
                case ARMORED -> region.leg() && legs[region.ordinal()] > 0;
                case EXPOSED -> region == Region.WEAKPOINT;
                default -> false;
            };
        }

        /**
         * Credit damage. A shot key that already landed on any region is a duplicate; a deflected hit
         * does not consume the key, so a splash that touched the hull first still reaches a leg.
         */
        public Hit hit(Region region, double amount, Object shotKey) {
            if (phase == Phase.DEAD) return new Hit(Outcome.DEFLECTED, 0, phase);
            if (!(amount > 0) || !Double.isFinite(amount) || !vulnerable(region)) return new Hit(Outcome.DEFLECTED, 0, phase);
            if (shotKey != null && credited.containsKey(shotKey)) return new Hit(Outcome.DUPLICATE, 0, phase);
            if (shotKey != null) credited.put(shotKey, now);
            if (region.leg()) {
                int i = region.ordinal();
                double applied = Math.min(legs[i], amount);
                legs[i] -= applied;
                if (legs[i] <= 1e-6) {
                    legs[i] = 0;
                    brokenLeg = region;
                    enter(Phase.LEG_BREAK);
                    return new Hit(Outcome.LEG_BROKEN, applied, phase);
                }
                return new Hit(Outcome.LEG_DAMAGE, applied, phase);
            }
            double applied = Math.min(core, amount * tuning.weakpointMultiplier());
            core -= applied;
            if (core <= 1e-6) {
                core = 0;
                enter(Phase.DEAD);
                return new Hit(Outcome.KILLED, applied, phase);
            }
            return new Hit(Outcome.CORE_DAMAGE, applied, phase);
        }

        /** Advance one tick. Returns the phase entered this tick, or null. */
        public Phase tick() {
            now++;
            if (!credited.isEmpty()) credited.values().removeIf(t -> now - t > 2);
            phaseTicks++;
            Phase next = switch (phase) {
                case LEG_BREAK -> phaseTicks >= tuning.legBreakTicks() ? Phase.STAGGER : null;
                case STAGGER -> phaseTicks >= tuning.staggerTicks() ? Phase.EXPOSED : null;
                case EXPOSED -> phaseTicks >= tuning.exposedTicks() ? Phase.RECOVER : null;
                case RECOVER -> phaseTicks >= tuning.recoverTicks() ? Phase.ARMORED : null;
                default -> null;
            };
            if (next == null) return null;
            if (next == Phase.ARMORED) {
                cycles++;
                if (brokenLeg != null) legs[brokenLeg.ordinal()] = tuning.legArmor() * tuning.legRestore();
                // Never leave every leg at zero: a fresh cycle always has a target.
                boolean any = false;
                for (double v : legs) any |= v > 0;
                if (!any) java.util.Arrays.fill(legs, tuning.legArmor() * tuning.legRestore());
                brokenLeg = null;
            }
            enter(next);
            return next;
        }

        private void enter(Phase next) { phase = next; phaseTicks = 0; }
    }

    /** Shot identity for de-duplication: same attacker + same direct entity in the same server tick. */
    public record ShotKey(int attacker, int direct, long tick) {
        static ShotKey of(DamageSource source, long tick) {
            var a = source.getEntity();
            var d = source.getDirectEntity();
            return new ShotKey(a == null ? -1 : a.getId(), d == null ? -1 : d.getId(), tick);
        }
    }

    // ---------------------------------------------------------------- layout (anchor-local, yaw 0 faces +Z)

    /** Region box: center offset (right, up, forward) and size. Tune against rg_walker bones leg_* / weakpoint. */
    record Box(double x, double y, double z, float width, float height) {}

    static final Map<Region, Box> LAYOUT = new EnumMap<>(Region.class);
    static {
        LAYOUT.put(Region.LEG_FL, new Box(-2.3, 0, 2.0, 1.25f, 4.0f));
        LAYOUT.put(Region.LEG_FR, new Box(2.3, 0, 2.0, 1.25f, 4.0f));
        LAYOUT.put(Region.LEG_BL, new Box(-2.3, 0, -2.0, 1.25f, 4.0f));
        LAYOUT.put(Region.LEG_BR, new Box(2.3, 0, -2.0, 1.25f, 4.0f));
        LAYOUT.put(Region.HULL, new Box(0, 3.7, -.2, 4.0f, 2.1f));
        LAYOUT.put(Region.WEAKPOINT, new Box(0, 2.75, 1.6, 1.1f, 1.1f));
    }

    static Vec3 offset(Box b, float yawDegrees) {
        double r = Math.toRadians(yawDegrees);
        double sin = Math.sin(r), cos = Math.cos(r);
        // Minecraft: forward for yaw is (-sin, cos); right is (-cos, -sin).
        double fx = -sin, fz = cos, rx = -cos, rz = -sin;
        return new Vec3(b.x() * rx + b.z() * fx, b.y(), b.x() * rz + b.z() * fz);
    }

    // ---------------------------------------------------------------- runtime

    /** Arena radius around the spawn point the Walker may roam. */
    /** The Walker holds its arena centre (spawn marker) and pivots; it never retreats from the player. */
    static final double ARENA_RADIUS = 8;
    /** Waypoints sit on the player's side of the centre, at most this far out. */
    static final double ADVANCE = 5;
    static final double WALK_SPEED = .055;

    public static final class Runtime {
        final FallenMob anchor;
        final Machine machine;
        final Vec3 arena;
        final EnumMap<Region, FallenMob> parts = new EnumMap<>(Region.class);
        private boolean disposing;
        private ServerPlayer target;
        private int retarget, cannonCooldown = 80, apCooldown = 40, chargeTicks = -1, apTelegraph = -1;
        private int apBurstLeft, apGap, waypointTicks, sparkTicks;
        private Vec3 cannonTarget, waypoint;
        private ServerLevel level;
        private final FallenCallouts callouts = new FallenCallouts();
        private int armorImpactTick = -100, steps;
        private boolean landed;
        private boolean opened;

        Runtime(FallenMob anchor, Tuning tuning) {
            this.anchor = anchor;
            this.machine = new Machine(tuning);
            this.arena = anchor.position();
            this.level = (ServerLevel) anchor.level();
        }

        public Machine machine() { return machine; }

        void spawnParts() {
            if (!landed) { landed = true; FallenSounds.play(level, anchor.position().add(0, 2, 0), FallenSounds.Ev.WALKER_LAND); }
            for (Region region : Region.values()) ensurePart(region);
            placeParts();
        }

        private void ensurePart(Region region) {
            var existing = parts.get(region);
            if (existing != null && !existing.isRemoved()) return;
            var part = RisingFallen.WALKER_PART.create(level, EntitySpawnReason.EVENT);
            if (part == null) return;
            part.bindPart(this, region, LAYOUT.get(region));
            Vec3 at = anchor.position().add(offset(LAYOUT.get(region), anchor.getYRot()));
            part.snapTo(at.x, at.y, at.z, anchor.getYRot(), 0);
            level.addFreshEntity(part);
            parts.put(region, part);
        }

        private void placeParts() {
            float yaw = anchor.getYRot();
            for (var e : parts.entrySet()) {
                var part = e.getValue();
                if (part.isRemoved()) continue;
                Vec3 at = anchor.position().add(offset(LAYOUT.get(e.getKey()), yaw));
                part.setPos(at.x, at.y, at.z);
                part.setYRot(yaw);
                // Pool lives in the Machine; the part only displays the last hit number.
                if (part.getHealth() < part.getMaxHealth() && part.isAlive()) part.setHealth(part.getMaxHealth());
            }
        }

        /** A region entity was hit. Returns the amount the part should show as taken (0 = deflected). */
        float partHit(Region region, DamageSource source, float amount, Vec3 hitPos) {
            if (disposing || anchor.isDeadOrDying()) return 0;
            if (source.getEntity() instanceof LivingEntity attacker && attacker != anchor) anchor.aggro(attacker);
            var hit = machine.hit(region, amount, ShotKey.of(source, level.getServer().getTickCount()));
            Vec3 at = hitPos != null ? hitPos : parts.get(region).position();
            switch (hit.outcome()) {
                case DEFLECTED -> {
                    if (sparkTicks <= 0) {
                        sparkTicks = 3;
                        level.sendParticles(ParticleTypes.CRIT, at.x, at.y, at.z, 4, .15, .15, .15, .2);
                        if (anchor.tickCount - armorImpactTick >= 8) {
                            armorImpactTick = anchor.tickCount;
                            FallenSounds.play(level, at, FallenSounds.Ev.WALKER_ARMOR_IMPACT, .5f, 1f);
                        }
                    }
                }
                case LEG_DAMAGE -> {
                    level.sendParticles(ParticleTypes.ELECTRIC_SPARK, at.x, at.y, at.z, 3, .2, .2, .2, .1);
                    // Armour plates chipping off: a metal tick at most every 3 ticks.
                    if (sparkTicks <= 0) {
                        sparkTicks = 3;
                        level.playSound(null, at.x, at.y, at.z, SoundEvents.IRON_GOLEM_HURT, SoundSource.HOSTILE, .45f, 1.7f);
                    }
                }
                case LEG_BROKEN -> legBroken(region);
                case CORE_DAMAGE -> level.sendParticles(FallenWeapons.dust(0xFFD27A, 1.2f), at.x, at.y, at.z, 4, .2, .2, .2, 0);
                case KILLED -> killed(source);
                default -> {}
            }
            return (float) hit.applied();
        }

        private void legBroken(Region region) {
            var part = parts.get(region);
            Vec3 at = part == null ? anchor.position() : part.position().add(0, 2.2, 0);
            FallenVfx.legBreak(level, at);
            level.sendParticles(ParticleTypes.EXPLOSION, at.x, at.y, at.z, 2, .4, .6, .4, 0);
            level.sendParticles(ParticleTypes.LAVA, at.x, at.y, at.z, 12, .4, .8, .4, 0);
            level.sendParticles(ParticleTypes.LARGE_SMOKE, at.x, at.y, at.z, 16, .5, 1, .5, .02);
            FallenSounds.play(level, at, FallenSounds.Ev.WALKER_LEG_EXPLO);
            chargeTicks = -1;
            apBurstLeft = 0;
            apTelegraph = -1;
            anchor.models().charge(false, 0);
            anchor.models().play(FallenModels.Action.LEG_BREAK);
            // The break happens inside Machine.hit (not tick): log + callout here.
            enter(Phase.LEG_BREAK);
            // Readable break: shockwave ring + a second, lower crunch so it is heard over gunfire.
            FallenWeapons.groundWarning(level, new Vec3(at.x, anchor.getY() + .1, at.z), 2.5, 0xFFB347);
            FallenSounds.play(level, at, FallenSounds.Ev.WALKER_STEP_RUMBLE);
        }

        private void killed(DamageSource source) {
            Vec3 at = anchor.position().add(0, 3, 0);
            level.sendParticles(ParticleTypes.EXPLOSION_EMITTER, at.x, at.y, at.z, 1, 0, 0, 0, 0);
            FallenSounds.play(level, at, FallenSounds.Ev.WALKER_EXPLODE);
            FallenVfx.walkerDeath(level, at);
            if (source.getEntity() instanceof ServerPlayer p) anchor.setLastHurtByPlayer(p, 100);
            DestinyGuardians.LOGGER.info("[Walker] phase=DEAD legArmor={}/{} core=0/{} cycles={} pos={}",
                    Math.round(machine.legArmorTotal()), Math.round(machine.tuning().legArmor() * 4),
                    Math.round(machine.tuning().core()), machine.cycles(), anchor.blockPosition().toShortString());
            callout(FallenCallouts.Cue.DOWN);
            for (var part : List.copyOf(parts.values())) if (!part.isRemoved()) part.discard();
            parts.clear();
            anchor.bossKilled(source);
        }

        void tick(ServerLevel level, boolean active) {
            this.level = level;
            if (sparkTicks > 0) sparkTicks--;
            if (anchor.isDeadOrDying()) return;
            Phase entered = machine.tick();
            if (entered != null) enter(entered);
            if (machine.phase() == Phase.DEAD) return;
            if (level.getServer().getTickCount() % 20 == 0) for (Region r : Region.values()) ensurePart(r);
            if (active) {
                if (--retarget <= 0 || target == null || !FallenBrain.validTarget(anchor, target, 56)) {
                    retarget = 20;
                    target = FallenBrain.nearestPlayer(anchor, 56);
                }
                if (!opened && target != null) {
                    opened = true;
                    callout(FallenCallouts.Cue.LEGS);
                    FallenSounds.play(level, anchor.position().add(0, 4, 0), FallenSounds.Ev.WALKER_INTIMIDATE);
                }
                switch (machine.phase()) {
                    case ARMORED -> armored(level);
                    case EXPOSED -> exposed(level);
                    default -> {}
                }
            }
            placeParts();
        }

        private void enter(Phase phase) {
            DestinyGuardians.LOGGER.info("[Walker] phase={} legArmor={}/{} core={}/{} cycles={} pos={}",
                    phase, Math.round(machine.legArmorTotal()), Math.round(machine.tuning().legArmor() * 4),
                    Math.round(machine.core()), Math.round(machine.tuning().core()), machine.cycles(),
                    anchor.blockPosition().toShortString());
            FallenCallouts.forPhase(phase).ifPresent(this::callout);
            var models = anchor.models();
            switch (phase) {
                case STAGGER -> {
                    models.play(FallenModels.Action.STAGGER);
                    Vec3 at = anchor.position().add(0, 3, 0);
                    FallenSounds.play(level, at, FallenSounds.Ev.WALKER_STEP_RUMBLE, 1f, .85f);
                    FallenVfx.emp(level, at);
                }
                case EXPOSED -> {
                    models.hold(FallenModels.Action.WEAKPOINT_OPEN);
                    Vec3 at = weakpointCenter();
                    level.playSound(null, at.x, at.y, at.z, SoundEvents.BEACON_ACTIVATE, SoundSource.HOSTILE, 3f, 1.4f);
                    FallenWeapons.flash(level, at.x, at.y, at.z);
                    FallenVfx.weakpointExpose(level, at);
                }
                case RECOVER -> {
                    models.play(FallenModels.Action.RECOVER);
                    Vec3 at = anchor.position().add(0, 3, 0);
                    FallenSounds.play(level, at, FallenSounds.Ev.WALKER_WEAKSPOT_CLOSE);
                }
                case ARMORED -> {
                    models.base(FallenModels.Action.IDLE);
                    FallenSounds.play(level, anchor.position().add(0, 4, 0), FallenSounds.Ev.WALKER_INTIMIDATE);
                    cannonCooldown = Math.max(cannonCooldown, 50);
                }
                default -> {}
            }
        }

        private Vec3 weakpointCenter() {
            var box = LAYOUT.get(Region.WEAKPOINT);
            return anchor.position().add(offset(box, anchor.getYRot())).add(0, box.height() / 2, 0);
        }

        private void exposed(ServerLevel level) {
            if (machine.phaseTicks() % 4 == 0) {
                Vec3 at = weakpointCenter();
                level.sendParticles(FallenWeapons.dust(0xFFC14D, 1.6f), at.x, at.y, at.z, 6, .3, .3, .3, 0);
                FallenVfx.weakpointPulse(level, at);
                level.sendParticles(ParticleTypes.ELECTRIC_SPARK, at.x, at.y, at.z, 2, .25, .25, .25, .05);
                // Closing warning in the last 1.5 s.
                if (machine.phaseTicks() > machine.tuning().exposedTicks() - 30 && machine.phaseTicks() % 8 == 0)
                    level.playSound(null, at.x, at.y, at.z, SoundEvents.NOTE_BLOCK_BIT.value(), SoundSource.HOSTILE, 1.5f, .8f);
            }
        }

        private void armored(ServerLevel level) {
            var arch = anchor.archetype();
            // Face the target slowly; a 2-3 block-per-second walk inside the arena.
            if (target != null) {
                float want = FallenBrain.yawTo(anchor.position(), target.position());
                float yaw = FallenBrain.approachAngle(anchor.getYRot(), want, chargeTicks >= 0 ? 1.2f : 2.4f);
                anchor.setYRot(yaw); anchor.setYBodyRot(yaw); anchor.setYHeadRot(yaw);
            }
            walk(level);
            // Main cannon: long telegraph with a ground warning ring where the shell will land.
            if (chargeTicks >= 0) {
                chargeTicks++;
                Vec3 muzzle = muzzle(arch.primary().splashRadius());
                FallenWeapons.charge(level, muzzle, FallenArchetypes.WALKER_ORANGE, chargeTicks, arch.primary().telegraphTicks(), 1.8f);
                if (cannonTarget != null && chargeTicks % 3 == 0)
                    FallenWeapons.groundWarning(level, cannonTarget, arch.primary().splashRadius(), FallenArchetypes.WALKER_ORANGE);
                if (chargeTicks >= arch.primary().telegraphTicks()) {
                    anchor.models().charge(false, 0);
                    if (cannonTarget != null)
                        FallenWeapons.lob(level, anchor, muzzle, cannonTarget, arch.primary().projectileSpeed(),
                                arch.primary().damageFraction(), arch.primary().splashRadius(), FallenArchetypes.WALKER_ORANGE);
                    anchor.models().play(FallenModels.Action.FIRE);
                    FallenSounds.play(level, muzzle, FallenSounds.Ev.WALKER_CANNON_FIRE);
                    chargeTicks = -1;
                    cannonCooldown = FallenArchetypes.cooldown(arch.primary(), anchor.getRandom().nextDouble());
                }
                return;
            }
            if (cannonCooldown > 0) cannonCooldown--;
            if (apCooldown > 0) apCooldown--;
            if (target == null) return;
            double dist = anchor.position().distanceTo(target.position());
            if (cannonCooldown <= 0 && apBurstLeft == 0 && apTelegraph < 0
                    && dist >= arch.primary().rangeMin() && dist <= arch.primary().rangeMax()) {
                chargeTicks = 0;
                anchor.models().charge(true, FallenArchetypes.WALKER_ORANGE);
                // Aim where the target is now: a readable telegraph the player can walk out of.
                cannonTarget = FallenWeapons.groundBelow(level, target.position());
                Vec3 m = muzzle(0);
                level.playSound(null, m.x, m.y, m.z, SoundEvents.WARDEN_SONIC_CHARGE, SoundSource.HOSTILE, 2.5f, .7f);
                return;
            }
            // Anti-personnel guns: short telegraph, burst of fast bolts.
            var ap = arch.secondary();
            if (apTelegraph >= 0) {
                apTelegraph++;
                FallenWeapons.charge(level, muzzle(0).add(0, -.6, 0), FallenArchetypes.ARC_BLUE, apTelegraph, ap.telegraphTicks(), .9f);
                if (apTelegraph >= ap.telegraphTicks()) { anchor.models().charge(false, 0); apTelegraph = -1; apBurstLeft = ap.burst(); apGap = 0; }
                return;
            }
            if (apBurstLeft > 0) {
                if (--apGap <= 0) {
                    apGap = ap.burstGap();
                    apBurstLeft--;
                    if (FallenBrain.validTarget(anchor, target, 56)) {
                        Vec3 from = muzzle(0).add(0, -.6, 0);
                        Vec3 dir = FallenWeapons.aim(anchor, target, from, ap.projectileSpeed(), arch.accuracy());
                        FallenWeapons.bolt(level, anchor, from, dir, ap.projectileSpeed(), ap.damageFraction(), 0,
                                FallenArchetypes.ARC_BLUE, FallenWeapons.Style.ARC);
                        FallenSounds.play(level, from, FallenSounds.Ev.WALKER_NOSE_FIRE);
                    }
                    if (apBurstLeft == 0) apCooldown = FallenArchetypes.cooldown(ap, anchor.getRandom().nextDouble());
                }
                return;
            }
            if (apCooldown <= 0 && dist <= ap.rangeMax() && anchor.getSensing().hasLineOfSight(target)) {
                apTelegraph = 0;
                anchor.models().charge(true, FallenArchetypes.ARC_BLUE);
                Vec3 m = muzzle(0);
                FallenSounds.play(level, m, FallenSounds.Ev.WALKER_NOSE_OPEN);
            }
        }

        private Vec3 muzzle(double ignored) {
            float yaw = anchor.getYRot();
            return anchor.position().add(offset(new Box(0, 4.3, 4.9, 0, 0), yaw));
        }

        private void walk(ServerLevel level) {
            if (chargeTicks >= 0) { anchor.models().base(FallenModels.Action.IDLE); return; }
            if (waypoint == null || --waypointTicks <= 0 || horizontal(anchor.position(), waypoint) < .4) {
                waypointTicks = 100 + anchor.getRandom().nextInt(80);
                waypoint = clampArena(holdPoint(arena, target == null ? null : target.position(),
                        anchor.getRandom().nextDouble() * 2 - 1, anchor.getRandom().nextDouble()));
            }
            Vec3 pos = anchor.position();
            Vec3 delta = waypoint.subtract(pos).multiply(1, 0, 1);
            double len = delta.length();
            if (len < .4) { anchor.models().base(FallenModels.Action.IDLE); return; }
            Vec3 step = delta.scale(Math.min(WALK_SPEED, len) / len);
            Vec3 next = clampArena(pos.add(step));
            var body = new AABB(next.x - 2.6, next.y + .2, next.z - 2.6, next.x + 2.6, next.y + 5, next.z + 2.6);
            if (!level.noCollision(body)) { waypoint = null; anchor.models().base(FallenModels.Action.IDLE); return; }
            anchor.setPos(next.x, arena.y, next.z);
            anchor.models().base(FallenModels.Action.MOVE);
            if (anchor.tickCount % 22 == 0)
            {
                FallenSounds.play(level, next, FallenSounds.Ev.WALKER_STEP);
                if (++steps % 2 == 0) FallenSounds.play(level, next, FallenSounds.Ev.WALKER_STEP_RUMBLE, .7f, 1f);
            }
        }

        private Vec3 clampArena(Vec3 p) { return WalkerBoss.clampArena(arena, p); }

        private static double horizontal(Vec3 a, Vec3 b) {
            double dx = a.x - b.x, dz = a.z - b.z;
            return Math.sqrt(dx * dx + dz * dz);
        }

        /** Ghost callout to every player in this fight (same level, within 72 blocks), deduped per cycle. */
        private void callout(FallenCallouts.Cue cue) {
            var presentation = kim.biryeong.destiny.campaign.RisingServices.presentation().orElse(null);
            if (presentation == null || level == null) return;
            if (callouts.request(cue, machine.cycles(), level.getServer().getTickCount()).isEmpty()) return;
            Vec3 at = anchor.position();
            for (ServerPlayer p : level.players()) {
                if (!p.isAlive() || p.isSpectator() || p.position().distanceToSqr(at) > 72 * 72) continue;
                try { presentation.voice(p, cue.lineId); }
                catch (RuntimeException e) { DestinyGuardians.LOGGER.warn("Walker callout {} failed: {}", cue, e.toString()); }
            }
        }

        void dispose() {
            if (disposing) return;
            disposing = true;
            for (var part : new ArrayList<>(parts.values())) if (!part.isRemoved()) part.discard();
            parts.clear();
        }

        boolean disposing() { return disposing; }
    }

    /**
     * Where the Walker should stand: on the player's side of the arena centre, ADVANCE blocks out, swaying
     * sideways by {@code sway} (-1..1) * 3 blocks. Never further from the player than the centre itself.
     */
    static Vec3 holdPoint(Vec3 arena, Vec3 player, double sway, double depth) {
        if (player == null) return arena;
        Vec3 to = player.subtract(arena).multiply(1, 0, 1);
        if (to.lengthSqr() < 1e-4) return arena;
        Vec3 dir = to.normalize();
        Vec3 side = new Vec3(-dir.z, 0, dir.x);
        double out = Math.min(ADVANCE * (.5 + .5 * Math.max(0, Math.min(1, depth))), Math.max(0, to.length() - 12));
        return arena.add(dir.scale(out)).add(side.scale(Math.max(-1, Math.min(1, sway)) * 3));
    }

    static Vec3 clampArena(Vec3 arena, Vec3 p) {
        Vec3 d = p.subtract(arena).multiply(1, 0, 1);
        if (d.length() <= ARENA_RADIUS) return new Vec3(p.x, arena.y, p.z);
        d = d.normalize().scale(ARENA_RADIUS);
        return new Vec3(arena.x + d.x, arena.y, arena.z + d.z);
    }

    static Runtime create(FallenMob anchor, RisingServices.Difficulty tuning) {
        var runtime = new Runtime(anchor, Tuning.BASE.scaled(tuning.health()));
        DestinyGuardians.LOGGER.debug("Walker spawned at {}", anchor.position());
        return runtime;
    }
}
