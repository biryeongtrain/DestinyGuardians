package kim.biryeong.destiny.tutorial;

import com.google.gson.JsonParser;
import kim.biryeong.destiny.DestinyGuardians;
import net.minecraft.core.Holder;
import net.minecraft.network.protocol.game.ClientboundSoundEntityPacket;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.network.protocol.game.ClientboundStopSoundPacket;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundSource;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.Map;
import java.util.HashMap;

/** Personal voice with the supplied translation and measured duration. */
final class TutorialVoice {
    record Cue(String text, int ticks) {}
    private static final Map<String, Cue> CUES = load();
    private TutorialVoice() {}
    private static Map<String, Cue> load() {
        var input = TutorialVoice.class.getResourceAsStream("/data/destiny/tutorial/ghost_lines.json");
        if (input == null) throw new IllegalStateException("Missing Ghost lines");
        try (var reader = new InputStreamReader(input, StandardCharsets.UTF_8)) {
            var result = new HashMap<String, Cue>();
            for (var entry : JsonParser.parseReader(reader).getAsJsonObject().entrySet()) {
                var value = entry.getValue().getAsJsonObject();
                result.put(entry.getKey(), new Cue(value.get("text").getAsString(), value.get("ticks").getAsInt()));
            }
            return Map.copyOf(result);
        } catch (java.io.IOException e) { throw new IllegalStateException(e); }
    }
    static Cue cue(String key) { return CUES.get(key); }
    static void play(ServerPlayer p, String key) {
        // Follow the listener during sprint/teleport instead of leaving a positional voice behind.
        p.connection.send(new ClientboundSoundEntityPacket(Holder.direct(SoundEvent.createFixedRangeEvent(
                DestinyGuardians.id("tutorial.ghost." + key), 32f)), SoundSource.PLAYERS,
                p, .85f, 1f, p.level().getRandom().nextLong()));
    }
    static void stop(ServerPlayer p, String key) {
        if (key != null && !p.hasDisconnected()) p.connection.send(new ClientboundStopSoundPacket(
                DestinyGuardians.id("tutorial.ghost." + key), SoundSource.PLAYERS));
    }
}
