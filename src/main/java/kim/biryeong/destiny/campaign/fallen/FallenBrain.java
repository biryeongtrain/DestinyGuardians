package kim.biryeong.destiny.campaign.fallen;

import kim.biryeong.destiny.campaign.fallen.FallenArchetypes.Archetype;
import kim.biryeong.destiny.campaign.fallen.FallenArchetypes.Attack;
import kim.biryeong.destiny.campaign.fallen.FallenArchetypes.Role;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.util.Mth;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;

/**
 * Infantry and Shank AI (W300, original design, Destiny-inspired). One per-mob state machine driven from
 * {@link FallenMob#customServerAiStep}; no goal selectors, no per-tick world scans. Target search is every 20
 * ticks over the level's player list; paths are refreshed at most every 10 ticks; cover sampling is on demand.
 * Every attack telegraphs (charge particles at the weapon + sound + animation) before damage can land.
 */
final class FallenBrain {
    private enum Attacking { READY, TELEGRAPH, BURST, COOLDOWN }
    private enum Move { ADVANCE, HOLD, STRAFE, COVER, RETREAT, HOME }

    private final FallenMob mob;
    private LivingEntity target;
    private int retarget, repath, cooldown, telegraph, burstLeft, burstGap, stagger, spawnGrace = 24;
    private int strafeTicks, coverTicks, coverCooldown = 60, blinkCooldown, sinceHurt = 999, hurtFlinch;
    private int strafeSign = 1;
    private int evadeCooldown = 40;
    private boolean taunted;
    private Attacking attacking = Attacking.READY;
    private Attack current;
    private Move move = Move.ADVANCE;
    private Vec3 moveGoal;
    private double recentDamage;
    private double hoverPhase;
    /** Body/head yaw override while engaged (NaN = let vanilla body rotation follow movement). */
    private float facing = Float.NaN;
    private boolean sighted;

    FallenBrain(FallenMob mob) {
        this.mob = mob;
        this.hoverPhase = mob.getRandom().nextDouble() * Math.PI * 2;
        this.cooldown = 10 + mob.getRandom().nextInt(30);
        this.strafeSign = mob.getRandom().nextBoolean() ? 1 : -1;
    }

    Archetype arch() { return mob.archetype(); }

    // ------------------------------------------------------------------------------------------ static helpers

    static boolean validTarget(LivingEntity self, LivingEntity t, double range) {
        if (t == null || t.isRemoved() || !t.isAlive() || t.level() != self.level()) return false;
        if (t instanceof ServerPlayer p && (p.isSpectator() || p.isCreative() || !p.canBeSeenAsEnemy())) return false;
        return t.distanceToSqr(self) <= range * range;
    }

    static ServerPlayer nearestPlayer(LivingEntity self, double range) {
        ServerPlayer best = null;
        double bestD = range * range;
        for (ServerPlayer p : ((ServerLevel) self.level()).players()) {
            if (!validTarget(self, p, range)) continue;
            double d = p.distanceToSqr(self);
            if (d < bestD) { bestD = d; best = p; }
        }
        return best;
    }

    static float yawTo(Vec3 from, Vec3 to) {
        return (float) (Mth.atan2(to.z - from.z, to.x - from.x) * Mth.RAD_TO_DEG) - 90f;
    }

    static float approachAngle(float current, float wanted, float maxStep) {
        float d = Mth.wrapDegrees(wanted - current);
        return current + Mth.clamp(d, -maxStep, maxStep);
    }

    // ------------------------------------------------------------------------------------------ events

    void aggro(LivingEntity attacker) {
        if (attacker instanceof ServerPlayer p && validTarget(mob, p, 64)) { target = p; retarget = 40; }
    }

