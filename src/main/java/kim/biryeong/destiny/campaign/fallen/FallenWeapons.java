package kim.biryeong.destiny.campaign.fallen;

import kim.biryeong.destiny.DestinyGuardians;
import kim.biryeong.destiny.campaign.fallen.FallenArchetypes.Attack;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.DustParticleOptions;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.damagesource.DamageType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;

import java.util.ArrayList;
import java.util.Iterator;
import java.util.List;
import java.util.Optional;

/**
 * Fallen weapons and their readable VFX (W300, original). Projectiles are simulated server-side points with
 * particle trails so they are visible and dodgeable; they never spawn entities. Damage to Guardians goes through
 * native {@code hurtServer} so absorption/overshields, death handling, PlayerDamageMixin and IncomingDamageHud
 * all apply. The damage type is {@code destiny:fallen} (scaling never, not resistance-bypassing): peaceful/easy
 * world difficulty does not zero or halve mission damage, while Resistance/armour/absorption still mitigate it.
 * A per-hit cap and a rolling one-second budget prevent one-shots.
 */
public final class FallenWeapons {
    private FallenWeapons() {}

    public enum Style { ARC, ORB, SHELL }

    private static final int MAX_BOLTS = 384;
    private static final List<Bolt> BOLTS = new ArrayList<>();
    /**
     * destiny:fallen — scaling "never" (world difficulty does not zero/halve mission damage) but, unlike
     * destiny:crucible, NOT in bypasses_resistance/armor/enchantments, so Resistance, armour and protection apply
     * exactly like ordinary mob damage (W300 r3: Resistance IV players were dying to crucible-typed Walker shells).
     */
    private static final ResourceKey<DamageType> TYPE = ResourceKey.create(Registries.DAMAGE_TYPE, DestinyGuardians.id("fallen"));
    /** No single Fallen hit may request more than this fraction of max health. */
    static final double MAX_HIT_FRACTION = .35;
    /** Rolling budget: requested Fallen damage within WINDOW_TICKS never exceeds this fraction of max health. */
    static final double WINDOW_BUDGET = .55;
    static final int WINDOW_TICKS = 20;
    private static final java.util.Map<java.util.UUID, double[]> RECENT = new java.util.HashMap<>();

    private static final class Bolt {
        final ServerLevel level;
        final LivingEntity shooter;
        final Vec3 origin;
        Vec3 pos, vel;
        final double fraction, splash, gravity;
        final int color, maxAge;
        final Style style;
        final Vec3 warnAt;
        /** {thwack, lethal thwack, flyby}; flyby plays once per bolt per listener. */
        final FallenSounds.Ev[] impact;
        java.util.Set<ServerPlayer> flewBy;
        int age;
        Bolt(ServerLevel level, LivingEntity shooter, Vec3 pos, Vec3 vel, double fraction, double splash, double gravity,
             int color, int maxAge, Style style, Vec3 warnAt) {
            this.level = level; this.shooter = shooter; this.origin = pos; this.pos = pos; this.vel = vel;
            this.fraction = fraction; this.splash = splash; this.gravity = gravity; this.color = color;
            this.maxAge = maxAge; this.style = style; this.warnAt = warnAt;
            var kind = FallenSounds.kindOf(shooter);
            this.impact = FallenSounds.impact(kind == null ? kim.biryeong.destiny.campaign.RisingServices.FallenKind.DREG : kind,
                    splash > 0);
        }
    }

    public static DustParticleOptions dust(int rgb, float size) { return new DustParticleOptions(rgb, size); }

    // ------------------------------------------------------------------------------------------ aiming

