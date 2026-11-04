package kim.biryeong.destiny.mixin;

import kim.biryeong.destiny.weapon.WeaponRuntime;
import net.minecraft.network.protocol.game.ServerboundPlayerActionPacket;
import net.minecraft.network.protocol.game.ServerboundUseItemPacket;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.server.network.ServerGamePacketListenerImpl;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Shadow;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

/** Observe actual server-main-thread receipt. No cancellation or argument replacement. */
@Mixin(ServerGamePacketListenerImpl.class)
public abstract class WeaponUseTraceMixin {
    @Shadow public ServerPlayer player;

    @Inject(method = "handleUseItem", at = @At(value = "INVOKE", target =
            "Lnet/minecraft/network/protocol/PacketUtils;ensureRunningOnSameThread(Lnet/minecraft/network/protocol/Packet;Lnet/minecraft/network/PacketListener;Lnet/minecraft/server/level/ServerLevel;)V", shift = At.Shift.AFTER))
    private void destiny$useReceived(ServerboundUseItemPacket packet, CallbackInfo ci) {
        WeaponRuntime.traceUse(player, "packet.use." + packet.hand().name(), packet.sequence());
    }

    @Inject(method = "handlePlayerAction", at = @At(value = "INVOKE", target =
            "Lnet/minecraft/network/protocol/PacketUtils;ensureRunningOnSameThread(Lnet/minecraft/network/protocol/Packet;Lnet/minecraft/network/PacketListener;Lnet/minecraft/server/level/ServerLevel;)V", shift = At.Shift.AFTER))
    private void destiny$actionReceived(ServerboundPlayerActionPacket packet, CallbackInfo ci) {
        WeaponRuntime.traceUse(player, "packet.action." + packet.getAction().name(), packet.getSequence());
    }
}
