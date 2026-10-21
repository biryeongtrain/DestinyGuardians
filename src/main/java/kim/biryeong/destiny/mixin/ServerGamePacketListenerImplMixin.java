package kim.biryeong.destiny.mixin;

import kim.biryeong.destiny.input.InputRouter;
import net.minecraft.network.protocol.game.ServerboundPlayerActionPacket;
import net.minecraft.network.protocol.game.ServerboundPlayerInputPacket;
import net.minecraft.network.protocol.game.ServerboundPunchPacket;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.server.network.ServerGamePacketListenerImpl;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Shadow;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

/** 바닐라 입력 패킷을 InputRouter 로 넘긴다. 모두 서버 스레드에서 실행되는 지점에 건다. */
@Mixin(ServerGamePacketListenerImpl.class)
public abstract class ServerGamePacketListenerImplMixin {
    @Shadow
    public ServerPlayer player;

    @Inject(method = "handlePlayerInput", at = @At(value = "INVOKE",
            target = "Lnet/minecraft/server/level/ServerPlayer;setLastClientInput(Lnet/minecraft/world/entity/player/Input;)V"))
    private void destiny$input(ServerboundPlayerInputPacket packet, CallbackInfo ci) {
        InputRouter.onPlayerInput(player, player.getLastClientInput(), packet.input());
    }

    @Inject(method = "handlePlayerAction", at = @At(value = "INVOKE",
            target = "Lnet/minecraft/network/protocol/PacketUtils;ensureRunningOnSameThread(Lnet/minecraft/network/protocol/Packet;Lnet/minecraft/network/PacketListener;Lnet/minecraft/server/level/ServerLevel;)V",
            shift = At.Shift.AFTER), cancellable = true)
    private void destiny$action(ServerboundPlayerActionPacket packet, CallbackInfo ci) {
        if (InputRouter.onPlayerAction(player, packet.getAction())) {
            ci.cancel();
        }
    }

    @Inject(method = "handlePunch", at = @At(value = "INVOKE",
            target = "Lnet/minecraft/network/protocol/PacketUtils;ensureRunningOnSameThread(Lnet/minecraft/network/protocol/Packet;Lnet/minecraft/network/PacketListener;Lnet/minecraft/server/level/ServerLevel;)V",
            shift = At.Shift.AFTER))
    private void destiny$punch(ServerboundPunchPacket packet, CallbackInfo ci) {
        InputRouter.onPunch(player);
    }
}
