package kim.biryeong.destiny.sound;

import com.google.gson.JsonParser;
import org.junit.jupiter.api.Test;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.HashSet;
import static org.junit.jupiter.api.Assertions.*;

class EnemyHeadburstAssetsW343Test {
    @Test void fourSourceEventsRetainFortySelectableMonoVariants() throws Exception {
        try (var in = getClass().getResourceAsStream("/assets/destiny_headburst/sounds.json")) {
            assertNotNull(in);
            var sounds = JsonParser.parseReader(new InputStreamReader(in, StandardCharsets.UTF_8)).getAsJsonObject();
            int[] expected = {5, 6, 5, 24}; int group = 0;
            var files = new HashSet<String>();
            for (var family : EnemyHeadburstSounds.Family.values()) {
                var variants = sounds.getAsJsonObject(family.event().getPath()).getAsJsonArray("sounds");
                assertEquals(expected[group++], variants.size());
                for (var entry : variants) {
                    var row = entry.getAsJsonObject();
                    assertEquals(24, row.get("attenuation_distance").getAsInt());
                    String name = row.get("name").getAsString(); assertTrue(files.add(name));
                    try (var ogg = getClass().getResourceAsStream("/assets/destiny_headburst/sounds/" + name.split(":")[1] + ".ogg")) {
                        assertNotNull(ogg, name); byte[] header = ogg.readNBytes(44);
                        assertEquals("OggS", new String(header, 0, 4, StandardCharsets.US_ASCII));
                        assertEquals("vorbis", new String(header, 29, 6, StandardCharsets.US_ASCII));
                        assertEquals(1, header[39], "Positional mono derivative");
                    }
                }
            }
            assertEquals(40, files.size()); assertEquals(4, sounds.size());
        }
    }
    @Test void fullSourceDurationAndExplicitConversionProvenanceAreRetained() throws Exception {
        var manifest = JsonParser.parseString(Files.readString(Path.of("art/audio/enemy-headburst-w343/manifest.json"))).getAsJsonObject();
        for (var value : manifest.getAsJsonArray("files")) {
            var row = value.getAsJsonObject();
            assertEquals(2, row.get("channels").getAsInt());
            assertEquals(1, row.get("outputChannels").getAsInt());
            assertTrue(Math.abs(row.get("sourceFrames").getAsLong() - row.get("outputFrames").getAsLong()) <= 256);
            assertTrue(row.get("seconds").getAsDouble() >= 3);
            assertEquals(64, row.get("sourceWavSha256").getAsString().length());
        }
        assertTrue(manifest.get("conversion").getAsString().contains("no trim/normalization"));
    }
}
