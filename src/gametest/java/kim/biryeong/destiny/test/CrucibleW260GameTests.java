package kim.biryeong.destiny.test;

import kim.biryeong.destiny.combat.Combat;
import kim.biryeong.destiny.crucible.ControlMatch;
import kim.biryeong.destiny.crucible.CrucibleRuntime;
import kim.biryeong.destiny.crucible.CrucibleWorld;
import kim.biryeong.destiny.guardian.Element;
import kim.biryeong.destiny.world.TowerSpawnWorld;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.level.GameType;
import net.minecraft.world.phys.Vec3;
import java.util.ArrayList;
import java.util.List;
import java.util.Set;

/** Run alone in the owned tower-enabled QA server; it owns the singleton session. */
public final class CrucibleW260GameTests {
    private static void check(GameTestHelper h, boolean value, String message) {
        h.assertTrue(value, Component.literal(message));
    }

    private static final class Login {
        final ServerPlayer initial;
        final io.netty.channel.embedded.EmbeddedChannel channel;
        net.minecraft.world.entity.PositionMoveRotation clientPose;
        Login(ServerPlayer initial, io.netty.channel.embedded.EmbeddedChannel channel) {
            this.initial=initial;this.channel=channel;
            clientPose=net.minecraft.world.entity.PositionMoveRotation.of(initial);
        }
        ServerPlayer initial() { return initial; }
        io.netty.channel.embedded.EmbeddedChannel channel() { return channel; }
    }
    private static ServerPlayer login(GameTestHelper h, List<Login> logins, String name, Element element) {
        check(h,name.length()<=16,"Fixture profile respects protocol username length");
        var server=h.getLevel().getServer();
        var profile=new com.mojang.authlib.GameProfile(java.util.UUID.randomUUID(),name);
        var cookie=net.minecraft.server.network.CommonListenerCookie.createInitial(profile,false);
        var p=new ServerPlayer(server,h.getLevel(),profile,cookie.clientInformation());
        p.setPos(h.absoluteVec(new Vec3(2,1,2)));
        var connection=new net.minecraft.network.Connection(net.minecraft.network.protocol.PacketFlow.SERVERBOUND);
        var channel=new io.netty.channel.embedded.EmbeddedChannel(connection);
        logins.add(new Login(p,channel));
        TestPacketContexts.initialize(connection,server,profile);
        server.getPlayerList().placeNewPlayer(connection,p,cookie);
        p.connection.handleAcceptPlayerLoad(new net.minecraft.network.protocol.game.ServerboundPlayerLoadedPacket());
        TowerSpawnWorld.tick(server);
        var data=kim.biryeong.destiny.guardian.Guardians.data(p);
        data.setGuardianClass(kim.biryeong.destiny.guardian.GuardianClass.HUNTER);
        data.setLoadout(kim.biryeong.destiny.guardian.GuardianClass.HUNTER,
                kim.biryeong.destiny.ability.hunter.HunterAbilities.preset(element));
        return p;
    }

    /** Emulate only the network acknowledgements a real client sends after teleport/respawn.
     * CameraViews uses negative synthetic teleport IDs; those must not move the server body.
     */
    private static void acknowledge(Login login, ServerPlayer player, Object packet) {
        if (packet instanceof net.minecraft.network.protocol.BundlePacket<?> bundle) {
            for (var child : bundle.subPackets()) acknowledge(login,player,child);
        } else if (packet instanceof net.minecraft.network.protocol.game.ClientboundPlayerPositionPacket position
                && position.id() >= 0) {
            login.clientPose=net.minecraft.world.entity.PositionMoveRotation.calculateAbsolute(
                    login.clientPose,position.change(),position.relatives());
            var at=login.clientPose.position();
            player.connection.handleAcceptTeleportPacket(
                    new net.minecraft.network.protocol.game.ServerboundAcceptTeleportationPacket(position.id(),
                            at.x,at.y,at.z,login.clientPose.yRot(),login.clientPose.xRot()));
        } else if (packet instanceof net.minecraft.network.protocol.common.ClientboundKeepAlivePacket keepAlive) {
            player.connection.handleKeepAlive(new net.minecraft.network.protocol.common.ServerboundKeepAlivePacket(keepAlive.getId()));
        } else if (packet instanceof net.minecraft.network.protocol.game.ClientboundChunkBatchFinishedPacket) {
            player.connection.handleChunkBatchReceived(new net.minecraft.network.protocol.game.ServerboundChunkBatchReceivedPacket(64f));
        } else if (packet instanceof net.minecraft.network.protocol.game.ClientboundRespawnPacket) {
            player.connection.handleAcceptPlayerLoad(new net.minecraft.network.protocol.game.ServerboundPlayerLoadedPacket());
        }
    }
    private static void tickLogin(net.minecraft.server.MinecraftServer server, Login login) {
        var player=server.getPlayerList().getPlayer(login.initial().getUUID());
        if(player!=null && !player.hasDisconnected()) player.connection.tick();
        login.channel().runPendingTasks();
        Object packet;
        while((packet=login.channel().readOutbound())!=null) {
            try { if(player!=null && !player.hasDisconnected()) acknowledge(login,player,packet); }
            finally { io.netty.util.ReferenceCountUtil.release(packet); }
        }
    }

