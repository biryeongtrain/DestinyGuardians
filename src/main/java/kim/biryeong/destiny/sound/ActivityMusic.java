package kim.biryeong.destiny.sound;

import com.google.gson.JsonParser;
import kim.biryeong.destiny.DestinyGuardians;
import kim.biryeong.destiny.crucible.CrucibleRuntime;
import kim.biryeong.destiny.crucible.ControlMatch;
import kim.biryeong.destiny.world.TowerSpawnWorld;
import kim.biryeong.minigamelib.cinematic.CameraViews;
import kim.biryeong.minigamelib.MinigameLib;
import kim.biryeong.minigamelib.Playback;
import kim.biryeong.minigamelib.music.MusicPacks;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerLifecycleEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.fabricmc.fabric.api.networking.v1.ServerPlayConnectionEvents;
import net.minecraft.network.protocol.game.ClientboundStopSoundPacket;
import net.minecraft.resources.Identifier;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundSource;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.*;

/** Personal MUSIC channel for hub and match transitions; no client mod required. */
public final class ActivityMusic {
    private static final Map<MusicSequence.Scene,List<MusicSequence.Track>> PLAYLISTS = load();
    private static final Map<UUID,Listener> LISTENERS = new HashMap<>();
    private static final boolean TRACE = Boolean.getBoolean("destiny.sound.qa");
    private static boolean initialized;
    private static final class Listener {
        final ServerPlayer player;
        final MusicSequence sequence = new MusicSequence();
        Identifier sounding;
        Playback playback;
        Listener(ServerPlayer player) { this.player = player; }
    }
    private ActivityMusic() { }
    public static void init() {
        if (initialized) return;
        initialized = true;
        ServerTickEvents.END_SERVER_TICK.register(ActivityMusic::tick);
        ServerPlayConnectionEvents.DISCONNECT.register((handler, server) -> remove(handler.getPlayer()));
        ServerLifecycleEvents.SERVER_STOPPING.register(server -> {
            for (var listener : List.copyOf(LISTENERS.values())) stop(listener);
            LISTENERS.clear();
        });
    }
    private static Map<MusicSequence.Scene,List<MusicSequence.Track>> load() {
        var result = new EnumMap<MusicSequence.Scene,List<MusicSequence.Track>>(MusicSequence.Scene.class);
        var stream = ActivityMusic.class.getResourceAsStream("/data/destiny/activity_music.json");
        if (stream == null) throw new IllegalStateException("Missing activity music catalog");
        try (var reader = new InputStreamReader(stream, StandardCharsets.UTF_8)) {
            var root = JsonParser.parseReader(reader).getAsJsonObject();
            for (var scene : MusicSequence.Scene.values()) {
                var rows = new ArrayList<MusicSequence.Track>();
                if (scene != MusicSequence.Scene.NONE) for (var entry : root.getAsJsonArray(scene.name().toLowerCase(Locale.ROOT))) {
                    var row = entry.getAsJsonObject();
                    rows.add(new MusicSequence.Track(row.get("event").getAsString(), row.get("seconds").getAsDouble(), row.get("volume").getAsFloat()));
                }
                if (scene != MusicSequence.Scene.NONE && rows.isEmpty()) throw new IllegalStateException("Empty music scene " + scene);
                result.put(scene, List.copyOf(rows));
            }
        } catch (java.io.IOException e) { throw new IllegalStateException(e); }
        return Map.copyOf(result);
    }
    static MusicSequence.Scene scene(boolean tower, boolean participant, ControlMatch.Phase phase) {
        if (participant) return switch (phase) {
            case INTRO -> MusicSequence.Scene.INTRO;
            case RESULTS -> MusicSequence.Scene.RESULTS;
            default -> MusicSequence.Scene.NONE;
        };
        return tower ? MusicSequence.Scene.TOWER : MusicSequence.Scene.NONE;
    }
    private static void tick(MinecraftServer server) {
        long now = System.nanoTime();
        var phase = CrucibleRuntime.snapshot().phase();
        for (ServerPlayer player : server.getPlayerList().getPlayers()) {
            var old = LISTENERS.get(player.getUUID());
            // Native respawn replaces ServerPlayer, including the entity sound anchor.
            if (old != null && old.player != player) { stop(old); LISTENERS.remove(player.getUUID()); }
            var listener = LISTENERS.computeIfAbsent(player.getUUID(), id -> new Listener(player));
            var desired = scene(TowerSpawnWorld.isTower(player.level()), CrucibleRuntime.participating(player), phase);
            boolean ready = !player.hasDisconnected() && player.connection.hasClientLoaded() && MusicPacks.ready(player);
            var change = listener.sequence.update(desired, PLAYLISTS.get(desired), ready, listener.playback == null || listener.playback.done(), now);
            if (change.stop()) stop(listener);
            if (change.play() != null) play(listener, change.play());
            // These void-biome worlds otherwise schedule vanilla overworld/creative music.
            // Only stop those built-in events, never the custom MUSIC channel or VOICE.
            if (desired != MusicSequence.Scene.NONE && ready && server.getTickCount() % 20 == 0)
                for (String vanilla : List.of("music.game", "music.creative", "music.under_water"))
                    CameraViews.send(player, new ClientboundStopSoundPacket(Identifier.withDefaultNamespace(vanilla), SoundSource.MUSIC));
        }
    }
    private static void play(Listener listener, MusicSequence.Track track) {
        var p = listener.player;
        var sound = Identifier.fromNamespaceAndPath("destiny_music", track.event());
        listener.playback = MinigameLib.get(p.level().getServer()).music().playSound(
                sound, track.seconds(), track.volume(), List.of(p), true);
        listener.sounding = sound;
        if (TRACE) DestinyGuardians.LOGGER.info("[W262 music] player={} play={} scene={} api=minigame-lib", p.getScoreboardName(), sound, listener.sequence.scene());
    }
    private static void stop(Listener listener) {
        if (listener.sounding == null) return;
        if (listener.playback != null) listener.playback.stop();
        listener.playback = null;
        if (TRACE) DestinyGuardians.LOGGER.info("[W262 music] player={} stop={}", listener.player.getScoreboardName(), listener.sounding);
        listener.sounding = null;
    }
    private static void remove(ServerPlayer p) {
        var listener = LISTENERS.remove(p.getUUID());
        if (listener != null) stop(listener);
    }
    /** Observation for server QA, not an assertion of audible output. */
    public static String current(ServerPlayer p) {
        var listener = LISTENERS.get(p.getUUID());
        return listener == null || listener.sounding == null ? "" : listener.sounding.toString();
    }
}
