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

/** 능력 피해·대상 선택 공통 함수. PvE 기준: 플레이어는 대상이 아니다. */
public final class Combat {
    private Combat() {
    }

    public static boolean isEnemy(ServerPlayer source, Entity entity) {
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
        if (source.level() != level || target.level() != level || !source.isAlive() || !target.isAlive()) {
            return false;
        }
        if (!kim.biryeong.destiny.world.TowerSpawnWorld.mayAttack(level, target)) return false;
        if (attribution.kind() == kim.biryeong.destiny.weapon.AmmoGeneration.Kind.PRIMARY
                || attribution.kind() == kim.biryeong.destiny.weapon.AmmoGeneration.Kind.SPECIAL
                || attribution.kind() == kim.biryeong.destiny.weapon.AmmoGeneration.Kind.HEAVY) {
            amount *= (float) kim.biryeong.destiny.ability.warlock.WarlockExpandedSupers.outgoingDamageMultiplier(source);
        }
        target.damageCooldownTime = 0;
        target.hurtServer(level, source.damageSources().playerAttack(source), amount);
        target.setLastHurtByPlayer(source, 100);
        boolean killed = !target.isAlive() || target.isDeadOrDying();
        if (killed) {
            AbilityService.onKill(source, target, element);
        }
        return killed;
    }
}
