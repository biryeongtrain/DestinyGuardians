package kim.biryeong.destiny.hud;

import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import org.junit.jupiter.api.Test;

import javax.imageio.ImageIO;
import java.awt.image.BufferedImage;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Set;

import static org.junit.jupiter.api.Assertions.*;

/** Independent pack/pixel contracts; native framebuffer checks belong to the parent suite. */
class CriticalHudW89AssetTest {
    private static final Path ROOT = Path.of("src/main/resources/assets/destiny");
    private static final int WIDTH = 512, HEIGHT = 288, CUTOFF = 26;

    @Test
    void everyActiveFrameIsWhiteRgbaAtTheFullScreenTextureSize() throws IOException {
        for (int frame = 0; frame < 8; frame++) {
            var image = image(frame);
            assertTrue(image.getColorModel().hasAlpha(), name(frame));
            for (int y = 0; y < HEIGHT; y++) for (int x = 0; x < WIDTH; x++)
                assertEquals(0xFFFFFF, image.getRGB(x, y) & 0xFFFFFF,
                        "CMD tint requires white RGB, including transparent pixels: " + name(frame));
        }
    }

    @Test
    void allEightFramesIncludingZeroRetainTwentyPercentCoverageAfterShaderCutoff() throws IOException {
        for (int frame = 0; frame < 8; frame++) {
            var image = image(frame);
            int surviving = 0;
            for (int y = 0; y < HEIGHT; y++) for (int x = 0; x < WIDTH; x++)
                if ((image.getRGB(x, y) >>> 24) >= CUTOFF) surviving++;
            assertTrue(surviving >= WIDTH * HEIGHT * .20,
                    name(frame) + " must remain active at alpha >= 26; surviving pixels=" + surviving);
        }
    }

    @Test
    void centerEllipseThroughRadiusPointSixRemainsCompletelyClearInEveryFrame() throws IOException {
        for (int frame = 0; frame < 8; frame++) {
            var image = image(frame);
            for (int y = 0; y < HEIGHT; y++) for (int x = 0; x < WIDTH; x++) {
                double nx = (x + .5 - WIDTH / 2.0) / (WIDTH / 2.0);
                double ny = (y + .5 - HEIGHT / 2.0) / (HEIGHT / 2.0);
                if (nx * nx + ny * ny <= .60 * .60)
                    assertEquals(0, image.getRGB(x, y) >>> 24,
                            name(frame) + " clear center at " + x + "," + y);
            }
        }
    }

    @Test
    void alphaIsPointwiseMonotonicAndNeverExceeds170() throws IOException {
        BufferedImage previous = null;
        long previousTotal = -1;
        for (int frame = 0; frame < 8; frame++) {
            var image = image(frame);
            long total = 0;
            for (int y = 0; y < HEIGHT; y++) for (int x = 0; x < WIDTH; x++) {
                int alpha = image.getRGB(x, y) >>> 24;
                assertTrue(alpha <= 170, name(frame) + " max alpha at " + x + "," + y);
                if (previous != null) assertTrue(alpha >= (previous.getRGB(x, y) >>> 24),
                        name(frame) + " alpha regression at " + x + "," + y);
                total += alpha;
            }
            assertTrue(total > previousTotal, "Each authored bank frame must have a distinct increasing gain");
            previous = image;
            previousTotal = total;
        }
    }

    @Test
    void everyItemRoutesCmdTintZeroThroughBothFullUvUnshadedPlanes() throws IOException {
        for (int frame = 0; frame < 8; frame++) {
            String name = name(frame), modelId = "destiny:gui/hud/" + name;
            var item = json("items/gui/hud/" + name + ".json");
            var routed = item.getAsJsonObject("model");
            assertEquals("minecraft:model", routed.get("type").getAsString());
            assertEquals(modelId, routed.get("model").getAsString());
            var tints = routed.getAsJsonArray("tints");
            assertEquals(1, tints.size());
            var tint = tints.get(0).getAsJsonObject();
            assertEquals("minecraft:custom_model_data", tint.get("type").getAsString());
            assertEquals(0, tint.get("index").getAsInt());
            assertEquals(0xFFFFFF, tint.get("default").getAsInt());

            var model = json("models/gui/hud/" + name + ".json");
            assertFalse(model.get("ambientocclusion").getAsBoolean());
            assertEquals("front", model.get("gui_light").getAsString());
            var elements = model.getAsJsonArray("elements");
            assertEquals(1, elements.size(), name);
            var plane = elements.get(0).getAsJsonObject();
            assertEquals(JsonParser.parseString("[0,0,8]"), plane.get("from"));
            assertEquals(JsonParser.parseString("[16,16,8]"), plane.get("to"));
            assertFalse(plane.get("shade").getAsBoolean());
            var faces = plane.getAsJsonObject("faces");
            assertEquals(Set.of("north", "south"), faces.keySet());
            for (var faceValue : faces.entrySet()) {
                var face = faceValue.getValue().getAsJsonObject();
                assertEquals(JsonParser.parseString("[0,0,16,16]"), face.get("uv"));
                assertEquals(0, face.get("tintindex").getAsInt());
                String reference = face.get("texture").getAsString();
                assertTrue(reference.startsWith("#"));
                assertEquals("destiny:item/hud/" + name,
                        model.getAsJsonObject("textures").get(reference.substring(1)).getAsString());
            }
            noUnsupportedRenderType(item);
            noUnsupportedRenderType(model);
        }
    }

    @Test
    void everyPngSelectsMeanMipmapMetadataWithoutPretendingToOverrideFragmentCutoff() throws IOException {
        for (int frame = 0; frame < 8; frame++) {
            var metadata = json("textures/item/hud/" + name(frame) + ".png.mcmeta");
            assertEquals("mean", metadata.getAsJsonObject("texture").get("mipmap_strategy").getAsString());
            noUnsupportedRenderType(metadata);
        }
    }

    private static void noUnsupportedRenderType(JsonElement value) {
        if (value.isJsonObject()) for (var entry : value.getAsJsonObject().entrySet()) {
            assertNotEquals("render_type", entry.getKey(), "Vanilla HUD assets cannot select an unsupported render_type");
            noUnsupportedRenderType(entry.getValue());
        }
        else if (value.isJsonArray()) for (var child : value.getAsJsonArray()) noUnsupportedRenderType(child);
    }

    private static String name(int frame) { return "incoming_w89_critical_" + frame; }

    private static BufferedImage image(int frame) throws IOException {
        var image = ImageIO.read(ROOT.resolve("textures/item/hud/" + name(frame) + ".png").toFile());
        assertNotNull(image, name(frame));
        assertEquals(WIDTH, image.getWidth(), name(frame));
        assertEquals(HEIGHT, image.getHeight(), name(frame));
        return image;
    }

    private static JsonObject json(String path) throws IOException {
        return JsonParser.parseString(Files.readString(ROOT.resolve(path))).getAsJsonObject();
    }
}
