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

/** Player overrides actuallyHurt. Measure after native armor/magic/absorption, including shield-only hits.
 * No callback for ALLOW_DAMAGE denial, iframe rejection or a fully blocked hit with no real loss. */
@Mixin(Player.class)
public abstract class PlayerDamageMixin {
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
            kim.biryeong.destiny.crucible.CrucibleHealth.damaged(p, p.getHealth() < healthBefore);
            kim.biryeong.destiny.weapon.WeaponUnrelenting.damaged(p,loss);
            kim.biryeong.destiny.weapon.WeaponPulseMonitor.damaged(p,loss);
            kim.biryeong.destiny.weapon.WeaponFrenzy.received(p,source,loss);
            WeaponAiming.damaged(p,source,loss);
            kim.biryeong.destiny.hud.IncomingDamageHud.damaged(p,source,loss);
        }
    }
}
