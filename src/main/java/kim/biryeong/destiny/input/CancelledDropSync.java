package kim.biryeong.destiny.input;

import net.minecraft.network.protocol.game.ClientboundContainerSetSlotPacket;
import net.minecraft.network.protocol.game.ServerboundPlayerActionPacket;
import net.minecraft.server.level.ServerPlayer;

/** Restores the slot that vanilla's dropItem has already removed on the client.
 * Call only after cancelling an action, on the server thread. A rejected reload
 * leaves the server stack unchanged, so ordinary remote-slot diffing cannot repair it.
 */
public final class CancelledDropSync {
    private CancelledDropSync() { }

    public static void restore(ServerPlayer player, ServerboundPlayerActionPacket.Action action) {
        if (action != ServerboundPlayerActionPacket.Action.DROP_ITEM
                && action != ServerboundPlayerActionPacket.Action.DROP_ALL_ITEMS) return;
        var menu = player.inventoryMenu;
        var slot = menu.findSlot(player.getInventory(), player.getInventory().getSelectedSlot());
        if (slot.isEmpty()) return;
        // Use the recipient listener so the existing Polymer/profile presentation
        // applies to a copy of the live source. Never replace the authoritative stack,
        // suppress remote updates, or touch another slot/full inventory to fix one drop.
        player.connection.send(new ClientboundContainerSetSlotPacket(menu.containerId,
                menu.incrementStateId(), slot.getAsInt(), menu.getSlot(slot.getAsInt()).getItem().copy()));
    }
}
