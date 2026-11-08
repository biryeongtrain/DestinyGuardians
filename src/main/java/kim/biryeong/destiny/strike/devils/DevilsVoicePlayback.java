package kim.biryeong.destiny.strike.devils;

import kim.biryeong.destiny.campaign.presentation.DevilsSubtitles;
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
public final class DevilsVoicePlayback implements AutoCloseable {
    private final java.util.function.Supplier<List<ServerPlayer>> audience;
    private final java.util.function.LongConsumer completed;
    private final Set<ServerPlayer> listeners = new HashSet<>();
    private DevilsVoiceCatalog.Line line;
    private final java.util.function.Predicate<DevilsVoiceCatalog.Line> clipAvailable;
    private String fallback, currentId = "";
    private long token;
    private int age;

    public DevilsVoicePlayback(java.util.function.Supplier<List<ServerPlayer>> audience,
                               java.util.function.LongConsumer completed) {
        this(audience, completed, DevilsVoicePlayback::packagedClipAvailable);
    }
    DevilsVoicePlayback(java.util.function.Supplier<List<ServerPlayer>> audience,
                        java.util.function.LongConsumer completed,
                        java.util.function.Predicate<DevilsVoiceCatalog.Line> clipAvailable) {
        this.clipAvailable = java.util.Objects.requireNonNull(clipAvailable);
        this.audience = java.util.Objects.requireNonNull(audience);
        this.completed = java.util.Objects.requireNonNull(completed);
    }
    /** Zero means unavailable audio: show a 60-tick authored notice, while the director owns fallback progression. */
    public int start(long token, String id) {
        if (playing()) throw new IllegalStateException("Required strike speech must be serialized, not dropped");
        var next = DevilsVoiceCatalog.line(id).orElse(null);
        this.token = token;
        this.currentId = id;
        this.line = next != null && clipAvailable.test(next) ? next : null;
        this.fallback = line == null ? fallbackText(id) : null;
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
        DevilsSubtitles.render(player, line == null ? "임무 안내" : line.speaker(), line == null ? fallback : line.text());
    }
    static boolean packagedClipAvailable(DevilsVoiceCatalog.Line line) {
        try (var input = DevilsVoicePlayback.class.getResourceAsStream("/assets/destiny_devils/sounds/voice/" + line.id() + ".ogg")) {
            return input != null && java.util.Arrays.equals(input.readNBytes(4), new byte[]{'O','g','g','S'});
        } catch (java.io.IOException unavailable) { return false; }
    }
    /** Authored gameplay notices; never attributed to the original Ghost or Zavala dialogue. */
    static String fallbackText(String id) {
        return switch (id) {
            case "80b59f27" -> "정제소로 향하는 길을 확보하세요.";
            case "80b59f22" -> "정제소의 몰락자와 군체를 처치하세요.";
            case "80b59f1d" -> "보안 장치에 고스트를 배치하세요.";
            case "80b59f26" -> "해킹을 시작합니다. 적의 공격에 대비하세요.";
            case "80b59f25", "80b59f20", "80b59f21" -> "증원 병력이 접근합니다. 고스트를 보호하세요.";
            case "80b59f24" -> "장벽이 해제되었습니다. 화력팀과 함께 이동하세요.";
            case "80b59f23" -> "워커와 브리그를 파괴하고 진입로를 확보하세요.";
            case "80b59f1e" -> "워커가 파괴되었습니다. 남은 목표를 확인하세요.";
            case "80b59f1f" -> "세픽스 프라임의 소굴에 진입합니다.";
            case "80b59f28" -> "공격전을 완료했습니다. 귀환을 준비하세요.";
            default -> "음성 안내를 재생할 수 없습니다. 임무 목표를 확인하세요.";
        };
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
        DevilsSubtitles.remove(player);
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
