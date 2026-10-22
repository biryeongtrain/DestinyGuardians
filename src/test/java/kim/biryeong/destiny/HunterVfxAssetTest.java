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
            assertTrue(model.getAsJsonArray("elements").size() <= 96);
            assertEquals(128, model.getAsJsonObject("resolution").get("width").getAsInt());
            assertEquals(128, model.getAsJsonObject("resolution").get("height").getAsInt());
            Set<String> cubes = new HashSet<>(); // IDs include both mesh and card elements.
            int meshTriangles = 0, cards = 0, meshes = 0;
            for (var e : model.getAsJsonArray("elements")) {
                var c = e.getAsJsonObject();
                assertTrue(cubes.add(c.get("uuid").getAsString()), "Unique element UUID");
                if (c.get("type").getAsString().equals("mesh")) {
                    meshes++;
                    var vertices = c.getAsJsonObject("vertices");
                    for (var v : vertices.asMap().values()) finiteVector(v, 3);
                    for (var f : c.getAsJsonObject("faces").asMap().values()) {
                        var face = f.getAsJsonObject();
                        var points = face.getAsJsonArray("vertices");
                        assertEquals(3, points.size(), "Explicit triangulation avoids ambiguous polygons");
                        Set<String> faceIds = new HashSet<>();
                        double[][] p = new double[3][3];
                        for (int i = 0; i < 3; i++) {
                            String id = points.get(i).getAsString();
                            assertTrue(faceIds.add(id) && vertices.has(id));
                            finiteVector(face.getAsJsonObject("uv").get(id), 2);
                            for (int a = 0; a < 3; a++) p[i][a] = vertices.getAsJsonArray(id).get(a).getAsDouble();
                        }
                        double[] u = new double[3], v = new double[3];
                        for (int a = 0; a < 3; a++) { u[a] = p[1][a] - p[0][a]; v[a] = p[2][a] - p[0][a]; }
                        double area = Math.pow(u[1]*v[2]-u[2]*v[1],2) + Math.pow(u[2]*v[0]-u[0]*v[2],2)
                                + Math.pow(u[0]*v[1]-u[1]*v[0],2);
                        assertTrue(area > 1e-14, "No degenerate triangle");
                        int material = face.get("texture").getAsInt();
                        assertTrue(material >= 1 && material <= 4, "Mesh uses constant-color material");
                        meshTriangles++;
                    }
                } else {
                    assertEquals("cube", c.get("type").getAsString()); cards++;
                    for (int axis = 0; axis < 3; axis++) {
                        double from = c.getAsJsonArray("from").get(axis).getAsDouble();
                        double to = c.getAsJsonArray("to").get(axis).getAsDouble();
                        assertTrue(Double.isFinite(from) && Double.isFinite(to) && to > from);
                    }
                    if (name.contains("smoke") && c.has("rotation")) {
                        for (var angle : c.getAsJsonArray("rotation")) assertEquals(0, angle.getAsDouble(), 1e-9,
                                "Billboard smoke cards share a local facing direction");
                    }
                    long visibleFaces = c.getAsJsonObject("faces").asMap().values().stream()
                            .filter(f -> !f.getAsJsonObject().get("texture").isJsonNull()).count();
                    assertEquals(2, visibleFaces, "Only front/back cutout faces are rendered");
                }
            }
            assertTrue(cards > 0 && cards <= 64);
            if (name.contains("smoke")) {
                assertEquals(0, meshes); assertEquals(0, meshTriangles); assertEquals(30, cards);
            } else {
                assertTrue(meshes > 0 && meshTriangles >= 256 && meshTriangles <= 1800, name + " mesh triangle budget");
            }
            Set<String> referenced = new HashSet<>();
            int renderBones = countBones(model.getAsJsonArray("outliner"), cubes, referenced);
            assertTrue(renderBones > 0 && renderBones <= 8, name + " rendered bone budget");
            assertEquals(cubes, referenced, "Every element belongs to the rig exactly once");
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
            var textures = model.getAsJsonArray("textures");
            assertEquals(5, textures.size());
            for (int i = 0; i < textures.size(); i++) {
                var texture = textures.get(i).getAsJsonObject();
                String data = texture.get("source").getAsString();
                assertTrue(data.startsWith("data:image/png;base64,"));
                var image = ImageIO.read(new ByteArrayInputStream(Base64.getDecoder().decode(data.substring(data.indexOf(",") + 1))));
                assertEquals(i == 0 ? 128 : 16, image.getWidth());
                assertEquals(i == 0 ? 128 : 16, image.getHeight());
                if (i > 0) {
                    int color = image.getRGB(0, 0);
                    for (int y = 0; y < 16; y++) for (int x = 0; x < 16; x++) assertEquals(color, image.getRGB(x,y));
                } else {
                    long opaque = 0, clear = 0;
                    for (int y = 0; y < 128; y++) for (int x = 0; x < 128; x++) {
                        if ((image.getRGB(x,y) >>> 24) == 0) clear++; else opaque++;
                    }
                    assertTrue(opaque > 4096 && clear > 1024, "Atlas has detailed cutouts, not solid cards");
                }
            }
            assertFalse(new String(bytes, java.nio.charset.StandardCharsets.UTF_8).contains("/Users/"));
        }
    }

    private static void finiteVector(JsonElement value, int length) {
        assertNotNull(value); assertEquals(length, value.getAsJsonArray().size());
        for (var number : value.getAsJsonArray()) assertTrue(Double.isFinite(number.getAsDouble()));
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