    /** Lead the target by part of its velocity and add an accuracy cone. Returns a unit direction. */
    static Vec3 aim(LivingEntity shooter, LivingEntity target, Vec3 from, double speed, double accuracy) {
        Vec3 chest = target.position().add(0, target.getBbHeight() * .6, 0);
        Vec3 vel = target.getDeltaMovement().multiply(1, 0, 1);
        if (target instanceof ServerPlayer p) vel = p.getKnownMovement().multiply(1, 0, 1);
        double t = speed > 0 ? from.distanceTo(chest) / speed : 0;
        Vec3 aimAt = chest.add(vel.scale(t * FallenArchetypes.leadFraction(accuracy)));
        Vec3 dir = aimAt.subtract(from);
        if (dir.lengthSqr() < 1e-6) dir = new Vec3(0, 0, 1);
        dir = dir.normalize();
        double cone = FallenArchetypes.spreadRadians(accuracy);
        var rnd = shooter.getRandom();
        Vec3 right = dir.cross(new Vec3(0, 1, 0));
        if (right.lengthSqr() < 1e-6) right = new Vec3(1, 0, 0);
        right = right.normalize();
        Vec3 up = right.cross(dir).normalize();
        double a = rnd.nextDouble() * Math.PI * 2, r = cone * Math.sqrt(rnd.nextDouble());
        return dir.add(right.scale(Math.cos(a) * r)).add(up.scale(Math.sin(a) * r)).normalize();
    }

    static Vec3 groundBelow(ServerLevel level, Vec3 p) {
        var hit = level.clip(new ClipContext(p.add(0, .5, 0), p.add(0, -12, 0), ClipContext.Block.COLLIDER,
                ClipContext.Fluid.NONE, net.minecraft.world.phys.shapes.CollisionContext.empty()));
        return hit.getType() == HitResult.Type.MISS ? p : hit.getLocation();
    }

    // ------------------------------------------------------------------------------------------ firing

    static void bolt(ServerLevel level, LivingEntity shooter, Vec3 from, Vec3 dir, double speed, double fraction,
                     double splash, int color, Style style) {
        if (BOLTS.size() >= MAX_BOLTS) return;
        int maxAge = (int) Math.ceil(48 / Math.max(.2, speed)) + 4;
        BOLTS.add(new Bolt(level, shooter, from, dir.scale(speed), fraction, splash, 0, color, maxAge, style, null));
        FallenVfx.muzzle(level, shooter, from, dir, color, style);
        // Muzzle flash, readable from the side.
        level.sendParticles(dust(color, 1.4f), from.x, from.y, from.z, 3, .05, .05, .05, 0);
        level.sendParticles(ParticleTypes.ELECTRIC_SPARK, from.x, from.y, from.z, 3, .08, .08, .08, .12);
    }

    /** Arcing shell that lands on {@code target} after a flight time proportional to distance. */
    static void lob(ServerLevel level, LivingEntity shooter, Vec3 from, Vec3 target, double speed, double fraction,
                    double splash, int color) {
        if (BOLTS.size() >= MAX_BOLTS) return;
        double g = .04;
        double horizontal = Math.sqrt(Math.pow(target.x - from.x, 2) + Math.pow(target.z - from.z, 2));
        int flight = Math.max(18, (int) Math.round(horizontal / speed));
        Vec3 v = new Vec3((target.x - from.x) / flight, (target.y - from.y + .5 * g * flight * flight) / flight,
                (target.z - from.z) / flight);
        BOLTS.add(new Bolt(level, shooter, from, v, fraction, splash, g, color, flight + 30, Style.SHELL, target));
        FallenVfx.muzzle(level, shooter, from, v, color, Style.SHELL);
        level.sendParticles(ParticleTypes.LARGE_SMOKE, from.x, from.y, from.z, 10, .3, .3, .3, .05);
        level.sendParticles(ParticleTypes.FLAME, from.x, from.y, from.z, 8, .2, .2, .2, .08);
    }

    static boolean melee(ServerLevel level, FallenMob mob, LivingEntity target, Attack attack, int color) {
        Vec3 from = mob.position().add(0, mob.getBbHeight() * .6, 0);
        // Shock-blade arc in front of the attacker, visible whether or not it connects.
        double yaw = Math.toRadians(mob.getYRot());
        Vec3 f = new Vec3(-Math.sin(yaw), 0, Math.cos(yaw));
        Vec3 r = new Vec3(-f.z, 0, f.x);
        for (int i = -3; i <= 3; i++) {
            Vec3 p = from.add(f.scale(1.1)).add(r.scale(i * .3)).add(0, -Math.abs(i) * .08, 0);
            level.sendParticles(dust(color, 1.1f), p.x, p.y, p.z, 1, 0, 0, 0, 0);
        }
        level.sendParticles(ParticleTypes.SWEEP_ATTACK, from.x + f.x, from.y, from.z + f.z, 1, 0, 0, 0, 0);
        for (var ev : FallenSounds.melee(mob.fallenKind())) FallenSounds.play(level, from, ev);
        if (!(target instanceof ServerPlayer p) || !FallenBrain.validTarget(mob, p, attack.rangeMax() + .6)) return false;
        Vec3 to = p.position().subtract(mob.position()).multiply(1, 0, 1);
        if (to.lengthSqr() > 1e-4 && to.normalize().dot(f) < .35) return false; // dodged around the swing
        if (!mob.getSensing().hasLineOfSight(p)) return false;
        boolean hit = hurt(level, mob, p, attack.damageFraction(), from,
                new FallenSounds.Ev[]{FallenSounds.Ev.THWACK, FallenSounds.Ev.THWACK_LETHAL});
        if (hit) {
            Vec3 at = p.position().add(0, 1, 0);
            level.sendParticles(ParticleTypes.ELECTRIC_SPARK, at.x, at.y, at.z, 10, .2, .3, .2, .2);
        }
        return hit;
    }

