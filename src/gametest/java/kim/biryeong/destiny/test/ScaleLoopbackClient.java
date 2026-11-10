package kim.biryeong.destiny.test;

import io.netty.buffer.ByteBuf;
import io.netty.channel.*;
import net.minecraft.core.RegistryAccess;
import net.minecraft.network.*;
import net.minecraft.network.protocol.Packet;
import net.minecraft.network.protocol.PacketFlow;
import net.minecraft.network.protocol.common.*;
import net.minecraft.network.protocol.configuration.*;
import net.minecraft.network.protocol.cookie.*;
import net.minecraft.network.protocol.game.*;
import net.minecraft.network.protocol.login.*;
import net.minecraft.server.level.ClientInformation;
import net.minecraft.server.network.EventLoopGroupHolder;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.Relative;
import net.minecraft.world.phys.Vec3;

import java.lang.reflect.*;
import java.net.InetSocketAddress;
import java.nio.charset.StandardCharsets;
import java.util.*;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.LongAdder;

/** Test-only real loopback TCP peer. Native codecs/compression; no renderer, auth service or independent registry build. */
final class ScaleLoopbackClient implements AutoCloseable, InvocationHandler {
    final String name;
    final UUID uuid;
    final Connection connection = new Connection(PacketFlow.CLIENTBOUND);
    final LongAdder receivedBytes = new LongAdder(), sentBytes = new LongAdder();
    final Map<String, LongAdder> received = new ConcurrentHashMap<>();
    final Set<Long> receivedChunks = ConcurrentHashMap.newKeySet();
    private final RegistryAccess.Frozen registries;
    private final Set<String> cachedPackHashes;
    private final ClientLoginPacketListener login;
    private final ClientConfigurationPacketListener configuration;
    private final ClientGamePacketListener game;
    volatile String failure;
    volatile boolean playing;
    volatile Vec3 position = Vec3.ZERO;
    volatile float yaw, pitch;
    volatile String lastTeleport = "none";
    private boolean loadedAcknowledged;
    private int sequence;

    ScaleLoopbackClient(String name, int port, RegistryAccess.Frozen registries, String cachedPackHash) {
        this(name, port, registries, Set.of(cachedPackHash));
    }

    ScaleLoopbackClient(String name, int port, RegistryAccess.Frozen registries, Set<String> cachedPackHashes) {
        this.name = name;
        this.uuid = UUID.nameUUIDFromBytes(("OfflinePlayer:" + name).getBytes(StandardCharsets.UTF_8));
        this.registries = registries; this.cachedPackHashes = Set.copyOf(cachedPackHashes);
        login = listener(ClientLoginPacketListener.class);
        configuration = listener(ClientConfigurationPacketListener.class);
        game = listener(ClientGamePacketListener.class);
        Connection.connect(new InetSocketAddress("127.0.0.1", port), EventLoopGroupHolder.remote(false), connection)
                .addListener((ChannelFutureListener) future -> {
                    if (!future.isSuccess()) { failure = String.valueOf(future.cause()); return; }
                    future.channel().pipeline().addFirst("scale_loopback_bytes", new ChannelDuplexHandler() {
                        @Override public void channelRead(ChannelHandlerContext ctx, Object message) throws Exception {
                            if (message instanceof ByteBuf bytes) receivedBytes.add(bytes.readableBytes());
                            super.channelRead(ctx, message);
                        }
                        @Override public void write(ChannelHandlerContext ctx, Object message, ChannelPromise promise) throws Exception {
                            if (message instanceof ByteBuf bytes) sentBytes.add(bytes.readableBytes());
                            super.write(ctx, message, promise);
                        }
                    });
                    connection.initiateServerboundPlayConnection("127.0.0.1", port, login);
                    connection.send(new ServerboundHelloPacket(name, uuid));
                });
    }

    private <T> T listener(Class<T> type) {
        return type.cast(Proxy.newProxyInstance(type.getClassLoader(), new Class<?>[]{type}, this));
    }

