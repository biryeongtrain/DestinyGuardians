package kim.biryeong.destiny.mixin;

import kim.biryeong.destiny.camera.SuperCamera;
import net.minecraft.server.level.ServerPlayer;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

@Mixin(ServerPlayer.class)
public abstract class SuperCameraPlayerMixin {
    @Inject(method = "setCamera", at = @At("HEAD"), cancellable = true)
    private void destiny$holdDeathCamera(net.minecraft.world.entity.Entity camera, CallbackInfo ci) {
        if (kim.biryeong.destiny.crucible.CrucibleDeathScene.blocksCameraChange((ServerPlayer)(Object)this, camera)
                || kim.biryeong.destiny.down.GuardianDown.blocksCameraChange((ServerPlayer)(Object)this, camera)) ci.cancel();
    }

    @Inject(method = "doTick", at = @At("HEAD"))
    private void destiny$serverCameraInput(CallbackInfo ci) {
        SuperCamera.beforePhysics((ServerPlayer) (Object) this);
        kim.biryeong.destiny.combat.MeleeLunge.beforePhysics((ServerPlayer)(Object)this);
    }

    @Inject(method = "doTick", at = @At("TAIL"))
    private void destiny$serverCameraFall(CallbackInfo ci) {
        SuperCamera.afterPhysics((ServerPlayer) (Object) this);
        kim.biryeong.destiny.combat.MeleeLunge.afterPhysics((ServerPlayer)(Object)this);
    }
}
