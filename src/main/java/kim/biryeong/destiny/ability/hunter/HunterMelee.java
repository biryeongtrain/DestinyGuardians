package kim.biryeong.destiny.ability.hunter;

import kim.biryeong.destiny.ability.Ability;
import kim.biryeong.destiny.ability.Motion;
import kim.biryeong.destiny.ability.Tasks;
import kim.biryeong.destiny.combat.AbilityDamage;
import kim.biryeong.destiny.combat.Combat;
import kim.biryeong.destiny.combat.Keyword;
import kim.biryeong.destiny.combat.Statuses;
import kim.biryeong.destiny.fx.Fx;
import kim.biryeong.destiny.fx.AbilityParticles;
import kim.biryeong.destiny.sound.DestinySounds;
import kim.biryeong.destiny.fx.HunterVfx;
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
        HunterSkillCast cast = HunterSkillCast.begin(player, slot(), HunterAbilityVisuals.meleeAnimation(element()),
                HunterAbilityVisuals.melee(element()));
        if (cast == null) return false;
        var weaponTraits = kim.biryeong.destiny.weapon.MeleeWeaponTraits.accepted(player);
        if (element() == Element.ARC) {
            cast.at(HunterSkillTiming.ARC_LUNGE_TICKS, () -> {
                Vec3 dir = Motion.horizontalLook(player);
                Motion.setVelocity(player, new Vec3(dir.x * param("lunge", 1.3), 0.1, dir.z * param("lunge", 1.3)));
            });
        }
        cast.contact(element() == Element.ARC ? HunterSkillTiming.ARC_CONTACT_TICKS : HunterSkillTiming.THROW_CONTACT_TICKS,
                () -> {
                    switch (element()) {
                        case ARC -> combinationBlow(player, cast, weaponTraits);
                        case SOLAR -> knife(player, cast, weaponTraits);
                        default -> smoke(player, cast);
                    }
                });
        return true;
    }

    private void combinationBlow(ServerPlayer player, HunterSkillCast cast, kim.biryeong.destiny.weapon.MeleeWeaponTraits.Snapshot traits) {
        ServerLevel level = cast.level();
        DestinySounds.hunterOrVanilla(level, player.position(), element(), "melee.cast", SoundEvents.PLAYER_ATTACK_SWEEP, 1f, 1.8f);
        float damage = (float) param("damage", 12);
        double reach = param("reach", 2.8);
        Vec3 center = player.position().add(0, 1, 0).add(Motion.horizontalLook(player).scale(1.2));
        AbilityParticles.send(player, level, ParticleTypes.ELECTRIC_SPARK, center.x, center.y, center.z, 6, 0.4, 0.4, 0.4, 0.1);
        boolean contacted = false;
        for (LivingEntity e : kim.biryeong.destiny.combat.MeleeSweep.frontal(player,Math.clamp(reach,.1,8),.25,1.6)) {
            contacted = true;
            Fx.line(player, level, player.getEyePosition(), e.position().add(0, e.getBbHeight() / 2, 0), element().color(), 0.25, 1.0f);
            if (kim.biryeong.destiny.weapon.MeleeWeaponTraits.poweredDamage(level, player, e, AbilityDamage.pvp(this, "strike", e, damage), element(), traits)) {
                Statuses.apply(player, Keyword.AMPLIFIED, (int) param("amplified_ticks", 120));
                player.heal((float) param("heal_on_kill", 4));
            }
        }
        if (contacted) DestinySounds.hunter(level, center, element(), "melee.impact", .8f);
        boolean modeled = HunterVfx.play(player, level, center, HunterVfx.Kind.ARC_STRIKE, 1.1, 16);
        Fx.burst(player, level, center, element(), modeled ? 8 : 30, 0.6);
    }

    private void knife(ServerPlayer player, HunterSkillCast cast, kim.biryeong.destiny.weapon.MeleeWeaponTraits.Snapshot traits) {
        ServerLevel level = cast.level();
        float damage = (float) param("damage", 10);
        SimProjectile.launch(player, player.getEyePosition(), player.getLookAngle().scale(param("speed", 2.2)), 0.008, 30,
                HunterAbilityVisuals.melee(element()), 0.6f, element().color(), hit -> {
                    if (!cast.valid()) return;
                    boolean modeled = HunterVfx.play(player, level, hit.getLocation(), HunterVfx.Kind.SOLAR_KNIFE, 0.65, 22);
                    Fx.burst(player, level, hit.getLocation(), element(), modeled ? 6 : 20, 0.3);
                    DestinySounds.hunter(level, hit.getLocation(), element(), "melee.impact", .7f);
                    if (hit instanceof EntityHitResult eh && eh.getEntity() instanceof LivingEntity target) {
                        kim.biryeong.destiny.weapon.MeleeWeaponTraits.poweredDamage(level, player, target, AbilityDamage.pvp(this, "knife", target, damage), element(), traits);
                        Statuses.scorch(player, target, (int) param("scorch_ticks", 80));
                    }
                });
        DestinySounds.hunterOrVanilla(level, player.getEyePosition(), element(), "melee.cast", SoundEvents.TRIDENT_THROW.value(), 0.8f, 1.5f);
    }

    private void smoke(ServerPlayer player, HunterSkillCast cast) {
        ServerLevel level = cast.level();
        double radius = param("radius", 3.5);
        int duration = (int) param("duration_ticks", 100);
        DestinySounds.hunter(level, player.getEyePosition(), element(), "melee.cast", .7f);
        SimProjectile.launch(player, player.getEyePosition(), player.getLookAngle().scale(1.0).add(0, 0.1, 0), 0.05, 60,
                HunterAbilityVisuals.melee(element()), 0.5f, element().color(), hit -> {
                    if (!cast.valid()) return;
                    Vec3 pos = hit.getLocation();
                    boolean modeled = HunterVfx.play(player, level, pos, HunterVfx.Kind.VOID_SMOKE, radius, duration);
                    DestinySounds.hunterOrVanilla(level, pos, element(), "melee.impact", SoundEvents.FIRE_EXTINGUISH, 0.8f, 0.6f);
                    Tasks.run(player, level, age -> {
                        if (!cast.valid()) return false;
                        if (!modeled || age % 4 == 0) {
                            AbilityParticles.send(player, level, ParticleTypes.LARGE_SMOKE, pos.x, pos.y + 0.5, pos.z, modeled ? 2 : 6, radius / 2, 0.5, radius / 2, 0.01);
                            AbilityParticles.send(player, level, Fx.dust(element().color(), 2.0f), pos.x, pos.y + 0.5, pos.z, modeled ? 1 : 4, radius / 2, 0.5, radius / 2, 0.0);
                        }
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
    }
}
