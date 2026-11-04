package kim.biryeong.destiny.fx;

import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import net.minecraft.client.resources.model.cuboid.CuboidModel;
import org.junit.jupiter.api.Test;

import javax.imageio.ImageIO;
import java.io.ByteArrayInputStream;
import java.io.StringReader;
import java.nio.charset.StandardCharsets;
import java.util.Arrays;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

import static org.junit.jupiter.api.Assertions.*;

/** Resource contracts, not a claim about client rendering or original Destiny geometry.
 * Void ribbons and Stasis spikes/mist may use different names, axes, faces and layouts.
 */
class WaveCrestW79AssetTest {
    private static final List<String> NAMES = List.of("wave_crest_void_w79", "wave_crest_stasis_w79");
    private static final Set<String> SIDES = Set.of("north", "south", "east", "west", "up", "down");
    private static final Set<Double> ANGLES = Set.of(-45.0, -22.5, 0.0, 22.5, 45.0);

    private byte[] bytes(String relative) throws Exception {
        try (var stream = getClass().getResourceAsStream("/assets/destiny/" + relative)) {
            assertNotNull(stream, "Missing W79 resource: " + relative);
            return stream.readAllBytes();
        }
    }

    private JsonObject json(String relative) throws Exception {
        return JsonParser.parseString(new String(bytes(relative), StandardCharsets.UTF_8)).getAsJsonObject();
    }

    @Test
    void bothItemsResolveToNativeParseableDistinctWaveModelsAndTextures() throws Exception {
        for (String name : NAMES) {
            var item = json("items/fx/" + name + ".json").getAsJsonObject("model");
            assertEquals("minecraft:model", item.get("type").getAsString(), name);
            assertEquals("destiny:fx/" + name, item.get("model").getAsString(), name);
            var model = json("models/fx/" + name + ".json");
            assertNotNull(CuboidModel.fromStream(new StringReader(model.toString())), name);
            assertFalse(model.has("parent"), "Crest uses its own authored geometry: " + name);
            assertFalse(model.get("ambientocclusion").getAsBoolean(), name);
            var texture = "destiny:item/fx/" + name;
            assertEquals(texture, model.getAsJsonObject("textures").get("0").getAsString(), name);
            assertEquals(texture, model.getAsJsonObject("textures").get("particle").getAsString(), name);
            assertNotNull(ImageIO.read(new ByteArrayInputStream(bytes("textures/item/fx/" + name + ".png"))), name);
        }
        assertFalse(Arrays.equals(bytes("textures/item/fx/" + NAMES.get(0) + ".png"),
                bytes("textures/item/fx/" + NAMES.get(1) + ".png")), "Void and Stasis have distinct original textures");
    }

