package kim.biryeong.destiny.loot;

import com.google.gson.JsonParser;
import org.junit.jupiter.api.Test;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.HexFormat;
import static org.junit.jupiter.api.Assertions.*;

class RewardChestAudioAssetTest {
    @Test void suppliedChestCuePreservesEntireDecodedMp3AndExactBinding() throws Exception {
        var manifest = JsonParser.parseString(Files.readString(Path.of("art/audio/reward-chest/manifest.json"))).getAsJsonObject();
        assertEquals("e83c126dc8f306c64e32e21754d44a56a3f378e251e2fddb616a0fc2df4ef458", manifest.get("sourceSha256").getAsString());
        assertEquals("src/main/resources/assets/destiny/sounds/loot/chest_open.ogg", manifest.get("output").getAsString());
        byte[] bytes = Files.readAllBytes(Path.of(manifest.get("output").getAsString()));
        assertEquals(manifest.get("outputBytes").getAsLong(), bytes.length);
        assertEquals(manifest.get("outputSha256").getAsString(), HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)));
        var data = ByteBuffer.wrap(bytes).order(ByteOrder.LITTLE_ENDIAN);
        int offset = 0; long last = -1;
        while (offset < bytes.length) {
            assertTrue(offset + 27 <= bytes.length); assertEquals(0x5367674F, data.getInt(offset));
            int segments = bytes[offset + 26] & 255, length = 0;
            assertTrue(offset + 27 + segments <= bytes.length);
            for (int j = 0; j < segments; j++) length += bytes[offset + 27 + j] & 255;
            int start = offset + 27 + segments; assertTrue(start + length <= bytes.length);
            if (offset == 0) {
                assertEquals(1, bytes[start]);
                assertEquals("vorbis", new String(bytes, start + 1, 6, java.nio.charset.StandardCharsets.US_ASCII));
                assertEquals(2, bytes[start + 11]); assertEquals(48000, data.getInt(start + 12));
            }
            last = data.getLong(offset + 6); offset = start + length;
        }
        assertEquals(123264, last); assertEquals(last, manifest.get("sourceDecodedFrames").getAsLong());
        var fragment = JsonParser.parseString(Files.readString(Path.of("art/audio/reward-chest/sounds-fragment.json"))).getAsJsonObject();
        var current = JsonParser.parseString(Files.readString(Path.of("src/main/resources/assets/destiny/sounds.json"))).getAsJsonObject();
        assertEquals(1, fragment.size()); assertEquals(fragment.get("loot.chest.open"), current.get("loot.chest.open"));
        assertEquals("destiny:loot/chest_open", fragment.getAsJsonObject("loot.chest.open").getAsJsonArray("sounds").get(0).getAsJsonObject().get("name").getAsString());
    }
}
