package kim.biryeong.destiny;

import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import kim.biryeong.destiny.fx.HunterVfxAssets;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

import javax.imageio.ImageIO;
import java.io.ByteArrayInputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Base64;
import java.util.HashSet;
import java.util.Set;

import static org.junit.jupiter.api.Assertions.*;

class HunterVfxAssetTest {
    private byte[] resource(String name) throws Exception {
        try (var stream = getClass().getResourceAsStream("/destiny/vfx/" + name + ".bbmodel")) {
            assertNotNull(stream, name);
            return stream.readAllBytes();
        }
    }

    @Test
    void editableAndBundledAnimatedModelsMatchWithinDisplayBudget() throws Exception {
        for (String name : HunterVfxAssets.MODELS) {
            byte[] bytes = resource(name);
            assertArrayEquals(Files.readAllBytes(Path.of("art/blockbench/vfx/" + name + ".bbmodel")), bytes);
            var model = JsonParser.parseString(new String(bytes, java.nio.charset.StandardCharsets.UTF_8)).getAsJsonObject();
            assertEquals("free", model.getAsJsonObject("meta").get("model_format").getAsString());
            assertTrue(model.getAsJsonArray("elements").size() <= 64);
            assertEquals(32, model.getAsJsonObject("resolution").get("width").getAsInt());
            assertEquals(32, model.getAsJsonObject("resolution").get("height").getAsInt());
            Set<String> cubes = new HashSet<>();
            for (var e : model.getAsJsonArray("elements")) {
                var c = e.getAsJsonObject();
                cubes.add(c.get("uuid").getAsString());
                for (int axis = 0; axis < 3; axis++) {
                    double from = c.getAsJsonArray("from").get(axis).getAsDouble();
                    double to = c.getAsJsonArray("to").get(axis).getAsDouble();
                    assertTrue(Double.isFinite(from) && Double.isFinite(to) && to > from);
                }
            }
            Set<String> referenced = new HashSet<>();
            int renderBones = countBones(model.getAsJsonArray("outliner"), cubes, referenced);
            assertTrue(renderBones > 0 && renderBones <= 8, name + " rendered bone budget");
            assertEquals(cubes, referenced, "Every cube belongs to the rig exactly once");
            assertEquals(1, model.getAsJsonArray("animations").size());
            var animation = model.getAsJsonArray("animations").get(0).getAsJsonObject();
            boolean loop = name.contains("vortex") || name.contains("smoke");
            assertEquals(loop ? "loop" : "spawn", animation.get("name").getAsString());
            assertEquals(loop ? "loop" : "once", animation.get("loop").getAsString());
            double length = animation.get("length").getAsDouble();
            assertTrue(length > 0 && length <= 2);
            int animatedBones = 0;
            for (var animator : animation.getAsJsonObject("animators").asMap().values()) {
                if (!animator.getAsJsonObject().has("keyframes")) continue; // Empty root animator is valid Blockbench metadata.
                animatedBones++;
                for (var k : animator.getAsJsonObject().getAsJsonArray("keyframes")) {
                    var key = k.getAsJsonObject();
                    double t = key.get("time").getAsDouble();
                    assertTrue(Double.isFinite(t) && t >= 0 && t <= length);
                    for (var point : key.getAsJsonArray("data_points")) {
                        for (String axis : new String[]{"x", "y", "z"}) {
                            assertTrue(Double.isFinite(point.getAsJsonObject().get(axis).getAsDouble()));
                        }
                    }
                }
            }
            assertEquals(renderBones, animatedBones, "Every rendered group is animated");
            var texture = model.getAsJsonArray("textures").get(0).getAsJsonObject();
            String data = texture.get("source").getAsString();
            assertTrue(data.startsWith("data:image/png;base64,"));
            var image = ImageIO.read(new ByteArrayInputStream(Base64.getDecoder().decode(data.substring(data.indexOf(",") + 1))));
            assertEquals(32, image.getWidth()); assertEquals(32, image.getHeight());
            assertFalse(new String(bytes, java.nio.charset.StandardCharsets.UTF_8).contains("/Users/"));
        }
    }

    private int countBones(Iterable<JsonElement> nodes, Set<String> cubes, Set<String> referenced) {
        int count = 0;
        for (var node : nodes) {
            if (node.isJsonPrimitive()) {
                assertTrue(cubes.contains(node.getAsString()));
                assertTrue(referenced.add(node.getAsString()));
            } else {
                JsonObject group = node.getAsJsonObject();
                var children = group.getAsJsonArray("children");
                if (children.asList().stream().anyMatch(JsonElement::isJsonPrimitive)) count++;
                count += countBones(children, cubes, referenced);
            }
        }
        return count;
    }

    @Test
    void installDefaultsIsIdempotentAndNeverOverwritesArtistsFile(@TempDir Path directory) throws Exception {
        assertEquals(4, HunterVfxAssets.install(directory));
        for (String name : HunterVfxAssets.MODELS) assertArrayEquals(resource(name), Files.readAllBytes(directory.resolve(name + ".bbmodel")));
        Path custom = directory.resolve(HunterVfxAssets.MODELS.getFirst() + ".bbmodel");
        Files.writeString(custom, "artist customized model");
        assertEquals(0, HunterVfxAssets.install(directory));
        assertEquals("artist customized model", Files.readString(custom));
    }
}