    /** After real damage. shieldBroken = absorption went from positive to zero. */
    void hurt(DamageSource source, float amount, boolean shieldBroken) {
        if (source.getEntity() instanceof LivingEntity attacker) aggro(attacker);
        sinceHurt = 0;
        recentDamage += amount;
        double max = Math.max(1, mob.getMaxHealth() + arch().shield());
        boolean big = amount >= max * .3;
        if (shieldBroken || big) {
            stagger = shieldBroken ? 18 : 12;
            cancelAttack();
            mob.getNavigation().stop();
            mob.models().play(FallenModels.Action.STAGGER);
        } else if (hurtFlinch <= 0) {
            hurtFlinch = 8;
            mob.models().play(FallenModels.Action.HIT);
        }
        FallenSounds.bark(mob, FallenSounds.hurt(arch().kind()), false);
        // Dreg sidestep (W300 r6 handoff evade clips): a short dodge away from fire instead of soaking it.
        if (arch().role() == Role.RUSHER && stagger == 0 && evadeCooldown <= 0 && mob.onGround()
                && mob.getRandom().nextDouble() < .35) evade();
        // Vandal blink: when pressured, vanish sideways (Destiny vandal blink, original timing).
        if (arch().blinkCooldown() > 0 && blinkCooldown <= 0 && stagger == 0
                && recentDamage >= max * .22 && mob.getRandom().nextDouble() < .7) blink();
        // Wounded marksmen go to cover sooner.
        if (arch().role() == Role.MARKSMAN && mob.getHealth() < mob.getMaxHealth() * .55 && coverCooldown > 20) coverCooldown = 20;
    }

    void stop() { cancelAttack(); mob.getNavigation().stop(); facing = Float.NaN; }

    float facing() { return facing; }

    private void cancelAttack() {
        mob.models().charge(false, 0);
        if (attacking == Attacking.TELEGRAPH || attacking == Attacking.BURST) {
            attacking = Attacking.COOLDOWN;
            cooldown = 20;
        }
        burstLeft = 0;
    }

    // ------------------------------------------------------------------------------------------ tick

    void tick(ServerLevel level) {
        if (hurtFlinch > 0) hurtFlinch--;
        if (blinkCooldown > 0) blinkCooldown--;
        if (evadeCooldown > 0) evadeCooldown--;
        if (coverCooldown > 0) coverCooldown--;
        sinceHurt++;
        if (sinceHurt > 30) recentDamage = 0;
        shieldRegen(level);
        if (spawnGrace > 0) { spawnGrace--; mob.getNavigation().stop(); return; }
        if (stagger > 0) { stagger--; mob.getNavigation().stop(); return; }

        if (--retarget <= 0 || !validTarget(mob, target, 48)) {
            retarget = 20;
            if (!validTarget(mob, target, 48)) target = nearestPlayer(mob, 40);
        }
        if (target == null) { idle(level); return; }
        boolean sight = mob.getSensing().hasLineOfSight(target);
        if (sight && !sighted) { sighted = true; FallenSounds.bark(mob, FallenSounds.sighted(arch().kind()), false); }
        // First contact: Dregs sometimes posture before rushing (handoff taunt clip, ~1.8 s, no attack meanwhile).
        if (!taunted && sight) {
            taunted = true;
            if (arch().role() == Role.RUSHER && mob.models().has(FallenModels.Action.TAUNT) && mob.getRandom().nextDouble() < .4) {
                mob.models().play(FallenModels.Action.TAUNT);
                FallenSounds.bark(mob, FallenSounds.Ev.DREG_TAUNT, false);
                mob.getNavigation().stop();
                stagger = 20;
                cooldown = Math.max(cooldown, 30);
                return;
            }
        }
        double dist = mob.distanceTo(target);

        if (arch().flying()) hover(level, sight, dist); else ground(level, sight, dist);
        face(sight);
        attack(level, sight, dist);
    }

    private void idle(ServerLevel level) {
        if (arch().flying()) { hoverAt(mob.home().add(0, 2.5, 0), .5); return; }
        if (mob.position().distanceToSqr(mob.home()) > 9 && --repath <= 0) {
            repath = 20;
            mob.getNavigation().moveTo(mob.home().x, mob.home().y, mob.home().z, speed(false));
        }
        mob.models().base(mob.getNavigation().isDone() ? FallenModels.Action.IDLE : FallenModels.Action.MOVE);
    }

    private double speed(boolean run) {
        // Navigation speed is a multiplier on the movement attribute that RisingFallen set to walkSpeed.
        return run ? arch().runSpeed() / arch().walkSpeed() : 1.0;
    }

