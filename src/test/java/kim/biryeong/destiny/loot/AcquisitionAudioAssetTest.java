package kim.biryeong.destiny.loot;

import com.google.gson.JsonParser;
import org.junit.jupiter.api.Test;

import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.HexFormat;
import java.util.List;
import java.util.Set;

import static org.junit.jupiter.api.Assertions.*;

class AcquisitionAudioAssetTest {
    @Test void suppliedRecordingsKeepTheirHashesStereoRateAndEntireGranuleLength() throws Exception {
        var manifest = JsonParser.parseString(Files.readString(Path.of("art/audio/loot-acquisition/manifest.json"))).getAsJsonObject();
        var files = manifest.getAsJsonArray("files"); assertEquals(3, files.size());
        var sourceHashes = List.of("075c8478b61bf214778d89f5ef11cbf4b20e75b445c1ba9f5f065aef0244e2cc",
                "eab91049a13e4eb58d30613f33233aabdabe518803538b706422097382c0abf6",
                "092ae4a1c800ebcdf529f78a0cf7ec3a07b54b026fdb6c56398b4c5e1fd1117d");
        var frames = List.of(126912L, 61376L, 295104L);
        for (int i = 0; i < files.size(); i++) {
            var file = files.get(i).getAsJsonObject();
            String tier = List.of("basic", "legendary", "exotic").get(i);
            assertEquals("destiny:loot.acquire." + tier, file.get("soundEvent").getAsString());
            assertEquals("src/main/resources/assets/destiny/sounds/loot/acquire_" + tier + ".ogg", file.get("output").getAsString());
            assertEquals(sourceHashes.get(i), file.get("sourceSha256").getAsString());
            byte[] bytes = Files.readAllBytes(Path.of(file.get("output").getAsString()));
            assertEquals(file.get("outputBytes").getAsLong(), bytes.length);
            assertEquals(file.get("outputSha256").getAsString(), HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)));
            var data = ByteBuffer.wrap(bytes).order(ByteOrder.LITTLE_ENDIAN);
            int offset = 0; long lastGranule = -1; boolean identification = false;
            while (offset < bytes.length) {
                assertTrue(offset + 27 <= bytes.length);
                assertEquals(0x5367674F, data.getInt(offset)); // OggS
                assertEquals(0, bytes[offset + 4]);
                int segments = bytes[offset + 26] & 255, length = 0;
                assertTrue(offset + 27 + segments <= bytes.length);
                for (int j = 0; j < segments; j++) length += bytes[offset + 27 + j] & 255;
                int payload = offset + 27 + segments;
                assertTrue(payload + length <= bytes.length);
                if (offset == 0) {
                    assertEquals(1, bytes[payload]);
                    assertEquals("vorbis", new String(bytes, payload + 1, 6, java.nio.charset.StandardCharsets.US_ASCII));
                    assertEquals(2, bytes[payload + 11]); assertEquals(48000, data.getInt(payload + 12));
                    identification = true;
                }
                lastGranule = data.getLong(offset + 6);
                offset = payload + length;
            }
            assertTrue(identification); assertEquals(bytes.length, offset); assertEquals(frames.get(i).longValue(), lastGranule);
        }
    }

    @Test void reviewedEventFragmentResolvesExactlyToTheThreeSuppliedAssets() throws Exception {
        var fragment = JsonParser.parseString(Files.readString(Path.of("art/audio/loot-acquisition/sounds-fragment.json"))).getAsJsonObject();
        var current = JsonParser.parseString(Files.readString(Path.of("src/main/resources/assets/destiny/sounds.json"))).getAsJsonObject();
        assertEquals(Set.of("loot.acquire.basic", "loot.acquire.legendary", "loot.acquire.exotic"), fragment.keySet());
        for (var event : fragment.entrySet()) {
            assertEquals(event.getValue(), current.get(event.getKey()));
            var sounds = event.getValue().getAsJsonObject().getAsJsonArray("sounds"); assertEquals(1, sounds.size());
            var sound = sounds.get(0).getAsJsonObject(); assertFalse(sound.get("stream").getAsBoolean());
            assertEquals("destiny:loot/acquire_" + event.getKey().substring("loot.acquire.".length()), sound.get("name").getAsString());
            assertTrue(Files.isRegularFile(Path.of("src/main/resources/assets/destiny/sounds/" + sound.get("name").getAsString().substring("destiny:".length()) + ".ogg")));
        }
    }
}
