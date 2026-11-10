package kim.biryeong.destiny.weapon;

import eu.pb4.polymer.core.api.item.PolymerItem;
import eu.pb4.polymer.core.api.item.PolymerItemUtils;
import net.fabricmc.fabric.api.networking.v1.context.PacketContext;
import net.minecraft.core.component.DataComponents;
import net.minecraft.network.RegistryFriendlyByteBuf;
import net.minecraft.server.network.ServerGamePacketListenerImpl;
import net.minecraft.world.item.ItemStack;

/** Equipment-only wire representation. Other players cannot return worn equipment as inventory input. */
public final class WeaponObserverEquipment {
    private WeaponObserverEquipment() { }

    /** Called only by the equipment packet's item encoder, inside Fabric's recipient context.
     * Never consult a live inventory or mutate the shared packet snapshot on the networking thread.
     */
    public static ItemStack project(int entityId, ItemStack snapshot, RegistryFriendlyByteBuf buffer) {
        var context = PacketContext.get();
        if (context == null) return snapshot;
        var connection = context.get(PacketContext.CONNECTION);
        if (connection == null || !(connection.getPacketListener() instanceof ServerGamePacketListenerImpl listener)
                || entityId == listener.getPlayer().getId() || WeaponItems.entry(snapshot).isEmpty()) return snapshot;

        // Resolve the complete ordinary representation BEFORE removing Polymer's private roundtrip tag.
        // The subsequent normal item encoder sees a vanilla item; no private tag is reattached.
        var projected = PolymerItemUtils.getPolymerItemStack(snapshot, context, buffer.registryAccess());
        if (projected.isEmpty() || projected.getItem() instanceof PolymerItem) return snapshot;
        var carrier = projected.copy();
        carrier.remove(DataComponents.CUSTOM_DATA);
        carrier.remove(DataComponents.LORE);
        return carrier;
    }
}