    private void ground(ServerLevel level, boolean sight, double dist) {
        // Leash: never chase out of the encounter space.
        if (mob.position().distanceTo(mob.home()) > 34) move = Move.HOME;
        if (attacking == Attacking.TELEGRAPH && current != null && current.melee()) {
            // Commit to the swing: keep closing but no path churn.
            if (--repath <= 0) { repath = 6; mob.getNavigation().moveTo(target, speed(true)); }
            mob.models().base(FallenModels.Action.RUN);
            return;
        }
        Role role = arch().role();
        Move want;
        if (move == Move.HOME && mob.position().distanceTo(mob.home()) > 8) want = Move.HOME;
        else if (move == Move.COVER && coverTicks > 0) want = Move.COVER;
        else if (role == Role.RUSHER) want = dist > 1.8 ? Move.ADVANCE : Move.HOLD;
        else if (!sight || dist > arch().preferredMax()) want = Move.ADVANCE;
        else if (dist < arch().preferredMin()) want = Move.RETREAT;
        else want = Move.STRAFE;
        if (want != Move.COVER && role == Role.MARKSMAN && coverCooldown <= 0 && sight) {
            coverCooldown = 90 + mob.getRandom().nextInt(70);
            Vec3 cover = findCover(level);
            if (cover != null) { want = Move.COVER; moveGoal = cover; coverTicks = 50 + mob.getRandom().nextInt(30); repath = 0; }
        }
        if (want != move) { move = want; repath = 0; }
        if (move == Move.COVER && --coverTicks <= 0) { move = Move.STRAFE; repath = 0; }
        if (--repath > 0) { animateMove(); return; }
        repath = 10;
        var nav = mob.getNavigation();
        switch (move) {
            case HOME -> nav.moveTo(mob.home().x, mob.home().y, mob.home().z, speed(true));
            case ADVANCE -> {
                if (role == Role.RUSHER && dist > 3) {
                    // Dregs skitter: approach on a slight zig-zag rather than a straight line.
                    Vec3 to = target.position().subtract(mob.position());
                    Vec3 side = new Vec3(-to.z, 0, to.x).normalize().scale(Math.min(2.5, dist * .2) * strafeSign);
                    if (mob.getRandom().nextInt(3) == 0) strafeSign = -strafeSign;
                    Vec3 g = target.position().add(side);
                    nav.moveTo(g.x, g.y, g.z, speed(true));
                } else nav.moveTo(target, speed(role == Role.RUSHER));
            }
            case HOLD -> nav.stop();
            case RETREAT -> {
                Vec3 away = mob.position().subtract(target.position()).multiply(1, 0, 1);
                if (away.lengthSqr() < 1e-4) away = new Vec3(1, 0, 0);
                Vec3 g = mob.position().add(away.normalize().scale(4));
                nav.moveTo(g.x, g.y, g.z, speed(false));
            }
            case STRAFE -> {
                if (--strafeTicks <= 0) { strafeTicks = 3 + mob.getRandom().nextInt(5); strafeSign = -strafeSign; }
                Vec3 to = target.position().subtract(mob.position()).multiply(1, 0, 1);
                if (to.lengthSqr() < 1e-4) to = new Vec3(0, 0, 1);
                Vec3 side = new Vec3(-to.z, 0, to.x).normalize().scale(3.5 * strafeSign);
                Vec3 g = mob.position().add(side);
                nav.moveTo(g.x, g.y, g.z, speed(false));
            }
            case COVER -> { if (moveGoal != null) nav.moveTo(moveGoal.x, moveGoal.y, moveGoal.z, speed(true)); }
        }
        animateMove();
    }

    private void animateMove() {
        if (mob.getNavigation().isDone()) { mob.models().base(FallenModels.Action.IDLE); return; }
        boolean run = move == Move.COVER || move == Move.HOME || (arch().role() == Role.RUSHER && move == Move.ADVANCE);
        mob.models().base(run ? FallenModels.Action.RUN : FallenModels.Action.MOVE);
    }

