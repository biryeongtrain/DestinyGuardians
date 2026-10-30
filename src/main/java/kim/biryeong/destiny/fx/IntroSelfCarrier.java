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
import net.minecraft.world.phys.Vec3;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.Set;
import java.util.stream.Collectors;

/** Owner-only packet carrier. CameraViews moves the client's local player to the
 * camera, so its BM limb passengers must ride a separate stage anchor instead.
 * No world entity, second animation clock, skin copy or real player mutation.
 */
final class IntroSelfCarrier implements AutoCloseable {
    private final ServerPlayer owner;
    private final Display.ItemDisplay marker;
    private final Channel channel;
    private final MountRelay relay;
    private volatile boolean installed, closed;

    IntroSelfCarrier(ServerPlayer owner, EntityTracker tracker) {
        this.owner = owner;
        marker = new Display.ItemDisplay(EntityTypes.ITEM_DISPLAY, owner.level());
        // Match the normal player's native passenger seat, subtracting the
        // marker's own native seat offset instead of assuming a magic height.
        // The authored stage stays fixed; source root motion remains in BM bones.
        Vec3 seatOffset = marker.getPassengerRidingPosition(marker).subtract(marker.position());
        marker.setPos(owner.getPassengerRidingPosition(owner).subtract(seatOffset));
        marker.setNoGravity(true);
        marker.setSilent(true);
        channel = PacketsKt.getChannel(PacketsKt.getConnection(owner.connection));
        relay = new MountRelay(owner.getId(), marker.getId(),
                tracker.displays().map(d -> d.id()).collect(Collectors.toUnmodifiableSet()));
        ordered(() -> {
            if (closed || !channel.isActive()) return;
            var pipeline = channel.pipeline();
            var betterModel = pipeline.context(PlayerChannelHandlerImpl.class);
            if (betterModel == null) {
                DestinyGuardians.LOGGER.warn("Intro self carrier: BetterModel channel handler missing");
                return;
            }
            // Outbound flows toward the pipeline head. Run AFTER BM has generated
            // its mount IDs, but BEFORE packet bundle encoding. No tick-order race.
            pipeline.addBefore(betterModel.name(), "destiny_intro_self_" + marker.getId(), relay);
            installed = true;
        });
    }

    boolean ready() { return !closed && installed && channel.isActive(); }

    /** Called before every owner model snapshot, including camera respawn/cut.
     * This is idempotent at the client entity ID; it does not restart animation.
     */
    void spawn() {
        if (!ready()) throw new IllegalStateException("Intro self carrier not ready");
        Vec3 p = marker.position();
        CameraViews.send(owner, new ClientboundAddEntityPacket(marker.getId(), marker.getUUID(), p.x, p.y, p.z,
                0, 0, marker.getType(), 0, Vec3.ZERO, 0));
        var data = marker.getEntityData().getNonDefaultValues();
        if (data != null) CameraViews.send(owner, new ClientboundSetEntityDataPacket(marker.getId(), data));
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

        MountRelay(int ownerId, int carrierId, Set<Integer> displays) {
            this.ownerId = ownerId;
            this.carrierId = carrierId;
            this.displays = Set.copyOf(displays);
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
            if (packet instanceof ClientboundSetPassengersPacket mount && mount.getVehicle() == ownerId) {
                int[] own = Arrays.stream(mount.getPassengers()).filter(displays::contains).toArray();
                if (own.length > 0) {
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
