package kim.biryeong.destiny.ability.hunter;

import kim.biryeong.destiny.ability.Ability;
import kim.biryeong.destiny.ability.Motion;
import kim.biryeong.destiny.ability.Tasks;
import kim.biryeong.destiny.combat.Combat;
import kim.biryeong.destiny.combat.Keyword;
import kim.biryeong.destiny.combat.Statuses;
import kim.biryeong.destiny.fx.Fx;
import kim.biryeong.destiny.fx.SimProjectile;
import kim.biryeong.destiny.guardian.AbilitySlot;
import kim.biryeong.destiny.guardian.Element;
import kim.biryeong.destiny.guardian.GuardianClass;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.phys.EntityHitResult;
import net.minecraft.world.phys.Vec3;

/**
 * 헌터 근접 능력 3종.
 * Arc 연속 타격(돌진 + 처치 시 증폭), Solar 칼 투척(연소), Void 연막탄(억제 + 본인 투명).
 */
public final class HunterMelee extends Ability {
    public HunterMelee(Identifier id, String name, Element element, double cooldownSeconds) {
        super(id, GuardianClass.HUNTER, AbilitySlot.MELEE, element, cooldownSeconds, name);
    }

    @Override
    public boolean activate(ServerPlayer player) {
        return switch (element()) {
            case ARC -> combinationBlow(player);
            case SOLAR -> knife(player);
            default -> smoke(player);
        };
    }

    private boolean combinationBlow(ServerPlayer player) {
        ServerLevel level = player.level();
        Vec3 dir = Motion.horizontalLook(player);
        Motion.setVelocity(player, new Vec3(dir.x * param("lunge", 1.3), 0.1, dir.z * param("lunge", 1.3)));
        Fx.sound(level, player.position(), SoundEvents.PLAYER_ATTACK_SWEEP, 1f, 1.8f);
        float damage = (float) param("damage", 12);
        double reach = param("reach", 2.8);
        Tasks.run(player, level, age -> {
            Vec3 center = player.position().add(0, 1, 0).add(Motion.horizontalLook(player).scale(1.2));
            level.sendParticles(ParticleTypes.ELECTRIC_SPARK, center.x, center.y, center.z, 6, 0.4, 0.4, 0.4, 0.1);
            if (age == 3) {
                for (LivingEntity e : Combat.enemiesNear(level, player, center, reach)) {
                    Fx.line(level, player.getEyePosition(), e.position().add(0, e.getBbHeight() / 2, 0), element().color(), 0.25, 1.0f);
                    if (Combat.damage(level, player, e, damage, element())) {
                        Statuses.apply(player, Keyword.AMPLIFIED, (int) param("amplified_ticks", 120));
                        player.heal((float) param("heal_on_kill", 4));
                    }
                }
                Fx.burst(level, center, element(), 30, 0.6);
                return false;
            }
            return true;
        });
        return true;
    }

    private boolean knife(ServerPlayer player) {
        float damage = (float) param("damage", 10);
        SimProjectile.launch(player, player.getEyePosition(), player.getLookAngle().scale(param("speed", 2.2)), 0.008, 30,
                HunterAbilityVisuals.melee(element()), 0.6f, element().color(), hit -> {
                    ServerLevel level = player.level();
                    Fx.burst(level, hit.getLocation(), element(), 20, 0.3);
                    if (hit instanceof EntityHitResult eh && eh.getEntity() instanceof LivingEntity target) {
                        Combat.damage(level, player, target, damage, element());
                        Statuses.scorch(player, target, (int) param("scorch_ticks", 80));
                    }
                });
        Fx.sound(player.level(), player.getEyePosition(), SoundEvents.TRIDENT_THROW.value(), 0.8f, 1.5f);
        return true;
    }

    private boolean smoke(ServerPlayer player) {
        double radius = param("radius", 3.5);
        int duration = (int) param("duration_ticks", 100);
        SimProjectile.launch(player, player.getEyePosition(), player.getLookAngle().scale(1.0).add(0, 0.1, 0), 0.05, 60,
                HunterAbilityVisuals.melee(element()), 0.5f, element().color(), hit -> {
                    ServerLevel level = player.level();
                    Vec3 pos = hit.getLocation();
                    Fx.sound(level, pos, SoundEvents.FIRE_EXTINGUISH, 0.8f, 0.6f);
                    Tasks.run(player, level, age -> {
                        level.sendParticles(ParticleTypes.LARGE_SMOKE, pos.x, pos.y + 0.5, pos.z, 6, radius / 2, 0.5, radius / 2, 0.01);
                        level.sendParticles(Fx.dust(element().color(), 2.0f), pos.x, pos.y + 0.5, pos.z, 4, radius / 2, 0.5, radius / 2, 0.0);
                        if (age % 10 == 0) {
                            for (LivingEntity e : Combat.enemiesNear(level, player, pos, radius)) {
                                Statuses.apply(e, Keyword.SUPPRESSED, 20);
                            }
                            for (Player p : level.getEntitiesOfClass(Player.class, new net.minecraft.world.phys.AABB(pos, pos).inflate(radius))) {
                                p.addEffect(new MobEffectInstance(MobEffects.INVISIBILITY, 40, 0, false, false));
                            }
                        }
                        return age < duration;
                    });
                });
        return true;
    }
}