    /** Shanks: orbit at the preferred band, bob 2.5-4 blocks above the target's feet. */
    private void hover(ServerLevel level, boolean sight, double dist) {
        hoverPhase += .045 * strafeSign;
        double radius = (arch().preferredMin() + arch().preferredMax()) / 2;
        if (!sight) radius = Math.max(3, radius * .6);
        Vec3 c = target.position();
        Vec3 goal = c.add(Math.cos(hoverPhase) * radius, 2.8 + Math.sin(hoverPhase * 2.3) * .7, Math.sin(hoverPhase) * radius);
        if (mob.position().distanceTo(mob.home()) > 34) goal = mob.home().add(0, 3, 0);
        hoverAt(goal, sight ? arch().walkSpeed() : arch().runSpeed());
        if (mob.getRandom().nextInt(120) == 0) strafeSign = -strafeSign;
    }

    private void hoverAt(Vec3 goal, double speed) {
        Vec3 d = goal.subtract(mob.position());
        double len = d.length();
        Vec3 v = len < .05 ? Vec3.ZERO : d.scale(Math.min(speed, len * .25) / len);
        // Smooth steering; vanilla travel applies air drag after this.
        mob.setDeltaMovement(mob.getDeltaMovement().scale(.6).add(v.scale(.55)));
        mob.models().base(FallenModels.Action.MOVE);
    }

    private void face(boolean sight) {
        if (target == null) return;
        mob.getLookControl().setLookAt(target, 40, 40);
        boolean engaged = sight && (attacking != Attacking.READY || move == Move.STRAFE || move == Move.HOLD
                || arch().flying() || move == Move.RETREAT);
        if (!engaged) { facing = Float.NaN; return; }
        float want = yawTo(mob.position(), target.position());
        float from = Float.isNaN(facing) ? mob.yBodyRot : facing;
        facing = approachAngle(from, want, attacking == Attacking.TELEGRAPH ? 18 : 12);
        // Movement direction (yRot) stays with the path when strafing; only a standing mob turns its whole body.
        if (mob.getNavigation().isDone() || arch().flying()) mob.setYRot(facing);
    }

    // ------------------------------------------------------------------------------------------ attacks

    private void attack(ServerLevel level, boolean sight, double dist) {
        switch (attacking) {
            case COOLDOWN -> { if (--cooldown <= 0) attacking = Attacking.READY; }
            case READY -> {
                Attack choice = choose(sight, dist);
                if (choice == null) return;
                current = choice;
                attacking = Attacking.TELEGRAPH;
                telegraph = 0;
                mob.models().play(choice.melee() ? FallenModels.Action.MELEE : FallenModels.Action.SHOOT);
                FallenWeapons.telegraphSound(level, mob, choice);
                if (arch().flying()) FallenSounds.bark(mob, FallenSounds.Ev.SHANK_SHOOT, false);
                mob.models().charge(true, arch().arcColor());
            }
            case TELEGRAPH -> {
                telegraph++;
                Vec3 at = muzzle();
                FallenWeapons.charge(level, at, arch().arcColor(), telegraph, current.telegraphTicks(),
                        current.melee() ? .8f : current.splashRadius() > 0 ? 1.5f : 1.0f);
                if (telegraph < current.telegraphTicks()) return;
                mob.models().charge(false, 0);
                if (current.melee()) {
                    FallenWeapons.melee(level, mob, target, current, arch().arcColor());
                    finish();
                } else {
                    attacking = Attacking.BURST;
                    burstLeft = current.burst();
                    burstGap = 0;
                }
            }
            case BURST -> {
                if (--burstGap > 0) return;
                burstGap = current.burstGap();
                burstLeft--;
                if (validTarget(mob, target, current.rangeMax() + 8)) {
                    Vec3 from = muzzle();
                    Vec3 dir = FallenWeapons.aim(mob, target, from, current.projectileSpeed(), arch().accuracy());
                    FallenWeapons.bolt(level, mob, from, dir, current.projectileSpeed(), current.damageFraction(),
                            current.splashRadius(), arch().arcColor(),
                            current.splashRadius() > 0 ? FallenWeapons.Style.ORB : FallenWeapons.Style.ARC);
                    FallenWeapons.fireSound(level, mob, current);
                }
                if (burstLeft <= 0) finish();
            }
        }
    }

