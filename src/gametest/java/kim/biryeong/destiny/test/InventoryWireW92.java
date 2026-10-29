package kim.biryeong.destiny.test;

import com.mojang.authlib.GameProfile;
import eu.pb4.polymer.common.api.PolymerCommonUtils;
import io.netty.buffer.ByteBuf;
import io.netty.buffer.Unpooled;
import io.netty.channel.Channel;
import io.netty.channel.ChannelInitializer;
import io.netty.channel.embedded.EmbeddedChannel;
import io.netty.util.ReferenceCountUtil;
import kim.biryeong.destiny.hud.CombatHud;
import kim.biryeong.destiny.hud.WeaponPerkHud;
import kim.biryeong.destiny.hud.WeaponScopeHud;
import kim.biryeong.destiny.weapon.WeaponRuntime;
import net.fabricmc.fabric.api.networking.v1.context.PacketContext;
import net.fabricmc.fabric.api.networking.v1.context.PacketContextProvider;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.Connection;
import net.minecraft.network.PacketEncoder;
import net.minecraft.network.PacketDecoder;
import net.minecraft.network.ProtocolInfo;
import net.minecraft.network.RegistryFriendlyByteBuf;
import net.minecraft.network.VarInt;
import net.minecraft.network.UnconfiguredPipelineHandler;
import net.minecraft.network.protocol.Packet;
import net.minecraft.network.protocol.PacketFlow;
import net.minecraft.network.protocol.game.ClientGamePacketListener;
import net.minecraft.network.protocol.game.GameProtocols;
import net.minecraft.network.protocol.game.ServerboundPlayerLoadedPacket;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.server.network.CommonListenerCookie;
import net.minecraft.server.network.ServerGamePacketListenerImpl;
import net.minecraft.world.level.GameType;
import net.minecraft.world.phys.Vec3;

import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

/** Independent PLAY connection: native menu -> synchronizer -> packet encoder -> framed bytes.
 * Uses login-equivalent test metadata, not a claim of a real authenticated socket/client.
 * Deliberately does not alter TestPlayers or reach into its channel registry.
 */
final class InventoryWireW92 implements AutoCloseable {
    final ServerPlayer player;
    final Connection connection;
    private final GameTestHelper helper;
    private final ProtocolInfo<ClientGamePacketListener> clientbound;
    private EmbeddedChannel channel;
    private boolean closed;

    InventoryWireW92(GameTestHelper helper, Vec3 relative) {
        this.helper = helper;
        var server = helper.getLevel().getServer();
        var profile = new GameProfile(UUID.randomUUID(), "W92_" + UUID.randomUUID().toString().substring(0, 8));
        var cookie = CommonListenerCookie.createInitial(profile, false);
        player = new ServerPlayer(server, helper.getLevel(), profile, cookie.clientInformation());
        connection = new Connection(PacketFlow.SERVERBOUND);
        clientbound = GameProtocols.CLIENTBOUND_TEMPLATE.bind(RegistryFriendlyByteBuf.decorator(server.registryAccess()));
        // Register before any channel/listener setup; construction failures also close this attempt.
        TestCleanup.register(helper, this::close);
        TestPacketContexts.initialize(connection, server, profile);
        channel = new EmbeddedChannel(new ChannelInitializer<Channel>() {
            @Override protected void initChannel(Channel ch) {
                Connection.configureSerialization(ch.pipeline(), PacketFlow.SERVERBOUND, false, null);
                connection.configurePacketHandler(ch.pipeline());
            }
        });
        // configureSerialization installs the protocol transition handlers, not a PLAY encoder yet.
        // Native setupOutboundProtocol also attaches this connection's Fabric context to the encoder.
        connection.setupOutboundProtocol(clientbound);
        player.connection = new ServerGamePacketListenerImpl(server, connection, player, cookie);
        // configureSerialization begins with a HANDSHAKE decoder. A real terminal
        // handshake removes it and installs this native transition handler before
        // setupInboundProtocol. This login-equivalent fixture starts at that boundary;
        // otherwise the inbound configuration task escapes as an unencoded object.
        // Never hide/drop that task in takeBytes: require actual PLAY decoder setup.
        channel.pipeline().replace("decoder", "inbound_config", new UnconfiguredPipelineHandler.Inbound());
        connection.setupInboundProtocol(GameProtocols.SERVERBOUND_TEMPLATE.bind(
                RegistryFriendlyByteBuf.decorator(server.registryAccess()), player.connection), player.connection);
        if (channel.pipeline().get(PacketEncoder.class) == null || channel.pipeline().get(PacketDecoder.class) == null
                || channel.pipeline().get("inbound_config") != null)
            throw new IllegalStateException("Native PLAY encoder/decoder transition did not finish");
        var context = ((PacketContextProvider) (Object) player.connection).getPacketContext();
        if (context != ((PacketContextProvider) (Object) connection).getPacketContext()
                || context.get(PacketContext.CONNECTION) != connection
                || connection.getPacketListener() != player.connection
                || context.get(PacketContext.GAME_PROFILE) != player.getGameProfile()
                || context.get(PacketContext.SERVER_INSTANCE) != server
                || context.get(PacketContext.REGISTRY_ACCESS) != server.registryAccess())
            throw new IllegalStateException("Native recipient context is not this fixture's exact identity");
        player.setPos(helper.absoluteVec(relative));
        player.setYRot(-90); player.setYHeadRot(-90); player.setXRot(90);
        player.setNoGravity(true); player.setOnGround(true);
        player.connection.handleAcceptPlayerLoad(new ServerboundPlayerLoadedPacket());
        player.setGameMode(GameType.SURVIVAL);
        // ServerPlayer construction alone does not attach its native container synchronizer.
        player.initInventoryMenu();
        discard();
    }

