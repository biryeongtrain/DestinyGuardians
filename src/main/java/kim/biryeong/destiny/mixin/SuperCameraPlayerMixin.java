package kim.biryeong.destiny.mixin;

import kim.biryeong.destiny.camera.SuperCamera;
import net.minecraft.server.level.ServerPlayer;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

@Mixin(ServerPlayer.class)
public abstract class SuperCameraPlayerMixin {
    @Inject(method = "doTick", at = @At("HEAD"))
    private void destiny$serverCameraInput(CallbackInfo ci) {
        SuperCamera.beforePhysics((ServerPlayer) (Object) this);
    }

    @Inject(method = "doTick", at = @At("TAIL"))
    private void destiny$serverCameraFall(CallbackInfo ci) {
        SuperCamera.afterPhysics((ServerPlayer) (Object) this);
    }
}