    private void finish() {
        attacking = Attacking.COOLDOWN;
        cooldown = FallenArchetypes.cooldown(current, mob.getRandom().nextDouble());
    }

    private Attack choose(boolean sight, double dist) {
        if (!sight) return null;
        Attack p = arch().primary(), s = arch().secondary();
        if (p.melee() && dist <= p.rangeMax()) return p;
        if (s != null && s.melee() && dist <= s.rangeMax()) return s;
        if (!p.melee() && dist >= p.rangeMin() && dist <= p.rangeMax()) return p;
        if (s != null && !s.melee() && dist >= s.rangeMin() && dist <= s.rangeMax()
                && (arch().role() != Role.RUSHER || mob.getRandom().nextInt(3) == 0)) return s;
        return null;
    }

    /** Weapon point: chest height, forward and to the right of the body yaw. */
    Vec3 muzzle() {
        if (arch().flying()) return mob.position().add(0, mob.getBbHeight() * .5, 0).add(forward().scale(.5));
        Vec3 f = forward();
        Vec3 right = new Vec3(-f.z, 0, f.x);
        return mob.position().add(0, mob.getBbHeight() * .66, 0).add(f.scale(.55)).add(right.scale(.32));
    }

    private Vec3 forward() {
        double r = Math.toRadians(mob.getYRot());
        return new Vec3(-Math.sin(r), 0, Math.cos(r));
    }

    // ------------------------------------------------------------------------------------------ shield / blink / cover

    private void shieldRegen(ServerLevel level) {
        double shield = arch().shield();
        if (shield <= 0) return;
        float now = mob.getAbsorptionAmount();
        if (sinceHurt > 100 && now < shield) {
            float next = (float) Math.min(shield, now + shield * .2 / 20);
            mob.setAbsorptionAmount(next);
            if (now <= 0) FallenWeapons.shieldUp(level, mob);
        }
    }

    /** Side-step (evade_left/right clip) with a ground impulse; only towards standable, unobstructed ground. */
    private void evade() {
        var level = (ServerLevel) mob.level();
        Vec3 to = target == null ? forward() : target.position().subtract(mob.position()).multiply(1, 0, 1);
        if (to.lengthSqr() < 1e-4) return;
        Vec3 right = new Vec3(-to.z, 0, to.x).normalize();
        int sign = mob.getRandom().nextBoolean() ? 1 : -1;
        for (int attempt = 0; attempt < 2; attempt++, sign = -sign) {
            FallenModels.Action clip = sign > 0 ? FallenModels.Action.EVADE_RIGHT : FallenModels.Action.EVADE_LEFT;
            if (!mob.models().has(clip)) return;
            Vec3 spot = standable(level, mob.position().add(right.scale(2.2 * sign)));
            if (spot == null || Math.abs(spot.y - mob.getY()) > .6) continue;
            if (!clearPath(level, mob.position().add(0, .6, 0), spot.add(0, .6, 0))) continue;
            mob.getNavigation().stop();
            mob.setDeltaMovement(right.scale(.62 * sign).add(0, .12, 0));
            mob.models().play(clip);
            Vec3 at = mob.position().add(0, .8, 0);
            FallenSounds.play(level, at, FallenSounds.Ev.DREG_EVADE_SPIN);
            FallenSounds.play(level, at, FallenSounds.Ev.DREG_SHORTMOVE);
            FallenSounds.bark(mob, FallenSounds.Ev.DREG_EVADE, false);
            evadeCooldown = 70 + mob.getRandom().nextInt(50);
            return;
        }
    }

