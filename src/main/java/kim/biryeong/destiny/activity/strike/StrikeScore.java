package kim.biryeong.destiny.activity.strike;

import com.google.gson.JsonObject;
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
import java.util.IdentityHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Random;

/**
 * Session-owned, bank-derived score for one strike run: a clock per listener over the strike's own score data, so
 * a late joiner enters the current section without restarting anyone else. No category-wide stop and no playlists
 * built from file names. The strike supplies the data and maps its phases to score sections.
 */
public final class StrikeScore implements AutoCloseable {
    /** @param resource classpath JSON ({@code sections}, {@code playlists}, {@code segments}, transition rules)
     *  @param namespace sound namespace of the segment events ({@code <namespace>:<segment event>})
     *  @param logTag    prefix of the per-listener start log line */
    public record Spec(String resource, String namespace, String logTag) {
        public Spec { Objects.requireNonNull(resource); Objects.requireNonNull(namespace); Objects.requireNonNull(logTag); }
    }
    private final JsonObject data;
    private final Spec spec;
    private final Map<ServerPlayer, Listener> listeners = new IdentityHashMap<>();
    private final long seed = new Random().nextLong();
    private static final class Listener {
        final ScoreTimeline timeline;
        Playback playback;
        Listener(JsonObject data, long seed) { timeline = new ScoreTimeline(data, seed); }
        void stop() { if (playback != null) playback.stop(); playback = null; }
    }
    /** Parsed once per score, not per run; the parsed data is never mutated. */
    private static final Map<Spec, JsonObject> DATA = new java.util.concurrent.ConcurrentHashMap<>();
    public StrikeScore(Spec spec) { this.spec = Objects.requireNonNull(spec); data = DATA.computeIfAbsent(spec, StrikeScore::load); }
    private static JsonObject load(Spec spec) {
        try (var reader = new InputStreamReader(Objects.requireNonNull(StrikeScore.class.getResourceAsStream(spec.resource())),
                StandardCharsets.UTF_8)) {
            return JsonParser.parseReader(reader).getAsJsonObject();
        } catch (Exception e) { throw new IllegalStateException("Invalid strike score " + spec.resource(), e); }
    }
    /** @param desired score section for the current phase, or negative for silence. */
    public void tick(int desired, List<ServerPlayer> audience, long now) {
        if (desired < 0) { close(); return; }
        var ready = audience.stream().filter(p -> !p.hasDisconnected() && p.connection.hasClientLoaded() && MusicPacks.ready(p)).toList();
        for (var p : List.copyOf(listeners.keySet())) if (!ready.contains(p)) remove(p);
        for (var p : ready) {
            // Each listener joins the CURRENT phase immediately. Reconnect/pack readiness cannot reset teammates.
            var listener = listeners.computeIfAbsent(p, k -> new Listener(data, seed));
            var change = listener.timeline.update(desired, now);
            if (change.stop()) listener.stop();
            if (change.segment() == null) continue;
            var clip = data.getAsJsonObject("segments").getAsJsonObject(change.segment().toString());
            var event = Identifier.fromNamespaceAndPath(spec.namespace(), clip.get("event").getAsString());
            listener.playback = MinigameLib.get(p.level().getServer()).music().playSound(
                    event, clip.get("seconds").getAsDouble(), 1f, List.of(p), true, SoundSource.RECORDS);
            DestinyGuardians.LOGGER.info("[{}] player={} section={} segment={} transition={}",
                    spec.logTag(), p.getScoreboardName(), listener.timeline.section(), change.segment(), change.transition());
        }
    }
    public void remove(ServerPlayer p) { var listener = listeners.remove(p); if (listener != null) listener.stop(); }
    @Override public void close() { listeners.values().forEach(Listener::stop); listeners.clear(); }
}
