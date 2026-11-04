package kim.biryeong.destiny.mixin;

import kim.biryeong.destiny.inventory.WeaponScreen;
import net.minecraft.network.protocol.game.*;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.server.network.ServerGamePacketListenerImpl;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Shadow;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

/** All hooks follow vanilla thread validation; no Netty-thread inventory/HUD writes. */
@Mixin(value=ServerGamePacketListenerImpl.class, priority=1500)
public abstract class WeaponScreenInputMixin {
    @Shadow public ServerPlayer player;
    @Shadow public abstract void ackBlockChangesUpTo(int sequence);
    private static final String THREAD = "Lnet/minecraft/network/protocol/PacketUtils;ensureRunningOnSameThread(Lnet/minecraft/network/protocol/Packet;Lnet/minecraft/network/PacketListener;Lnet/minecraft/server/level/ServerLevel;)V";

    @Inject(method="handleMovePlayer", at=@At(value="INVOKE", target=THREAD, shift=At.Shift.AFTER), cancellable=true)
    private void destiny$equipmentMove(ServerboundMovePlayerPacket packet, CallbackInfo ci) {
        if (WeaponScreen.move(player, packet)) ci.cancel();
    }
    @Inject(method="handlePlayerInput", at=@At(value="INVOKE", target=THREAD, shift=At.Shift.AFTER), cancellable=true)
    private void destiny$equipmentInput(ServerboundPlayerInputPacket packet, CallbackInfo ci) {
        if (WeaponScreen.input(player, packet.input())) ci.cancel();
    }
    @Inject(method="handleUseItem", at=@At(value="INVOKE", target=THREAD, shift=At.Shift.AFTER), cancellable=true)
    private void destiny$equipmentUse(ServerboundUseItemPacket packet, CallbackInfo ci) {
        if (WeaponScreen.click(player, true)) { ackBlockChangesUpTo(packet.sequence()); ci.cancel(); }
    }
    @Inject(method="handleUseItemOn", at=@At(value="INVOKE", target=THREAD, shift=At.Shift.AFTER), cancellable=true)
    private void destiny$equipmentUseBlock(ServerboundUseItemOnPacket packet, CallbackInfo ci) {
        if (WeaponScreen.click(player, true)) { ackBlockChangesUpTo(packet.sequence()); ci.cancel(); }
    }
    @Inject(method={"handlePunch", "handleAttack"}, at=@At(value="INVOKE", target=THREAD, shift=At.Shift.AFTER), cancellable=true)
    private void destiny$equipmentAttack(CallbackInfo ci) {
        if (WeaponScreen.click(player, false)) ci.cancel();
    }
    @Inject(method="handleInteract", at=@At(value="INVOKE", target=THREAD, shift=At.Shift.AFTER), cancellable=true)
    private void destiny$equipmentInteract(CallbackInfo ci) { if (WeaponScreen.click(player, true)) ci.cancel(); }
    @Inject(method="handlePlayerAction", at=@At(value="INVOKE", target=THREAD, shift=At.Shift.AFTER), cancellable=true)
    private void destiny$equipmentAction(ServerboundPlayerActionPacket packet, CallbackInfo ci) {
        if (!WeaponScreen.active(player)) return;
        ackBlockChangesUpTo(packet.getSequence());
        switch (packet.getAction()) {
            case START_DESTROY_BLOCK -> WeaponScreen.click(player, false);
            case DROP_ITEM, DROP_ALL_ITEMS -> kim.biryeong.destiny.input.CancelledDropSync.restore(player, packet.getAction());
            case SWAP_ITEM_WITH_OFFHAND -> { } // routed by InputRouter.onPlayerAction (runs first)
            default -> { }
        }
        ci.cancel();
    }
    @Inject(method="handleSetCarriedItem", at=@At(value="INVOKE", target=THREAD, shift=At.Shift.AFTER), cancellable=true)
    private void destiny$equipmentSlot(ServerboundSetCarriedItemPacket packet, CallbackInfo ci) {
        if (WeaponScreen.active(player)) {
            player.connection.send(new ClientboundSetHeldSlotPacket(player.getInventory().getSelectedSlot())); ci.cancel();
        }
    }
    @Inject(method="handlePlayerCommand", at=@At(value="INVOKE", target=THREAD, shift=At.Shift.AFTER), cancellable=true)
    private void destiny$equipmentCommand(CallbackInfo ci) { if (WeaponScreen.active(player)) ci.cancel(); }
    @Inject(method="handleContainerClick", at=@At(value="INVOKE", target=THREAD, shift=At.Shift.AFTER), cancellable=true)
    private void destiny$equipmentContainer(CallbackInfo ci) {
        // Opening the native E screen is client-local. Cancel that screen's inventory edits and retire ours.
        if (WeaponScreen.active(player)) {
            WeaponScreen.close(player); player.containerMenu.broadcastFullState(); ci.cancel();
        }
    }
}
