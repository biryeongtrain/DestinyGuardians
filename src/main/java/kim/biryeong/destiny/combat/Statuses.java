package kim.biryeong.destiny.combat;

import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.player.Player;

import java.util.EnumMap;
import java.util.HashMap;
import java.util.Iterator;
import java.util.Map;
import java.util.UUID;

/**
 * 키워드 상태 관리. 바닐라 효과로 보이게 하고, 바닐라에 없는 효과(약화·지속 피해·몹 실명)는 여기서 처리한다.
 */
public final class Statuses {
    public static final float WEAKEN_MULTIPLIER = 1.3f;

    private static final Map<UUID, Map<Keyword, Long>> ACTIVE = new HashMap<>();
    private static final Map<UUID, ServerLevel> LEVELS = new HashMap<>();
    private static final Map<UUID, net.minecraft.server.level.ServerPlayer> SCORCH_OWNERS = new HashMap<>();

    private Statuses() {
    }

    public static void apply(LivingEntity target, Keyword keyword, int ticks) {
        if (!(target.level() instanceof ServerLevel level)) {
            return;
        }
        long until = level.getGameTime() + ticks;
        ACTIVE.computeIfAbsent(target.getUUID(), id -> new EnumMap<>(Keyword.class)).merge(keyword, until, Math::max);
        LEVELS.put(target.getUUID(), level);
        switch (keyword) {
            case BLINDED -> {
                if (target instanceof Player) {
                    target.addEffect(new MobEffectInstance(MobEffects.BLINDNESS, ticks, 0));
                }
                target.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, ticks, 2));
                clearTarget(target);
            }
            case AMPLIFIED -> target.addEffect(new MobEffectInstance(MobEffects.SPEED, ticks, 1));
            case SCORCHED -> {
                // PvP scorch has its own normalized non-lethal pulse; vanilla fire would double-charge it.
                if (!(target instanceof Player))
                    target.setRemainingFireTicks(Math.max(target.getRemainingFireTicks(), ticks));
            }
            case WEAKENED -> target.addEffect(new MobEffectInstance(MobEffects.GLOWING, ticks, 0));
            case SUPPRESSED -> {
                target.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, ticks, 3));
                target.addEffect(new MobEffectInstance(MobEffects.WEAKNESS, ticks, 1));
                clearTarget(target);
            }
        }
    }

    public static boolean has(Entity target, Keyword keyword) {
        Map<Keyword, Long> map = ACTIVE.get(target.getUUID());
        if (map == null || !(target.level() instanceof ServerLevel level)) {
            return false;
        }
        Long until = map.get(keyword);
        return until != null && until > level.getGameTime();
    }

    public static void scorch(net.minecraft.server.level.ServerPlayer owner, LivingEntity target, int ticks) {
        apply(target, Keyword.SCORCHED, ticks);
        SCORCH_OWNERS.put(target.getUUID(), owner);
        target.setLastHurtByPlayer(owner, ticks);
    }

    /** Includes vanilla fire ticks, which can kill before the explicit scorch pulse. */
    public static void creditFireDeath(LivingEntity target, net.minecraft.world.damagesource.DamageSource source) {
        var owner = SCORCH_OWNERS.remove(target.getUUID());
        if (owner != null && has(target, Keyword.SCORCHED)
                && source.is(net.minecraft.tags.DamageTypeTags.IS_FIRE)
                && owner.isAlive() && !owner.isRemoved()) {
            kim.biryeong.destiny.ability.AbilityService.onKill(owner, target, kim.biryeong.destiny.guardian.Element.SOLAR);
        }
    }

    public static void forget(Entity entity) {
        ACTIVE.remove(entity.getUUID());
        LEVELS.remove(entity.getUUID());
        SCORCH_OWNERS.remove(entity.getUUID());
        if (entity instanceof net.minecraft.server.level.ServerPlayer player) {
            SCORCH_OWNERS.values().removeIf(owner -> owner == player);
        }
    }

    /** 받는 피해 보정 (LivingEntityMixin). */
    public static float modifyIncoming(LivingEntity target, float amount) {
        return has(target, Keyword.WEAKENED)
                ? amount * (target instanceof Player ? 1.075f : WEAKEN_MULTIPLIER) : amount;
    }

    public static void tick(MinecraftServer server) {
        Iterator<Map.Entry<UUID, Map<Keyword, Long>>> it = ACTIVE.entrySet().iterator();
        while (it.hasNext()) {
            var entry = it.next();
            ServerLevel level = LEVELS.get(entry.getKey());
            Entity entity = level == null ? null : level.getEntity(entry.getKey());
            if (!(entity instanceof LivingEntity living) || !living.isAlive()) {
                it.remove();
                LEVELS.remove(entry.getKey());
                SCORCH_OWNERS.remove(entry.getKey());
                continue;
            }
            long now = level.getGameTime();
            entry.getValue().values().removeIf(until -> until <= now);
            if (!entry.getValue().containsKey(Keyword.SCORCHED)) SCORCH_OWNERS.remove(entry.getKey());
            if (entry.getValue().isEmpty()) {
                it.remove();
                LEVELS.remove(entry.getKey());
                continue;
            }
            if (entry.getValue().containsKey(Keyword.BLINDED) || entry.getValue().containsKey(Keyword.SUPPRESSED)) {
                clearTarget(living);
            }
            if (entry.getValue().containsKey(Keyword.SCORCHED)) {
                if (living instanceof net.minecraft.server.level.ServerPlayer player) {
                    // DDC x50 representative: 6.5 points / .56s, rounded to 11 server ticks.
                    // Stack/ignition simulation is not implemented; retain the accepted cast duration.
                    var owner = SCORCH_OWNERS.get(player.getUUID());
                    if (now % 11 == 0 && owner != null) {
                        float points = 6.5f * player.getMaxHealth() / 230f;
                        // Reserve HP even if the common PvP weakness (7.5%) modifies this pulse later.
                        float budget = Math.max(0, (player.getHealth() - .1f) / 1.075f);
                        if (budget > 0) Combat.damage(level, owner, player, Math.min(points, budget),
                                kim.biryeong.destiny.guardian.Element.SOLAR);
                    }
                } else if (now % 20 == 0) {
                    living.damageCooldownTime = 0;
                    living.hurtServer(level, living.damageSources().onFire(), 2f);
                }
            }
        }
    }

    public static void clearAll() {
        ACTIVE.clear();
        LEVELS.clear();
        SCORCH_OWNERS.clear();
    }

    private static void clearTarget(LivingEntity target) {
        if (target instanceof Mob mob) {
            mob.setTarget(null);
        }
    }
}
