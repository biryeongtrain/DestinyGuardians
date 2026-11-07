package kim.biryeong.destiny.fx;

import io.netty.buffer.Unpooled;
import io.netty.channel.Channel;
import io.netty.channel.ChannelHandlerContext;
import io.netty.channel.ChannelOutboundHandlerAdapter;
import io.netty.channel.ChannelPromise;
import kim.biryeong.destiny.DestinyGuardians;
import kim.biryeong.minigamelib.cinematic.CameraViews;
import kr.toxicity.model.api.tracker.EntityTracker;
import kr.toxicity.model.impl.fabric.entity.PlayerChannelHandlerImpl;
import kr.toxicity.model.impl.fabric.network.BetterModelBundlePacket;
import kr.toxicity.model.impl.fabric.network.PacketsKt;
import net.minecraft.network.FriendlyByteBuf;
import net.minecraft.network.protocol.Packet;
import net.minecraft.network.protocol.game.*;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.Display;
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.item.ItemStack;
import com.mojang.datafixers.util.Pair;
import net.minecraft.world.phys.Vec3;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.network.syncher.EntityDataSerializers;
import kr.toxicity.model.mixin.EntityAccessor;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Set;
import java.util.stream.Collectors;

/** Owner-only model anchor, independent of the camera and the client's local player.
 * Spawn, mount and body hiding are ordered on the same outbound channel, rather
 * than depending on a server tick or a model spawn-success callback.
 */
final class OwnerModelCarrier implements AutoCloseable {
    private final ServerPlayer owner;
    private final Display.ItemDisplay marker;
    private final Channel channel;
    private final MountRelay relay;
    private final boolean fixed;
    private volatile boolean installed, installPending, closed;
    private boolean warnedMissingHandler;

    OwnerModelCarrier(ServerPlayer owner, EntityTracker tracker, boolean fixed) {
        this.owner = owner;
        this.fixed = fixed;
        marker = new Display.ItemDisplay(EntityTypes.ITEM_DISPLAY, owner.level());
        // Match the normal player's native passenger seat, subtracting the
        // marker's own native seat offset instead of assuming a magic height.
        // Fixed stages and moving supers use the same native passenger seat.
        position();
        marker.setNoGravity(true);
        marker.setSilent(true);
        ((kim.biryeong.destiny.mixin.DisplayCameraAccessor) marker).destiny$setCameraInterpolation(2);
        channel = PacketsKt.getChannel(PacketsKt.getConnection(owner.connection));
        relay = new MountRelay(owner.getId(), marker.getId(),
                tracker.displays().map(d -> d.id()).collect(Collectors.toUnmodifiableSet()), snapshot(), flags());
        install();
    }

    private void install() {
        if (closed || installed || installPending || !channel.isActive()) return;
        installPending = true;
        ordered(() -> { try {
            if (closed || !channel.isActive()) return;
            var pipeline = channel.pipeline();
            var betterModel = pipeline.context(PlayerChannelHandlerImpl.class);
            if (betterModel == null) {
                if (!warnedMissingHandler) DestinyGuardians.LOGGER.warn("Owner model carrier: waiting for BetterModel channel handler");
                warnedMissingHandler = true;
                return;
            }
            // Outbound flows toward the pipeline head. Run AFTER BM has generated
            // its mount IDs, but BEFORE packet bundle encoding. No tick-order race.
            pipeline.addBefore(betterModel.name(), "destiny_owner_model_" + marker.getId(), relay);
            installed = true;
        } finally { installPending = false; } });
    }

    boolean ready() { install(); return !closed && installed && channel.isActive(); }

    /** Also binds an already-spawned model when a super acquires the camera. */
    void spawn() {
        if (closed) return;
        install();
        CameraViews.send(owner, passengers(owner.getId(), relay.displays.stream().mapToInt(Integer::intValue).toArray()));
    }

