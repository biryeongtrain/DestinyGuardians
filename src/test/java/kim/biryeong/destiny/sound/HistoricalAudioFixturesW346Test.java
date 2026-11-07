package kim.biryeong.destiny.sound;

import org.junit.jupiter.api.Test;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.HexFormat;
import java.util.Map;
import static org.junit.jupiter.api.Assertions.*;

/** These commitments authenticate recovered fixtures independently of runtime files. */
class HistoricalAudioFixturesW346Test {
    @Test void archivedSnapshotsMatchOriginalArtAndGitCommitments() throws Exception {
        var expected = Map.ofEntries(
                Map.entry("w55-sounds.json", "2c4b673fc944dd8f88853ca8d93c0dc331c5acbe236eace87542ac2e14c604bc"),
                Map.entry("w96-sounds.json", "77b45b55199896266101c98a79215b41b430a64834b0b1eee2e2a51efeed471b"),
                Map.entry("w230/audio-provenance.json", "06460cee6974e872528d838d3daa5d94e5e03b5a483a1bdadc0452d911f09d0a"),
                Map.entry("w230/sounds-additions.json", "b2c505a4cb482d49bf524335d62e02efe65b47f983001d459928b45fccd6f500"),
                Map.entry("w270/sounds-fragment.json", "8cd7cbbe9ecb7580d13ef573a08e68b66271000c4ae0770636e9c13bf8c7a98e"),
                Map.entry("w270/audio-import.json", "2c2f4cdc7956acc10d68b3602c5919f3238ca89ffab051565c7c6b25ff56ca8a"));
        for (var entry : expected.entrySet()) {
            var path=Path.of("src/test/resources/destiny-test/audio").resolve(entry.getKey());
            assertEquals(entry.getValue(),HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256")
                    .digest(Files.readAllBytes(path))),entry.getKey());
        }
    }
}