    // ------------------------------------------------------------------------------------------ damage

    /** Fraction of the victim's max health through the native player damage path. */
    static boolean hurt(ServerLevel level, LivingEntity attacker, ServerPlayer victim, double fraction, Vec3 origin) {
        return hurt(level, attacker, victim, fraction, origin, null);
    }

    /**
     * As above; on a landed hit plays {@code impact[0]} (or {@code impact[1]} when it downed the Guardian) at the
     * victim, and the attacker's kill bark when it downed them.
     */
    static boolean hurt(ServerLevel level, LivingEntity attacker, ServerPlayer victim, double fraction, Vec3 origin,
                        FallenSounds.Ev[] impact) {
        boolean wasAlive = victim.isAlive();
        boolean hit = hurtRaw(level, attacker, victim, fraction, origin);
        if (!hit) return false;
        boolean downed = wasAlive && (!victim.isAlive() || victim.isDeadOrDying());
        Vec3 at = victim.position().add(0, victim.getBbHeight() * .6, 0);
        if (impact != null && impact.length >= 2) FallenSounds.play(level, at, downed ? impact[1] : impact[0]);
        if (downed && attacker instanceof FallenMob mob)
            FallenSounds.bark(mob, FallenSounds.kill(mob.fallenKind()), true);
        return true;
    }

    private static boolean hurtRaw(ServerLevel level, LivingEntity attacker, ServerPlayer victim, double fraction, Vec3 origin) {
        if (!victim.isAlive() || victim.isSpectator() || victim.isCreative() || victim.level() != level) return false;
        double[] window = RECENT.computeIfAbsent(victim.getUUID(), id -> new double[2]);
        long now = level.getServer().getTickCount();
        double allowed = guarded(window, now, fraction);
        float amount = (float) (allowed * victim.getMaxHealth());
        if (!(amount > 0)) return false;
        Optional<net.minecraft.core.Holder.Reference<DamageType>> type =
                level.registryAccess().lookupOrThrow(Registries.DAMAGE_TYPE).get(TYPE);
        DamageSource source;
        if (type.isPresent()) {
            source = attacker != null && attacker.isAlive() && attacker.level() == level
                    ? new DamageSource(type.get(), attacker, attacker) : new DamageSource(type.get(), origin);
        } else {
            source = attacker != null ? level.damageSources().mobAttack(attacker) : level.damageSources().magic();
        }
        // Destiny has no invulnerability frames between bolts of a burst.
        victim.damageCooldownTime = 0;
        return victim.hurtServer(level, source, amount);
    }

    /**
     * One-shot guard (pure; tested). window = {windowStartTick, spentFraction}. Returns the fraction that may be
     * requested now: capped per hit and by what remains of the rolling budget. Mitigation (resistance, absorption)
     * still applies afterwards, so this only bounds the worst case for an unprotected Guardian.
     */
    static double guarded(double[] window, long now, double fraction) {
        if (!(fraction > 0) || !Double.isFinite(fraction)) return 0;
        if (now - (long) window[0] >= WINDOW_TICKS || now < (long) window[0]) { window[0] = now; window[1] = 0; }
        double allowed = Math.max(0, Math.min(Math.min(fraction, MAX_HIT_FRACTION), WINDOW_BUDGET - window[1]));
        window[1] += allowed;
        return allowed;
    }

