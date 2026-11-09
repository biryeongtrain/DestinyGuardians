package kim.biryeong.destiny.mixin;

import kim.biryeong.destiny.compat.pack.ActivityPacks;
import io.netty.channel.ChannelFutureListener;
import net.minecraft.network.protocol.Packet;
import net.minecraft.network.protocol.common.ClientboundResourcePackPopPacket;
import net.minecraft.network.protocol.common.ServerboundResourcePackPacket;
import net.minecraft.server.network.ServerCommonPacketListenerImpl;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.*;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

@Mixin(ServerCommonPacketListenerImpl.class)
public abstract class ActivityPackResponseMixin {
    @Inject(method = "handleResourcePackResponse", at = @At("HEAD"))
    private void destiny$activityPackResponse(ServerboundResourcePackPacket packet, CallbackInfo ci) {
        ActivityPacks.response((ServerCommonPacketListenerImpl)(Object)this, packet);
    }
    @Inject(method = "send(Lnet/minecraft/network/protocol/Packet;Lio/netty/channel/ChannelFutureListener;)V", at = @At("HEAD"))
    private void destiny$activityPackRemoved(Packet<?> packet, ChannelFutureListener listener, CallbackInfo ci) {
        if (packet instanceof ClientboundResourcePackPopPacket pop)
            ActivityPacks.removed((ServerCommonPacketListenerImpl)(Object)this, pop.id());
    }
}
