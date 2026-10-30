package kim.biryeong.destiny.ability.warlock;

import kim.biryeong.destiny.ability.Ability;
import kim.biryeong.destiny.combat.Combat;
import kim.biryeong.destiny.fx.*;
import kim.biryeong.destiny.guardian.*;
import kim.biryeong.destiny.weapon.MeleeWeaponTraits;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.phys.*;
import java.util.*;

/** Real powered contacts only; own finite pulses do not outlive their captured class epoch. */
public final class WarlockMelee extends Ability {
    private static final List<Burn> BURNS = new ArrayList<>();
    private static final class Burn {
        final WarlockAbilities.Lease lease; final LivingEntity target; final Vec3 origin;
        int age;
        Burn(WarlockAbilities.Lease lease, LivingEntity target, Vec3 origin) { this.lease = lease; this.target = target; this.origin = origin; }
    }
    static void tick() {
        for (Burn burn : List.copyOf(BURNS)) {
            if (!burn.lease.valid() || !WarlockAbilities.enemy(burn.lease.owner, burn.target) || burn.age >= 30) { BURNS.remove(burn); continue; }
            if (++burn.age % 10 == 0 && WarlockAbilities.center(burn.target).distanceToSqr(burn.origin) <= 36
                    && WarlockAbilities.visible(burn.lease, burn.origin, WarlockAbilities.center(burn.target)))
                Combat.damage(burn.lease.level, burn.lease.owner, burn.target, 1f, Element.SOLAR);
        }
    }
    static void cleanup(ServerPlayer p) { BURNS.removeIf(b -> b.lease.owner == p); }

    public WarlockMelee(Identifier id, Element e) {
        super(id, GuardianClass.WARLOCK, AbilitySlot.MELEE, e, 22,
                e == Element.ARC ? "연쇄 번개" : e == Element.SOLAR ? "소각의 손가락 튕기기" : "소형 특이점");
    }
    @Override public boolean activate(ServerPlayer p) {
        var lease = WarlockAbilities.acquire(p, this);
        if (lease == null) return false;
        var traits = MeleeWeaponTraits.accepted(p);
        float damage = (float) WarlockAbilities.value(this, "damage", 6, .1, 30);
        switch (element()) {
            case ARC -> {
                LivingEntity first = WarlockAbilities.aimed(lease, WarlockAbilities.value(this, "range", 5, 1, 8));
                if (first == null) return false;
                chain(lease, first, damage, traits);
            }
            case SOLAR -> {
                Vec3 look = p.getLookAngle(), side = new Vec3(-look.z, 0, look.x).normalize();
                Set<UUID> contacted = new HashSet<>();
                // Five real fire sparks; a target may receive one powered contact per accepted snap.
                for (int i = -2; i <= 2; i++) {
                    Vec3 velocity = look.add(side.scale(i * .17)).normalize().scale(.7);
                    WarlockAbilities.own(lease, SimProjectile.launch(p, p.getEyePosition(), velocity, 0, 7,
                            ClassAbilityEffects.item(id().getPath()), .2f, element().color(), hit -> {
                                if (!lease.valid() || !(hit instanceof EntityHitResult eh)
                                        || !(eh.getEntity() instanceof LivingEntity target)
                                        || !WarlockAbilities.enemy(p, target) || !contacted.add(target.getUUID())) return;
                                MeleeWeaponTraits.poweredDamage(lease.level, p, target, damage, element(), traits);
                                if (target.isAlive()) {
                                    BURNS.removeIf(b -> b.lease.owner == p && b.target == target);
                                    BURNS.add(new Burn(lease, target, p.getEyePosition()));
                                }
                                ClassAbilityEffects.sound(p, element(), "melee.impact");
                                ClassAbilityEffects.burst(p, hit.getLocation(), element(), .6);
                            }));
                }
            }
            case VOID -> WarlockAbilities.own(lease, SimProjectile.launch(p, p.getEyePosition(), p.getLookAngle().scale(1.1), 0, 35,
                    ClassAbilityEffects.item(id().getPath()), .45f, element().color(), hit -> {
                        if (!lease.valid()) return;
                        ClassAbilityEffects.burst(p, WarlockAbilities.impactPoint(hit), element(), .8);
                        ClassAbilityEffects.sound(p, element(), "melee.impact");
                        if (hit instanceof EntityHitResult eh && eh.getEntity() instanceof LivingEntity target
                                && WarlockAbilities.enemy(p, target)) {
                            MeleeWeaponTraits.poweredDamage(lease.level, p, target, damage, element(), traits);
                            if (target.isAlive()) {
                                Vec3 away = WarlockAbilities.center(target).subtract(p.getEyePosition());
                                if (away.lengthSqr() > .001) target.setDeltaMovement(target.getDeltaMovement()
                                        .add(away.normalize().scale(.5)).add(0, .15, 0));
                            }
                        }
                    }));
            default -> { return false; }
        }
        ClassAbilityEffects.sound(p, element(), "melee.cast");
        return true;
    }
    private void chain(WarlockAbilities.Lease lease, LivingEntity first, float damage, MeleeWeaponTraits.Snapshot traits) {
        Set<UUID> visited = new HashSet<>();
        LivingEntity target = first; Vec3 from = lease.owner.getEyePosition();
        int cap = WarlockAbilities.ticks(this, "max_targets", 3, 1, 5);
        double hop = WarlockAbilities.value(this, "chain_range", 4, 1, 6);
        for (int i = 0; i < cap && target != null; i++) {
            Vec3 end = WarlockAbilities.center(target);
            if (!WarlockAbilities.visible(lease, from, end)) break;
            visited.add(target.getUUID());
            MeleeWeaponTraits.poweredDamage(lease.level, lease.owner, target, damage, element(), traits);
            Fx.line(lease.owner, lease.level, from, end, element().color(), .25, .8f);
            from = end;
            target = WarlockAbilities.targets(lease, from, hop).stream().filter(e -> !visited.contains(e.getUUID())).findFirst().orElse(null);
        }
        ClassAbilityEffects.sound(lease.owner, element(), "melee.impact");
    }
}
