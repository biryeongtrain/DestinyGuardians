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

class ShadowshotContinuousW36Test {
    private JsonObject json(String path) throws Exception {
        try (var input = getClass().getResourceAsStream(path)) {
            assertNotNull(input, path);
            return JsonParser.parseReader(new InputStreamReader(input, StandardCharsets.UTF_8)).getAsJsonObject();
        }
    }
    @Test void activationMapsOneContinuousSourceIntervalWithoutPhaseSplices() throws Exception {
        var manifest=json("/destiny/sounds/w36.json");
        var events=manifest.getAsJsonObject("events");
        assertEquals(Set.of("hunter.void.super.start"),events.keySet());
        var record=events.getAsJsonObject("hunter.void.super.start");
        var window=record.getAsJsonArray("source_window_seconds");
        assertEquals(1047.47,window.get(0).getAsDouble(),.00001);
        assertEquals(1049.70,window.get(1).getAsDouble(),.00001);
        var tx=record.getAsJsonObject("transforms");
        assertEquals(0,tx.get("internal_cuts").getAsInt());
        for (String key:new String[]{"concatenation","inserted_silence","time_stretch","pitch_shift"})
            assertFalse(tx.get(key).getAsBoolean(),key);
        var sound=json("/assets/destiny/sounds.json").getAsJsonObject("hunter.void.super.start").getAsJsonArray("sounds");
        assertEquals(1,sound.size());
        assertEquals(record.get("sound").getAsString(),sound.get(0).getAsJsonObject().get("name").getAsString());
        assertEquals(4,manifest.getAsJsonObject("playback").getAsJsonArray("suppressed_phase_actions").size());
        assertEquals("destiny/sounds/w36.json",json("/destiny/sounds/w33.json").getAsJsonObject("active_sequence_overlay").get("manifest").getAsString());
    }
    @Test void continuousOggIsPinnedAndSafeButNotFalselyLabeledAsListened() throws Exception {
        var m=json("/destiny/sounds/w36.json");
        assertTrue(m.get("verification_limits").getAsString().contains("No independent acoustic listening"));
        var record=m.getAsJsonObject("events").getAsJsonObject("hunter.void.super.start");
        var out=record.getAsJsonObject("output");
        assertEquals(1,out.get("channels").getAsInt());
        assertEquals(32000,out.get("sample_rate_hz").getAsInt());
        assertEquals(2.23,out.get("duration_seconds").getAsDouble(),.05);
        assertEquals(0,out.get("clipped_samples").getAsInt());
        assertTrue(out.get("sample_peak_dbfs").getAsDouble()<=-1);
        try(var input=getClass().getResourceAsStream(record.get("asset_path").getAsString().substring("src/main/resources".length()))) {
            assertNotNull(input);var bytes=input.readAllBytes();
            assertEquals("OggS",new String(bytes,0,4,StandardCharsets.US_ASCII));
            assertEquals(out.get("sha256").getAsString(),HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)));
        }
    }
}