    @Test
    void eachModelHasTwentyFourThinFullbrightPanelsWithValidNativeRotationsAndUvs() throws Exception {
        for (String name : NAMES) {
            var elements = json("models/fx/" + name + ".json").getAsJsonArray("elements");
            assertEquals(24, elements.size(), "Bounded mesh payload per lane: " + name);
            boolean rotated = false;
            for (var value : elements) {
                var element = value.getAsJsonObject();
                var from = element.getAsJsonArray("from");
                var to = element.getAsJsonArray("to");
                assertEquals(3, from.size(), name);
                assertEquals(3, to.size(), name);
                int broadAxes = 0;
                double thickness = Double.POSITIVE_INFINITY;
                for (int axis = 0; axis < 3; axis++) {
                    double low = from.get(axis).getAsDouble();
                    double high = to.get(axis).getAsDouble();
                    assertTrue(Double.isFinite(low) && Double.isFinite(high), name);
                    assertTrue(low >= -16 && high <= 32, "Native model coordinate bounds: " + name);
                    assertTrue(high >= low, "Panel cannot have inverted bounds: " + name);
                    thickness = Math.min(thickness, high - low);
                    if (high - low > 1e-7) broadAxes++;
                }
                assertTrue(broadAxes >= 2 && thickness <= .25,
                        "Each panel is a thin, nonzero-area sheet in model units: " + name);
                assertEquals(15, element.get("light_emission").getAsInt(), name);
                assertFalse(element.get("shade").getAsBoolean(), name);
                var rotation = element.getAsJsonObject("rotation");
                assertNotNull(rotation, name);
                assertTrue(Set.of("x", "y", "z").contains(rotation.get("axis").getAsString()), name);
                double angle = rotation.get("angle").getAsDouble();
                assertTrue(ANGLES.contains(angle), "Rotation must use a native Java model angle: " + name);
                rotated |= angle != 0;
                assertEquals(3, rotation.getAsJsonArray("origin").size(), name);
                for (var coordinate : rotation.getAsJsonArray("origin"))
                    assertTrue(Double.isFinite(coordinate.getAsDouble()), name);
                var faces = element.getAsJsonObject("faces");
                assertTrue(faces.size() >= 2 && faces.size() <= 6, "Thin panels have visible faces on both sides: " + name);
                for (var entry : faces.entrySet()) {
                    assertTrue(SIDES.contains(entry.getKey()), name);
                    var face = entry.getValue().getAsJsonObject();
                    assertEquals("#0", face.get("texture").getAsString(), name);
                    var uv = face.getAsJsonArray("uv");
                    assertEquals(4, uv.size(), name);
                    for (var coordinate : uv) {
                        double n = coordinate.getAsDouble();
                        assertTrue(Double.isFinite(n) && n >= 0 && n <= 16, "UV uses the 64x64 animation frame: " + name);
                    }
                    assertTrue(Math.abs(uv.get(0).getAsDouble() - uv.get(2).getAsDouble()) > 1e-7, name);
                    assertTrue(Math.abs(uv.get(1).getAsDouble() - uv.get(3).getAsDouble()) > 1e-7, name);
                }
            }
            assertTrue(rotated, "Crest has authored angled geometry: " + name);
        }
    }

    @Test
    void texturesContainFourVisibleDifferentFramesAtTwoTicksWithoutInterpolation() throws Exception {
        for (String name : NAMES) {
            var image = ImageIO.read(new ByteArrayInputStream(bytes("textures/item/fx/" + name + ".png")));
            assertNotNull(image, name);
            assertEquals(64, image.getWidth(), name);
            assertEquals(256, image.getHeight(), name);
            var animation = json("textures/item/fx/" + name + ".png.mcmeta").getAsJsonObject("animation");
            assertEquals(64, animation.get("width").getAsInt(), name);
            assertEquals(64, animation.get("height").getAsInt(), name);
            assertEquals(2, animation.get("frametime").getAsInt(), name);
            assertFalse(animation.get("interpolate").getAsBoolean(), name);
            var frames = animation.getAsJsonArray("frames");
            assertEquals(4, frames.size(), name);
            var framePixels = new int[4][];
            for (int frame = 0; frame < 4; frame++) {
                assertEquals(frame, frames.get(frame).getAsInt(), name);
                framePixels[frame] = image.getRGB(0, frame * 64, 64, 64, null, 0, 64);
                var visibleColors = new HashSet<Integer>();
                boolean transparent = false;
                for (int color : framePixels[frame]) {
                    if ((color >>> 24) != 0) visibleColors.add(color);
                    if ((color >>> 24) < 255) transparent = true;
                }
                assertTrue(visibleColors.size() > 1, "Every frame contains visible textured energy: " + name + "/" + frame);
                assertTrue(transparent, "Energy uses alpha instead of a solid opaque rectangle: " + name + "/" + frame);
                for (int previous = 0; previous < frame; previous++)
                    assertFalse(Arrays.equals(framePixels[previous], framePixels[frame]), "Animation frames differ: " + name);
            }
        }
    }
}