    // ------------------------------------------------------------------------------------------ simulation

    public static void tick(MinecraftServer server) {
        if (!RECENT.isEmpty() && server.getTickCount() % 200 == 0)
            RECENT.values().removeIf(w -> server.getTickCount() - (long) w[0] > WINDOW_TICKS);
        if (BOLTS.isEmpty()) return;
        Iterator<Bolt> it = BOLTS.iterator();
        while (it.hasNext()) {
            Bolt b = it.next();
            if (b.level.getServer() != server) continue;
            if (step(b)) it.remove();
        }
    }

    /** @return true when the bolt is finished. */
    private static boolean step(Bolt b) {
        b.age++;
        var level = b.level;
        Vec3 next = b.pos.add(b.vel);
        if (!level.isLoaded(BlockPos.containing(next))) return true;
        var wall = level.clip(new ClipContext(b.pos, next, ClipContext.Block.COLLIDER, ClipContext.Fluid.NONE,
                net.minecraft.world.phys.shapes.CollisionContext.empty()));
        Vec3 end = wall.getType() == HitResult.Type.MISS ? next : wall.getLocation();
        // Players only: Fallen fire never damages other Fallen.
        ServerPlayer hitPlayer = null;
        double best = Double.MAX_VALUE;
        Vec3 hitAt = null;
        for (ServerPlayer p : level.players()) {
            if (p.isSpectator() || !p.isAlive()) continue;
            if (p.distanceToSqr(end) > 36 && p.distanceToSqr(b.pos) > 36) continue;
            AABB box = p.getBoundingBox().inflate(b.style == Style.ARC ? .15 : .3);
            var clip = box.clip(b.pos, end);
            if (box.contains(b.pos)) clip = Optional.of(b.pos);
            if (clip.isPresent()) {
                double d = clip.get().distanceToSqr(b.pos);
                if (d < best) { best = d; hitPlayer = p; hitAt = clip.get(); }
            }
        }
        if (b.impact[2] != null) flyby(b, b.pos, hitAt != null ? hitAt : end, hitPlayer);
        trail(b, b.pos, hitAt != null ? hitAt : end);
        if (hitPlayer != null) {
            if (b.splash > 0) explode(b, hitAt);
            else {
                hurt(level, b.shooter, hitPlayer, b.fraction, b.origin, b.impact);
                level.sendParticles(ParticleTypes.ELECTRIC_SPARK, hitAt.x, hitAt.y, hitAt.z, 6, .1, .1, .1, .15);
                FallenVfx.impact(level, hitAt, b.color, true);
            }
            return true;
        }
        if (wall.getType() != HitResult.Type.MISS) {
            if (b.splash > 0) explode(b, end);
            else {
                level.sendParticles(ParticleTypes.ELECTRIC_SPARK, end.x, end.y, end.z, 5, .05, .05, .05, .1);
                FallenVfx.impact(level, end, b.color, false);
                level.sendParticles(dust(b.color, .9f), end.x, end.y, end.z, 2, .05, .05, .05, 0);
            }
            return true;
        }
        b.pos = next;
        b.vel = b.vel.add(0, -b.gravity, 0);
        if (b.warnAt != null && b.age % 3 == 0) groundWarning(level, b.warnAt, b.splash, b.color);
        if (b.age >= b.maxAge) {
            if (b.splash > 0) explode(b, b.pos);
            return true;
        }
        return false;
    }

    /** Near-miss whoosh for players the bolt passed within FLYBY_RADIUS of their head without hitting them. */
    static final double FLYBY_RADIUS = 2.5;

    private static void flyby(Bolt b, Vec3 from, Vec3 to, ServerPlayer hit) {
        for (ServerPlayer p : b.level.players()) {
            if (p == hit || p.isSpectator() || !p.isAlive()) continue;
            Vec3 eye = p.getEyePosition();
            if (eye.distanceToSqr(from) > 64 && eye.distanceToSqr(to) > 64) continue;
            Vec3 closest = closestOnSegment(from, to, eye);
            if (closest.distanceToSqr(eye) > FLYBY_RADIUS * FLYBY_RADIUS) continue;
            if (b.flewBy == null) b.flewBy = java.util.Collections.newSetFromMap(new java.util.IdentityHashMap<>());
            if (b.flewBy.add(p)) FallenSounds.playTo(p, closest, b.impact[2]);
        }
    }

