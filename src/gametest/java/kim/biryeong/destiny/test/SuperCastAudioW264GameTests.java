package kim.biryeong.destiny.test;

import io.netty.channel.embedded.EmbeddedChannel;
import kim.biryeong.destiny.ability.AbilityService;
import kim.biryeong.destiny.ability.hunter.HunterAbilities;
import kim.biryeong.destiny.crucible.ControlMatch;
import kim.biryeong.destiny.crucible.CrucibleRuntime;
import kim.biryeong.destiny.crucible.CrucibleWorld;
import kim.biryeong.destiny.fx.ClassAbilityEffects;
import kim.biryeong.destiny.guardian.AbilitySlot;
import kim.biryeong.destiny.guardian.Element;
import kim.biryeong.destiny.guardian.GuardianClass;
import kim.biryeong.destiny.guardian.Guardians;
import kim.biryeong.destiny.sound.DestinySounds;
import kim.biryeong.destiny.sound.SuperCastSounds;
import kim.biryeong.destiny.world.TowerSpawnWorld;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.core.Holder;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.game.ClientboundSoundPacket;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.phys.Vec3;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;

/**
 * Manual, sequential, master-owned tower-enabled server only: owns the singleton Control session.
 * Actual PlayerList logins and outbound sound packets; not native client decode or acoustic evidence.
 * W263's private login/ack lifecycle is retained minimally; shared cleanup/context helpers are reused.
 */
public final class SuperCastAudioW264GameTests {
    private static final String CAST = "hunter.arc.super.start";
    private static final String MISSING = "w264.unmapped.super.start";

    private static void check(GameTestHelper h, boolean ok, String message) {
        h.assertTrue(ok, Component.literal(message));
    }

    private static final class Login {
        final ServerPlayer player;
        final EmbeddedChannel channel;
        final net.minecraft.network.Connection connection;
        net.minecraft.world.entity.PositionMoveRotation clientPose;

        Login(ServerPlayer player, EmbeddedChannel channel, net.minecraft.network.Connection connection) {
            this.player = player;
            this.channel = channel;
            this.connection = connection;
            clientPose = net.minecraft.world.entity.PositionMoveRotation.of(player);
        }
    }

    private static Login login(GameTestHelper h, List<Login> logins, String name) {
        check(h, name.length() <= 16, "Protocol username length");
        var server = h.getLevel().getServer();
        var profile = new com.mojang.authlib.GameProfile(java.util.UUID.randomUUID(), name);
        var cookie = net.minecraft.server.network.CommonListenerCookie.createInitial(profile, false);
        var player = new ServerPlayer(server, h.getLevel(), profile, cookie.clientInformation());
        player.setPos(h.absoluteVec(new Vec3(2, 1, 2)));
        var connection = new net.minecraft.network.Connection(net.minecraft.network.protocol.PacketFlow.SERVERBOUND);
        var channel = new EmbeddedChannel(connection);
        var login = new Login(player, channel, connection);
        logins.add(login);
        // Register before placeNewPlayer can fail; each connection has its own cleanup callback.
        TestCleanup.register(h, () -> {
            var current = server.getPlayerList().getPlayer(player.getUUID());
            try {
                if (current != null) {
                    try {
                        AbilityService.cleanup(current);
                    } finally {
                        try { CrucibleRuntime.leave(current, true); }
                        finally { current.connection.disconnect(Component.literal("W264 audio QA cleanup")); }
                    }
                }
            } finally {
                try { channel.finishAndReleaseAll(); }
                finally {
                    if (current != null && current != player) Guardians.forget(current);
                    Guardians.forget(player);
                }
            }
        });
        TestPacketContexts.initialize(connection, server, profile);
        server.getPlayerList().placeNewPlayer(connection, player, cookie);
        player.connection.handleAcceptPlayerLoad(new net.minecraft.network.protocol.game.ServerboundPlayerLoadedPacket());
        TowerSpawnWorld.tick(server);
        Guardians.data(player).setGuardianClass(GuardianClass.HUNTER);
        Guardians.data(player).setLoadout(GuardianClass.HUNTER, HunterAbilities.preset(Element.ARC));
        return login;
    }