    /** QA recovery only. Sends the ordinary respawn handler action; never claims OS/native input. */
    @GameTest(structure="destiny-test:floor", environment="destiny-test:w90_isolated", maxTicks=80, manualOnly=true)
    public void recoverOwnedVisionClient(GameTestHelper h) {
        var server=h.getLevel().getServer();
        check(h,server.getPort()==25611,"Recovery is restricted to the owned isolated QA port");
        var player=server.getPlayerList().getPlayerByName("WeaponW129QA");
        check(h,player!=null && player.isDeadOrDying(),"Owned QA player must be at the death screen");
        player.connection.handleClientCommand(new net.minecraft.network.protocol.game.ServerboundClientCommandPacket(
                net.minecraft.network.protocol.game.ServerboundClientCommandPacket.Action.PERFORM_RESPAWN));
        h.runAfterDelay(20,()->{
            var next=server.getPlayerList().getPlayerByName("WeaponW129QA");
            check(h,next!=null && next.isAlive() && TowerSpawnWorld.isTower(next.level()),"QA player respawns into Tower");
            h.succeed();
        });
    }

    /** Visible counterpart for the real Vision client; server fixtures are not native-input evidence. */
    @GameTest(structure="destiny-test:floor", environment="destiny-test:w90_isolated", maxTicks=6010, manualOnly=true)
    public void visualCounterpartForOwnedVisionClient(GameTestHelper h) {
        var server=h.getLevel().getServer();
        check(h,CrucibleRuntime.snapshot().members().size()==1,"Real QA viewer must join alone first");
        var logins=new ArrayList<Login>();
        TestCleanup.register(h,()->{
            for(var login:logins) {
                var current=server.getPlayerList().getPlayer(login.initial().getUUID());
                if(current!=null) {
                    CrucibleRuntime.leave(current,true);
                    current.connection.disconnect(Component.literal("Visual counterpart complete"));
                }
                login.channel().finishAndReleaseAll();
                kim.biryeong.destiny.guardian.Guardians.forget(login.initial());
            }
        });
        var p=login(h,logins,"ControlVisionBot",Element.ARC);
        check(h,CrucibleRuntime.join(p),"Counterpart joins the real session");
        var ally=login(h,logins,"ControlAllyQA",Element.ARC);
        check(h,CrucibleRuntime.join(ally),"Friendly counterpart joins the real session");
        // Fill the authored three-per-team intro, including the real client's own actor.
        for (String name : List.of("ControlBravo2", "ControlAlpha3", "ControlBravo3")) {
            check(h,CrucibleRuntime.join(login(h,logins,name,Element.ARC)),"Additional intro counterpart joins");
        }
        h.onEachTick(()->{
            for(var login:logins) {
                tickLogin(server,login);
                var current=server.getPlayerList().getPlayer(login.initial().getUUID());
                if(current!=null && current.isAlive()) current.connection.handleMovePlayer(
                        new net.minecraft.network.protocol.game.ServerboundMovePlayerPacket.Rot(
                                current.getYRot(),current.getXRot(),current.onGround(),false));
            }
        });
        h.runAfterDelay(6000,h::succeed);
    }