    @Override public Object invoke(Object proxy, Method method, Object[] args) throws Throwable {
        if (method.getDeclaringClass() == Object.class) return switch (method.getName()) {
            case "toString" -> "ScaleLoopbackClient[" + name + "]";
            case "hashCode" -> System.identityHashCode(proxy);
            case "equals" -> proxy == args[0];
            default -> null;
        };
        if (method.getName().equals("flow")) return PacketFlow.CLIENTBOUND;
        if (method.getName().equals("isAcceptingMessages") || method.getName().equals("shouldHandleMessage")) return true;
        if (method.getName().equals("onDisconnect")) { if (failure == null) failure = String.valueOf(args[0]); return null; }
        if (method.getName().equals("onPacketError")) { failure = String.valueOf(args[1]); throw (Throwable) args[1]; }
        if (args != null && args.length == 1 && args[0] instanceof Packet<?> packet) {
            received.computeIfAbsent(packet.getClass().getSimpleName(), ignored -> new LongAdder()).increment();
            handle(packet);
            return null;
        }
        if (method.isDefault()) return InvocationHandler.invokeDefault(proxy, method, args == null ? new Object[0] : args);
        return null;
    }

    @SuppressWarnings({"rawtypes", "unchecked"})
    private void handle(Packet<?> packet) {
        if (packet instanceof ClientboundBundlePacket bundle) {
            for (var sub : bundle.subPackets()) ((Packet) sub).handle(game);
        } else if (packet instanceof ClientboundLoginCompressionPacket compression) {
            connection.setupCompression(compression.getCompressionThreshold(), false);
        } else if (packet instanceof ClientboundLoginFinishedPacket) {
            connection.setupInboundProtocol(ConfigurationProtocols.CLIENTBOUND, configuration);
            connection.send(ServerboundLoginAcknowledgedPacket.INSTANCE);
            connection.setupOutboundProtocol(ConfigurationProtocols.SERVERBOUND);
            connection.send(new ServerboundClientInformationPacket(new ClientInformation("en_us",
                    Math.clamp(Integer.getInteger("destiny.gametest.scale.requestedViewDistance", 32), 2, 32),
                    net.minecraft.world.entity.player.ChatVisiblity.FULL, true, 127,
                    net.minecraft.world.entity.HumanoidArm.RIGHT, false, true,
                    net.minecraft.server.level.ParticleStatus.ALL)));
        } else if (packet instanceof ClientboundCustomQueryPacket query) {
            connection.send(new ServerboundCustomQueryAnswerPacket(query.transactionId(), null));
        } else if (packet instanceof ClientboundHelloPacket) {
            failure = "Online authentication requested: loopback fixture requires an offline owned GameTest server";
            close();
        } else if (packet instanceof ClientboundSelectKnownPacks) {
            connection.send(new ServerboundSelectKnownPacks(List.of()));
        } else if (packet instanceof ClientboundCodeOfConductPacket) {
            connection.send(ServerboundAcceptCodeOfConductPacket.INSTANCE);
        } else if (packet instanceof ClientboundFinishConfigurationPacket) {
            connection.setupInboundProtocol(GameProtocols.CLIENTBOUND_TEMPLATE.bind(RegistryFriendlyByteBuf.decorator(registries)), game);
            connection.send(ServerboundFinishConfigurationPacket.INSTANCE);
            connection.setupOutboundProtocol(GameProtocols.SERVERBOUND_TEMPLATE.bind(RegistryFriendlyByteBuf.decorator(registries), new GameProtocols.Context() {
                public boolean hasInfiniteMaterials() { return false; }
                public boolean canUseCommandBlocks() { return false; }
            }));
        } else if (packet instanceof ClientboundKeepAlivePacket keepAlive) {
            connection.send(new ServerboundKeepAlivePacket(keepAlive.getId()));
        } else if (packet instanceof ClientboundPingPacket ping) {
            connection.send(new ServerboundPongPacket(ping.getId()));
        } else if (packet instanceof ClientboundCookieRequestPacket cookie) {
            connection.send(new ServerboundCookieResponsePacket(cookie.key(), null));
        } else if (packet instanceof ClientboundResourcePackPushPacket pack) {
            if (!cachedPackHashes.contains(pack.hash())) { failure = "Unverified resource-pack hash"; close(); return; }
            // Explicit warm-cache scenario: this tests gameplay transport, not pack download/render time.
            connection.send(new ServerboundResourcePackPacket(pack.id(), ServerboundResourcePackPacket.Action.ACCEPTED));
            connection.send(new ServerboundResourcePackPacket(pack.id(), ServerboundResourcePackPacket.Action.DOWNLOADED));
            connection.send(new ServerboundResourcePackPacket(pack.id(), ServerboundResourcePackPacket.Action.SUCCESSFULLY_LOADED));
        } else if (packet instanceof ClientboundLoginPacket) {
            playing = true;
            loadedAcknowledged = false;
            receivedChunks.clear();
        } else if (packet instanceof ClientboundRespawnPacket) {
            loadedAcknowledged = false;
            receivedChunks.clear();
        } else if (packet instanceof ClientboundLevelChunkWithLightPacket chunk) {
            receivedChunks.add(new net.minecraft.world.level.ChunkPos(chunk.x(), chunk.z()).pack());
        } else if (packet instanceof ClientboundPlayerPositionPacket move) {
            var absolute = net.minecraft.world.entity.PositionMoveRotation.calculateAbsolute(
                    new net.minecraft.world.entity.PositionMoveRotation(position, Vec3.ZERO, yaw, pitch), move.change(), move.relatives());
            position = absolute.position(); yaw = absolute.yRot(); pitch = absolute.xRot();
            lastTeleport = move.toString();
            connection.send(new ServerboundAcceptTeleportationPacket(move.id(), position.x, position.y, position.z, yaw, pitch));
            acknowledgeLoaded();
        } else if (packet instanceof ClientboundPlayerRotationPacket rotation) {
            yaw = rotation.yRot() + (rotation.relativeY() ? yaw : 0);
            pitch = Math.clamp(rotation.xRot() + (rotation.relativeX() ? pitch : 0), -90, 90);
        } else if (packet instanceof ClientboundChunkBatchFinishedPacket) {
            connection.send(new ServerboundChunkBatchReceivedPacket(8));
            acknowledgeLoaded();
        } else if (packet instanceof ClientboundDisconnectPacket disconnect) {
            failure = disconnect.reason().getString();
        } else if (packet instanceof ClientboundLoginDisconnectPacket disconnect) {
            failure = disconnect.reason().getString();
        }
    }

