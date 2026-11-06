package kim.biryeong.destiny.test;

import com.mojang.authlib.GameProfile;
import io.netty.channel.embedded.EmbeddedChannel;
import kim.biryeong.destiny.campaign.RisingCampaign;
import kim.biryeong.destiny.campaign.RisingMission;
import kim.biryeong.destiny.fireteam.ActivityCatalog;
import kim.biryeong.destiny.fireteam.Fireteams;
import kim.biryeong.destiny.tutorial.Tutorial;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.Connection;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.PacketFlow;
import net.minecraft.network.protocol.game.*;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.server.network.CommonListenerCookie;
import net.minecraft.world.phys.Vec3;
import java.util.*;

/** Real shared launch controller + real connection packets; no native-client/audio-engine acceptance claim. */
public final class ActivityLaunchW329GameTests {
    private static final String FLOOR = "destiny-test:floor", ENV = "destiny-test:w90_isolated";
    private static void check(GameTestHelper h, boolean value, String why) { h.assertTrue(value, Component.literal(why)); }
    private static Object call(Class<?> type, Object target, String name, Class<?>[] types, Object... args) {
        try { var m = type.getDeclaredMethod(name, types); m.setAccessible(true); return m.invoke(target, args); }
        catch (ReflectiveOperationException e) { throw new IllegalStateException(e); }
    }
    private static final class Login implements AutoCloseable {
        final ServerPlayer player; final EmbeddedChannel channel;
        final List<Integer> numbers = new ArrayList<>();
        int soundStarts, soundStops;
        int lastConnectionTick = Integer.MIN_VALUE;
        boolean closed;
        net.minecraft.world.entity.PositionMoveRotation clientPose;
        Login(GameTestHelper h) { this(h, UUID.randomUUID()); }
        Login(GameTestHelper h, UUID id) {
            var server = h.getLevel().getServer();
            var profile = new GameProfile(id, "Launch" + id.toString().substring(0, 8));
            var cookie = CommonListenerCookie.createInitial(profile, false);
            player = new ServerPlayer(server, h.getLevel(), profile, cookie.clientInformation());
            player.setPos(h.absoluteVec(new Vec3(2, 1, 2)));
            clientPose = net.minecraft.world.entity.PositionMoveRotation.of(player);
            player.setAttached(Tutorial.COMPLETED_REVISION, Tutorial.REQUIRED_REVISION);
            player.setAttached(RisingCampaign.COMPLETED_REVISION, RisingMission.REVISION);
            var connection = new Connection(PacketFlow.SERVERBOUND); channel = new EmbeddedChannel(connection);
            TestPacketContexts.initialize(connection, server, profile);
            server.getPlayerList().placeNewPlayer(connection, player, cookie);
            player.connection.handleAcceptPlayerLoad(new ServerboundPlayerLoadedPacket());
            kim.biryeong.destiny.world.TowerSpawnWorld.tick(server);
            player.setNoGravity(true); player.setDeltaMovement(Vec3.ZERO);
            drain(); TestCleanup.register(h, this::close);
        }
        void packet(Object packet) {
            if (packet instanceof net.minecraft.network.protocol.BundlePacket<?> bundle) {
                for (var child : bundle.subPackets()) packet(child);
            } else if (packet instanceof ClientboundPlayerPositionPacket position && position.id() >= 0) {
                clientPose = net.minecraft.world.entity.PositionMoveRotation.calculateAbsolute(clientPose, position.change(), position.relatives());
                var at = clientPose.position();
                player.connection.handleAcceptTeleportPacket(new ServerboundAcceptTeleportationPacket(position.id(),
                        at.x, at.y, at.z, clientPose.yRot(), clientPose.xRot()));
                player.connection.handleAcceptPlayerLoad(new ServerboundPlayerLoadedPacket());
            } else if (packet instanceof net.minecraft.network.protocol.common.ClientboundKeepAlivePacket keepAlive) {
                player.connection.handleKeepAlive(new net.minecraft.network.protocol.common.ServerboundKeepAlivePacket(keepAlive.getId()));
            } else if (packet instanceof ClientboundRespawnPacket) {
                player.connection.handleAcceptPlayerLoad(new ServerboundPlayerLoadedPacket());
            } else if (packet instanceof ClientboundChunkBatchFinishedPacket) {
                player.connection.handleChunkBatchReceived(new ServerboundChunkBatchReceivedPacket(64));
            } else if (packet instanceof ClientboundSoundPacket sound
                    && sound.getSound().value().location().getNamespace().equals("destiny_activity_launch")) soundStarts++;
            else if (packet instanceof ClientboundStopSoundPacket stop && stop.getName() != null
                    && stop.getName().getNamespace().equals("destiny_activity_launch")) soundStops++;
            else if (packet instanceof ClientboundSetTitleTextPacket title) {
                String text = title.text().getString();
                if (text.matches("[0-9]+")) numbers.add(Integer.parseInt(text));
            }
        }
        void drain() {
            int now = player.level().getServer().getTickCount();
            if (lastConnectionTick != now && player.level().getServer().getPlayerList().getPlayer(player.getUUID()) == player && !player.hasDisconnected()) {
                lastConnectionTick = now; player.connection.tick();
            }
            channel.runPendingTasks(); Object value;
            while ((value = channel.readOutbound()) != null) {
                try { packet(value); } finally { io.netty.util.ReferenceCountUtil.release(value); }
            }
        }
        @Override public void close() {
            if (closed) return;
            closed = true;
            var server = player.level().getServer();
            if (server.getPlayerList().getPlayer(player.getUUID()) == player) {
                Fireteams.leave(player, "test cleanup"); server.getPlayerList().remove(player);
            } else if (!player.isRemoved() && player.level().getEntity(player.getId()) == player)
                player.level().removePlayerImmediately(player, net.minecraft.world.entity.Entity.RemovalReason.DISCARDED);
            channel.finishAndReleaseAll();
        }
    }
    private static final class Fixture implements AutoCloseable {
        final Login login; final ActivityCatalog.Activity activity; final int started;
        int calls, launchTick = -1; boolean active, closed;
        Fixture(GameTestHelper h) {
            login = new Login(h); started = h.getLevel().getServer().getTickCount();
            String category = "launch_w329";
            if (ActivityCatalog.category(category).isEmpty()) ActivityCatalog.category(new ActivityCatalog.Category(category,
                    "Launch test", "fixture", "", "", 999));
            String id = "launch_" + UUID.randomUUID().toString().replace("-", "");
            activity = new ActivityCatalog.Activity(id, category, "Launch fixture", "fixture", "", "", "", 1, 1, 999,
                    new ActivityCatalog.Launcher() {
                        public String check(List<ServerPlayer> players) { return players.size() == 1 && players.getFirst() == login.player ? null : "wrong accepted identity"; }
                        public String launch(List<ServerPlayer> players) { calls++; launchTick = login.player.level().getServer().getTickCount(); active = true; return null; }
                        public boolean entered(ServerPlayer p) { return active && !closed && p == login.player; }
                        public boolean participating(ServerPlayer p) { return active && !closed && p == login.player; }
                    });
            ActivityCatalog.activity(activity); TestCleanup.register(h, this::close);
        }
        String play() { return (String) call(Fireteams.class, null, "play", new Class<?>[]{ServerPlayer.class, ActivityCatalog.Activity.class}, login.player, activity); }
        String cancel() { return (String) call(Fireteams.class, null, "cancel", new Class<?>[]{ServerPlayer.class}, login.player); }
        Object launch() {
            var team = Fireteams.team(login.player).orElseThrow();
            return ((Optional<?>) call(Fireteams.class, null, "launch", new Class<?>[]{team.getClass()}, team)).orElseThrow();
        }
        @Override public void close() { if (closed) return; closed = true; login.close(); }
    }

