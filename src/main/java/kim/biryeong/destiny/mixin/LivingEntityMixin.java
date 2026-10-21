package kim.biryeong.destiny.mixin;

import kim.biryeong.destiny.combat.Statuses;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.LivingEntity;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.ModifyVariable;

/** 약화(WEAKENED) 상태의 받는 피해 증가. */
@Mixin(LivingEntity.class)
public abstract class LivingEntityMixin {
    @ModifyVariable(method = "hurtServer", at = @At("HEAD"), argsOnly = true)
    private float destiny$weaken(float amount, ServerLevel level, DamageSource source) {
        return Statuses.modifyIncoming((LivingEntity) (Object) this, amount);
    }
}
