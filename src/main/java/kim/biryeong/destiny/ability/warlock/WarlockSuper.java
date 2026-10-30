package kim.biryeong.destiny.ability.warlock;

import kim.biryeong.destiny.ability.*;
import kim.biryeong.destiny.combat.Combat;
import kim.biryeong.destiny.fx.*;
import kim.biryeong.destiny.guardian.*;
import kim.biryeong.destiny.weapon.AmmoGeneration;
import kim.biryeong.destiny.weapon.SwordTiming;
import kim.biryeong.destiny.camera.SuperCamera;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.phys.*;
import java.util.*;

/** Automatic Nova, finite Stormtrance channels and colliding Daybreak sword emissions. */
public final class WarlockSuper extends Ability {
    private static final Map<ServerPlayer, Session> ACTIVE = new IdentityHashMap<>();
    private static final List<Vortex> VORTICES = new ArrayList<>();
    /** Post-impact field owns its lease, not the completed one-shot camera/session. */
    private static final class Vortex {
        final WarlockAbilities.Lease lease;
        final Vec3 origin;
        final int delay, duration, interval;
        final double radius;
        final float damage;
        int age;
        Vortex(WarlockAbilities.Lease lease, WarlockSuper ability, Vec3 origin) {
            this.lease = lease; this.origin = origin;
            delay = WarlockAbilities.ticks(ability, "vortex_delay_ticks", 9, 0, 40);
            duration = WarlockAbilities.ticks(ability, "vortex_duration_ticks", 200, 1, 400);
            interval = WarlockAbilities.ticks(ability, "vortex_pulse_ticks", 10, 5, 40);
            radius = WarlockAbilities.value(ability, "radius", 4, 1, 6);
            damage = (float) WarlockAbilities.value(ability, "vortex_damage", 2, .1, 30);
        }
    }
    static void tickEffects() {
        for (Vortex vortex : List.copyOf(VORTICES)) {
            if (!vortex.lease.valid() || vortex.age >= vortex.delay + vortex.duration) {
                VORTICES.remove(vortex); continue;
            }
            int activeAge = vortex.age++ - vortex.delay;
            if (activeAge < 0) continue;
            if (activeAge % 5 == 0) Fx.ring(vortex.lease.owner, vortex.lease.level, vortex.origin, vortex.radius, Element.VOID.color(), 32);
            if (activeAge % vortex.interval != 0) continue;
            for (LivingEntity target : WarlockAbilities.targets(vortex.lease, vortex.origin, vortex.radius))
                Combat.damage(vortex.lease.level, vortex.lease.owner, target, vortex.damage, Element.VOID, AmmoGeneration.SUPER);
        }
    }
    public static int vortexCount(ServerPlayer p) {
        return (int) VORTICES.stream().filter(v -> v.lease.owner == p).count();
    }
    public WarlockSuper(Identifier id, Element e) {
        super(id, GuardianClass.WARLOCK, AbilitySlot.SUPER, e, e == Element.VOID ? 500 : 556,
                e == Element.ARC ? "폭풍몰입" : e == Element.SOLAR ? "새벽칼날" : "신성 폭탄");
    }
    @Override public boolean activate(ServerPlayer p) {
        if (AbilityService.inSuper(p) || ACTIVE.containsKey(p)) return false;
        var lease = WarlockAbilities.acquire(p, this);
        if (lease == null || !ClassAbilityEffects.beginSuper(p, element(), id().getPath())) return false;
        Session session = new Session(lease, this);
        ACTIVE.put(p, session);
        SuperCamera.blockMovement(p, element() == Element.VOID ? session.attackDuration : session.windup);
        AbilityService.startSuper(p, session);
        return true;
    }
    private static final class Session implements SuperSession {
        final WarlockAbilities.Lease lease; final WarlockSuper ability;
        final int duration, windup, interval, projectileLife, contactDelay, attackDuration;
        final List<SimProjectile> flights = new ArrayList<>();
        int age, nextAttack, channelUntil, emitted, impacts;
        int swordContact = -1, stormContact = -1;
        boolean ended, novaReleased, novaResolved, novaPreparing;
        Session(WarlockAbilities.Lease lease, WarlockSuper ability) {
            this.lease = lease; this.ability = ability;
            duration = WarlockAbilities.ticks(ability, "duration_ticks", ability.element() == Element.SOLAR ? 480 : 320, 40, 600);
            // Manifest clip ticks exclude ONCE start blending. Kinematic candidates are tentative.
            windup = ability.element() == Element.VOID ? 0 : WarlockAbilities.ticks(ability, "cast_ticks",
                    ability.element() == Element.SOLAR ? 32 : 25, 1, 80) + SwordTiming.START_TICKS;
            contactDelay = WarlockAbilities.ticks(ability, "attack_contact_ticks",
                    ability.element() == Element.SOLAR ? 8 : ability.element() == Element.ARC ? 5 : 14, 1, 40) + SwordTiming.START_TICKS;
            attackDuration = Math.max(contactDelay, WarlockAbilities.ticks(ability, "attack_duration_ticks",
                    ability.element() == Element.SOLAR ? 21 : ability.element() == Element.ARC ? 10 : 26, 1, 80) + SwordTiming.START_TICKS);
            interval = WarlockAbilities.ticks(ability, "attack_interval_ticks", ability.element() == Element.ARC ? 8 : 12, 5, 40);
            projectileLife = WarlockAbilities.ticks(ability, "projectile_life_ticks", 60, 10, 80);
        }
        @Override public boolean damageResistanceActive() {
            return !ended && lease.valid() && age < (ability.element() == Element.VOID ? attackDuration : duration);
        }
        @Override public boolean tick() {
            if (ended || !lease.valid()) return false;
            ClassAbilityEffects.superTick(lease.owner, ability.element(), ability.id().getPath(), age);
            flights.removeIf(SimProjectile::isDone);
            if (ability.element() == Element.VOID) {
                if (!novaPreparing) {
                    novaPreparing = true;
                    ClassAbilityEffects.attack(lease.owner, ability.element(), ability.id().getPath());
                }
                if (!novaReleased && age >= contactDelay) releaseNova();
                if (novaResolved && age >= attackDuration) return false;
                // Nova always has enough time to finish its finite flight, even with tuned windup.
                if (age++ >= contactDelay + projectileLife + 2) return false;
                return true;
            }
            if (age >= duration) return false;
            if (swordContact >= 0 && age >= swordContact) { swordContact = -1; sword(); }
            if (stormContact >= 0 && age >= stormContact) { stormContact = -1; storm(); }
            if (ability.element() == Element.ARC && age >= windup && age < channelUntil
                    && age >= nextAttack && stormContact < 0) {
                ClassAbilityEffects.attack(lease.owner, ability.element(), ability.id().getPath());
                SuperCamera.blockMovement(lease.owner, attackDuration);
                stormContact = age + contactDelay;
                nextAttack = age + Math.max(interval, attackDuration);
            }
            age++;
            return true;
        }
        @Override public void primary() {
            if (ended || !lease.valid() || age >= duration) return;
            if (ability.element() == Element.VOID) return; // Nova is automatic, clicks can never release it.
            if (ability.element() == Element.ARC) {
                if (age < windup) return;
                channelUntil = Math.min(duration, age + 12);
                return;
            }
            if (age < windup || age < nextAttack || swordContact >= 0 || flights.size() >= 3) return;
            ClassAbilityEffects.attack(lease.owner, ability.element(), ability.id().getPath());
            SuperCamera.blockMovement(lease.owner, attackDuration);
            swordContact = age + contactDelay;
            nextAttack = age + Math.max(interval, attackDuration);
        }
        private void announce() {
            ClassAbilityEffects.sound(lease.owner, ability.element(), "super.fire");
        }
        private void storm() {
            LivingEntity target = WarlockAbilities.aimed(lease, WarlockAbilities.value(ability, "range", 10, 2, 16));
            if (target == null) return;
            announce();
            Set<UUID> visited = new HashSet<>(); Vec3 from = lease.owner.getEyePosition();
            int cap = WarlockAbilities.ticks(ability, "max_targets", 3, 1, 5);
            double hop = WarlockAbilities.value(ability, "chain_range", 4, 1, 6);
            float damage = (float) WarlockAbilities.value(ability, "damage", 5, .1, 30);
            for (int i = 0; i < cap && target != null; i++) {
                Vec3 end = WarlockAbilities.center(target);
                if (!WarlockAbilities.visible(lease, from, end)) break;
                visited.add(target.getUUID());
                superDamage(target, damage);
                Fx.line(lease.owner, lease.level, from, end, ability.element().color(), .2, 1f);
                from = end;
                target = WarlockAbilities.targets(lease, from, hop).stream().filter(e -> !visited.contains(e.getUUID())).findFirst().orElse(null);
            }
        }
        private void sword() {
            announce(); emitted++;
            Vec3 velocity = lease.owner.getLookAngle().scale(WarlockAbilities.value(ability, "projectile_speed", 1.8, .5, 3));
            flights.add(WarlockAbilities.own(lease, SimProjectile.launch(lease.owner, lease.owner.getEyePosition(), velocity, 0, projectileLife,
                    ClassAbilityEffects.item(ability.id().getPath()), 1f, ability.element().color(), hit -> {
                        if (!live()) return;
                        impacts++;
                        Vec3 origin = WarlockAbilities.impactPoint(hit);
                        float damage = (float) WarlockAbilities.value(ability, "damage", 12, .1, 60);
                        double radius = WarlockAbilities.value(ability, "radius", 2.5, .5, 4);
                        for (LivingEntity target : WarlockAbilities.targets(lease, origin, radius)) superDamage(target, damage);
                        impact(origin, radius);
                    })));
        }
        private void releaseNova() {
            novaReleased = true; emitted++; announce(); // Set before launch; reentrant input cannot duplicate.
            Vec3 velocity = lease.owner.getLookAngle().scale(WarlockAbilities.value(ability, "projectile_speed", .9, .3, 2));
            flights.add(WarlockAbilities.own(lease, SimProjectile.launch(lease.owner, lease.owner.getEyePosition(), velocity, 0, projectileLife,
                    ClassAbilityEffects.item(ability.id().getPath()), 1.6f, ability.element().color(), hit -> {
                        if (!live() || novaResolved) return;
                        novaResolved = true; impacts++;
                        Vec3 origin = WarlockAbilities.impactPoint(hit);
                        double radius = WarlockAbilities.value(ability, "radius", 4, 1, 6);
                        float damage = (float) WarlockAbilities.value(ability, "damage", 24, .1, 100);
                        for (LivingEntity target : WarlockAbilities.targets(lease, origin, radius)) superDamage(target, damage);
                        // Finite post-blast Vortex continues after Nova's cast/camera recovery ends.
                        VORTICES.removeIf(v -> v.lease.owner == lease.owner);
                        VORTICES.add(new Vortex(lease, ability, origin));
                        impact(origin, radius);
                    })));
        }
        private boolean live() { return !ended && lease.valid(); }
        private void superDamage(LivingEntity target, float damage) {
            if (live() && WarlockAbilities.enemy(lease.owner, target))
                Combat.damage(lease.level, lease.owner, target, damage, ability.element(), AmmoGeneration.SUPER);
        }
        private void impact(Vec3 origin, double radius) {
            ClassAbilityEffects.burst(lease.owner, origin, ability.element(), radius);
            ClassAbilityEffects.soundAt(lease.owner, ability.element(), ability.id().getPath(), "super.impact", origin);
        }
        @Override public void end() {
            if (ended) return;
            ended = true;
            flights.forEach(SimProjectile::cancel);
            flights.clear();
            ACTIVE.remove(lease.owner, this);
            SuperCamera.blockMovement(lease.owner, 0);
            ClassAbilityEffects.endSuper(lease.owner, ability.element(), ability.id().getPath());
        }
        @Override public float remaining() {
            int limit = ability.element() == Element.VOID ? contactDelay + projectileLife + 2 : duration;
            return ended ? 0 : Math.clamp(1f - (float) age / limit, 0f, 1f);
        }
    }
    static void cleanup(ServerPlayer p) {
        VORTICES.removeIf(v -> v.lease.owner == p);
        Session session = ACTIVE.remove(p);
        if (session == null) return;
        Guardians.runtimeIfPresent(p).ifPresent(r -> { if (r.superSession == session) r.superSession = null; });
        session.end();
    }
    public static int emitted(ServerPlayer p) { Session s = ACTIVE.get(p); return s == null ? 0 : s.emitted; }
    public static int impacts(ServerPlayer p) { Session s = ACTIVE.get(p); return s == null ? 0 : s.impacts; }
}
