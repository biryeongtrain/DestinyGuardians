package kim.biryeong.destiny.mixin;

import com.llamalad7.mixinextras.injector.wrapmethod.WrapMethod;
import com.llamalad7.mixinextras.injector.wrapoperation.Operation;
import kim.biryeong.destiny.weapon.WeaponAiming;
import kim.biryeong.destiny.weapon.WeaponDamageMeasurement;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.player.Player;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Unique;
import org.spongepowered.asm.mixin.injection.At;
import com.llamalad7.mixinextras.injector.ModifyExpressionValue;

/** Player overrides actuallyHurt. Measure after native armor/magic/absorption, including shield-only hits.
 * No callback for ALLOW_DAMAGE denial, iframe rejection or a fully blocked hit with no real loss. */
@Mixin(Player.class)
public abstract class PlayerDamageMixin {
    /** Native26.3 bytecode: armor -> magic -> this result -> absorption subtraction.
     * Resistance protects only this helper's ownedshield, not health or other providers. */
    @ModifyExpressionValue(method = "actuallyHurt", at = @At(value = "INVOKE",
            target = "Lnet/minecraft/world/entity/player/Player;getDamageAfterMagicAbsorb(Lnet/minecraft/world/damagesource/DamageSource;F)F"), require = 1, allow = 1)
    private float destiny$voidShield(float mitigated, ServerLevel level, DamageSource source, float originalAmount) {
        if (!((Object)this instanceof ServerPlayer p)) return mitigated;
        boolean combatant = source.getEntity() instanceof net.minecraft.world.entity.Mob mob
                && kim.biryeong.destiny.combat.Combat.isEnemy(p, mob);
        return kim.biryeong.destiny.combat.TemporaryVoidOvershield.incoming(p, mitigated, combatant);
    }
    @Unique private final WeaponDamageMeasurement destiny$loss = new WeaponDamageMeasurement();
    @WrapMethod(method = "actuallyHurt")
    private void destiny$actualDamage(ServerLevel level, DamageSource source, float amount, Operation<Void> original) {
        if (!((Object)this instanceof ServerPlayer p)) { original.call(level,source,amount); return; }
        float healthBefore = p.getHealth();
        destiny$loss.begin(p.getHealth()+p.getAbsorptionAmount());
        float loss;
        boolean complete=false;
        try { original.call(level,source,amount); complete=true; }
        finally {
            loss=destiny$loss.finish(p.getHealth()+p.getAbsorptionAmount());
        }
        if (complete && loss>0) {
            kim.biryeong.destiny.combat.GuardianRecovery.damaged(p, p.getHealth() < healthBefore);
            kim.biryeong.destiny.crucible.CrucibleHealth.damaged(p, p.getHealth() < healthBefore);
            kim.biryeong.destiny.weapon.WeaponUnrelenting.damaged(p,loss);
            kim.biryeong.destiny.weapon.WeaponPulseMonitor.damaged(p,loss);
            kim.biryeong.destiny.weapon.PerkBatchC.damaged(p,source,loss); // W322 batch C Energy Transfer
            kim.biryeong.destiny.weapon.WeaponFrenzy.received(p,source,loss);
            kim.biryeong.destiny.weapon.PerkExpansionStats.received(p,source,loss);
            if (source.getEntity() instanceof ServerPlayer owner)
                kim.biryeong.destiny.weapon.PerkExpansionStats.dealt(owner,p,source,loss);
            WeaponAiming.damaged(p,source,loss);
            kim.biryeong.destiny.hud.IncomingDamageHud.damaged(p,source,loss);
        }
    }
}