    void tick(boolean active, int age) {
        connection.tick();
        if (!playing || !connection.isConnected()) return;
        if (active) {
            if (!Double.isFinite(position.x) || !Double.isFinite(position.y) || !Double.isFinite(position.z)
                    || !Float.isFinite(yaw) || !Float.isFinite(pitch))
                throw new AssertionError("Invalid peer pose " + position + " / " + yaw + "/" + pitch + " last=" + lastTeleport);
            yaw = age * 1.5f;
            connection.send(new ServerboundMovePlayerPacket.PosRot(position, yaw, 0, false, false));
            if (age % 40 == 0) connection.send(ServerboundPunchPacket.INSTANCE);
            if (age % 20 == 0) connection.send(new ServerboundUseItemPacket(InteractionHand.MAIN_HAND, sequence++, yaw, 0));
            if (age % 20 == 5) connection.send(new ServerboundPlayerActionPacket(
                    ServerboundPlayerActionPacket.Action.RELEASE_USE_ITEM, net.minecraft.core.BlockPos.ZERO, net.minecraft.core.Direction.DOWN));
        }
        connection.send(ServerboundClientTickEndPacket.INSTANCE);
    }

    private void acknowledgeLoaded() {
        if (loadedAcknowledged) return;
        loadedAcknowledged = true;
        connection.send(new ServerboundPlayerLoadedPacket());
    }

    Map<String, Long> packetCounts() {
        var out = new TreeMap<String, Long>(); received.forEach((key, value) -> out.put(key, value.sum())); return out;
    }

    @Override public void close() { connection.disconnect(net.minecraft.network.chat.Component.literal("Owned scale fixture cleanup")); }
}