    /** Bundle recursion also captures sounds; negative cinematic teleport IDs must not move the body. */
    private static void receive(Login login, Object packet, List<ClientboundSoundPacket> sounds) {
        var player = login.player;
        if (packet instanceof net.minecraft.network.protocol.BundlePacket<?> bundle) {
            for (var child : bundle.subPackets()) receive(login, child, sounds);
        } else if (packet instanceof ClientboundSoundPacket sound) {
            sounds.add(sound);
        } else if (packet instanceof net.minecraft.network.protocol.game.ClientboundPlayerPositionPacket position
                && position.id() >= 0) {
            login.clientPose = net.minecraft.world.entity.PositionMoveRotation.calculateAbsolute(
                    login.clientPose, position.change(), position.relatives());
            var at = login.clientPose.position();
            player.connection.handleAcceptTeleportPacket(
                    new net.minecraft.network.protocol.game.ServerboundAcceptTeleportationPacket(position.id(),
                            at.x, at.y, at.z, login.clientPose.yRot(), login.clientPose.xRot()));
        } else if (packet instanceof net.minecraft.network.protocol.common.ClientboundKeepAlivePacket keepAlive) {
            player.connection.handleKeepAlive(
                    new net.minecraft.network.protocol.common.ServerboundKeepAlivePacket(keepAlive.getId()));
        } else if (packet instanceof net.minecraft.network.protocol.game.ClientboundChunkBatchFinishedPacket) {
            player.connection.handleChunkBatchReceived(
                    new net.minecraft.network.protocol.game.ServerboundChunkBatchReceivedPacket(64f));
        } else if (packet instanceof net.minecraft.network.protocol.game.ClientboundRespawnPacket) {
            player.connection.handleAcceptPlayerLoad(new net.minecraft.network.protocol.game.ServerboundPlayerLoadedPacket());
        }
    }

    private static List<ClientboundSoundPacket> drain(GameTestHelper h, Login login) {
        var sounds = new ArrayList<ClientboundSoundPacket>();
        login.connection.flushChannel();
        login.channel.runPendingTasks();
        login.channel.flushOutbound();
        login.channel.checkException();
        for (int n = 0; n < 8192; n++) {
            Object packet = login.channel.readOutbound();
            if (packet == null) return sounds;
            try { receive(login, packet, sounds); }
            finally { io.netty.util.ReferenceCountUtil.release(packet); }
        }
        check(h, false, "Outbound drain exceeded bound; cannot claim an empty/complete sound sample");
        return sounds;
    }

    private static void keepConnected(GameTestHelper h, List<Login> logins) {
        h.onEachTick(() -> {
            for (var login : logins) {
                if (!login.player.hasDisconnected()) login.player.connection.tick();
                drain(h, login);
            }
        });
    }

    /** Each action and complete sample share one server tick; ambient/lifecycle queues are cleared first. */
    private static Map<Login, List<ClientboundSoundPacket>> sample(GameTestHelper h, List<Login> logins,
                                                                  Runnable action) {
        for (var login : logins) {
            check(h, !login.player.hasDisconnected() && login.channel.isActive()
                    && login.player.level().getServer().getPlayerList().getPlayer(login.player.getUUID()) == login.player,
                    "Every positive and negative recipient is a live registered login: " + login.player.getScoreboardName());
            drain(h, login);
        }
        action.run();
        var result = new LinkedHashMap<Login, List<ClientboundSoundPacket>>();
        for (var login : logins) result.put(login, drain(h, login));
        return result;
    }

    private static void none(GameTestHelper h, Map<Login, List<ClientboundSoundPacket>> packets, Login login) {
        check(h, packets.get(login).isEmpty(), "No sound for " + login.player.getScoreboardName()
                + "; received=" + packets.get(login).stream().map(p -> p.getSound().value().location()).toList());
    }

    private static void one(GameTestHelper h, Map<Login, List<ClientboundSoundPacket>> packets, Login login,
                            String event, Vec3 at, float volume, float pitch) {
        var received = packets.get(login);
        check(h, received.size() == 1, "Exactly one sound for " + login.player.getScoreboardName()
                + " / " + event + "; received=" + received.stream().map(p -> p.getSound().value().location()).toList());
        var actual = received.getFirst();
        // Use the native packet constructor solely for 1/8-block wire quantization, not production routing.
        var expected = new ClientboundSoundPacket(Holder.direct(SoundEvents.BEACON_ACTIVATE), SoundSource.PLAYERS,
                at.x, at.y, at.z, volume, pitch, 0L);
        check(h, actual.getSound().value().location().toString().equals(event), "Correct event: " + event);
        check(h, actual.getSource() == SoundSource.PLAYERS && actual.getVolume() == volume
                && actual.getPitch() == pitch, "Source/volume/pitch preserved for " + event);
        check(h, actual.getX() == expected.getX() && actual.getY() == expected.getY()
                && actual.getZ() == expected.getZ(), "Correct quantized XYZ for " + login.player.getScoreboardName()
                + " / " + event + "; expected origin=" + at
                + ", actual=" + actual.getX() + "," + actual.getY() + "," + actual.getZ());
    }

    private static void move(GameTestHelper h, Login login, ServerLevel level, Vec3 at) {
        check(h, login.player.teleportTo(level, at.x, at.y, at.z, Set.of(), 0, 0, false), "Fixture teleport succeeds");
        login.player.setDeltaMovement(Vec3.ZERO);
        login.player.fallDistance = 0;
        login.player.setNoGravity(true);
        drain(h, login);
        check(h, login.player.level() == level && login.player.position().distanceToSqr(at) < 1e-8,
                "Acknowledged fixture stays at its requested position");
    }