    /** Pure: closest point to {@code p} on segment a-b. */
    static Vec3 closestOnSegment(Vec3 a, Vec3 b, Vec3 p) {
        Vec3 ab = b.subtract(a);
        double len2 = ab.lengthSqr();
        if (len2 < 1e-12) return a;
        double t = Math.max(0, Math.min(1, p.subtract(a).dot(ab) / len2));
        return a.add(ab.scale(t));
    }

    private static void trail(Bolt b, Vec3 from, Vec3 to) {
        var level = b.level;
        Vec3 d = to.subtract(from);
        double len = d.length();
        FallenVfx.tracer(level, from, to, b.color, b.style);
        switch (b.style) {
            case ARC -> {
                int n = Math.max(1, (int) Math.ceil(len / 1.5)); // r5b: sparse vanilla dust; the FallenVfx contrail is the line
                for (int i = 0; i < n; i++) {
                    Vec3 p = from.add(d.scale(i / (double) n));
                    level.sendParticles(dust(b.color, .85f), p.x, p.y, p.z, 1, 0, 0, 0, 0);
                }
                if (b.age % 2 == 0) level.sendParticles(ParticleTypes.ELECTRIC_SPARK, to.x, to.y, to.z, 1, .02, .02, .02, .02);
            }
            case ORB -> {
                level.sendParticles(dust(b.color, 2.2f), to.x, to.y, to.z, 4, .12, .12, .12, 0);
                level.sendParticles(dust(0xFFFFFF, 1.0f), to.x, to.y, to.z, 1, 0, 0, 0, 0);
                level.sendParticles(ParticleTypes.ELECTRIC_SPARK, to.x, to.y, to.z, 2, .18, .18, .18, .05);
                if (b.age % 5 == 0)
                    level.playSound(null, to.x, to.y, to.z, SoundEvents.BEACON_AMBIENT, SoundSource.HOSTILE, .8f, 2f);
            }
            case SHELL -> {
                level.sendParticles(dust(b.color, 2.0f), to.x, to.y, to.z, 3, .1, .1, .1, 0);
                level.sendParticles(ParticleTypes.FLAME, to.x, to.y, to.z, 2, .08, .08, .08, .01);
                level.sendParticles(ParticleTypes.SMOKE, from.x, from.y, from.z, 2, .08, .08, .08, .01);
            }
        }
    }

    private static void explode(Bolt b, Vec3 at) {
        var level = b.level;
        boolean big = b.style == Style.SHELL;
        FallenVfx.explosion(level, at, b.splash, b.color, big);
        level.sendParticles(big ? ParticleTypes.EXPLOSION_EMITTER : ParticleTypes.EXPLOSION, at.x, at.y, at.z, 1, 0, 0, 0, 0);
        level.sendParticles(dust(b.color, 2.4f), at.x, at.y + .3, at.z, 24, b.splash * .4, .4, b.splash * .4, 0);
        level.sendParticles(ParticleTypes.ELECTRIC_SPARK, at.x, at.y + .3, at.z, 18, b.splash * .3, .3, b.splash * .3, .3);
        if (big) FallenSounds.play(level, at, FallenSounds.Ev.WALKER_CANNON_EXPLO);
        else level.playSound(null, at.x, at.y, at.z, SoundEvents.FIREWORK_ROCKET_LARGE_BLAST, SoundSource.HOSTILE, 1.8f, .8f);
        for (ServerPlayer p : level.players()) {
            if (!p.isAlive() || p.isSpectator()) continue;
            Vec3 chest = p.position().add(0, p.getBbHeight() * .5, 0);
            double d = chest.distanceTo(at);
            if (d > b.splash + .5) continue;
            if (!FallenBrain.clearPath(level, at.add(0, .3, 0), chest)) continue;
            double falloff = 1 - .55 * Math.min(1, d / Math.max(.1, b.splash));
            hurt(level, b.shooter, p, b.fraction * falloff, at, big ? null : b.impact);
        }
    }

    public static void clear(ServerLevel level) { BOLTS.removeIf(b -> b.level == level); }
    public static void clearAll() { BOLTS.clear(); RECENT.clear(); }
    static int activeBolts() { return BOLTS.size(); }

