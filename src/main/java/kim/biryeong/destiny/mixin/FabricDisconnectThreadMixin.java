package kim.biryeong.destiny.mixin;

import net.fabricmc.fabric.impl.networking.AbstractNetworkAddon;
import net.fabricmc.fabric.impl.networking.server.ServerPlayNetworkAddon;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

/** Fabric 6.3.10 can reach the play disconnect event from Netty channelInactive.
 * Handoff must precede its native once-only CAS: otherwise an off-thread listener
 * failure consumes the event and the server-thread fallback cannot deliver it.
 */
@Mixin(value = AbstractNetworkAddon.class, remap = false)
public abstract class FabricDisconnectThreadMixin {
    @Inject(method = "handleDisconnect", at = @At("HEAD"), cancellable = true, remap = false)
    private void destiny$serverThreadDisconnect(CallbackInfo ci) {
        if ((Object) this instanceof ServerPlayNetworkAddon) {
            var server = ((ServerPlayNetworkAddonAccessor) this).destiny$server();
            if (!server.isSameThread()) {
                server.execute(((AbstractNetworkAddon<?>) (Object) this)::handleDisconnect);
                ci.cancel();
            }
        }
    }
}
