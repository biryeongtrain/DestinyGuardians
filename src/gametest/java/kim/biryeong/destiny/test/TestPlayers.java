package kim.biryeong.destiny.test;

import com.mojang.authlib.GameProfile;
import io.netty.channel.embedded.EmbeddedChannel;
import kim.biryeong.destiny.guardian.Element;
import kim.biryeong.destiny.guardian.GuardianClass;
import kim.biryeong.destiny.guardian.GuardianData;
import kim.biryeong.destiny.guardian.Guardians;
import kim.biryeong.destiny.ability.hunter.HunterAbilities;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.Connection;
import net.minecraft.network.RegistryFriendlyByteBuf;
import net.minecraft.network.protocol.PacketFlow;
import net.minecraft.network.protocol.game.GameProtocols;
import net.minecraft.network.protocol.game.ServerboundPlayerLoadedPacket;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.server.network.CommonListenerCookie;
import net.minecraft.server.network.ServerGamePacketListenerImpl;
import net.minecraft.world.level.GameType;
import net.minecraft.world.phys.Vec3;

import java.util.HashMap;
import java.util.Map;
import java.util.UUID;

/** GameTest 용 가짜 접속 플레이어 (minigame-lib LibraryGameTests 방식). */
final class TestPlayers {
    private static final Map<UUID, EmbeddedChannel> CHANNELS = new HashMap<>();

    private TestPlayers() {
    }

    static ServerPlayer create(GameTestHelper h, Vec3 relative, float yaw, float pitch) {
        var server = h.getLevel().getServer();
        var profile = new GameProfile(UUID.randomUUID(), "HunterTest");
        var cookie = CommonListenerCookie.createInitial(profile, false);
        var player = new ServerPlayer(server, h.getLevel(), profile, cookie.clientInformation());
        var connection = new Connection(PacketFlow.SERVERBOUND);
        CHANNELS.put(player.getUUID(), new EmbeddedChannel(connection));
        player.connection = new ServerGamePacketListenerImpl(server, connection, player, cookie);
        connection.setupInboundProtocol(GameProtocols.SERVERBOUND_TEMPLATE.bind(
                RegistryFriendlyByteBuf.decorator(server.registryAccess()), player.connection), player.connection);
        player.setPos(h.absoluteVec(relative));
        player.setYRot(yaw);
        player.setYHeadRot(yaw);
        player.setXRot(pitch);
        player.connection.handleAcceptPlayerLoad(new ServerboundPlayerLoadedPacket());
        player.setGameMode(GameType.SURVIVAL);
        return player;
    }

    static ServerPlayer hunter(GameTestHelper h, Element element, Vec3 relative, float yaw, float pitch) {
        ServerPlayer p = create(h, relative, yaw, pitch);
        GuardianData data = Guardians.data(p);
        data.setGuardianClass(GuardianClass.HUNTER);
        data.setLoadout(GuardianClass.HUNTER, HunterAbilities.preset(element));
        return p;
    }

    static void drain(ServerPlayer player) {
        EmbeddedChannel channel = CHANNELS.get(player.getUUID());
        if (channel != null) {
            channel.runPendingTasks();
            while (channel.readOutbound() != null) {
                // discard
            }
        }
    }

    static void remove(ServerPlayer player) {
        kim.biryeong.destiny.ability.AbilityService.endSuper(player);
        Guardians.forget(player);
        EmbeddedChannel channel = CHANNELS.remove(player.getUUID());
        if (channel != null) {
            channel.finishAndReleaseAll();
        }
    }
}