    private void blink() {
        var level = (ServerLevel) mob.level();
        Vec3 from = mob.position();
        Vec3 to = target == null ? forward() : target.position().subtract(from).multiply(1, 0, 1);
        if (to.lengthSqr() < 1e-4) to = new Vec3(0, 0, 1);
        Vec3 side = new Vec3(-to.z, 0, to.x).normalize();
        for (int attempt = 0; attempt < 6; attempt++) {
            double d = 4 + mob.getRandom().nextDouble() * 3;
            int sign = mob.getRandom().nextBoolean() ? 1 : -1;
            Vec3 g = from.add(side.scale(d * sign)).add(to.normalize().scale((mob.getRandom().nextDouble() - .5) * 3));
            Vec3 spot = standable(level, g);
            if (spot == null || !safeBlink(level, from, spot)) continue;
            if (target != null && !clearPath(level, spot.add(0, 1.4, 0), target.getEyePosition())) continue;
            FallenWeapons.blink(level, mob, from, spot);
            FallenSounds.bark(mob, FallenSounds.Ev.VANDAL_EVADE, false);
            mob.teleportTo(spot.x, spot.y, spot.z);
            mob.getNavigation().stop();
            blinkCooldown = arch().blinkCooldown() + mob.getRandom().nextInt(60);
            recentDamage = 0;
            cancelAttack();
            return;
        }
    }

    /** Teleports stay on the same walkable arena surface. A floor beyond a wall or on a roof
     * is insufficient: require body clearance, home leash, clear travel and a complete path. */
    boolean safeBlink(ServerLevel level, Vec3 from, Vec3 spot) {
        if (spot.distanceToSqr(mob.home()) > 34 * 34 || Math.abs(spot.y - from.y) > 1.25) return false;
        var box = mob.getBoundingBox().move(spot.subtract(from));
        if (!level.getWorldBorder().isWithinBounds(box) || !level.noCollision(mob, box)) return false;
        if (!clearPath(level, from.add(0, .5, 0), spot.add(0, .5, 0))
                || !clearPath(level, from.add(0, mob.getBbHeight() * .8, 0), spot.add(0, mob.getBbHeight() * .8, 0))) return false;
        var path = mob.getNavigation().createPath(BlockPos.containing(spot), 0);
        return path != null && path.canReach();
    }

    /** Sample up to 10 spots near the mob that block the target's line of sight but stay within range. */
    private Vec3 findCover(ServerLevel level) {
        if (target == null) return null;
        Vec3 eye = target.getEyePosition();
        Vec3 best = null;
        double bestD = Double.MAX_VALUE;
        for (int i = 0; i < 10; i++) {
            double a = mob.getRandom().nextDouble() * Math.PI * 2, r = 3 + mob.getRandom().nextDouble() * 6;
            Vec3 spot = standable(level, mob.position().add(Math.cos(a) * r, 0, Math.sin(a) * r));
            if (spot == null) continue;
            double toTarget = spot.distanceTo(target.position());
            if (toTarget < arch().preferredMin() * .7 || toTarget > arch().preferredMax() + 6) continue;
            if (clearPath(level, spot.add(0, 1.5, 0), eye)) continue;
            double d = spot.distanceToSqr(mob.position());
            if (d < bestD) { bestD = d; best = spot; }
        }
        return best;
    }

    static boolean clearPath(ServerLevel level, Vec3 a, Vec3 b) {
        return level.clip(new ClipContext(a, b, ClipContext.Block.COLLIDER, ClipContext.Fluid.NONE,
                net.minecraft.world.phys.shapes.CollisionContext.empty())).getType() == HitResult.Type.MISS;
    }

    /** Floor within +-3 blocks of g with two clear blocks above, or null. */
    static Vec3 standable(ServerLevel level, Vec3 g) {
        BlockPos base = BlockPos.containing(g);
        for (int dy = 2; dy >= -3; dy--) {
            BlockPos feet = base.offset(0, dy, 0);
            if (!level.isLoaded(feet)) return null;
            var below = level.getBlockState(feet.below());
            if (!below.isFaceSturdy(level, feet.below(), Direction.UP)) continue;
            if (!level.getBlockState(feet).getCollisionShape(level, feet).isEmpty()) continue;
            if (!level.getBlockState(feet.above()).getCollisionShape(level, feet.above()).isEmpty()) continue;
            if (!level.getBlockState(feet.above(2)).getCollisionShape(level, feet.above(2)).isEmpty()) continue;
            return new Vec3(feet.getX() + .5, feet.getY(), feet.getZ() + .5);
        }
        return null;
    }
}
