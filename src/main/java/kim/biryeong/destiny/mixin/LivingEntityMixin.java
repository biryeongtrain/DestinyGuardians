package kim.biryeong.destiny.mixin;

import kim.biryeong.destiny.combat.Statuses;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.LivingEntity;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.ModifyVariable;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;
import com.llamalad7.mixinextras.injector.wrapmethod.WrapMethod;
import com.llamalad7.mixinextras.injector.ModifyExpressionValue;
import com.llamalad7.mixinextras.injector.wrapoperation.Operation;
import org.spongepowered.asm.mixin.Unique;
import kim.biryeong.destiny.weapon.WeaponDamageMeasurement;
import kim.biryeong.destiny.weapon.WeaponFrenzy;
import net.minecraft.server.level.ServerPlayer;

/** 약화(WEAKENED) 상태의 받는 피해 증가. */
@Mixin(LivingEntity.class)
public abstract class LivingEntityMixin {
    /** 26.3 floors fall power: native safe distance 3 + 6 means first damage at 10 blocks.
     * Add to the native attribute so jump-boost and other safe-distance bonuses survive.
     * Keep the normal damage multiplier, protections and world-rule checks downstream. */
    @ModifyExpressionValue(method = "calculateFallPower", at = @At(value = "INVOKE",
            target = "Lnet/minecraft/world/entity/LivingEntity;getAttributeValue(Lnet/minecraft/core/Holder;)D"))
    private double destiny$playerSafeFallDistance(double nativeDistance) {
        return (Object)this instanceof ServerPlayer ? nativeDistance + 6.0 : nativeDistance;
    }

    /** 26.3's five-argument/default damage paths delegate to this overload.
     * Cancel before needsSync/setDeltaMovement, not after a player velocity packet. */
    @Inject(method = "knockback(DDDLnet/minecraft/world/damagesource/DamageSource;FZ)V",
            at = @At("HEAD"), cancellable = true)
    private void destiny$customDamageWithoutKnockback(double strength, double x, double z,
            DamageSource source, float damage, boolean force, CallbackInfo ci) {
        if (kim.biryeong.destiny.combat.Combat.suppressesKnockback((LivingEntity)(Object)this, source)) ci.cancel();
    }
    @Unique private final WeaponDamageMeasurement destiny$frenzyLoss=new WeaponDamageMeasurement();
    /** Player has its own actuallyHurt override and exclusive loss measurement. */
    @WrapMethod(method="actuallyHurt")
    private void destiny$frenzyCombat(ServerLevel level, DamageSource source, float amount, Operation<Void> original) {
        var victim=(LivingEntity)(Object)this;
        if(victim instanceof ServerPlayer || !(source.getEntity() instanceof ServerPlayer owner)) {
            original.call(level,source,amount);return;
        }
        destiny$frenzyLoss.begin(victim.getHealth()+victim.getAbsorptionAmount());
        float loss;boolean complete=false;
        try {original.call(level,source,amount);complete=true;}
        finally {loss=destiny$frenzyLoss.finish(victim.getHealth()+victim.getAbsorptionAmount());}
        if(complete && loss>0) {
            WeaponFrenzy.dealt(owner,victim,source,loss);
            kim.biryeong.destiny.weapon.PerkExpansionStats.dealt(owner,victim,source,loss);
        }
    }
    @ModifyVariable(method = "hurtServer", at = @At("HEAD"), argsOnly = true)
    private float destiny$weaken(float amount, ServerLevel level, DamageSource source) {
        float modified=Statuses.modifyIncoming((LivingEntity) (Object) this, amount);
        if ((Object)this instanceof net.minecraft.server.level.ServerPlayer player) {
            modified = kim.biryeong.destiny.combat.SuperDamageResistance.modifyIncoming(player, source, modified);
            modified = kim.biryeong.destiny.combat.FrostArmor.modifyIncoming(player, modified); // W322 batch C
            return kim.biryeong.destiny.weapon.WeaponRuntime.guardDamage(player,source,modified);
        }
        return modified;
    }
}
