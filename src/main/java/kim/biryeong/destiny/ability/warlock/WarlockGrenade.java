package kim.biryeong.destiny.ability.warlock;

import kim.biryeong.destiny.ability.Ability;
import kim.biryeong.destiny.fx.*;
import kim.biryeong.destiny.guardian.*;
import kim.biryeong.destiny.weapon.WeaponAdrenalineJunkie;
import kim.biryeong.destiny.weapon.WeaponDemolitionist;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.phys.Vec3;
import java.util.*;

/** Storm, solar and vortex: a colliding throw followed by an owner-scoped finite field. */
public final class WarlockGrenade extends Ability {
    private static final List<Emission> FLIGHTS = new ArrayList<>();
    private static final List<Field> FIELDS = new ArrayList<>();
    private static final class Emission {
        final WarlockAbilities.Lease lease; SimProjectile projectile; boolean cancelled;
        Emission(WarlockAbilities.Lease lease) { this.lease = lease; }
        boolean valid() { return !cancelled && lease.valid(); }
    }
    private static final class Field {
        final WarlockAbilities.Lease lease; final WarlockGrenade ability; final Vec3 origin;
        final WeaponAdrenalineJunkie.GrenadeToken token;
        final int duration, interval; final double radius; final float damage;
        int age, pulses, lastTargets;
        float actualDamage;
        Field(WarlockAbilities.Lease lease, WarlockGrenade ability, Vec3 origin, WeaponAdrenalineJunkie.GrenadeToken token) {
            this.lease = lease; this.ability = ability; this.origin = origin; this.token = token;
            duration = WarlockAbilities.ticks(ability, "duration_ticks", 80, 1, 200);
            interval = WarlockAbilities.ticks(ability, "pulse_ticks", 10, 5, 40);
            radius = WarlockAbilities.value(ability, "radius", 3.5, 1, 5);
            damage = (float) WarlockAbilities.value(ability, "damage", ability.element() == Element.ARC ? 3 : 2, .1, 15);
        }
    }
    public WarlockGrenade(Identifier id, Element element) {
        super(id, GuardianClass.WARLOCK, AbilitySlot.GRENADE, element, element == Element.VOID ? 219.5 : 40,
                element == Element.ARC ? "폭풍 수류탄" : element == Element.SOLAR ? "태양 수류탄" : "소용돌이 수류탄");
    }
    @Override public boolean activate(ServerPlayer p) {
        var lease = WarlockAbilities.acquire(p, this);
        if (lease == null || ownedCount(p) >= 4) return false;
        var adrenaline = WeaponAdrenalineJunkie.grenadeAccepted(p);
        var demolitionist = WeaponDemolitionist.grenadeAccepted(p);
        return kim.biryeong.destiny.ability.GrenadeThrow.begin(p,id(),GrenadeModels.item(GuardianClass.WARLOCK,element()),lease::valid,()->{
        Emission emission = new Emission(lease);
        Vec3 velocity = p.getLookAngle().scale(WarlockAbilities.value(this, "throw_speed", 1.1, .4, 2)).add(0, .12, 0);
        emission.projectile = WarlockAbilities.own(lease, SimProjectile.launch(p, kim.biryeong.destiny.ability.GrenadeThrow.origin(p), velocity, .045, 60,
                GrenadeModels.item(GuardianClass.WARLOCK,element()), .5f, element().color(), hit -> {
                    if (!emission.valid()) return;
                    Vec3 center = WarlockAbilities.impactPoint(hit);
                    FIELDS.add(new Field(lease, this, center, adrenaline));
                    ClassAbilityEffects.burst(p, center, element(), 1);
                    ClassAbilityEffects.sound(p, element(), "grenade.impact");
                }));
        FLIGHTS.add(emission);
        WeaponDemolitionist.grenadeReleased(p, demolitionist); // Actual successful emission, once.
        ClassAbilityEffects.sound(p, element(), "grenade.throw");
        });
    }
    private static int ownedCount(ServerPlayer p) {
        return (int) (FLIGHTS.stream().filter(e -> e.lease.owner == p && !e.projectile.isDone()).count()
                + FIELDS.stream().filter(f -> f.lease.owner == p).count());
    }
    static void tick() {
        FLIGHTS.removeIf(e -> !e.valid() || e.projectile.isDone());
        for (Field f : List.copyOf(FIELDS)) {
            if (!f.lease.valid() || f.age >= f.duration) { FIELDS.remove(f); continue; }
            if (f.age % 5 == 0) Fx.ring(f.lease.level, f.origin, f.radius, f.ability.element().color(), 24);
            if (f.age % f.interval == 0) pulse(f);
            f.age++;
        }
    }
    private static void pulse(Field f) {
        Element element = f.ability.element();
        var targets = WarlockAbilities.targets(f.lease, f.origin, f.radius);
        f.pulses++; f.lastTargets = targets.size();
        for (LivingEntity target : targets) {
            float before = target.getHealth() + target.getAbsorptionAmount();
            WeaponAdrenalineJunkie.grenadeDamage(f.lease.owner, f.token, f.lease.level, target, f.damage, element);
            f.actualDamage += Math.max(0, before - target.getHealth() - target.getAbsorptionAmount());
            if (element == Element.VOID && target.isAlive()) {
                Vec3 pull = f.origin.subtract(WarlockAbilities.center(target));
                if (pull.lengthSqr() > .04) target.setDeltaMovement(target.getDeltaMovement().add(pull.normalize().scale(.08)));
            }
            if (element == Element.ARC) Fx.line(f.lease.level, f.origin, WarlockAbilities.center(target), element.color(), .3, .6f);
        }
    }
    static void cleanup(ServerPlayer p) {
        for (Emission e : FLIGHTS) if (e.lease.owner == p) e.cancelled = true;
        FLIGHTS.removeIf(e -> e.lease.owner == p);
        FIELDS.removeIf(f -> f.lease.owner == p);
    }
    public record FieldSnapshot(Vec3 origin, int age, int duration, int pulses, int lastTargets, float actualDamage) {}
    public static List<FieldSnapshot> fields(ServerPlayer p) {
        return FIELDS.stream().filter(f -> f.lease.owner == p)
                .map(f -> new FieldSnapshot(f.origin, f.age, f.duration, f.pulses, f.lastTargets, f.actualDamage)).toList();
    }
    public static int fieldCount(ServerPlayer p) { return (int) FIELDS.stream().filter(f -> f.lease.owner == p).count(); }
}
