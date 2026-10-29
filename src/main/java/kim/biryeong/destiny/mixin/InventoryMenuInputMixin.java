package kim.biryeong.destiny.mixin;

import kim.biryeong.destiny.inventory.InventoryMenuRedirect;
import net.minecraft.network.protocol.game.ServerboundContainerClosePacket;
import net.minecraft.network.protocol.game.ServerboundRecipeBookSeenRecipePacket;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.server.network.ServerGamePacketListenerImpl;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Shadow;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

@Mixin(ServerGamePacketListenerImpl.class)
public abstract class InventoryMenuInputMixin {
    @Shadow public ServerPlayer player;
    private static final String THREAD = "Lnet/minecraft/network/protocol/PacketUtils;ensureRunningOnSameThread(Lnet/minecraft/network/protocol/Packet;Lnet/minecraft/network/PacketListener;Lnet/minecraft/server/level/ServerLevel;)V";
    @Inject(method="handleRecipeBookSeenRecipePacket", at=@At(value="INVOKE", target=THREAD, shift=At.Shift.AFTER), cancellable=true)
    private void destiny$inventorySeen(ServerboundRecipeBookSeenRecipePacket packet, CallbackInfo ci) {
        if (InventoryMenuRedirect.seen(player, packet.recipe())) ci.cancel();
    }
    @Inject(method="handleContainerClose", at=@At("TAIL"))
    private void destiny$inventoryClosed(ServerboundContainerClosePacket packet, CallbackInfo ci) {
        InventoryMenuRedirect.closed(player);
    }
}
