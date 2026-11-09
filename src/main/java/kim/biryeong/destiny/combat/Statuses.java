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
    private record Weaken(ServerLevel level, long until, float pve, float pvp) {}
    private record ExternalScorch(ServerLevel level,long until) {}
    private static final Map<UUID, ExternalScorch> EXTERNAL_SCORCH = new HashMap<>();
    private static final Map<UUID, Weaken> STRONG_WEAKEN = new HashMap<>();
    private static final Map<UUID, ServerLevel> LEVELS = new HashMap<>();
    private static final Map<UUID, net.minecraft.server.level.ServerPlayer> SCORCH_OWNERS = new HashMap<>();

    private static final Map<UUID, kim.biryeong.destiny.weapon.WeaponAdrenalineJunkie.GrenadeToken> SCORCH_GRENADES = new HashMap<>();

    private static final Map<UUID, kim.biryeong.destiny.weapon.PerkExpansionCombat.AbilityToken> SCORCH_MELEES = new HashMap<>();

    /** Attribution is explicit; generic statuses never infer an owner from last attacker. */
    public static void apply(net.minecraft.server.level.ServerPlayer owner, LivingEntity target, Keyword keyword, int ticks) {
        if (owner == null || target == null || ticks <= 0 || !target.isAlive() || owner.level() != target.level()
                || !Combat.isEnemy(owner, target)) return;
        apply(target, keyword, ticks);
        if (keyword != Keyword.AMPLIFIED && has(target, keyword))
            kim.biryeong.destiny.weapon.PerkExpansionSupport.debuffApplied(owner, target);
    }

    /** Strong nonstacking weaken, sharing the existing incoming-damage and expiry path. */
    public static void applyWeaken(net.minecraft.server.level.ServerPlayer owner, LivingEntity target, int ticks,
                                   float pveMultiplier, float pvpMultiplier) {
        if (!Float.isFinite(pveMultiplier) || !Float.isFinite(pvpMultiplier) || pveMultiplier < 1 || pvpMultiplier < 1
                || pveMultiplier > 3 || pvpMultiplier > 3 || owner == null || target == null || ticks <= 0
                || !target.isAlive() || owner.level()!=target.level() || !Combat.isEnemy(owner,target)) return;
        apply(owner,target,Keyword.WEAKENED,ticks);
        var old=STRONG_WEAKEN.get(target.getUUID());
        long until=owner.level().getGameTime()+ticks;
        // Strongest effect wins; a weaker later application cannot extend the stronger lease.
        if (old==null || old.level()!=target.level() || old.until()<=owner.level().getGameTime()
                || pveMultiplier>=old.pve() && pvpMultiplier>=old.pvp())
            STRONG_WEAKEN.put(target.getUUID(),new Weaken(owner.level(),until,pveMultiplier,pvpMultiplier));
    }

    /** A separate attributed stack service owns the damage pulses; expose the keyword without
     * also adding vanilla fire or the legacy generic scorch pulse a second time. */
    public static void markScorched(LivingEntity target,int ticks) {
        if(ticks<=0||!target.isAlive()||!(target.level() instanceof ServerLevel level))return;
        long until=level.getGameTime()+ticks;
        ACTIVE.computeIfAbsent(target.getUUID(),id->new EnumMap<>(Keyword.class)).put(Keyword.SCORCHED,until);
        LEVELS.put(target.getUUID(),level);
        EXTERNAL_SCORCH.put(target.getUUID(),new ExternalScorch(level,until));
        SCORCH_OWNERS.remove(target.getUUID());SCORCH_GRENADES.remove(target.getUUID());SCORCH_MELEES.remove(target.getUUID());
    }

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
                EXTERNAL_SCORCH.remove(target.getUUID());
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
        if (owner == null || target == null || ticks <= 0 || !target.isAlive()
                || owner.level() != target.level() || !Combat.isEnemy(owner, target)) return;
        SCORCH_GRENADES.remove(target.getUUID());
        SCORCH_MELEES.remove(target.getUUID());
        apply(owner, target, Keyword.SCORCHED, ticks);
        SCORCH_OWNERS.put(target.getUUID(), owner);
        target.setLastHurtByPlayer(owner, ticks);
    }

    /** Dedicated grenade attribution; later melee/super scorch explicitly replaces this credit. */
    public static void scorch(net.minecraft.server.level.ServerPlayer owner, LivingEntity target, int ticks,
                              kim.biryeong.destiny.weapon.WeaponAdrenalineJunkie.GrenadeToken token) {
        if (!target.isAlive()) return;
        scorch(owner, target, ticks);
        if (token != null && token != kim.biryeong.destiny.weapon.WeaponAdrenalineJunkie.GrenadeToken.NONE)
            SCORCH_GRENADES.put(target.getUUID(), token);
    }

    /** Captured powered melee scorch; later grenade/super/weapon scorch replaces attribution. */
    public static void scorch(net.minecraft.server.level.ServerPlayer owner, LivingEntity target, int ticks,
                              kim.biryeong.destiny.weapon.PerkExpansionCombat.AbilityToken token) {
        scorch(owner, target, ticks);
        if (target != null && SCORCH_OWNERS.get(target.getUUID()) == owner && target.isAlive()
                && token != null && token != kim.biryeong.destiny.weapon.PerkExpansionCombat.AbilityToken.NONE)
            SCORCH_MELEES.put(target.getUUID(), token);
    }

    /** Includes vanilla fire ticks, which can kill before the explicit scorch pulse. */
    public static void creditFireDeath(LivingEntity target, net.minecraft.world.damagesource.DamageSource source) {
        var owner = SCORCH_OWNERS.remove(target.getUUID());
        var grenade = SCORCH_GRENADES.remove(target.getUUID());
        var melee = SCORCH_MELEES.remove(target.getUUID());
        if (owner != null && has(target, Keyword.SCORCHED)
                && source.is(net.minecraft.tags.DamageTypeTags.IS_FIRE)
                && owner.isAlive() && !owner.isRemoved()) {
            kim.biryeong.destiny.ability.AbilityService.onKill(owner, target, kim.biryeong.destiny.guardian.Element.SOLAR);
            kim.biryeong.destiny.weapon.WeaponAdrenalineJunkie.grenadeKilled(owner, grenade, target);
            kim.biryeong.destiny.weapon.PerkExpansionCombat.abilityKilled(owner, melee, target);
        }
    }

    public static void forget(Entity entity) {
        EXTERNAL_SCORCH.remove(entity.getUUID());
        STRONG_WEAKEN.remove(entity.getUUID());
        ACTIVE.remove(entity.getUUID());
        LEVELS.remove(entity.getUUID());
        SCORCH_OWNERS.remove(entity.getUUID());
        SCORCH_GRENADES.remove(entity.getUUID());
        SCORCH_MELEES.remove(entity.getUUID());
        if (entity instanceof net.minecraft.server.level.ServerPlayer player) {
            SCORCH_OWNERS.values().removeIf(owner -> owner == player);
            SCORCH_GRENADES.keySet().retainAll(SCORCH_OWNERS.keySet());
            SCORCH_MELEES.keySet().retainAll(SCORCH_OWNERS.keySet());
        }
    }

    /** 받는 피해 보정 (LivingEntityMixin). */
    public static float modifyIncoming(LivingEntity target, float amount) {
        float multiplier=has(target,Keyword.WEAKENED)?target instanceof Player?1.075f:WEAKEN_MULTIPLIER:1;
        var strong=STRONG_WEAKEN.get(target.getUUID());
        if(strong!=null && strong.level()==target.level() && strong.until()>strong.level().getGameTime())
            multiplier=Math.max(multiplier,target instanceof Player?strong.pvp():strong.pve());
        return amount*multiplier;
    }

    public static void tick(MinecraftServer server) {
        EXTERNAL_SCORCH.entrySet().removeIf(e -> {
            var w=e.getValue();if(w.level().getServer()!=server)return false;
            var target=w.level().getEntity(e.getKey());
            return target==null||!target.isAlive()||w.until()<=w.level().getGameTime();
        });
        STRONG_WEAKEN.entrySet().removeIf(e -> {
            var w=e.getValue(); if(w.level().getServer()!=server)return false;
            var target=w.level().getEntity(e.getKey());
            return target==null || !target.isAlive() || w.until()<=w.level().getGameTime();
        });
        Iterator<Map.Entry<UUID, Map<Keyword, Long>>> it = ACTIVE.entrySet().iterator();
        while (it.hasNext()) {
            var entry = it.next();
            ServerLevel level = LEVELS.get(entry.getKey());
            Entity entity = level == null ? null : level.getEntity(entry.getKey());
            if (!(entity instanceof LivingEntity living) || !living.isAlive()) {
                it.remove();
                LEVELS.remove(entry.getKey());
                SCORCH_OWNERS.remove(entry.getKey());
                SCORCH_GRENADES.remove(entry.getKey()); SCORCH_MELEES.remove(entry.getKey());
                continue;
            }
            long now = level.getGameTime();
            entry.getValue().values().removeIf(until -> until <= now);
            if (!entry.getValue().containsKey(Keyword.SCORCHED)) {
                SCORCH_OWNERS.remove(entry.getKey()); SCORCH_GRENADES.remove(entry.getKey()); SCORCH_MELEES.remove(entry.getKey());
            }
            if (entry.getValue().isEmpty()) {
                it.remove();
                LEVELS.remove(entry.getKey());
                continue;
            }
            if (entry.getValue().containsKey(Keyword.BLINDED) || entry.getValue().containsKey(Keyword.SUPPRESSED)) {
                clearTarget(living);
            }
            if (entry.getValue().containsKey(Keyword.SCORCHED) && !EXTERNAL_SCORCH.containsKey(entry.getKey())) {
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
        EXTERNAL_SCORCH.clear();
        STRONG_WEAKEN.clear();
        ACTIVE.clear();
        LEVELS.clear();
        SCORCH_OWNERS.clear();
        SCORCH_GRENADES.clear();
        SCORCH_MELEES.clear();
    }

    private static void clearTarget(LivingEntity target) {
        if (target instanceof Mob mob) {
            mob.setTarget(null);
        }
    }
}
