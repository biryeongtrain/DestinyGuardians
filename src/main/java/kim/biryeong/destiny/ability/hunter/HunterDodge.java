package kim.biryeong.destiny.ability.hunter;

import kim.biryeong.destiny.ability.Ability;
import kim.biryeong.destiny.ability.AbilityService;
import kim.biryeong.destiny.ability.Motion;
import kim.biryeong.destiny.combat.Combat;
import kim.biryeong.destiny.fx.Fx;
import kim.biryeong.destiny.fx.PlayerAnimations;
import kim.biryeong.destiny.guardian.AbilitySlot;
import kim.biryeong.destiny.guardian.Element;
import kim.biryeong.destiny.guardian.GuardianClass;
import kim.biryeong.destiny.guardian.GuardianRuntime;
import kim.biryeong.destiny.guardian.Guardians;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.phys.Vec3;

/**
 * 헌터 회피 (직업 능력). 입력 방향으로 구르며 잠깐 무적.
 * 도박꾼: 근처에 적이 있으면 근접 능력 재충전. 명사수: 쿨타임이 짧다.
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
        GuardianRuntime runtime = Guardians.runtime(player);
        Vec3 dir = Motion.inputDirection(player, runtime.lastInput);
        double speed = param("speed", 1.15);
        Motion.setVelocity(player, new Vec3(dir.x * speed, param("lift", 0.18), dir.z * speed));
        runtime.invulnerableTicks = (int) param("invulnerable_ticks", 6);
        player.resetFallDistance();
        PlayerAnimations.play(player, "roll");
        Vec3 feet = player.position();
        player.level().sendParticles(Fx.dust(0xC9B79C, 1.4f), feet.x, feet.y + 0.1, feet.z, 16, 0.4, 0.05, 0.4, 0.0);
        Fx.sound(player.level(), feet, SoundEvents.PLAYER_ATTACK_SWEEP, 0.6f, 1.4f);
        if (variant == Variant.GAMBLER && !Combat.enemiesNear(player, player.position(), param("enemy_radius", 8)).isEmpty()) {
            AbilityService.resetCooldown(player, AbilitySlot.MELEE);
        }
        return true;
    }
}