    /** Read all fragments together: native prepender can emit header and payload separately. */
    private ByteBuf takeBytes() {
        if (closed) throw new IllegalStateException("Closed W92 wire fixture");
        connection.flushChannel();
        channel.runPendingTasks();
        channel.flushOutbound();
        channel.checkException();
        var bytes = Unpooled.buffer();
        try {
            Object value;
            while ((value = channel.readOutbound()) != null) {
                try {
                    if (!(value instanceof ByteBuf fragment))
                        throw new IllegalStateException("Unencoded outbound value: " + value.getClass().getName());
                    bytes.writeBytes(fragment);
                } finally {
                    ReferenceCountUtil.release(value);
                }
            }
            return bytes;
        } catch (Throwable error) {
            bytes.release();
            throw error;
        }
    }

    void discard() {
        var bytes = takeBytes();
        bytes.release();
    }

    List<Packet<?>> capture() {
        var bytes = takeBytes();
        try {
            // Polymer's decode hook restores real server items whenever SERVERBOUND context
            // is bound, even on the main server thread. Explicit client semantics are essential.
            return PacketContext.supplyWithoutContext(() -> {
                if (PacketContext.get() != null || PolymerCommonUtils.isServerNetworkingThread())
                    throw new IllegalStateException("Client wire oracle entered a server networking scope");
                var packets = new ArrayList<Packet<?>>();
                while (bytes.isReadable()) {
                    int size = VarInt.read(bytes);
                    if (size <= 0 || size > bytes.readableBytes())
                        throw new IllegalStateException("Truncated or invalid native frame length: " + size);
                    // Non-retained slice belongs to bytes, released by the outer finally.
                    var frame = bytes.readSlice(size);
                    packets.add(clientbound.codec().decode(frame));
                    if (frame.isReadable()) throw new IllegalStateException("Unconsumed clientbound packet bytes");
                }
                return List.copyOf(packets);
            });
        } finally {
            bytes.release();
        }
    }

    List<Packet<?>> incremental() {
        discard();
        player.inventoryMenu.broadcastChanges();
        return capture();
    }

    List<Packet<?>> full() {
        discard();
        player.inventoryMenu.sendAllDataToRemote();
        return capture();
    }

    @Override public void close() {
        if (closed) return;
        closed = true;
        try {
            player.setServerLevel(helper.getLevel());
            player.setShiftKeyDown(false); player.stopUsingItem();
            WeaponRuntime.cleanup(player);
            WeaponPerkHud.remove(player); WeaponScopeHud.remove(player); CombatHud.remove(player);
            TestPlayers.remove(player); // Generic production-state cleanup; this fixture owns its channel.
        } finally {
            if (channel != null) channel.finishAndReleaseAll();
        }
    }
}