    @GameTest(structure="destiny-test:floor", environment="destiny-test:w90_isolated", maxTicks=1520, manualOnly=true)
    public void towerJoinMidMatchCaptureDamageRespawnAndReturn(GameTestHelper h) {
        check(h, CrucibleRuntime.snapshot().members().isEmpty(), "Fixture requires an empty session");
        var server = h.getLevel().getServer();
        var tower = TowerSpawnWorld.open(server);
        List<Login> logins = new ArrayList<>();
        List<ServerPlayer> owned = new ArrayList<>();
        TestCleanup.register(h, () -> {
            for (var login : logins) {
                var current = server.getPlayerList().getPlayer(login.initial().getUUID());
                if (current != null) {
                    CrucibleRuntime.leave(current,true);
                    current.connection.disconnect(Component.literal("Control QA cleanup"));
                }
                login.channel().finishAndReleaseAll();
                kim.biryeong.destiny.guardian.Guardians.forget(login.initial());
            }
        });
        var a=login(h,logins,"ControlQA_A",Element.SOLAR);owned.add(a);
        var b=login(h,logins,"ControlQA_B",Element.ARC);owned.add(b);
        h.onEachTick(() -> {
            for(var login:logins) {
                tickLogin(server,login);
            }
        });
        check(h, TowerSpawnWorld.teleport(a) && TowerSpawnWorld.teleport(b), "Both fixtures start in Tower");
        var board = server.getScoreboard();
        var previous = board.addPlayerTeam("control_qa_previous");
        board.addPlayerToTeam(a.getScoreboardName(),previous);
        TestCleanup.register(h, () -> board.removePlayerTeam(previous));
        check(h, CrucibleRuntime.join(a) && CrucibleRuntime.join(b), "Tower to Control join succeeds");
        check(h, a.level() == b.level() && CrucibleWorld.isArena(a.level()), "One shared arena");
        check(h, a.gameMode() == GameType.ADVENTURE && !CrucibleRuntime.canAct(a), "Waiting/intro suppresses combat");

        h.runAfterDelay(450, () -> {
            check(h, CrucibleRuntime.snapshot().phase() == ControlMatch.Phase.PLAYING, "Original-length intro ends in play");
            var before = CrucibleRuntime.snapshot();
            var c = login(h,logins,"ControlQA_C",Element.VOID); owned.add(c);
            check(h, CrucibleRuntime.join(c), "Late join accepted");
            check(h, CrucibleRuntime.snapshot().round() == before.round()
                    && CrucibleRuntime.snapshot().remainingTicks() == before.remainingTicks(), "Late join never resets round or clock");
            check(h, CrucibleRuntime.team(a) == CrucibleRuntime.team(c), "Late join fills smaller team");
            check(h, !CrucibleRuntime.canFight(a,c) && CrucibleRuntime.canFight(a,b), "Friendly and enemy combat are distinct");
            float allyHealth = c.getHealth();
            Combat.damage(a,c,100,Element.ARC);
            check(h,c.getHealth()==allyHealth,"Actual friendly damage is rejected");
            var zone = CrucibleWorld.open(server).zones().getFirst();
            var at = zone.position();
            a.teleportTo(a.level(),at.x,at.y,at.z,Set.of(),0,0,false);
        });
        h.runAfterDelay(560, () -> {
            var snapshot = CrucibleRuntime.snapshot();
            check(h,snapshot.zones().get("A").owner()==CrucibleRuntime.team(a),"Physical occupancy captures A");
            check(h,snapshot.scores().get(CrucibleRuntime.team(a))>=1,"Capture awards team score");
            int score = snapshot.scores().get(CrucibleRuntime.team(a));
            Combat.damage(a,b,10000,Element.SOLAR);
            check(h,b.isDeadOrDying(),"Actual enemy damage kills; hp="+b.getHealth()+" canFight="+CrucibleRuntime.canFight(a,b)+" removed="+b.isRemoved());
            check(h,CrucibleRuntime.snapshot().scores().get(CrucibleRuntime.team(a))==score+1,"Death callback awards one kill once");
        });
        h.runAfterDelay(670, () -> {
            var next = server.getPlayerList().getPlayer(b.getUUID());
            check(h,next!=null && next!=b && next.isAlive(),"Five-second runtime respawn creates a living replacement");
            check(h,next.connection.getPlayer()==next,"Respawn network listener points at the living replacement");
            check(h,CrucibleRuntime.participating(next) && CrucibleWorld.isArena(next.level()),"Respawn retains membership and arena");
            check(h,TowerSpawnWorld.isSafeArrival(next.level(),next.position()),"Respawn reaches an actual safe arena floor; pos="+next.position()+" level="+next.level().dimension().identifier());
            check(h,!CrucibleRuntime.canFight(a,next),"Respawn protection rejects incoming damage");
            for (var original : List.copyOf(owned)) {
                if (original == a) continue;
                var current = server.getPlayerList().getPlayer(original.getUUID());
                var p = current == null ? original : current;
                check(h,CrucibleRuntime.leave(p,true),"Leave succeeds");
                check(h,p.level()==tower && p.gameMode()==GameType.SURVIVAL,"Leave restores Tower and original mode");
            }
            check(h,CrucibleRuntime.snapshot().members().size()==1,"One participant remains for forfeit/result lifecycle");
        });
        h.runAfterDelay(1280, () -> {
            var snap=CrucibleRuntime.snapshot();
            check(h,snap.phase()==ControlMatch.Phase.RESULTS && snap.winner()==CrucibleRuntime.team(a)
                    && snap.endReason()==ControlMatch.EndReason.FORFEIT,"Empty opposing team expires into an authoritative victory");
            check(h,!CrucibleRuntime.canAct(a),"Results freeze combat");
        });
        h.runAfterDelay(1490, () -> {
            check(h,a.level()==tower && a.gameMode()==GameType.SURVIVAL,"Result deadline automatically returns the winner to Tower");
            check(h,a.getTeam()==previous,"Original scoreboard team restored");
            check(h,CrucibleRuntime.snapshot().members().isEmpty()
                    && CrucibleRuntime.snapshot().phase()==ControlMatch.Phase.WAITING,"Result return clears session");
            h.succeed();
        });
    }
}
