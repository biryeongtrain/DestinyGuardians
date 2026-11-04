package kim.biryeong.destiny.strike.devils;

import com.google.gson.JsonParser;
import org.junit.jupiter.api.Test;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.HexFormat;
import static org.junit.jupiter.api.Assertions.*;

class DevilsVoiceCatalogTest {
    @Test void exactBaseVoiceBytesAndEventNamesArePackaged() throws Exception {
        var manifest = JsonParser.parseReader(new InputStreamReader(getClass().getResourceAsStream(
                "/destiny/devils_lair/audio-manifest.json"), StandardCharsets.UTF_8)).getAsJsonObject();
        var sounds = JsonParser.parseReader(new InputStreamReader(getClass().getResourceAsStream(
                "/assets/destiny_devils/sounds.json"), StandardCharsets.UTF_8)).getAsJsonObject();
        assertEquals(12, DevilsVoiceCatalog.lines().size());
        for (var entry : manifest.getAsJsonArray("voice")) {
            var row = entry.getAsJsonObject();
            var id = row.get("id").getAsString();
            var line = DevilsVoiceCatalog.line(id).orElseThrow();
            try (var input = getClass().getResourceAsStream("/assets/destiny_devils/sounds/voice/" + id + ".ogg")) {
                assertNotNull(input);
                var raw = input.readAllBytes();
                assertEquals("OggS", new String(raw, 0, 4, StandardCharsets.US_ASCII));
                assertEquals(row.get("sha256").getAsString(), HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw)));
            }
            assertEquals((int) Math.ceil(row.get("frames").getAsDouble() / row.get("rate").getAsDouble() * 20), line.ticks());
            var sound = sounds.getAsJsonObject("voice." + id).getAsJsonArray("sounds").get(0).getAsJsonObject();
            assertEquals("destiny_devils:voice/" + id, sound.get("name").getAsString());
            assertTrue(sound.get("stream").getAsBoolean());
        }
        assertTrue(DevilsVoiceCatalog.line("80b59f52").isEmpty()); // Hecate variant cannot leak into this strike.
    }
}
