package kim.biryeong.destiny.ability.hunter;

import kim.biryeong.destiny.ability.Ability;
import kim.biryeong.destiny.ability.AbilityService;
import kim.biryeong.destiny.ability.Motion;
import kim.biryeong.destiny.combat.Combat;
import kim.biryeong.destiny.camera.SuperCamera;
import kim.biryeong.destiny.fx.Fx;
import kim.biryeong.destiny.fx.AbilityParticles;
import kim.biryeong.destiny.sound.DestinySounds;
import kim.biryeong.destiny.fx.PlayerAnimations;
import kim.biryeong.destiny.guardian.AbilitySlot;
import kim.biryeong.destiny.guardian.Element;
import kim.biryeong.destiny.guardian.GuardianClass;
import kim.biryeong.destiny.guardian.GuardianRuntime;
import kim.biryeong.destiny.guardian.Guardians;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.phys.Vec3;

/**
 * 헌터 회피 (직업 능력). 입력 방향으로 구르며 잠깐 무적.
 * 도박꾼: 근처에 적이 있으면 근접 능력 재충전. 명사수: 발동 시 장착 무기 재장전·주변 개인 탄약 수집.
 */
public final class HunterDodge extends Ability {
    public enum Variant { GAMBLER, MARKSMAN }

    private final Variant variant;

    public HunterDodge(Identifier id, String name, Variant variant, double cooldownSeconds) {
        super(id, GuardianClass.HUNTER, AbilitySlot.CLASS_ABILITY, Element.KINETIC, cooldownSeconds, name);
        this.variant = variant;
    }

    @Override
    public boolean activate(ServerPlayer player) {
        // A class cast may replace our sword view, never another camera owner.
        if (SuperCamera.active(player) && !SuperCamera.swordActive(player)
                || player.getCamera() != player
                || kim.biryeong.minigamelib.cinematic.CameraViews.get(player) != null) return false;
        SuperCamera.stopSword(player);
        GuardianRuntime runtime = Guardians.runtime(player);
        HunterSkillCast cast = HunterSkillCast.begin(player, slot(), PlayerAnimations.dodgeAnimation(runtime.lastInput, variant == Variant.MARKSMAN), ItemStack.EMPTY);
        if (cast == null) return false;
        // Never accept a first-person dodge when the authored limb/camera cannot start.
        if (!cast.modeled() || !SuperCamera.startDodge(player)) {
            HunterSkillCast.cancelPending(player);
            if (cast.modeled()) PlayerAnimations.stop(player);
            return false;
        }
        DestinySounds.orVanilla(cast.level(), player.position(),
                variant == Variant.GAMBLER ? "class.hunter.dodge.gambler" : "class.hunter.dodge.marksman",
                SoundEvents.PLAYER_ATTACK_SWEEP, 0.6f, 1.4f);
        if (variant == Variant.MARKSMAN) kim.biryeong.destiny.weapon.WeaponRuntime.reloadFromMarksmanDodge(player);
        Vec3 dir = Motion.inputDirection(player, runtime.lastInput);
        double speed = param("speed", 1.15);
        Motion.setVelocity(player, new Vec3(dir.x * speed, param("lift", 0.18), dir.z * speed));
        runtime.invulnerableTicks = (int) param("invulnerable_ticks", 6);
        player.resetFallDistance();
        cast.contact(HunterSkillTiming.DODGE_CONTACT_TICKS, () -> {
            Vec3 feet = player.position();
            AbilityParticles.send(player, cast.level(), Fx.dust(0xC9B79C, 1.4f), feet.x, feet.y + 0.1, feet.z, 16, 0.4, 0.05, 0.4, 0.0);
        });
        if (variant == Variant.GAMBLER && !Combat.enemiesNear(player, player.position(), param("enemy_radius", 8)).isEmpty()) {
            AbilityService.resetCooldown(player, AbilitySlot.MELEE);
        }
        return true;
    }
}