    // ------------------------------------------------------------------------------------------ VFX

    /** Charge-up telegraph: gathering particles that intensify toward the shot. */
    static void charge(ServerLevel level, Vec3 at, int color, int t, int total, float size) {
        if (t % 2 != 0) return;
        double k = Math.min(1, t / (double) Math.max(1, total));
        level.sendParticles(dust(color, size * (float) (.6 + .8 * k)), at.x, at.y, at.z, 2 + (int) (k * 3),
                .12 * (1 - k) + .03, .12 * (1 - k) + .03, .12 * (1 - k) + .03, 0);
        if (k > .55) level.sendParticles(ParticleTypes.ELECTRIC_SPARK, at.x, at.y, at.z, 1, .05, .05, .05, .05);
        if (t + 2 >= total) level.sendParticles(dust(0xFFFFFF, size), at.x, at.y, at.z, 1, 0, 0, 0, 0);
    }

    static void groundWarning(ServerLevel level, Vec3 center, double radius, int color) {
        int points = Math.max(12, (int) (radius * 8));
        for (int i = 0; i < points; i++) {
            double a = Math.PI * 2 * i / points;
            level.sendParticles(dust(color, 1.3f), center.x + Math.cos(a) * radius, center.y + .1,
                    center.z + Math.sin(a) * radius, 1, 0, 0, 0, 0);
        }
        level.sendParticles(dust(color, 1.0f), center.x, center.y + .1, center.z, 3, radius * .3, 0, radius * .3, 0);
    }

    static void telegraphSound(ServerLevel level, FallenMob mob, Attack attack) {
        Vec3 p = mob.position();
        if (attack.melee()) FallenSounds.play(level, p.add(0, mob.getBbHeight() * .6, 0), FallenSounds.Ev.SWORD_TELEGRAPH);
        // No D2 charge-up event was traced for these guns; the vanilla cue stays as the readable telegraph.
        else if (attack.splashRadius() > 0) level.playSound(null, p.x, p.y, p.z, SoundEvents.BEACON_POWER_SELECT, SoundSource.HOSTILE, 1.4f, .7f);
        else level.playSound(null, p.x, p.y, p.z, SoundEvents.BEACON_POWER_SELECT, SoundSource.HOSTILE, .8f, 1.9f);
    }

    static void fireSound(ServerLevel level, FallenMob mob, Attack attack) {
        Vec3 p = mob.position().add(0, mob.getBbHeight() * .66, 0);
        var kind = mob.fallenKind();
        // Shanks fire the same shock pistol as Dregs (README: Shank sequence 80CEA1DB); pitched up for the small frame.
        FallenSounds.play(level, p, FallenSounds.fire(kind, attack.splashRadius() > 0), 1f,
                kind == kim.biryeong.destiny.campaign.RisingServices.FallenKind.SHANK ? 1.15f : 1f);
    }

    static void flash(ServerLevel level, double x, double y, double z) {
        level.sendParticles(net.minecraft.core.particles.ColorParticleOption.create(ParticleTypes.FLASH, 0xFFBFEFFF), x, y, z, 1, 0, 0, 0, 0);
    }

    static void hitSpark(ServerLevel level, LivingEntity mob) {
        Vec3 c = mob.position().add(0, mob.getBbHeight() * .6, 0);
        // Fallen bleed ether: pale blue vapour, not blood.
        level.sendParticles(dust(0xCFEFFF, 1.0f), c.x, c.y, c.z, 4, mob.getBbWidth() * .3, mob.getBbHeight() * .2, mob.getBbWidth() * .3, 0);
    }

    static void shieldHit(ServerLevel level, LivingEntity mob) {
        Vec3 c = mob.position().add(0, mob.getBbHeight() * .5, 0);
        double rx = mob.getBbWidth() * .7, ry = mob.getBbHeight() * .5;
        for (int i = 0; i < 6; i++) {
            double a = mob.getRandom().nextDouble() * Math.PI * 2, e = (mob.getRandom().nextDouble() - .5) * Math.PI;
            level.sendParticles(dust(FallenArchetypes.FALLEN_ARC, 1.1f), c.x + Math.cos(a) * Math.cos(e) * rx,
                    c.y + Math.sin(e) * ry, c.z + Math.sin(a) * Math.cos(e) * rx, 1, 0, 0, 0, 0);
        }
        level.sendParticles(ParticleTypes.ELECTRIC_SPARK, c.x, c.y, c.z, 3, rx * .6, ry * .6, rx * .6, .1);
    }

