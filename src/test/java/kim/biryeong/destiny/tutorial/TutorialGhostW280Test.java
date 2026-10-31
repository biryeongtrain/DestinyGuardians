package kim.biryeong.destiny.tutorial;

import com.google.gson.JsonParser;
import net.minecraft.client.resources.model.cuboid.CuboidModel;
import net.minecraft.client.resources.model.cuboid.UnbakedCuboidGeometry;
import org.junit.jupiter.api.Test;
import java.nio.file.Files;
import java.nio.file.Path;
import java.io.StringReader;
import static org.junit.jupiter.api.Assertions.*;

class TutorialGhostW280Test {
    @Test void nativeModelsFitBudgetAndResolveAtlas() throws Exception {
        var root = Path.of("src/main/resources/assets/destiny");
        int elements = 0, parts = 0;
        try (var files = Files.list(root.resolve("models/tutorial/ghost"))) {
            for (var file : files.toList()) {
                String source = Files.readString(file);
                var json = JsonParser.parseString(source).getAsJsonObject();
                for (var texture : json.getAsJsonObject("textures").entrySet()) {
                    String id = texture.getValue().getAsString();
                    // 26.3 items atlas includes textures/item, not arbitrary textures/tutorial.
                    assertTrue(id.startsWith("destiny:item/"), "Outside native item atlas: " + id);
                    assertTrue(Files.isRegularFile(root.resolve("textures/" + id.substring(8) + ".png")));
                }
                var model = CuboidModel.fromStream(new StringReader(source));
                var geometry = assertInstanceOf(UnbakedCuboidGeometry.class, model.geometry());
                elements += geometry.elements().size(); parts++;
                for (var e : geometry.elements()) {
                    assertEquals(2, e.faces().size());
                    assertTrue(Float.isFinite(e.rotation().transform().m00()));
                }
                var item = JsonParser.parseString(Files.readString(root.resolve("items/tutorial/ghost/" + file.getFileName()))).getAsJsonObject();
                assertEquals("destiny:tutorial/ghost/" + file.getFileName().toString().replace(".json", ""),
                    item.getAsJsonObject("model").get("model").getAsString());
            }
        }
        assertEquals(11, parts);
        assertTrue(elements > 0 && elements <= 1000);
        var atlas = javax.imageio.ImageIO.read(root.resolve("textures/item/tutorial/ghost.png").toFile());
        assertEquals(2048, atlas.getWidth());
        assertEquals(0, atlas.getRGB(63, 0) >>> 24);
        assertEquals(255, atlas.getRGB(0, 63) >>> 24);
    }
    @Test void everyAccountRequiresRolloutOnceAndActiveSessionsDoNotRestart() {
        assertTrue(TutorialEnrollment.required(0, false));
        assertFalse(TutorialEnrollment.required(0, true));
        assertFalse(TutorialEnrollment.required(TutorialEnrollment.REQUIRED_REVISION, false));
        assertFalse(TutorialEnrollment.required(TutorialEnrollment.REQUIRED_REVISION + 1, false));
    }

    @Test void voiceCuesResolveAndHaveBoundedRealDurations() throws Exception {
        var root = Path.of("src/main/resources/assets/destiny");
        var sounds = JsonParser.parseString(Files.readString(root.resolve("sounds.json"))).getAsJsonObject();
        var korean = JsonParser.parseString(Files.readString(Path.of("art/ghost/w282/audio-manifest.json"))).getAsJsonObject();
        for (String key : java.util.List.of("awaken", "walk", "titan", "hunter", "warlock", "light", "equip", "fire", "aim", "traverse", "grenade", "melee", "class_ability", "super", "ascend")) {
            var cue = TutorialVoice.cue(key);
            assertNotNull(cue); assertFalse(cue.text().isBlank());
            var recording = korean.getAsJsonObject(key);
            assertEquals("ko", recording.get("locale").getAsString());
            assertEquals(recording.get("text").getAsString(), cue.text());
            assertEquals((int) Math.ceil(recording.get("duration_sec").getAsDouble() * 20) + 10, cue.ticks());
            assertTrue(cue.ticks() >= 20 && cue.ticks() <= 210);
            var sound = sounds.getAsJsonObject("tutorial.ghost." + key).getAsJsonArray("sounds").get(0).getAsJsonObject();
            assertTrue(sound.get("stream").getAsBoolean());
            byte[] bytes = Files.readAllBytes(root.resolve("sounds/" + sound.get("name").getAsString().substring(8) + ".ogg"));
            assertEquals("OggS", new String(bytes, 0, 4, java.nio.charset.StandardCharsets.US_ASCII));
            assertTrue(bytes.length < 150000);
        }
    }
}
