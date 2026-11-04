package kim.biryeong.destiny.mixin;

import kim.biryeong.destiny.weapon.WeaponOutboundPresentation;
import net.minecraft.network.protocol.Packet;
import net.minecraft.server.network.ServerCommonPacketListenerImpl;
import net.minecraft.server.network.ServerGamePacketListenerImpl;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.ModifyVariable;

/** Native recipient boundary, not an injection into Polymer's merged private methods. */
@Mixin(ServerCommonPacketListenerImpl.class)
public abstract class WeaponListenerPresentationMixin {
    @ModifyVariable(method = "send(Lnet/minecraft/network/protocol/Packet;Lio/netty/channel/ChannelFutureListener;)V",
            at = @At("HEAD"), argsOnly = true)
    private Packet<?> destiny$preserveLiveModel(Packet<?> packet) {
        return (Object) this instanceof ServerGamePacketListenerImpl listener
                && listener.player.connection == listener
                ? WeaponOutboundPresentation.projectPacket(listener.player, packet) : packet;
    }
}