    private static void castAudience(GameTestHelper h, Map<Login, List<ClientboundSoundPacket>> packets,
                                     List<Login> players, Vec3 origin, String event, float volume, float pitch,
                                     boolean boundaryAlly) {
        one(h, packets, players.get(0), event, origin, volume, pitch);
        one(h, packets, players.get(1), event, players.get(1).player.getEyePosition(), volume, pitch);
        if (boundaryAlly) one(h, packets, players.get(2), event, origin, volume, pitch);
        else none(h, packets, players.get(2));
        one(h, packets, players.get(3), event, players.get(3).player.getEyePosition(), volume, pitch);
        none(h, packets, players.get(4));
        none(h, packets, players.get(5));
    }

    @GameTest(structure = "destiny-test:floor", environment = "destiny-test:w90_isolated",
            maxTicks = 540, manualOnly = true)
    public void matchCastRecipientsFallbackAndAbilityRoutes(GameTestHelper h) {
        check(h, CrucibleRuntime.snapshot().members().isEmpty(), "Requires exclusive empty Control session");
        var players = new ArrayList<Login>();
        for (String name : List.of("W264Caster", "W264NearEnemy", "W264EdgeAlly", "W264FarEnemy", "W264FarAlly")) {
            var login = login(h, players, name);
            check(h, TowerSpawnWorld.teleport(login.player) && CrucibleRuntime.join(login.player), "Real Control join");
        }
        var outsider = login(h, players, "W264Outsider");
        keepConnected(h, players);
        h.runAfterDelay(450, () -> {
            var owner = players.get(0).player;
            check(h, CrucibleRuntime.snapshot().phase() == ControlMatch.Phase.PLAYING
                    && CrucibleRuntime.canAct(owner) && CrucibleWorld.isArena(owner.level()), "Intro finished in actual arena");
            for (int i = 0; i < 5; i++) {
                check(h, CrucibleRuntime.participating(players.get(i).player)
                        && CrucibleRuntime.team(players.get(i).player) != null
                        && (CrucibleRuntime.team(players.get(i).player) == CrucibleRuntime.team(owner)) == (i % 2 == 0),
                        "Runtime assigned the expected alternating teams, index=" + i);
            }
            check(h, !CrucibleRuntime.participating(outsider.player), "Outsider never joined");
            Vec3 origin = new Vec3(.375, owner.getY() + 8, .625);
            double[] offsets = {-1, 4, 32, 64, -64, 2};
            for (int i = 0; i < players.size(); i++) move(h, players.get(i), owner.level(), origin.add(offsets[i], 0, 0));
            check(h, DestinySounds.has(CAST) && !DestinySounds.has(MISSING), "Mapped and missing branches are real");
            for (double distance : new double[]{31.875, 32, 32.125}) {
                move(h, players.get(2), owner.level(), origin.add(distance, 0, 0));
                var packets = sample(h, players, () -> SuperCastSounds.play(owner, origin, CAST,
                        SoundEvents.BEACON_ACTIVATE, .7f, .43f));
                castAudience(h, packets, players, origin, "destiny:" + CAST, .7f, 1f, distance <= 32);
            }
            move(h, players.get(2), owner.level(), origin.add(32, 0, 0));
            var fallback = sample(h, players, () -> SuperCastSounds.play(owner, origin, MISSING,
                    SoundEvents.BEACON_ACTIVATE, .7f, .43f));
            castAudience(h, fallback, players, origin, SoundEvents.BEACON_ACTIVATE.location().toString(), .7f, .43f, true);

            Guardians.data(owner).setGuardianClass(GuardianClass.WARLOCK);
            var nova = sample(h, players, () -> {
                ClassAbilityEffects.soundAt(owner, Element.VOID, "warlock/void_super", "super.start", origin);
                ClassAbilityEffects.soundAt(owner, Element.VOID, "warlock/void_super", "super.fire", origin);
            });
            castAudience(h, nova, players, origin, "destiny:warlock.void.super.start", .65f, 1f, true);
            Vec3 hit = origin.add(0, 0, 4);
            var impact = sample(h, players, () -> ClassAbilityEffects.soundAt(owner, Element.VOID,
                    "warlock/void_super", "super.impact", hit));
            for (int i : new int[]{0, 1, 5}) one(h, impact, players.get(i), "destiny:warlock.void.super.impact", hit, .65f, 1f);
            for (int i : new int[]{2, 3, 4}) none(h, impact, players.get(i));

            Guardians.data(owner).setGuardianClass(GuardianClass.HUNTER);
            var silentBlade = sample(h, players, () -> {
                ClassAbilityEffects.soundAt(owner, Element.SOLAR, "hunter/blade_barrage", "super.start", origin);
                ClassAbilityEffects.soundAt(owner, Element.SOLAR, "hunter/blade_barrage", "super.end", origin);
            });
            for (var login : players) none(h, silentBlade, login);
            var blade = sample(h, players, () -> ClassAbilityEffects.soundAt(owner, Element.SOLAR,
                    "hunter/blade_barrage", "super.fire", origin));
            castAudience(h, blade, players, origin, "destiny:hunter.solar.blade_barrage.fire", .65f, 1f, true);
            var fire = sample(h, players, () -> ClassAbilityEffects.soundAt(owner, Element.SOLAR,
                    "hunter/solar_super", "super.fire", hit));
            for (int i : new int[]{0, 1, 5}) one(h, fire, players.get(i), "destiny:hunter.solar.super.fire", hit, .65f, 1f);
            for (int i : new int[]{2, 3, 4}) none(h, fire, players.get(i));

            // Actual HunterSuper activation catches an unchanged direct start path, not just helper behavior.
            Vec3 hunterOrigin = owner.position();
            move(h, players.get(2), owner.level(), hunterOrigin.add(32, 0, 0));
            Guardians.data(owner).setSuperEnergy(1f);
            var hunter = sample(h, players, () -> check(h,
                    AbilityService.use(owner, AbilitySlot.SUPER) == AbilityService.Result.OK, "Real Hunter super accepted"));
            castAudience(h, hunter, players, hunterOrigin, "destiny:" + CAST, 1f, 1f, true);
            var busy = sample(h, players, () -> check(h,
                    AbilityService.use(owner, AbilitySlot.SUPER) == AbilityService.Result.BUSY, "Second activation rejected"));
            for (var login : players) none(h, busy, login);
            AbilityService.endSuper(owner);

            // Real cross-world transfer immediately leaves Control; do not fabricate stale membership.
            var departed = players.get(3);
            move(h, departed, h.getLevel(), origin);
            check(h, departed.player.level() != owner.level() && !CrucibleRuntime.participating(departed.player),
                    "Enemy transfer really changes dimension and performs normal match leave");
            var crossWorld = sample(h, players, () -> SuperCastSounds.play(owner, origin, CAST,
                    SoundEvents.BEACON_ACTIVATE, .7f, .43f));
            none(h, crossWorld, departed);
            one(h, crossWorld, players.get(1), "destiny:" + CAST, players.get(1).player.getEyePosition(), .7f, 1f);
            for (var login : players) if (CrucibleRuntime.participating(login.player))
                check(h, CrucibleRuntime.leave(login.player, true), "Normal owned participant leave");
            check(h, CrucibleRuntime.snapshot().members().isEmpty(), "Owned match is empty before cleanup");
            h.succeed();
        });
    }