    void tick() {
        if (closed) return;
        install();
        if (fixed) return;
        position();
        // Snapshot on the server thread. Netty must never read mutable world state.
        relay.spawnPackets = snapshot();
        if (ready() && relay.spawned) CameraViews.send(owner, ClientboundEntityPositionSyncPacket.of(marker));
    }

    private void position() {
        Vec3 seatOffset = marker.getPassengerRidingPosition(marker).subtract(marker.position());
        marker.setPos(owner.getPassengerRidingPosition(owner).subtract(seatOffset));
    }

    private List<Packet<? super ClientGamePacketListener>> snapshot() {
        var packets = new ArrayList<Packet<? super ClientGamePacketListener>>();
        Vec3 p = marker.position();
        packets.add(new ClientboundAddEntityPacket(marker.getId(), marker.getUUID(), p.x, p.y, p.z,
                0, 0, marker.getType(), 0, Vec3.ZERO, 0));
        var data = marker.getEntityData().getNonDefaultValues();
        if (data != null) packets.add(new ClientboundSetEntityDataPacket(marker.getId(), data));
        return List.copyOf(packets);
    }

    private ClientboundSetEntityDataPacket flags() {
        var key = EntityAccessor.bettermodel$getDataSharedFlagsId();
        return new ClientboundSetEntityDataPacket(owner.getId(), List.of(
                SynchedEntityData.DataValue.create(key, owner.getEntityData().get(key))));
    }

    private ClientboundSetEquipmentPacket equipment() {
        return new ClientboundSetEquipmentPacket(owner.getId(), Arrays.stream(EquipmentSlot.values())
                .map(slot -> Pair.of(slot, owner.getItemBySlot(slot).copy())).toList());
    }

    @Override public void close() {
        if (closed) return;
        closed = true;
        try {
            if (!owner.hasDisconnected()) CameraViews.send(owner, new ClientboundRemoveEntitiesPacket(marker.getId()));
        } finally {
            // Queue AFTER the owned tracker/audience removal packets. Instance
            // identity prevents an old disconnect/close from removing a new relay.
            ordered(() -> {
                if (channel.pipeline().context(relay) != null) channel.pipeline().remove(relay);
                installed = false;
            });
            // Queue after relay removal, otherwise our own restore would be hidden again.
            if (!owner.hasDisconnected()) CameraViews.send(owner, new ClientboundBundlePacket(List.of(flags(), equipment())));
        }
    }

    private void ordered(Runnable action) {
        if (channel.eventLoop().inEventLoop()) action.run();
        else channel.eventLoop().execute(action);
    }

    /** Immutable ID snapshot only: Netty never reads player/world/tracker state.
     * Preserve every non-owned passenger (including HUD) and other actors' mounts.
     */
    static final class MountRelay extends ChannelOutboundHandlerAdapter {
        private final int ownerId, carrierId;
        private final Set<Integer> displays;
        private volatile List<Packet<? super ClientGamePacketListener>> spawnPackets;
        private final ClientboundSetEntityDataPacket hiddenFlags;
        private final int flagId;
        private volatile boolean spawned;

        MountRelay(int ownerId, int carrierId, Set<Integer> displays) {
            this(ownerId, carrierId, displays, List.of(), null);
        }

        MountRelay(int ownerId, int carrierId, Set<Integer> displays,
                   List<Packet<? super ClientGamePacketListener>> spawnPackets,
                   ClientboundSetEntityDataPacket flags) {
            this.ownerId = ownerId;
            this.carrierId = carrierId;
            this.displays = Set.copyOf(displays);
            this.spawnPackets = List.copyOf(spawnPackets);
            flagId = flags == null ? -1 : flags.packedItems().getFirst().id();
            hiddenFlags = flags == null ? null : hide(flags);
        }

        @Override public void write(ChannelHandlerContext ctx, Object message, ChannelPromise promise) throws Exception {
            super.write(ctx, message instanceof Packet<?> packet ? rewrite(packet) : message, promise);
        }

