package kim.biryeong.destiny;

import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import org.junit.jupiter.api.Test;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.HashSet;
import java.util.Set;

import static org.junit.jupiter.api.Assertions.*;

/** Pack routing checks complement GameTests: the server cannot detect missing client assets. */
class HunterAssetTest {
    private String resource(String path) throws IOException {
        try (var stream = getClass().getClassLoader().getResourceAsStream(path)) {
            assertNotNull(stream, "Missing pack resource " + path);
            return new String(stream.readAllBytes(), StandardCharsets.UTF_8);
        }
    }

    private JsonObject json(String path) throws IOException {
        return JsonParser.parseString(resource(path)).getAsJsonObject();
    }

    @Test
    void eachSuperHasDistinctTintAndResolvesShader() throws IOException {
        Set<String> tints = new HashSet<>();
        for (String element : new String[]{"arc", "solar", "void"}) {
            var chain = json("assets/destiny/post_effect/super/" + element + "_active.json");
            var passes = chain.getAsJsonArray("passes");
            assertEquals(2, passes.size());
            var grade = passes.get(0).getAsJsonObject();
            String shader = grade.get("fragment_shader").getAsString().replace(":", "/shaders/") + ".fsh";
            String glsl = resource("assets/" + shader);
            var uniforms = grade.getAsJsonObject("uniforms").getAsJsonArray("SuperConfig");
            assertTrue(glsl.contains("uniform SuperConfig"));
            for (var uniform : uniforms) {
                var u = uniform.getAsJsonObject();
                assertTrue(glsl.contains("vec4 " + u.get("name").getAsString()));
                assertEquals(4, u.getAsJsonArray("value").size());
            }
            tints.add(uniforms.get(0).getAsJsonObject().getAsJsonArray("value").toString());
            assertEquals(grade.get("output"), passes.get(1).getAsJsonObject().getAsJsonArray("inputs")
                    .get(0).getAsJsonObject().get("target"));
            assertEquals("minecraft:main", passes.get(1).getAsJsonObject().get("output").getAsString());
        }
        assertEquals(3, tints.size());
    }

    @Test
    void superItemDefinitionsResolveNonemptyCubeModels() throws IOException {
        for (String name : new String[]{"arc_staff", "golden_gun", "shadow_bow"}) {
            var definition = json("assets/destiny/items/" + name + ".json").getAsJsonObject("model");
            assertEquals("minecraft:model", definition.get("type").getAsString());
            String path = definition.get("model").getAsString().replace(":", "/models/");
            var model = json("assets/" + path + ".json");
            assertFalse(model.getAsJsonArray("elements").isEmpty());
            assertTrue(model.has("display"));
        }
    }

    @Test
    void everyPlayerHeartVariantIsTransparentButMountHeartsAreNotOverridden() throws IOException {
        var entries = JsonParser.parseString(resource("assets/destiny/hud_heart_sprites.json")).getAsJsonArray();
        assertEquals(44, entries.size());
        for (var entry : entries) {
            var e = entry.getAsJsonObject();
            String path = e.get("path").getAsString();
            assertFalse(path.contains("vehicle_"));
            try (var stream = getClass().getClassLoader().getResourceAsStream(path)) {
                assertNotNull(stream, path);
                var image = javax.imageio.ImageIO.read(stream);
                assertNotNull(image, path);
                assertEquals(e.get("width").getAsInt(), image.getWidth());
                assertEquals(e.get("height").getAsInt(), image.getHeight());
                for (int y = 0; y < image.getHeight(); y++) for (int x = 0; x < image.getWidth(); x++)
                    assertEquals(0, image.getRGB(x, y) >>> 24, path + " must not leave blinking/poisoned hearts visible");
            }
        }
    }

    @Test
    void hudGlyphModelsResolveTexturesAndRuntimeTint() throws IOException {
        for (String name : new String[]{"solid", "tile", "diamond", "flash", "flame", "vortex", "fist", "knife", "smoke", "dodge", "staff", "gun", "bow"}) {
            var item = json("assets/destiny/items/gui/hud/" + name + ".json").getAsJsonObject("model");
            assertEquals("minecraft:custom_model_data", item.getAsJsonArray("tints").get(0).getAsJsonObject().get("type").getAsString());
            var model = json("assets/destiny/models/gui/hud/" + name + ".json");
            assertEquals("destiny:item/hud/" + name, model.getAsJsonObject("textures").get("layer0").getAsString(), "Item atlas only discovers item/ textures automatically");
            assertEquals(0, model.getAsJsonArray("elements").get(0).getAsJsonObject().getAsJsonObject("faces").getAsJsonObject("north").get("tintindex").getAsInt());
            try (var stream = getClass().getClassLoader().getResourceAsStream("assets/destiny/textures/item/hud/" + name + ".png")) {
                assertNotNull(stream, name);
                var image = javax.imageio.ImageIO.read(stream);
                assertNotNull(image);
                assertEquals(64, image.getWidth());
                assertEquals(64, image.getHeight());
            }
        }
    }
}
