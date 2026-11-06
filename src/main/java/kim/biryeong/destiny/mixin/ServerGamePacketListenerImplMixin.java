package kim.biryeong.destiny.mixin;

import kim.biryeong.destiny.input.InputRouter;
import net.minecraft.network.protocol.game.ServerboundPlayerActionPacket;
import net.minecraft.network.protocol.game.ServerboundPlayerInputPacket;
import net.minecraft.network.protocol.game.ServerboundPunchPacket;
import net.minecraft.network.protocol.game.ServerboundMovePlayerPacket;
import net.minecraft.network.protocol.game.ServerboundSetCarriedItemPacket;
import kim.biryeong.destiny.camera.SuperCamera;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.server.network.ServerGamePacketListenerImpl;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Shadow;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

/** 바닐라 입력 패킷을 InputRouter 로 넘긴다. 모두 서버 스레드에서 실행되는 지점에 건다. */
@Mixin(ServerGamePacketListenerImpl.class)
public abstract class ServerGamePacketListenerImplMixin {
    @Shadow
    public ServerPlayer player;

    @Shadow
    private boolean clientIsFloating;

    @Shadow
    public abstract void resetPosition();

    /** Vanilla rewinds doTick movement to firstGoodXYZ immediately after this call.
     * During camera ownership, keep the one collision-resolved native step as that baseline.
     * resetPosition only updates connection bookkeeping; it neither moves nor sends a teleport.
     */
    @Inject(method = "tickPlayer", at = @At(value = "INVOKE",
            target = "Lnet/minecraft/server/level/ServerPlayer;doTick()V", shift = At.Shift.AFTER))
    private void destiny$retainCameraPhysics(CallbackInfoReturnable<Boolean> cir) {
        if (kim.biryeong.destiny.down.GuardianDown.holdReviveMovement(player) || SuperCamera.active(player)) {
            resetPosition();
            // Camera ownership cancels handleMovePlayer, so an earlier floating flag
            // is otherwise never recomputed, even after native physics lands the player.
            clientIsFloating = false;
            player.connection.resetFlyingTicks();
            if (player.level().getEntity(player.getId()) == player) {
                player.level().getChunkSource().move(player);
            }
        }
    }

    @Inject(method = "handleMovePlayer", at = @At(value = "INVOKE",
            target = "Lnet/minecraft/network/protocol/PacketUtils;ensureRunningOnSameThread(Lnet/minecraft/network/protocol/Packet;Lnet/minecraft/network/PacketListener;Lnet/minecraft/server/level/ServerLevel;)V",
            shift = At.Shift.AFTER), cancellable = true)
    private void destiny$cameraRotation(ServerboundMovePlayerPacket packet, CallbackInfo ci) {
        if (kim.biryeong.destiny.down.GuardianDown.holdReviveMovement(player)) {
            resetPosition(); clientIsFloating = false; player.connection.resetFlyingTicks();
            ci.cancel(); return;
        }
        if (SuperCamera.move(player, packet)) ci.cancel();
    }

    @Inject(method = "handlePlayerInput", at = @At(value = "INVOKE",
            target = "Lnet/minecraft/server/level/ServerPlayer;setLastClientInput(Lnet/minecraft/world/entity/player/Input;)V"))
    private void destiny$input(ServerboundPlayerInputPacket packet, CallbackInfo ci) {
        InputRouter.onPlayerInput(player, player.getLastClientInput(), packet.input());
    }

    @Inject(method = "handleSetCarriedItem", at = @At(value = "INVOKE",
            target = "Lnet/minecraft/network/protocol/PacketUtils;ensureRunningOnSameThread(Lnet/minecraft/network/protocol/Packet;Lnet/minecraft/network/PacketListener;Lnet/minecraft/server/level/ServerLevel;)V",
            shift = At.Shift.AFTER), cancellable = true)
    private void destiny$combatSlotGuard(ServerboundSetCarriedItemPacket packet, CallbackInfo ci) {
        if (kim.biryeong.destiny.inventory.WeaponHotbarGuard.rejectSlot(player, packet.getSlot())) ci.cancel();
    }

    @Inject(method = "handleSetCarriedItem", at = @At(value = "INVOKE",
            target = "Lnet/minecraft/world/entity/player/Inventory;setSelectedSlot(I)V"))
    private void destiny$swordSlotChange(ServerboundSetCarriedItemPacket packet, CallbackInfo ci) {
        kim.biryeong.destiny.weapon.WeaponRuntime.selectedSlotChanging(player,packet.getSlot());
    }

    @Inject(method = "handlePlayerAction", at = @At(value = "INVOKE",
            target = "Lnet/minecraft/network/protocol/PacketUtils;ensureRunningOnSameThread(Lnet/minecraft/network/protocol/Packet;Lnet/minecraft/network/PacketListener;Lnet/minecraft/server/level/ServerLevel;)V",
            shift = At.Shift.AFTER), cancellable = true)
    private void destiny$action(ServerboundPlayerActionPacket packet, CallbackInfo ci) {
        if (InputRouter.onPlayerAction(player, packet.getAction())) {
            kim.biryeong.destiny.input.CancelledDropSync.restore(player, packet.getAction());
            ci.cancel();
        }
    }

    /** A packet-only rear camera can ray-pick its own body. Consume only that owned-camera
     * self hit; vanilla still validates every other target (and ordinary self-attack packets). */
    @Inject(method = "handleAttack", at = @At(value = "INVOKE",
            target = "Lnet/minecraft/network/protocol/PacketUtils;ensureRunningOnSameThread(Lnet/minecraft/network/protocol/Packet;Lnet/minecraft/network/PacketListener;Lnet/minecraft/server/level/ServerLevel;)V",
            shift = At.Shift.AFTER), cancellable = true)
    private void destiny$cameraSelfAttack(net.minecraft.network.protocol.game.ServerboundAttackPacket packet, CallbackInfo ci) {
        if (packet.entityId() != player.getId()) return;
        var runtime = kim.biryeong.destiny.guardian.Guardians.runtime(player);
        if (!SuperCamera.active(player) && !(runtime.gcbClient && runtime.gcbThirdPerson)) return;
        if (player.connection.hasClientLoaded() && player.isAlive() && !player.isSpectator()) {
            player.resetLastActionTime();
            InputRouter.onPunch(player);
        }
        ci.cancel();
    }

    /** JOIN can send displays before the client replaces its world. Resend full spawn + metadata
     * after the client's load acknowledgement, including unchanged cached HUD elements. */
    @Inject(method = "handleAcceptPlayerLoad", at = @At("TAIL"))
    private void destiny$loadedHud(net.minecraft.network.protocol.game.ServerboundPlayerLoadedPacket packet, CallbackInfo ci) {
        ServerPlayer loaded = player;
        kim.biryeong.minigamelib.displayhud.DisplayHudManager.runLater(1, () -> {
            if (!loaded.hasDisconnected() && loaded.connection.hasClientLoaded()
                    && loaded.level().getServer().getPlayerList().getPlayer(loaded.getUUID()) == loaded)
                kim.biryeong.minigamelib.displayhud.DisplayHudManager.resend(loaded);
        });
    }

    @Inject(method = "handlePunch", at = @At(value = "INVOKE",
            target = "Lnet/minecraft/network/protocol/PacketUtils;ensureRunningOnSameThread(Lnet/minecraft/network/protocol/Packet;Lnet/minecraft/network/PacketListener;Lnet/minecraft/server/level/ServerLevel;)V",
            shift = At.Shift.AFTER))
    private void destiny$punch(ServerboundPunchPacket packet, CallbackInfo ci) {
        InputRouter.onPunch(player);
    }
}
