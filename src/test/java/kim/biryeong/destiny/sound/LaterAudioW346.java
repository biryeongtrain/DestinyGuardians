package kim.biryeong.destiny.sound;

import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.*;
import static org.junit.jupiter.api.Assertions.*;

/** Admit individual later assets from their reviewed import manifests, never a whole namespace. */
final class LaterAudioW346 {
    private LaterAudioW346() {}
    private static JsonObject json(String path) throws Exception {
        return JsonParser.parseString(Files.readString(Path.of(path))).getAsJsonObject();
    }
    private static void pin(Map<String,String> pins, String path, String hash) {
        assertTrue(path.startsWith("src/main/resources/assets/") && path.endsWith(".ogg"), path);
        assertEquals(Path.of(path), Path.of(path).normalize(), path);
        assertTrue(hash.matches("[0-9a-f]{64}"), path);
        assertNull(pins.putIfAbsent(path, hash), "Overlapping later provenance: " + path);
    }
    static Set<String> verifiedPaths() throws Exception {
        var pins = new TreeMap<String,String>();
        for (var value : json("src/main/resources/destiny/devils_lair/audio-manifest.json").getAsJsonArray("voice")) {
            var row=value.getAsJsonObject();
            pin(pins,"src/main/resources/assets/destiny_devils/sounds/voice/"+row.get("id").getAsString()+".ogg",row.get("sha256").getAsString());
        }
        for (var entry : json("src/main/resources/destiny/devils_lair/combat-audio-manifest.json").getAsJsonObject("files").entrySet())
            pin(pins,"src/main/resources/assets/destiny_devils_sfx/sounds/"+entry.getKey()+".ogg",entry.getValue().getAsJsonObject().get("sha256").getAsString());
        for (var entry : json("src/main/resources/destiny/down/fireteam-audio-provenance.json").getAsJsonObject("sha256").entrySet()) {
            assertTrue(entry.getKey().startsWith("minecraft/assets/destiny_fireteam/"));
            pin(pins,"src/main/resources/"+entry.getKey().substring("minecraft/".length()),entry.getValue().getAsString());
        }
        for (var value : json("src/main/resources/destiny/down/respawn-audio-provenance.json").getAsJsonArray("files")) {
            var row=value.getAsJsonObject();pin(pins,row.get("output").getAsString(),row.get("outputSha256").getAsString());
        }
        for (var value : json("docs/qa/2026-11-04/devils-lair/music-linkage/import.json").getAsJsonArray("segments")) {
            var row=value.getAsJsonObject();
            pin(pins,"src/main/resources/assets/destiny_music/sounds/devils/"+row.get("segment").getAsString()+".ogg",row.get("sha256").getAsString());
        }
        var descent=json("docs/qa/2026-11-03/devils-lair/music/source-inventory.json").getAsJsonArray("clips").asList().stream()
                .map(v->v.getAsJsonObject()).filter(v->v.get("wem").getAsString().equals("80D715DA")).toList();
        assertEquals(1,descent.size());
        pin(pins,"src/main/resources/assets/destiny_music/sounds/devils_descent_80d715da.ogg",descent.getFirst().get("sha256").getAsString());
        for (String manifest : List.of("art/audio/activity-launch-w329/manifest.json","art/audio/activity-transition-w329/manifest.json")) {
            var row=json(manifest);pin(pins,row.get("output").getAsString(),row.get("output_sha256").getAsString());
        }
        for (var value : json("art/audio/activity-failure-w329/conversion.json").getAsJsonArray("audio")) {
            var row=value.getAsJsonObject();pin(pins,row.get("output").getAsString(),row.get("outputSha256").getAsString());
        }
        for (String manifest : List.of("art/audio/enemy-headburst-w343/manifest.json","art/audio/hive-death-w344/manifest.json"))
            for (var value : json(manifest).getAsJsonArray("files")) {
                var row=value.getAsJsonObject();pin(pins,row.get("output").getAsString(),row.get("outputSha256").getAsString());
            }
        assertEquals(467,pins.size(),"Finite approved post-campaign additions");
        for(var entry:pins.entrySet())
            assertEquals(entry.getValue(),HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256")
                    .digest(Files.readAllBytes(Path.of(entry.getKey())))),entry.getKey());
        return Set.copyOf(pins.keySet());
    }
}
