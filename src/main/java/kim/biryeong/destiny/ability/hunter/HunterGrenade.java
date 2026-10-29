package kim.biryeong.destiny.ability.hunter;

import kim.biryeong.destiny.ability.Ability;
import kim.biryeong.destiny.ability.Tasks;
import kim.biryeong.destiny.combat.Combat;
import kim.biryeong.destiny.combat.Keyword;
import kim.biryeong.destiny.combat.Statuses;
import kim.biryeong.destiny.fx.Fx;
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
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;

/** 헌터 수류탄 3종: Arc 섬광(실명), Solar 소이(연소), Void 소용돌이(끌어당김 지속 피해). */
public final class HunterGrenade extends Ability {
    public HunterGrenade(Identifier id, String name, Element element, double cooldownSeconds) {
        super(id, GuardianClass.HUNTER, AbilitySlot.GRENADE, element, cooldownSeconds, name);
    }

    @Override
    public boolean activate(ServerPlayer player) {
        HunterSkillCast cast = HunterSkillCast.snapshot(player, slot());
        if (cast == null) return false;
        var adrenalineJunkie=kim.biryeong.destiny.weapon.WeaponAdrenalineJunkie.grenadeAccepted(player);
        var demolitionist=kim.biryeong.destiny.weapon.WeaponDemolitionist.grenadeAccepted(player);
        return kim.biryeong.destiny.ability.GrenadeThrow.begin(player, id(),
                kim.biryeong.destiny.fx.GrenadeModels.item(GuardianClass.HUNTER, element()), cast::valid, () -> {
                    release(player, cast, adrenalineJunkie);
                    kim.biryeong.destiny.weapon.WeaponDemolitionist.grenadeReleased(player, demolitionist);
                });
    }

    private void release(ServerPlayer player, HunterSkillCast cast, kim.biryeong.destiny.weapon.WeaponAdrenalineJunkie.GrenadeToken adrenalineJunkie) {
        ServerLevel level = cast.level();
        // Aim/origin are sampled at release, so aiming during anticipation remains responsive.
        Vec3 eye = kim.biryeong.destiny.ability.GrenadeThrow.origin(player);
        Vec3 velocity = player.getLookAngle().scale(param("throw_speed", 1.1)).add(0, 0.12, 0);
        ItemStack visual = kim.biryeong.destiny.fx.GrenadeModels.projectile(id());
        SimProjectile.launch(player, eye, velocity, 0.045, 80, visual, 0.5f, element().color(), hit -> {
            if (cast.valid()) detonate(player, cast, hit, adrenalineJunkie);
        });
        DestinySounds.hunterOrVanilla(level, eye, element(), "grenade.throw", SoundEvents.SNOWBALL_THROW, 0.8f, 0.7f);
    }

    private void detonate(ServerPlayer player, HunterSkillCast cast, HitResult hit, kim.biryeong.destiny.weapon.WeaponAdrenalineJunkie.GrenadeToken adrenalineJunkie) {
        ServerLevel level = cast.level();
        Vec3 pos = hit.getLocation().add(0, 0.2, 0);
        double radius = param("radius", 4.5);
        switch (element()) {
            case ARC -> {
                boolean modeled = HunterVfx.play(player, level, pos, HunterVfx.Kind.ARC_FLASH, radius, 16);
                Fx.burst(level, pos, element(), modeled ? 18 : 60, radius / 3);
                if (!modeled) Fx.ring(level, pos, radius, element().glow(), 40);
                DestinySounds.hunterOrVanilla(level, pos, element(), "grenade.impact", SoundEvents.LIGHTNING_BOLT_IMPACT, 0.8f, 1.6f);
                for (LivingEntity e : Combat.enemiesNear(level, player, pos, radius)) {
                    kim.biryeong.destiny.weapon.WeaponAdrenalineJunkie.grenadeDamage(player, adrenalineJunkie, level, e, (float) param("damage", 5), element());
                    Statuses.apply(e, Keyword.BLINDED, (int) param("blind_ticks", 80));
                }
            }
            case SOLAR -> {
                boolean modeled = HunterVfx.play(player, level, pos, HunterVfx.Kind.SOLAR_BURST, radius, 22);
                Fx.burst(level, pos, element(), modeled ? 18 : 70, radius / 3);
                level.sendParticles(ParticleTypes.LAVA, pos.x, pos.y, pos.z, modeled ? 4 : 12, radius / 3, 0.2, radius / 3, 0.0);
                DestinySounds.hunterOrVanilla(level, pos, element(), "grenade.impact", SoundEvents.GENERIC_EXPLODE.value(), 0.8f, 1.3f);
                for (LivingEntity e : Combat.enemiesNear(level, player, pos, radius)) {
                    kim.biryeong.destiny.weapon.WeaponAdrenalineJunkie.grenadeDamage(player, adrenalineJunkie, level, e, (float) param("damage", 7), element());
                    if (e.isAlive()) Statuses.scorch(player, e, (int) param("scorch_ticks", 100), adrenalineJunkie);
                }
            }
            default -> {
                int duration = (int) param("duration_ticks", 60);
                float pulse = (float) param("damage", 3);
                boolean modeled = HunterVfx.play(player, level, pos, HunterVfx.Kind.VOID_VORTEX, radius, duration);
                DestinySounds.hunterOrVanilla(level, pos, element(), "grenade.impact", SoundEvents.PORTAL_TRIGGER, 0.6f, 1.8f);
                Tasks.run(player, level, age -> {
                    if (!cast.valid()) return false;
                    if (!modeled && age % 2 == 0) {
                        Fx.ring(level, pos, radius * (1 - (age % 20) / 20.0), element().color(), 24);
                        level.sendParticles(ParticleTypes.PORTAL, pos.x, pos.y, pos.z, 12, radius / 3, 0.4, radius / 3, 0.5);
                    }
                    for (LivingEntity e : Combat.enemiesNear(level, player, pos, radius)) {
                        Vec3 pull = pos.subtract(e.position()).scale(0.08);
                        e.setDeltaMovement(e.getDeltaMovement().add(pull.x, 0, pull.z));
                        e.needsSync = true;
                        if (age % 10 == 0) {
                            kim.biryeong.destiny.weapon.WeaponAdrenalineJunkie.grenadeDamage(player, adrenalineJunkie, level, e, pulse, element());
                        }
                    }
                    return age < duration;
                });
            }
        }
    }
}
