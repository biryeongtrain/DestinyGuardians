package kim.biryeong.destiny.combat;

import kim.biryeong.destiny.ability.AbilityService;
import kim.biryeong.destiny.guardian.Element;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.decoration.ArmorStand;
import net.minecraft.world.entity.monster.Enemy;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;

import java.util.Comparator;
import java.util.List;

/** 능력 피해·대상 선택. 플레이어 PvP는 시련의 장 세션의 적 팀 사이에서만 허용한다. */
public final class Combat {
    private record HurtContext(LivingEntity target, net.minecraft.world.damagesource.DamageSource source, Object emission) { }
    private static final ThreadLocal<HurtContext> ACTIVE_HURT = new ThreadLocal<>();
    private static final ThreadLocal<Object> EMISSION = new ThreadLocal<>();

    /** One accepted firing/contact event, shared by all of its multipart contacts. */
    public static EmissionScope emission(Object identity) { return new EmissionScope(java.util.Objects.requireNonNull(identity)); }
    public static final class EmissionScope implements AutoCloseable {
        private final Object previous=EMISSION.get();
        private boolean closed;
        private EmissionScope(Object identity){EMISSION.set(identity);}
        @Override public void close(){
            if(closed)return;closed=true;
            if(previous==null)EMISSION.remove();else EMISSION.set(previous);
        }
    }
    /** Exposed only during the matching synchronous hurt call, never a stale/nested source. */
    public static Object damageEmission(net.minecraft.world.damagesource.DamageSource source) {
        var context=ACTIVE_HURT.get();
        return context!=null&&context.source()==source?context.emission():null;
    }

    /** Enemy attacks do not push guardians; custom outgoing damage also keeps its scoped policy.
     * Cancel the impulse before velocity synchronization, without rewriting jump/dodge movement. */
    public static boolean suppressesKnockback(LivingEntity target, net.minecraft.world.damagesource.DamageSource source) {
        if (target instanceof ServerPlayer && source != null && source.getEntity() instanceof Mob) return true;
        var context = ACTIVE_HURT.get();
        return context != null && context.target() == target && context.source() == source;
    }
    private Combat() {
    }

    /** Multipart hitboxes keep region dispatch, but perks/rewards refer to one living actor. */
    public static LivingEntity damageOwner(LivingEntity target) {
        return target instanceof kim.biryeong.destiny.strike.devils.DevilsMob mob ? mob.damageOwner() : target;
    }
    public static float damagePool(LivingEntity target) {
        if(target instanceof kim.biryeong.destiny.strike.devils.DevilsMob mob && mob.walkerState()!=null)
            return (float)mob.walkerState().damagePool();
        return target.getHealth()+target.getAbsorptionAmount();
    }

    public static boolean isEnemy(ServerPlayer source, Entity entity) {
        if (entity instanceof ServerPlayer player) return player.isAlive()
                && kim.biryeong.destiny.crucible.CrucibleRuntime.canFight(source, player);
        return entity instanceof LivingEntity living
                && entity != source
                && living.isAlive()
                && !(entity instanceof Player)
                && !(entity instanceof ArmorStand)
                && !source.isAlliedTo(entity)
                && !(entity instanceof net.minecraft.world.entity.TamableAnimal tame && tame.isTame())
                && (entity instanceof Enemy || entity instanceof Mob);
    }

    public static List<LivingEntity> enemiesNear(ServerPlayer source, Vec3 center, double radius) {
        return enemiesNear(source.level(), source, center, radius);
    }

    public static List<LivingEntity> enemiesNear(ServerLevel level, ServerPlayer source, Vec3 center, double radius) {
        if (source.level() != level || !source.isAlive() || source.isRemoved()) return List.of();
        AABB box = AABB.ofSize(center, radius * 2, radius * 2, radius * 2);
        return level.getEntitiesOfClass(LivingEntity.class, box,
                        e -> isEnemy(source, e) && e.position().add(0, e.getBbHeight() / 2, 0).distanceTo(center) <= radius)
                .stream()
                .sorted(Comparator.comparingDouble(e -> e.distanceToSqr(center)))
                .toList();
    }

