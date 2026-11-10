package kim.biryeong.destiny.world;

import net.fabricmc.fabric.api.entity.event.v1.ServerEntityLevelChangeEvents;
import net.fabricmc.fabric.api.entity.event.v1.ServerPlayerEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerLifecycleEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerLevelEvents;
import net.fabricmc.fabric.api.networking.v1.ServerPlayConnectionEvents;
import net.minecraft.network.protocol.game.ClientboundSetChunkCacheRadiusPacket;
import net.minecraft.network.protocol.game.ClientboundSetSimulationDistancePacket;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.server.network.ServerGamePacketListenerImpl;

import java.util.IdentityHashMap;
import java.util.Map;

/** Limits only explicitly registered Destiny-owned levels. Public-world/server settings are never changed. */
public final class DestinyWorldDistances {
    private static final Limits CONFIG = parse(System.getProperty("destiny.world.viewDistance"),
            System.getProperty("destiny.world.simulationDistance"));
    private static final Map<MinecraftServer, State> SERVERS = new IdentityHashMap<>();
    private static boolean initialized;

    static record Limits(int view, int simulation) { }
    private record WorldState(int view, int simulation) { }
    private record Sent(ServerPlayer player, ServerLevel level, int view, int simulation) { }
    private static final class State {
        final Map<ServerLevel, WorldState> levels = new IdentityHashMap<>();
        final Map<ServerGamePacketListenerImpl, Sent> sent = new IdentityHashMap<>();
    }

    private DestinyWorldDistances() { }

    static Limits parse(String view, String simulation) {
        return new Limits(setting(view, 8), setting(simulation, 6));
    }

    private static int setting(String value, int fallback) {
        try { return Math.clamp(Integer.parseInt(value), 2, 32); }
        catch (NumberFormatException e) { return fallback; }
    }

    public static int configuredViewDistance() { return CONFIG.view; }
    public static int configuredSimulationDistance() { return CONFIG.simulation; }

    public static void init() {
        if (initialized) return;
        initialized = true;
        ServerPlayConnectionEvents.JOIN.register((handler, sender, server) -> synchronize(handler.getPlayer()));
        ServerPlayConnectionEvents.DISCONNECT.register((handler, server) -> {
            var state = SERVERS.get(server);
            if (state != null) state.sent.remove(handler);
        });
        ServerPlayerEvents.AFTER_RESPAWN.register((oldPlayer, newPlayer, alive) -> synchronize(newPlayer, true));
        ServerEntityLevelChangeEvents.AFTER_PLAYER_CHANGE_LEVEL.register((player, origin, destination) -> synchronize(player));
        ServerLevelEvents.UNLOAD.register(DestinyWorldDistances::unloaded);
        ServerLifecycleEvents.SERVER_STOPPED.register(SERVERS::remove);
    }

    /** Call immediately after opening an owned Fantasy level, before placement, warmup or admission. */
    public static void manage(ServerLevel level) {
        var server = level.getServer();
        if (!server.isSameThread()) throw new IllegalStateException("World distances require the server thread");
        var state = SERVERS.computeIfAbsent(server, ignored -> new State());
        if (state.levels.containsKey(level)) return;
        int view = Math.min(CONFIG.view, Math.clamp(server.getPlayerList().getViewDistance(), 2, 32));
        int simulation = Math.min(view, Math.min(CONFIG.simulation,
                Math.clamp(server.getPlayerList().getSimulationDistance(), 2, 32)));
        state.levels.put(level, new WorldState(view, simulation));
        level.getChunkSource().setViewDistance(server.getPlayerList().getViewDistance());
        level.getChunkSource().setSimulationDistance(server.getPlayerList().getSimulationDistance());
    }

    public static boolean managed(ServerLevel level) { return world(level) != null; }

    private static WorldState world(ServerLevel level) {
        var state = SERVERS.get(level.getServer());
        return state == null ? null : state.levels.get(level);
    }

    /** The proposed native setter argument is already global/server-authoritative. Never increase it. */
    public static int viewDistance(ServerLevel level, int proposed) {
        return managed(level) ? Math.min(CONFIG.view, Math.clamp(proposed, 2, 32)) : proposed;
    }

    public static int simulationDistance(ServerLevel level, int proposed) {
        var world = world(level);
        return world == null ? proposed : Math.min(world.view, Math.min(CONFIG.simulation, Math.clamp(proposed, 2, 32)));
    }

    /** Effective native per-level radius; callers must not substitute PlayerList's global radius. */
    public static int effectiveViewDistance(ServerLevel level) {
        var world = world(level);
        return world == null ? level.getServer().getPlayerList().getViewDistance() : world.view;
    }

    public static int effectiveViewDistance(ServerPlayer player) {
        return Math.clamp(player.requestedViewDistance(), 2, effectiveViewDistance(player.level()));
    }

    public static int effectiveSimulationDistance(ServerLevel level) {
        var world = world(level);
        return world == null ? level.getServer().getPlayerList().getSimulationDistance() : world.simulation;
    }

    /** Called after the native per-level setter, including PlayerList's global-setting rewrite. */
    public static void viewDistanceChanged(ServerLevel level, int applied) {
        var state = SERVERS.get(level.getServer());
        var old = state == null ? null : state.levels.get(level);
        if (old == null) return;
        state.levels.put(level, new WorldState(Math.clamp(applied, 2, 32), old.simulation));
        int simulation = simulationDistance(level, level.getServer().getPlayerList().getSimulationDistance());
        if (simulation != old.simulation) {
            level.getChunkSource().setSimulationDistance(simulation);
        } else {
            correctClients(level);
        }
    }

    public static void simulationDistanceChanged(ServerLevel level, int applied) {
        var state = SERVERS.get(level.getServer());
        var old = state == null ? null : state.levels.get(level);
        if (old == null) return;
        state.levels.put(level, new WorldState(old.view, applied));
        correctClients(level);
    }

    private static void correctClients(ServerLevel level) {
        // PlayerList already broadcast its global value. A cached effective value still needs correction.
        for (var player : level.players()) synchronize(player, true);
    }

    public static void synchronize(ServerPlayer player) { synchronize(player, false); }

    private static void synchronize(ServerPlayer player, boolean force) {
        var state = SERVERS.get(player.level().getServer());
        if (state == null) return;
        var connection = player.connection;
        if (player.hasDisconnected()) { state.sent.remove(connection); return; }
        var previous = state.sent.get(connection);
        boolean managed = state.levels.containsKey(player.level());
        if (!managed && previous == null) return;
        int view = effectiveViewDistance(player.level()), simulation = effectiveSimulationDistance(player.level());
        if (force || previous == null || previous.player != player || previous.level != player.level()
                || previous.view != view || previous.simulation != simulation) {
            connection.send(new ClientboundSetChunkCacheRadiusPacket(view));
            connection.send(new ClientboundSetSimulationDistancePacket(simulation));
        }
        if (managed) state.sent.put(connection, new Sent(player, player.level(), view, simulation));
        else state.sent.remove(connection); // Public-world distance has been restored; retain no connection ownership.
    }

    private static void unloaded(MinecraftServer server, ServerLevel level) {
        var state = SERVERS.get(server);
        if (state == null) return;
        state.levels.remove(level);
        state.sent.values().removeIf(sent -> sent.level == level);
        if (state.levels.isEmpty() && state.sent.isEmpty()) SERVERS.remove(server, state);
    }
}
