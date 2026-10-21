package kim.biryeong.destiny;

import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import org.junit.jupiter.api.Test;

import javax.imageio.ImageIO;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Base64;
import java.util.HashSet;
import java.util.Set;

import static org.junit.jupiter.api.Assertions.*;

class HunterPropAssetTest {
    private static final String[] NAMES = {"arc_flashbang", "solar_incendiary", "void_vortex", "solar_knife", "void_smoke_bomb"};

    private byte[] resource(String path) throws Exception {
        try (var stream = getClass().getClassLoader().getResourceAsStream(path)) {
            assertNotNull(stream, path);
            return stream.readAllBytes();
        }
    }

    private JsonObject json(String path) throws Exception {
        return JsonParser.parseString(new String(resource(path), StandardCharsets.UTF_8)).getAsJsonObject();
    }

    @Test
    void fiveDistinctPropsResolveTheirOwnAtlasAndLegalCubeGeometry() throws Exception {
        Set<String> atlases = new HashSet<>();
        for (String name : NAMES) {
            var definition = json("assets/destiny/items/hunter/" + name + ".json").getAsJsonObject("model");
            assertEquals("minecraft:model", definition.get("type").getAsString());
            assertEquals("destiny:hunter/" + name, definition.get("model").getAsString());
            var model = json("assets/destiny/models/hunter/" + name + ".json");
            assertEquals("destiny:item/hunter/" + name, model.getAsJsonObject("textures").get("0").getAsString());
            assertEquals(model.getAsJsonObject("textures").get("0"), model.getAsJsonObject("textures").get("particle"));
            var elements = model.getAsJsonArray("elements");
            assertTrue(elements.size() >= 16 && elements.size() <= 32, name + " cube budget");
            for (var element : elements) {
                var cube = element.getAsJsonObject();
                for (int axis = 0; axis < 3; axis++) {
                    double from = cube.getAsJsonArray("from").get(axis).getAsDouble();
                    double to = cube.getAsJsonArray("to").get(axis).getAsDouble();
                    assertTrue(from >= -16 && to <= 32 && to > from, name + " legal nonzero cube bounds");
                }
                if (cube.has("rotation")) {
                    double angle = cube.getAsJsonObject("rotation").get("angle").getAsDouble();
                    assertTrue(Math.abs(angle) <= 45 && angle % 22.5 == 0, "Portable single-axis rotation");
                }
                assertEquals(6, cube.getAsJsonObject("faces").size());
                for (var face : cube.getAsJsonObject("faces").asMap().values()) {
                    assertEquals("#0", face.getAsJsonObject().get("texture").getAsString());
                    for (var uv : face.getAsJsonObject().getAsJsonArray("uv"))
                        assertTrue(uv.getAsDouble() >= 0 && uv.getAsDouble() <= 16, "Atlas UV range");
                }
            }
            assertTrue(model.has("display"));
            byte[] png = resource("assets/destiny/textures/item/hunter/" + name + ".png");
            assertTrue(atlases.add(Base64.getEncoder().encodeToString(png)), "Distinct elemental palette");
            var image = ImageIO.read(new java.io.ByteArrayInputStream(png));
            assertEquals(64, image.getWidth()); assertEquals(32, image.getHeight());
            assertEquals(255, image.getRGB(4, 4) >>> 24);
        }
    }

    @Test
    void editableBlockbenchSourcesMatchExportedCubeCountAndEmbeddedTexture() throws Exception {
        for (String name : NAMES) {
            var source = JsonParser.parseString(Files.readString(Path.of("art/blockbench/hunter/" + name + ".bbmodel"))).getAsJsonObject();
            assertEquals("java_block", source.getAsJsonObject("meta").get("model_format").getAsString());
            assertEquals(64, source.getAsJsonObject("resolution").get("width").getAsInt());
            var model = json("assets/destiny/models/hunter/" + name + ".json");
            assertEquals(model.getAsJsonArray("elements").size(), source.getAsJsonArray("elements").size());
            assertFalse(source.getAsJsonArray("outliner").isEmpty());
            String data = source.getAsJsonArray("textures").get(0).getAsJsonObject().get("source").getAsString();
            assertArrayEquals(resource("assets/destiny/textures/item/hunter/" + name + ".png"),
                    Base64.getDecoder().decode(data.substring(data.indexOf(',') + 1)));
        }
    }
}
