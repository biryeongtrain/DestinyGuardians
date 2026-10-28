package kim.biryeong.destiny.inventory;

import eu.pb4.polymer.core.api.item.PolymerItemUtils;
import kim.biryeong.destiny.DestinyGuardians;
import net.fabricmc.fabric.api.networking.v1.context.PacketContextProvider;
import net.minecraft.core.component.DataComponents;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.Packet;
import net.minecraft.network.protocol.game.ClientboundContainerSetContentPacket;
import net.minecraft.network.protocol.game.ClientboundContainerSetSlotPacket;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.item.ItemStack;
import java.util.ArrayList;

/** Hide native hotbar decoration for this recipient while retaining native use input. */
public final class WeaponScreenPresentation {
    private WeaponScreenPresentation() {}
    public static Packet<?> project(ServerPlayer player, Packet<?> packet) {
        if (!WeaponScreen.active(player) || !player.level().getServer().isSameThread()) return packet;
        int menu = player.inventoryMenu.containerId;
        if (packet instanceof ClientboundContainerSetSlotPacket slot && slot.getContainerId() == menu) {
            var item = projectSlot(player, slot.getSlot(), slot.getItem());
            return item == slot.getItem() ? packet : new ClientboundContainerSetSlotPacket(
                    menu, slot.getStateId(), slot.getSlot(), item);
        }
        if (packet instanceof ClientboundContainerSetContentPacket content && content.containerId() == menu) {
            var items = new ArrayList<>(content.items());
            boolean changed = false;
            for (int index = 0; index < items.size(); index++) {
                var item = projectSlot(player, index, items.get(index));
                if (item != items.get(index)) { items.set(index, item); changed = true; }
            }
            if (changed) return new ClientboundContainerSetContentPacket(menu, content.stateId(), items, content.carriedItem());
        }
        return packet;
    }
    private static ItemStack projectSlot(ServerPlayer player, int index, ItemStack snapshot) {
        if (snapshot.isEmpty() || index < 0 || index >= player.inventoryMenu.slots.size()) return snapshot;
        var slot = player.inventoryMenu.slots.get(index);
        if (slot.container != player.getInventory() || slot.getContainerSlot() < 0 || slot.getContainerSlot() > 8) return snapshot;
        var context = ((PacketContextProvider) (Object) player.connection).getPacketContext();
        var result = PolymerItemUtils.getPolymerItemStack(snapshot, context, player.level().registryAccess()).copy();
        result.set(DataComponents.ITEM_MODEL, DestinyGuardians.id("weapon_sword_hand_empty"));
        result.set(DataComponents.ITEM_NAME, Component.empty());
        result.remove(DataComponents.CUSTOM_NAME);
        return result;
    }
}
