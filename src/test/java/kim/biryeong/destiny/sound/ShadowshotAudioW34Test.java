package kim.biryeong.destiny.sound;

import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import org.junit.jupiter.api.Test;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.HexFormat;
import java.util.Set;
import static org.junit.jupiter.api.Assertions.*;

class ShadowshotAudioW34Test {
    private JsonObject json(String path) throws Exception {
        try (var input = getClass().getResourceAsStream(path)) {
            assertNotNull(input, path);
            return JsonParser.parseReader(new InputStreamReader(input, StandardCharsets.UTF_8)).getAsJsonObject();
        }
    }
    @Test void archivedPhaseEditsRemainPinnedAndActivationUsesContinuousSuccessor() throws Exception {
        var overlay = json("/destiny/sounds/w34.json");
        var source = overlay.getAsJsonObject("source");
        assertEquals("O0uvtZMID9E", source.get("video_id").getAsString());
        assertEquals("Shadowshot - Deadfall", source.get("chapter").getAsString());
        var events = overlay.getAsJsonObject("events");
        assertEquals(Set.of("hunter.void.super.start", "hunter.void.super.draw", "hunter.void.super.fire",
                "hunter.void.super.impact", "hunter.void.super.end"), events.keySet());
        var definitions = json("/assets/destiny/sounds.json");
        for (var e : events.entrySet()) {
            var r = e.getValue().getAsJsonObject();
            var sound = definitions.getAsJsonObject(e.getKey()).getAsJsonArray("sounds").get(0).getAsJsonObject();
            var active = e.getKey().equals("hunter.void.super.start")
                    ? json("/destiny/sounds/w36.json").getAsJsonObject("events").getAsJsonObject(e.getKey()) : r;
            assertEquals(active.get("sound").getAsString(), sound.get("name").getAsString());
            assertTrue(sound.get("name").getAsString().startsWith(e.getKey().endsWith(".start")
                    ? "destiny:w36/hunter/void/super/" : "destiny:w34/hunter/void/super/"));
            assertEquals(32, sound.get("attenuation_distance").getAsInt());
            assertFalse(sound.get("stream").getAsBoolean());
        }
        var legacy = json("/destiny/sounds/w33.json");
        assertEquals("destiny/sounds/w34.json", legacy.getAsJsonObject("active_overlay").get("manifest").getAsString());
    }
    @Test void outputsAreHashPinnedBoundedAndHonestlyLabeledMixEdits() throws Exception {
        var root = json("/destiny/sounds/w34.json");
        assertTrue(root.get("verification_limits").getAsString().contains("No independent acoustic listening"));
        for (var e : root.getAsJsonObject("events").entrySet()) {
            var record = e.getValue().getAsJsonObject();
            assertEquals("video_mix_edit", record.get("status").getAsString());
            var interval = record.getAsJsonArray("source_window_seconds");
            double begin = interval.get(0).getAsDouble(), end = interval.get(1).getAsDouble();
            assertTrue(begin >= 1045 && end <= 1064 && end > begin && end-begin < 2);
            var output = record.getAsJsonObject("output");
            assertEquals(1, output.get("channels").getAsInt());
            assertEquals(32000, output.get("sample_rate_hz").getAsInt());
            assertEquals(0, output.get("clipped_samples").getAsInt());
            assertTrue(output.get("sample_peak_dbfs").getAsDouble() <= -1);
            assertTrue(Math.abs(output.get("duration_seconds").getAsDouble() - (end-begin)) < .05);
            var path = record.get("asset_path").getAsString().substring("src/main/resources".length());
            try (var input = getClass().getResourceAsStream(path)) {
                assertNotNull(input, path); var bytes = input.readAllBytes();
                assertEquals("OggS", new String(bytes, 0, 4, StandardCharsets.US_ASCII));
                assertEquals(output.get("sha256").getAsString(), HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)));
            }
            if (e.getKey().endsWith(".end"))
                assertTrue(record.get("limitations").getAsString().contains("NOT an identified Deadfall shutdown"));
        }
    }
}