    @GameTest(structure=FLOOR, environment=ENV, maxTicks=160)
    public void acceptedButtonStartsOneCueThenFiveNumbersAndExactlyOneLaunchAtTick120(GameTestHelper h) {
        var f = new Fixture(h); h.onEachTick(f.login::drain);
        check(h, f.play() == null, "Accepted shared play action"); f.login.drain();
        check(h, f.login.soundStarts == 1 && f.login.numbers.isEmpty(), "Selected click+countdown cue starts once at0, no initial number");
        check(h, f.play() != null, "Duplicate accepted-button callback rejected"); f.login.drain();
        check(h, f.login.soundStarts == 1, "Duplicate callback cannot duplicate cue");
        h.runAfterDelay(19, () -> { f.login.drain(); check(h, f.login.numbers.isEmpty() && f.calls == 0, "First second is a visual lead-in"); });
        h.runAfterDelay(21, () -> { f.login.drain(); check(h, f.login.numbers.equals(List.of(5)), "Five appears after lead-in"); });
        h.runAfterDelay(119, () -> check(h, f.calls == 0, "No activity launch before120ticks"));
        h.runAfterDelay(130, () -> {
            f.login.drain();
            check(h, f.login.numbers.equals(List.of(5, 4, 3, 2, 1)), "Exactly5..1, with no0 or duplicated numbers");
            check(h, f.calls == 1 && f.launchTick - f.started == 120, "Actual adapter invoked once at120ticks");
            check(h, f.login.soundStarts == 1 && f.login.soundStops == 0, "Success lets full audio tail finish naturally"); h.succeed();
        });
    }

