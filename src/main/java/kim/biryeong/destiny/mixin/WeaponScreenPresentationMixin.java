package kim.biryeong.destiny.mixin;

import kim.biryeong.destiny.inventory.WeaponScreenPresentation;
import net.minecraft.network.protocol.Packet;
import net.minecraft.server.network.ServerCommonPacketListenerImpl;
import net.minecraft.server.network.ServerGamePacketListenerImpl;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.ModifyVariable;

/** Runs after the weapon's live model projection; server inventory is never replaced. */
@Mixin(value = ServerCommonPacketListenerImpl.class, priority = 500)
public abstract class WeaponScreenPresentationMixin {
    @ModifyVariable(method = "send(Lnet/minecraft/network/protocol/Packet;Lio/netty/channel/ChannelFutureListener;)V",
            at = @At("HEAD"), argsOnly = true)
    private Packet<?> destiny$equipmentPresentation(Packet<?> packet) {
        return (Object) this instanceof ServerGamePacketListenerImpl listener && listener.player.connection == listener
                ? WeaponScreenPresentation.project(listener.player, packet) : packet;
    }
}