    /**
     * 능력 피해. 무적 시간을 무시하고 들어가며, 처치하면 궁극기 에너지를 준다.
     * @return 처치했으면 true
     */
    public static boolean damage(ServerPlayer source, LivingEntity target, float amount, Element element) {
        return damage(source.level(), source, target, amount, element);
    }

    public static boolean damage(ServerLevel level, ServerPlayer source, LivingEntity target, float amount, Element element) {
        return damage(level,source,target,amount,element,kim.biryeong.destiny.weapon.AmmoGeneration.ABILITY);
    }

    public static boolean damage(ServerLevel level, ServerPlayer source, LivingEntity target, float amount, Element element,
                                 kim.biryeong.destiny.weapon.AmmoGeneration attribution) {
        if (!Float.isFinite(amount) || amount <= 0 || source == target
                || source.level() != level || target.level() != level || !source.isAlive() || !target.isAlive()
                || source.isRemoved() || target.isRemoved()) {
            return false;
        }
        if (!kim.biryeong.destiny.strike.devils.DevilsLair.allows(source)) return false;
        if (!kim.biryeong.destiny.world.TowerSpawnWorld.mayAttack(level, target)) return false;
        if (target instanceof ServerPlayer player
                && !kim.biryeong.destiny.crucible.CrucibleRuntime.canFight(source, player)) return false;
        kim.biryeong.destiny.down.GuardianDown.attacked(source);
        if (attribution.kind() == kim.biryeong.destiny.weapon.AmmoGeneration.Kind.PRIMARY
                || attribution.kind() == kim.biryeong.destiny.weapon.AmmoGeneration.Kind.SPECIAL
                || attribution.kind() == kim.biryeong.destiny.weapon.AmmoGeneration.Kind.HEAVY) {
            amount *= (float) kim.biryeong.destiny.ability.warlock.WarlockExpandedSupers.outgoingDamageMultiplier(source);
        }
        amount = PveDamageBalance.scale(amount, attribution.kind(), target instanceof Player);
        if (!Float.isFinite(amount) || amount <= 0) return false;
        var recipient=damageOwner(target);
        if(!recipient.isAlive()||recipient.isRemoved())return false;
        float before=damagePool(target);
        target.damageCooldownTime = 0;
        var damageSource = target instanceof ServerPlayer
                ? new GuardianDamageSource(level.registryAccess().lookupOrThrow(
                        net.minecraft.core.registries.Registries.DAMAGE_TYPE).getOrThrow(
                        net.minecraft.resources.ResourceKey.create(net.minecraft.core.registries.Registries.DAMAGE_TYPE,
                                kim.biryeong.destiny.DestinyGuardians.id("crucible"))), source, attribution)
                : source.damageSources().playerAttack(source);
        var reward = kim.biryeong.destiny.crucible.CrucibleSuperRewards.begin(source, target, attribution);
        var previous = ACTIVE_HURT.get();
        ACTIVE_HURT.set(new HurtContext(target, damageSource, EMISSION.get()));
        boolean completed = false;
        try {
            target.hurtServer(level, damageSource, amount);
            completed = true;
        } finally {
            if (previous == null) ACTIVE_HURT.remove(); else ACTIVE_HURT.set(previous);
            reward.finish(completed);
        }
        float after=damagePool(target);
        kim.biryeong.destiny.weapon.AmmoEconomy.afterDamage(source,recipient,attribution,before,after);
        if(after<before)recipient.setLastHurtByPlayer(source, 100);
        boolean killed = after<before && (!recipient.isAlive() || recipient.isDeadOrDying());
        // PvP has its own actual-loss payout; do not also grant the old generic 4% kill reward.
        if (killed && !(recipient instanceof ServerPlayer)) {
            AbilityService.onKill(source, recipient, element);
        }
        return killed;
    }
}
