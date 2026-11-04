package kim.biryeong.destiny.mixin;

import kim.biryeong.destiny.weapon.WeaponCrouchPresentation;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.player.Player;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

/** Publish cosmetic item pose after vanilla resolves actual clearance, before its next
 * equipment snapshot. Key intent/ADS easing must not stand in for the resolved pose.
 * Neither pose nor client input is changed; END_SERVER_TICK retains lifecycle cleanup.
 */
@Mixin(Player.class)
public abstract class WeaponPlayerPoseMixin {
    @Inject(method = "updatePlayerPose", at = @At("RETURN"))
    private void destiny$resolvedWeaponPose(CallbackInfo ci) {
        if ((Object) this instanceof ServerPlayer player
                && WeaponCrouchPresentation.supports(player.getMainHandItem()))
            WeaponCrouchPresentation.update(player);
    }
}
