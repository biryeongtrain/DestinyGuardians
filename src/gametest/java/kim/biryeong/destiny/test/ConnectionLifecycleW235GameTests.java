package kim.biryeong.destiny.test;

import com.mojang.authlib.GameProfile;
import io.netty.channel.embedded.EmbeddedChannel;
import kim.biryeong.destiny.camera.SuperCamera;
import kim.biryeong.destiny.guardian.Element;
import kim.biryeong.destiny.guardian.GuardianClass;
import kim.biryeong.destiny.guardian.Guardians;
import kim.biryeong.destiny.ability.hunter.HunterAbilities;
import kim.biryeong.destiny.weapon.WeaponCatalog;
import kim.biryeong.destiny.weapon.WeaponItems;
import kim.biryeong.destiny.world.TowerSpawnWorld;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.core.SectionPos;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.Connection;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.PacketFlow;
import net.minecraft.network.protocol.game.ServerboundPlayerLoadedPacket;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.server.network.CommonListenerCookie;
import net.minecraft.server.network.ServerGamePacketListenerImpl;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.phys.Vec3;

import java.lang.reflect.Field;
import java.util.UUID;

/** Native login/tick/disconnect regressions; use an isolated dev server with tower enabled. */
public final class ConnectionLifecycleW235GameTests {
    private static void check(GameTestHelper h, boolean ok, String message) {
        h.assertTrue(ok, Component.literal(message));
    }

    private record Login(ServerPlayer player, EmbeddedChannel channel) {}

    private static Login login(GameTestHelper h, ServerLevel level, GameProfile profile) {
        var server = level.getServer();
        var cookie = CommonListenerCookie.createInitial(profile, false);
        var p = new ServerPlayer(server, level, profile, cookie.clientInformation());
        p.setPos(h.absoluteVec(new Vec3(2.5, 1, 6.5)));
        var connection = new Connection(PacketFlow.SERVERBOUND);
        var channel = new EmbeddedChannel(connection);
        TestPacketContexts.initialize(connection, server, profile);
        TestCleanup.register(h, () -> {
            if (server.getPlayerList().getPlayer(p.getUUID()) == p) {
                p.connection.disconnect(Component.literal("W235 fixture cleanup"));
            }
            channel.finishAndReleaseAll();
        });
        // Calls the real Fabric JOIN injection before native level.addNewPlayer.
        server.getPlayerList().placeNewPlayer(connection, p, cookie);
        p.connection.handleAcceptPlayerLoad(new ServerboundPlayerLoadedPacket());
        return new Login(p, channel);
    }

    private static void floating(ServerPlayer p, boolean flag, int ticks) {
        try {
            Field f = ServerGamePacketListenerImpl.class.getDeclaredField("clientIsFloating");
            Field n = ServerGamePacketListenerImpl.class.getDeclaredField("aboveGroundTickCount");
            f.setAccessible(true); n.setAccessible(true);
            f.setBoolean(p.connection, flag); n.setInt(p.connection, ticks);
        } catch (ReflectiveOperationException e) { throw new AssertionError(e); }
    }

    @GameTest(structure="destiny-test:floor", environment="destiny-test:w90_isolated", maxTicks=100, manualOnly=true)
    public void nativeLoginDefersTowerTransferAndCanDisconnectThenRejoin(GameTestHelper h) {
        var server = h.getLevel().getServer();
        var tower = TowerSpawnWorld.open(server);
        var profile = new GameProfile(UUID.randomUUID(), "W235Join");
        for (int i = 0; i < 2; i++) {
            var origin = i == 0 ? h.getLevel() : tower;
            var p = login(h, origin, profile).player();
            check(h, p.level() == origin && origin.getEntity(p.getId()) == p,
                    "JOIN must finish native registration in the original level first");
            TowerSpawnWorld.tick(server);
            check(h, p.level() == tower && tower.getEntity(p.getId()) == p,
                    "Following tick transfers exactly the registered player");
            if (origin != tower) check(h, origin.getEntity(p.getId()) == null, "Old tracker has no duplicate player");
            p.connection.disconnect(Component.literal("W235 reconnect"));
            check(h, server.getPlayerList().getPlayer(profile.id()) == null
                    && tower.getEntity(p.getId()) == null && origin.getEntity(p.getId()) == null,
                    "Native disconnect completes without DistanceManager exception or stale login identity");
        }
        h.succeed();
    }

    @GameTest(structure="destiny-test:floor", environment="destiny-test:w90_isolated", maxTicks=100, manualOnly=true)
    public void swordCameraClearsStaleFloatingAndTracksNativeChunkMoves(GameTestHelper h) {
        var server = h.getLevel().getServer();
        TowerSpawnWorld.open(server);
        var p = login(h, h.getLevel(), new GameProfile(UUID.randomUUID(), "W235Sword")).player();
        TowerSpawnWorld.tick(server);
        Guardians.data(p).setGuardianClass(GuardianClass.HUNTER);
        Guardians.data(p).setLoadout(GuardianClass.HUNTER, HunterAbilities.preset(Element.SOLAR));
        p.setItemInHand(InteractionHand.MAIN_HAND,
                WeaponItems.create(WeaponCatalog.find("abide_the_return").orElseThrow()));
        check(h, !server.allowFlight() && SuperCamera.startSword(p), "Camera test runs with vanilla flight detection enabled");
        // Reproduce the stale handleMovePlayer flag just before vanilla's kick threshold.
        floating(p, true, 80);
        for (int i = 0; i < 100; i++) p.connection.tick();
        check(h, !p.hasDisconnected() && SuperCamera.swordActive(p), "Over 80 native connection ticks cannot kick owned server physics");
        p.setPos(p.position().add(17, 0, 0));
        p.connection.tick();
        check(h, p.getLastSectionPos().equals(SectionPos.of(p)), "Owned movement updates real chunk distance tracking");
        check(h, !p.getAbilities().flying && !p.getAbilities().mayfly && !p.noPhysics && !p.isPassenger(),
                "No flight, noclip, or real mount granted");
        p.connection.disconnect(Component.literal("W235 sword quit"));
        check(h, server.getPlayerList().getPlayer(p.getUUID()) == null && !SuperCamera.active(p),
                "Disconnect releases owned camera without teleporting a closing connection");
        h.succeed();
    }

    @GameTest(structure="destiny-test:floor", environment="destiny-test:w90_isolated", maxTicks=100, manualOnly=true)
    public void ordinaryFloatingStillDisconnectsAndRemovesPlayerCleanly(GameTestHelper h) {
        var server = h.getLevel().getServer();
        TowerSpawnWorld.open(server);
        var p = login(h, h.getLevel(), new GameProfile(UUID.randomUUID(), "W235Float")).player();
        TowerSpawnWorld.tick(server);
        check(h, !server.allowFlight() && !SuperCamera.active(p), "Ordinary player has no camera exemption");
        floating(p, true, 80);
        p.connection.tick();
        check(h, p.hasDisconnected() && server.getPlayerList().getPlayer(p.getUUID()) == null,
                "Normal flight kick still runs and finishes native cleanup");
        h.succeed();
    }
}
