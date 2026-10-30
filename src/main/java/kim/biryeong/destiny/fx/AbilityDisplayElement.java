package kim.biryeong.destiny.fx;

import eu.pb4.polymer.virtualentity.api.data.DisplayEntityData;
import eu.pb4.polymer.virtualentity.api.elements.ItemDisplayElement;
import kim.biryeong.destiny.crucible.CrucibleRuntime;
import net.minecraft.network.protocol.Packet;
import net.minecraft.network.protocol.game.ClientGamePacketListener;
import net.minecraft.network.protocol.game.ClientboundSetEntityDataPacket;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.item.ItemStack;
import java.util.ArrayList;
import java.util.List;
import java.util.function.Consumer;

/** One display transform, viewer-specific ability item metadata. Never recolors a shared stack. */
public final class AbilityDisplayElement extends ItemDisplayElement {
    private final ServerPlayer owner;
    private final java.util.Map<net.minecraft.server.network.ServerGamePacketListenerImpl, Boolean> relationships = new java.util.IdentityHashMap<>();

    public AbilityDisplayElement(ServerPlayer owner, ItemStack item) {
        super(item);
        this.owner = owner;
    }

    private List<SynchedEntityData.DataValue<?>> forViewer(ServerPlayer viewer,
            List<SynchedEntityData.DataValue<?>> values) {
        if (!CrucibleRuntime.enemies(owner, viewer)) return values;
        List<SynchedEntityData.DataValue<?>> result = new ArrayList<>(values.size());
        for (var value : values) {
            if (value.id() == DisplayEntityData.Item.ITEM.id() && value.value() instanceof ItemStack item)
                result.add(SynchedEntityData.DataValue.create(DisplayEntityData.Item.ITEM,
                        AbilityVisualVariants.item(item, true)));
            else result.add(value);
        }
        return result;
    }

    @Override protected void sendChangedTrackerEntries(ServerPlayer player,
            Consumer<Packet<ClientGamePacketListener>> packets) {
        var values = syncedData.getChangedEntries();
        relationships.put(player.connection, CrucibleRuntime.enemies(owner, player));
        if (values != null && !values.isEmpty())
            packets.accept(new ClientboundSetEntityDataPacket(getEntityId(), forViewer(player, values)));
    }

    @Override protected void sendTrackerUpdates() {
        var values = syncedData.isDirty() ? syncedData.getDirtyEntries() : null;
        if (getHolder() == null) return;
        relationships.keySet().retainAll(getHolder().getWatchingPlayers());
        for (var connection : getHolder().getWatchingPlayers()) {
            boolean hostile = CrucibleRuntime.enemies(owner, connection.getPlayer());
            Boolean previous = relationships.put(connection, hostile);
            var updates = values;
            if (previous == null || previous != hostile) {
                updates = new ArrayList<>(values == null ? List.of() : values);
                updates.removeIf(value -> value.id() == DisplayEntityData.Item.ITEM.id());
                updates.add(SynchedEntityData.DataValue.create(DisplayEntityData.Item.ITEM, getItem()));
            }
            if (updates != null && !updates.isEmpty())
                connection.send(new ClientboundSetEntityDataPacket(getEntityId(), forViewer(connection.getPlayer(), updates)));
        }
    }
}