        Packet<?> rewrite(Packet<?> packet) {
            var output = new ArrayList<Packet<? super ClientGamePacketListener>>();
            if (!append(packet, output)) return packet;
            var copy = new ClientboundBundlePacket(output);
            if ((Object) packet instanceof BetterModelBundlePacket original
                    && (Object) copy instanceof BetterModelBundlePacket marked)
                marked.bettermodel$setBetterModelPacket(original.bettermodel$isBetterModelPacket());
            return copy;
        }

        private boolean append(Packet<?> packet, ArrayList<Packet<? super ClientGamePacketListener>> output) {
            if (packet instanceof ClientboundBundlePacket bundle) {
                boolean changed = false;
                for (var child : bundle.subPackets()) changed |= append(child, output);
                return changed; // Flatten replacements; native bundles cannot nest.
            }
            if (packet instanceof ClientboundRespawnPacket) spawned = false;
            if (packet instanceof ClientboundRemoveEntitiesPacket removal && removal.entityIds().contains(carrierId))
                spawned = false;
            if (packet instanceof ClientboundAddEntityPacket add && displays.contains(add.getId())) {
                boolean changed = ensureAnchor(output);
                output.add(add);
                return changed;
            }
            if (hiddenFlags != null && packet instanceof ClientboundSetEntityDataPacket data && data.id() == ownerId) {
                var hidden = hide(data);
                output.add(hidden);
                return hidden != data;
            }
            if (hiddenFlags != null && packet instanceof ClientboundSetEquipmentPacket equipment && equipment.getEntity() == ownerId) {
                output.add(hiddenEquipment());
                return true;
            }
            if (packet instanceof ClientboundSetPassengersPacket mount && mount.getVehicle() == ownerId) {
                int[] own = Arrays.stream(mount.getPassengers()).filter(displays::contains).toArray();
                if (own.length > 0) {
                    ensureAnchor(output);
                    int[] other = Arrays.stream(mount.getPassengers()).filter(id -> !displays.contains(id)).toArray();
                    output.add(passengers(ownerId, other));
                    output.add(passengers(carrierId, own));
                    return true;
                }
            }
            @SuppressWarnings("unchecked") var cast = (Packet<? super ClientGamePacketListener>) packet;
            output.add(cast);
            return false;
        }

        private boolean ensureAnchor(ArrayList<Packet<? super ClientGamePacketListener>> output) {
            if (spawned || spawnPackets.isEmpty()) return false;
            output.addAll(spawnPackets);
            if (hiddenFlags != null) {
                output.add(hiddenFlags);
                output.add(hiddenEquipment());
            }
            spawned = true;
            return true;
        }

        private ClientboundSetEquipmentPacket hiddenEquipment() {
            return new ClientboundSetEquipmentPacket(ownerId, Arrays.stream(EquipmentSlot.values())
                    .map(slot -> Pair.of(slot, ItemStack.EMPTY)).toList());
        }

        private ClientboundSetEntityDataPacket hide(ClientboundSetEntityDataPacket packet) {
            boolean changed = false;
            var data = new ArrayList<SynchedEntityData.DataValue<?>>();
            for (var value : packet.packedItems()) {
                if (value.id() == flagId && value.value() instanceof Byte flags && (flags & 0x20) == 0) {
                    data.add(new SynchedEntityData.DataValue<>(flagId, EntityDataSerializers.BYTE, (byte)(flags | 0x20)));
                    changed = true;
                } else data.add(value);
            }
            return changed ? new ClientboundSetEntityDataPacket(packet.id(), List.copyOf(data)) : packet;
        }
    }

    private static ClientboundSetPassengersPacket passengers(int vehicle, int[] riders) {
        FriendlyByteBuf buffer = new FriendlyByteBuf(Unpooled.buffer());
        try {
            buffer.writeVarInt(vehicle);
            buffer.writeVarIntArray(riders);
            return ClientboundSetPassengersPacket.STREAM_CODEC.decode(buffer);
        } finally { buffer.release(); }
    }
}
