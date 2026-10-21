package kim.biryeong.destiny.ability.hunter;

import kim.biryeong.destiny.ability.Ability;
import kim.biryeong.destiny.ability.Motion;
import kim.biryeong.destiny.fx.Fx;
import kim.biryeong.destiny.guardian.AbilitySlot;
import kim.biryeong.destiny.guardian.Element;
import kim.biryeong.destiny.guardian.GuardianClass;
import kim.biryeong.destiny.guardian.GuardianRuntime;
import kim.biryeong.destiny.guardian.Guardians;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.phys.Vec3;

/** 헌터 공중 점프. 2단(1회) / 3단(2회, 조금 약함). */
public final class HunterJump extends Ability {
    private final int defaultExtraJumps;
    private final double defaultStrength;

    public HunterJump(Identifier id, String name, int extraJumps, double strength) {
        super(id, GuardianClass.HUNTER, AbilitySlot.JUMP, Element.KINETIC, 0, name);
        this.defaultExtraJumps = extraJumps;
        this.defaultStrength = strength;
    }

    public int extraJumps() {
        return (int) param("extra_jumps", defaultExtraJumps);
    }

    @Override
    public boolean activate(ServerPlayer player) {
        GuardianRuntime runtime = Guardians.runtime(player);
        if (runtime.airJumpsUsed >= extraJumps()) {
            return false;
        }
        runtime.airJumpsUsed++;
        Vec3 v = player.getDeltaMovement();
        double strength = param("strength", defaultStrength);
        double carry = param("horizontal_carry", 1.0);
        Motion.setVelocity(player, new Vec3(v.x * carry, strength, v.z * carry));
        player.resetFallDistance();
        Vec3 feet = player.position();
        player.level().sendParticles(Fx.dust(0xE6EAF0, 1.0f), feet.x, feet.y, feet.z, 10, 0.25, 0.05, 0.25, 0.0);
        Fx.sound(player.level(), feet, SoundEvents.WIND_CHARGE_BURST.value(), 0.4f, 1.6f);
        return true;
    }
}
