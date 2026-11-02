package kim.biryeong.destiny.mixin;

import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.food.FoodData;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Shadow;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

/** Hunger is not a Guardian resource. Also replaces food/saturation healing and starvation. */
@Mixin(FoodData.class)
public abstract class GuardianFoodMixin {
    @Shadow private int foodLevel;
    @Shadow private float saturationLevel;
    @Shadow private float exhaustionLevel;
    @Shadow private int tickTimer;

    @Inject(method = "tick", at = @At("HEAD"), cancellable = true)
    private void destiny$fixedFood(ServerPlayer player, CallbackInfo ci) {
        foodLevel = 20;
        saturationLevel = 5;
        exhaustionLevel = 0;
        tickTimer = 0;
        ci.cancel();
    }
}
