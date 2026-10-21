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
            assertTrue(elements.size() >= 16 && elements.size() <= 256, name + " cube budget");
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
    @Test
    void reconstructedKnifeHasRealBladeFingerAndPommelHoles() throws Exception {
        var elements = json("assets/destiny/models/hunter/solar_knife.json").getAsJsonArray("elements");
        // Source chart holes: blade (1236,193), finger (503,253), pommel (120,279).
        for (double[] point : new double[][]{{1236,193}, {503,253}, {120,279}, {1530,100}}) {
            double z = 16 - point[0] / 128;
            double x = 6.2 + point[1] / 115;
            boolean filled = false;
            for (var e : elements) {
                var c = e.getAsJsonObject();
                if (c.has("rotation")) continue; // Engraved surface chevrons, not shell.
                filled |= x > c.getAsJsonArray("from").get(0).getAsDouble()
                        && x < c.getAsJsonArray("to").get(0).getAsDouble()
                        && z > c.getAsJsonArray("from").get(2).getAsDouble()
                        && z < c.getAsJsonArray("to").get(2).getAsDouble();
            }
            assertFalse(filled, "Three through holes and hooked spine notch must stay empty");
        }
    }

    @Test
    void manifestDoesNotClaimUnverifiedPropsAreDestinyDesigns() throws Exception {
        var manifest = JsonParser.parseString(Files.readString(Path.of("art/blockbench/hunter/manifest.json"))).getAsJsonObject();
        for (var model : manifest.getAsJsonArray("models")) {
            var m = model.getAsJsonObject();
            boolean verified = Set.of("solar_knife", "arc_flashbang").contains(m.get("name").getAsString());
            assertEquals(verified ? "reference_verified_reconstruction" : "provisional_not_destiny_verified",
                    m.get("design_status").getAsString());
            assertEquals(verified ? 2 : 0, m.getAsJsonArray("visual_reference_urls").size());
        }
    }

}
