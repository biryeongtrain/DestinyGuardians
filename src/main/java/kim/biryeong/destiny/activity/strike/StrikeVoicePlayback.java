package kim.biryeong.destiny.activity.strike;

import kim.biryeong.destiny.activity.presentation.StrikeSubtitles;
import kim.biryeong.minigamelib.cinematic.CameraViews;
import net.minecraft.core.Holder;
import net.minecraft.network.protocol.game.ClientboundSoundEntityPacket;
import net.minecraft.network.protocol.game.ClientboundStopSoundPacket;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundSource;

import java.util.HashSet;
import java.util.List;
import java.util.Set;

/** One shared speech clock, personal sound/subtitle projections, explicit completion vs cancellation. */
public final class StrikeVoicePlayback implements AutoCloseable {
    private final java.util.function.Supplier<List<ServerPlayer>> audience;
    private final java.util.function.LongConsumer completed;
    private final Set<ServerPlayer> listeners = new HashSet<>();
    private StrikeVoiceCatalog.Line line;
    private String fallback, currentId = "";
    private long token;
    private int age;

    private final StrikeVoiceCatalog catalog;
    private final java.util.function.Function<String, String> fallbackNotice;
    private final java.util.function.Predicate<StrikeVoiceCatalog.Line> clipAvailable;

    public StrikeVoicePlayback(StrikeVoiceCatalog catalog, java.util.function.Function<String, String> fallbackNotice,
                               java.util.function.Supplier<List<ServerPlayer>> audience, java.util.function.LongConsumer completed) {
        this(catalog, fallbackNotice, audience, completed, catalog::packaged);
    }
    public StrikeVoicePlayback(StrikeVoiceCatalog catalog, java.util.function.Function<String, String> fallbackNotice,
                               java.util.function.Supplier<List<ServerPlayer>> audience, java.util.function.LongConsumer completed,
                               java.util.function.Predicate<StrikeVoiceCatalog.Line> clipAvailable) {
        this.catalog = java.util.Objects.requireNonNull(catalog);
        this.fallbackNotice = java.util.Objects.requireNonNull(fallbackNotice);
        this.clipAvailable = java.util.Objects.requireNonNull(clipAvailable);
        this.audience = java.util.Objects.requireNonNull(audience);
        this.completed = java.util.Objects.requireNonNull(completed);
    }
    /** Zero means unavailable audio: show a 60-tick authored notice, while the director owns fallback progression. */
    public int start(long token, String id) {
        if (playing()) throw new IllegalStateException("Required strike speech must be serialized, not dropped");
        var next = catalog.line(id).orElse(null);
        this.token = token;
        this.currentId = id;
        this.line = next != null && clipAvailable.test(next) ? next : null;
        this.fallback = line == null ? fallbackNotice.apply(id) : null;
        this.age = 0;
        for (var player : audience.get()) {
            if (player.hasDisconnected() || !player.connection.hasClientLoaded()) continue;
            listeners.add(player);
            // The actual player's tracked entity follows movement; no temporary sound-emitter entity is needed.
            // The briefing is a camera-view cinematic, which drops every packet outside its allow-list (sound included),
            // so the opening line was silently discarded. CameraViews.send is the sanctioned route, as MusicService uses.
            if (line != null) CameraViews.send(player, new ClientboundSoundEntityPacket(
                    Holder.direct(SoundEvent.createFixedRangeEvent(Identifier.parse(next.event()), 32f)),
                    SoundSource.PLAYERS, player, 1f, 1f, player.getRandom().nextLong()));
            render(player);
        }
        return line == null ? 0 : line.ticks();
    }
    /** Call once per director tick. Offline suspension must suspend both clocks together. */
    public void tick() {
        if (!playing()) return;
        age++;
        var currentAudience = Set.copyOf(audience.get());
        for (var player : List.copyOf(listeners)) {
            if (player.hasDisconnected() || !currentAudience.contains(player)) {
                remove(player);
                listeners.remove(player);
            }
        }
        // Rejoining players see the current text; their return does not replay or extend the team's clip.
        for (var player : currentAudience) {
            if (player.hasDisconnected() || !player.connection.hasClientLoaded()) continue;
            listeners.add(player);
            if (age % 4 == 0) render(player);
        }
        if (age >= duration()) {
            long finished = token;
            boolean audible = line != null;
            close();
            if (audible) completed.accept(finished);
        }
    }
    private int duration() { return line == null ? 60 : line.ticks(); }
    private void render(ServerPlayer player) {
        StrikeSubtitles.render(player, line == null ? "임무 안내" : line.speaker(), line == null ? fallback : line.text());
    }
    public String current() { return currentId; }
    public int remaining() { return playing() ? Math.max(0, duration() - age) : 0; }
    public boolean playing() { return line != null || fallback != null; }
    public void disconnected(ServerPlayer player) {
        if (listeners.remove(player)) remove(player);
    }
    private void remove(ServerPlayer player) {
        if (!player.hasDisconnected() && line != null) CameraViews.send(player, new ClientboundStopSoundPacket(
                Identifier.parse(line.event()), SoundSource.PLAYERS));
        StrikeSubtitles.remove(player);
    }
    /** Cancellation always stays silent at the completion boundary, including reset/close/disconnect cleanup. */
    @Override public void close() {
        for (var player : List.copyOf(listeners)) remove(player);
        listeners.clear();
        line = null;
        fallback = null; currentId = "";
        age = 0;
    }
}