    @GameTest(structure = "destiny-test:floor", environment = "destiny-test:w90_isolated",
            maxTicks = 40, manualOnly = true)
    public void pveCastKeepsNearbyOriginAndExcludesOtherDimension(GameTestHelper h) {
        check(h, CrucibleRuntime.snapshot().members().isEmpty(), "Run sequentially outside any Control session");
        var players = new ArrayList<Login>();
        for (String name : List.of("W264PveCaster", "W264PveEdge", "W264PveFar", "W264PveWorld")) login(h, players, name);
        var owner = players.getFirst().player;
        Vec3 origin = h.absoluteVec(new Vec3(2.375, 5, 2.625));
        move(h, players.get(0), h.getLevel(), origin.add(-1, 0, 0));
        move(h, players.get(1), h.getLevel(), origin.add(32, 0, 0));
        move(h, players.get(2), h.getLevel(), origin.add(32.125, 0, 0));
        var other = TowerSpawnWorld.open(h.getLevel().getServer());
        check(h, other != h.getLevel(), "Different-dimension control is genuinely a different level");
        move(h, players.get(3), other, origin);
        for (var login : players) check(h, !CrucibleRuntime.participating(login.player), "PvE fixture is not a match member");
        for (boolean mapped : new boolean[]{true, false}) {
            var packets = sample(h, players, () -> SuperCastSounds.play(owner, origin, mapped ? CAST : MISSING,
                    SoundEvents.BEACON_ACTIVATE, .7f, .43f));
            String event = mapped ? "destiny:" + CAST : SoundEvents.BEACON_ACTIVATE.location().toString();
            float pitch = mapped ? 1f : .43f;
            one(h, packets, players.get(0), event, origin, .7f, pitch);
            one(h, packets, players.get(1), event, origin, .7f, pitch);
            none(h, packets, players.get(2));
            none(h, packets, players.get(3));
        }
        h.succeed();
    }
}
