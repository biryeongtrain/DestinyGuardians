package kim.biryeong.destiny.mixin;

import net.minecraft.server.level.ServerPlayer;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

@Mixin(ServerPlayer.class)
public abstract class GuardianNaturalHealingMixin {
    /** Peaceful has a separate vanilla healing path outside FoodData. Ability heals remain intact. */
    @Inject(method = "tickRegeneration", at = @At("HEAD"), cancellable = true)
    private void destiny$replacePeacefulHealing(CallbackInfo ci) { ci.cancel(); }
}