    static void shieldBreak(ServerLevel level, LivingEntity mob) {
        Vec3 c = mob.position().add(0, mob.getBbHeight() * .5, 0);
        level.sendParticles(ParticleTypes.ELECTRIC_SPARK, c.x, c.y, c.z, 30, .6, .9, .6, .35);
        level.sendParticles(dust(FallenArchetypes.FALLEN_ARC, 1.8f), c.x, c.y, c.z, 20, .7, 1, .7, 0);
        FallenWeapons.flash(level, c.x, c.y, c.z);
        level.playSound(null, c.x, c.y, c.z, SoundEvents.AMETHYST_BLOCK_BREAK, SoundSource.HOSTILE, 1.6f, .6f);
        FallenVfx.shieldPop(level, c, mob.getBbHeight());
        level.playSound(null, c.x, c.y, c.z, SoundEvents.BEACON_DEACTIVATE, SoundSource.HOSTILE, 1.2f, 1.6f);
    }

    static void shieldUp(ServerLevel level, LivingEntity mob) {
        Vec3 c = mob.position().add(0, mob.getBbHeight() * .5, 0);
        level.sendParticles(dust(FallenArchetypes.FALLEN_ARC, 1.4f), c.x, c.y, c.z, 16, .6, .9, .6, 0);
        FallenVfx.shieldUp(level, c, mob.getBbHeight());
        level.playSound(null, c.x, c.y, c.z, SoundEvents.BEACON_ACTIVATE, SoundSource.HOSTILE, 1f, 1.8f);
    }

    static void blink(ServerLevel level, LivingEntity mob, Vec3 from, Vec3 to) {
        for (Vec3 p : new Vec3[]{from, to}) {
            level.sendParticles(dust(0xE6F7FF, 1.6f), p.x, p.y + 1.1, p.z, 18, .3, .8, .3, 0);
            level.sendParticles(ParticleTypes.REVERSE_PORTAL, p.x, p.y + 1.1, p.z, 16, .25, .7, .25, .05);
        }
        FallenSounds.play(level, from.add(0, 1, 0), FallenSounds.Ev.TELEPORT_BEGIN);
        FallenSounds.play(level, to.add(0, 1, 0), FallenSounds.Ev.TELEPORT_END);
        FallenVfx.blink(level, from, to);
    }

    static void spawnPuff(ServerLevel level, LivingEntity mob) {
        Vec3 c = mob.position().add(0, mob.getBbHeight() * .5, 0);
        level.sendParticles(dust(0xCFEFFF, 1.4f), c.x, c.y, c.z, 14, .4, mob.getBbHeight() * .4, .4, 0);
        level.sendParticles(ParticleTypes.CLOUD, c.x, mob.getY() + .1, c.z, 6, .4, .05, .4, .02);
    }

    /** Ether-like death dissolve: pale vapour rising off the body, stronger as the clip ends. */
    static void dissolve(ServerLevel level, LivingEntity mob, int t, int total) {
        double k = Math.min(1, t / (double) Math.max(1, total));
        Vec3 c = mob.position();
        double w = mob.getBbWidth() * .45, h = mob.getBbHeight();
        if (t % 2 == 0) {
            level.sendParticles(dust(0xD9F2FF, 1.2f + (float) k), c.x, c.y + h * (.3 + .4 * k), c.z,
                    2 + (int) (k * 6), w, h * .3, w, 0);
            level.sendParticles(ParticleTypes.END_ROD, c.x, c.y + h * .5, c.z, k > .5 ? 2 : 1, w, h * .3, w, .015);
        }
        if (t + 1 == total) {
            level.sendParticles(ParticleTypes.CLOUD, c.x, c.y + h * .5, c.z, 12, w, h * .3, w, .03);
            level.sendParticles(dust(0xFFFFFF, 2.0f), c.x, c.y + h * .5, c.z, 10, w, h * .35, w, 0);
            FallenSounds.play(level, c.add(0, mob.getBbHeight() * .5, 0), FallenSounds.Ev.DISSOLVE);
        }
    }
}
