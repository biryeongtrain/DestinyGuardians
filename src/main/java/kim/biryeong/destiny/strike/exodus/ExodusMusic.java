package kim.biryeong.destiny.strike.exodus;

import com.google.gson.JsonParser;
import kim.biryeong.destiny.DestinyGuardians;
import kim.biryeong.minigamelib.MinigameLib;
import kim.biryeong.minigamelib.Playback;
import kim.biryeong.minigamelib.music.MusicPacks;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundSource;

import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.*;

/**
 * Exodus Crash's score: the extracted stems carry no section structure, so they are grouped by loudness into four
 * tiers (travel, combat, intense, climax) and each player hears a shuffled run of clips from the tier the encounter
 * asks for. A tier change cuts to the new tier at once; within a tier the next clip starts when the last one ends.
 */
final class ExodusMusic implements AutoCloseable {
    private record Clip(String event, double seconds) { }
    private static final List<List<Clip>> TIERS = load();
    private static final class Listener {
        Playback playback; int tier = -1; long endsAt; Clip last;
    }
    private final Map<ServerPlayer, Listener> listeners = new IdentityHashMap<>();
    private final Random random = new Random();

    static int section(ExodusPlan.BeatKind kind, boolean active, boolean complete) {
        if (complete) return 0;
        if (!active) return 0;
        return switch (kind) { case ADVANCE -> 0; case COMBAT -> 1; case CHARGE, DEFEND -> 2; case BOSS -> 3; };
    }
    private static List<List<Clip>> load() {
        try (var in = Objects.requireNonNull(ExodusMusic.class.getResourceAsStream("/destiny/exodus_crash/music.json"));
             var reader = new InputStreamReader(in, StandardCharsets.UTF_8)) {
            var result = new ArrayList<List<Clip>>();
            for (var tier : JsonParser.parseReader(reader).getAsJsonObject().getAsJsonArray("tiers")) {
                var clips = new ArrayList<Clip>();
                for (var c : tier.getAsJsonArray()) clips.add(new Clip(c.getAsJsonObject().get("event").getAsString(), c.getAsJsonObject().get("seconds").getAsDouble()));
                result.add(List.copyOf(clips));
            }
            return List.copyOf(result);
        } catch (Exception e) { throw new IllegalStateException("Invalid Exodus score", e); }
    }

    /** @param desired tier 0..3 (the boss tier also draws on the intense tier), negative for silence */
    void tick(int desired, List<ServerPlayer> audience, long now) {
        if (desired < 0) { close(); return; }
        var ready = audience.stream().filter(p -> !p.hasDisconnected() && p.connection.hasClientLoaded() && MusicPacks.ready(p)).toList();
        for (var p : List.copyOf(listeners.keySet())) if (!ready.contains(p)) remove(p);
        for (var p : ready) {
            var l = listeners.computeIfAbsent(p, k -> new Listener());
            if (l.tier == desired && now < l.endsAt) continue;
            if (l.playback != null) { l.playback.stop(); l.playback = null; }
            var pool = new ArrayList<>(TIERS.get(desired));
            if (desired == 3) pool.addAll(TIERS.get(2));
            if (pool.size() > 1) pool.remove(l.last);
            if (pool.isEmpty()) continue;
            var clip = pool.get(random.nextInt(pool.size()));
            l.tier = desired; l.last = clip; l.endsAt = now + (long) (clip.seconds() * 1_000_000_000L);
            l.playback = MinigameLib.get(p.level().getServer()).music().playSound(
                    Identifier.fromNamespaceAndPath("destiny_exodus_music", clip.event()), clip.seconds(), 1f, List.of(p), true, SoundSource.RECORDS);
            DestinyGuardians.LOGGER.info("[Exodus music] player={} tier={} clip={}", p.getScoreboardName(), desired, clip.event());
        }
    }
    void remove(ServerPlayer p) { var l = listeners.remove(p); if (l != null && l.playback != null) l.playback.stop(); }
    @Override public void close() { listeners.values().forEach(l -> { if (l.playback != null) l.playback.stop(); }); listeners.clear(); }
}