    @GameTest(structure=FLOOR, environment=ENV, maxTicks=70)
    public void cancelAndOldSessionCallbacksCannotStopAnotherLaunchOrLaunchAfterCancellation(GameTestHelper h) {
        var a = new Fixture(h); var b = new Fixture(h); h.onEachTick(() -> { a.login.drain(); b.login.drain(); });
        check(h, a.play() == null && b.play() == null, "Two independent accepted launches");
        Object old = a.launch();
        h.runAfterDelay(10, () -> {
            a.login.drain(); b.login.drain();
            check(h, a.login.soundStarts == 1 && b.login.soundStarts == 1, "Both independent cues were dispatched once before cancellation");
            check(h, a.cancel() == null, "Leader cancels during lead-in");
        });
        // Connection packet writes are asynchronous; allow one ordinary server flush before auditing exact stop counts.
        h.runAfterDelay(11, () -> {
            a.login.drain(); b.login.drain();
            check(h, a.login.soundStops == 1 && b.login.soundStops == 0,
                    "Only cancelling connection's exact event stopped; a=" + a.login.soundStops + " b=" + b.login.soundStops
                            + " starts=" + a.login.soundStarts + "/" + b.login.soundStarts);
        });
        h.runAfterDelay(12, () -> { check(h, a.play() == null, "Fresh launch after cancelled slot retires"); a.login.drain(); });
        h.runAfterDelay(14, () -> {
            call(old.getClass(), old, "abort", new Class<?>[]{});
            call(old.getClass(), old, "tick", new Class<?>[]{});
            a.login.drain(); b.login.drain();
            check(h, a.login.soundStarts == 2 && a.login.soundStops == 1 && b.login.soundStops == 0,
                    "Old session abort/tick cannot stop newer same-player cue or another player's cue");
            check(h, a.calls == 0 && b.calls == 0, "Cancelled old controller cannot start activity"); h.succeed();
        });
    }

    @GameTest(structure=FLOOR, environment=ENV, maxTicks=60)
    public void replacedConnectionInvalidatesCountdownAndOldButtonCannotActOnReplacement(GameTestHelper h) {
        var f = new Fixture(h); check(h, f.play() == null, "Initial exact connection accepted");
        var server = h.getLevel().getServer();
        server.getPlayerList().remove(f.login.player);
        var replacement = new Login(h, f.login.player.getUUID());
        h.onEachTick(() -> { f.login.drain(); replacement.drain(); });
        h.runAfterDelay(4, () -> {
            f.login.drain(); replacement.drain();
            check(h, f.play() != null, "Stale original entity cannot start a new launch for replacement UUID");
            check(h, f.calls == 0 && replacement.soundStarts == 0 && replacement.soundStops == 0 && replacement.numbers.isEmpty(),
                    "No old countdown/audio stop/title or launch is delivered to replacement connection"); h.succeed();
        });
    }
}
