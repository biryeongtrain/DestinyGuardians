package kim.biryeong.destiny;

import com.google.gson.JsonElement;
import com.google.gson.JsonParser;
import kim.biryeong.destiny.fx.HunterVfxAssets;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.HashSet;
import java.util.Set;

import static org.junit.jupiter.api.Assertions.*;

class HunterSuperVfxAssetTest {
    private byte[] resource(String path) throws Exception {
        try (var input = getClass().getResourceAsStream("/" + path)) {
            assertNotNull(input, path);
            return input.readAllBytes();
        }
    }

    @Test
    void dedicatedUltimateMeshesAreRiggedTriangulatedAndMatchEditableSources() throws Exception {
        for (String name : HunterVfxAssets.SUPER_MODELS) {
            byte[] bytes = resource("destiny/vfx/" + name + ".bbmodel");
            assertArrayEquals(Files.readAllBytes(Path.of("art/blockbench/vfx/" + name + ".bbmodel")), bytes);
            var model = JsonParser.parseString(new String(bytes, StandardCharsets.UTF_8)).getAsJsonObject();
            assertEquals("free", model.getAsJsonObject("meta").get("model_format").getAsString());
            assertFalse(new String(bytes, StandardCharsets.UTF_8).contains("/Users/"));
            Set<String> ids = new HashSet<>(), rigged = new HashSet<>();
            int triangles = 0;
            for (var element : model.getAsJsonArray("elements")) {
                var mesh = element.getAsJsonObject();
                assertEquals("mesh", mesh.get("type").getAsString());
                assertTrue(ids.add(mesh.get("uuid").getAsString()));
                var vertices = mesh.getAsJsonObject("vertices");
                for (var vertex : vertices.asMap().values()) for (var coordinate : vertex.getAsJsonArray())
                    assertTrue(Double.isFinite(coordinate.getAsDouble()));
                for (var value : mesh.getAsJsonObject("faces").asMap().values()) {
                    var face = value.getAsJsonObject();
                    var points = face.getAsJsonArray("vertices");
                    assertEquals(3, points.size());
                    var distinct = new HashSet<String>();
                    double[][] p = new double[3][3];
                    for (int i = 0; i < 3; i++) {
                        String id = points.get(i).getAsString();
                        assertTrue(distinct.add(id) && vertices.has(id));
                        for (int a = 0; a < 3; a++) p[i][a] = vertices.getAsJsonArray(id).get(a).getAsDouble();
                        var uv = face.getAsJsonObject("uv").getAsJsonArray(id);
                        assertEquals(2, uv.size());
                        for (var coordinate : uv) assertTrue(Double.isFinite(coordinate.getAsDouble()));
                    }
                    double[] u = new double[3], v = new double[3];
                    for (int i = 0; i < 3; i++) { u[i] = p[1][i] - p[0][i]; v[i] = p[2][i] - p[0][i]; }
                    assertTrue(Math.pow(u[1]*v[2]-u[2]*v[1],2) + Math.pow(u[2]*v[0]-u[0]*v[2],2)
                            + Math.pow(u[0]*v[1]-u[1]*v[0],2) > 1.0e-14);
                    int material = face.get("texture").getAsInt();
                    assertTrue(material >= 0 && material < 4);
                    triangles++;
                }
            }
            assertTrue(triangles >= 500 && triangles <= 1600, name + " triangle budget");
            assertEquals(3, countRenderBones(model.getAsJsonArray("outliner"), rigged));
            assertEquals(ids, rigged);
            var clip = model.getAsJsonArray("animations").get(0).getAsJsonObject();
            assertEquals(name.contains("anchor") ? "loop" : "spawn", clip.get("name").getAsString());
            assertEquals(name.contains("anchor") ? "loop" : "once", clip.get("loop").getAsString());
            assertEquals(3, clip.getAsJsonObject("animators").asMap().values().stream()
                    .filter(a -> a.getAsJsonObject().has("keyframes")
                            && !a.getAsJsonObject().getAsJsonArray("keyframes").isEmpty()).count());
        }
    }

    private int countRenderBones(Iterable<JsonElement> nodes, Set<String> referenced) {
        int count = 0;
        for (var node : nodes) {
            if (node.isJsonPrimitive()) assertTrue(referenced.add(node.getAsString()));
            else {
                var children = node.getAsJsonObject().getAsJsonArray("children");
                if (children.asList().stream().anyMatch(JsonElement::isJsonPrimitive)) count++;
                count += countRenderBones(children, referenced);
            }
        }
        return count;
    }

    @Test
    void ultimateDefaultsNeverReplaceAnExistingArtistsRevision(@TempDir Path dir) throws Exception {
        assertEquals(HunterVfxAssets.allModels().size(), HunterVfxAssets.install(dir));
        for (String name : HunterVfxAssets.SUPER_MODELS)
            assertArrayEquals(resource("destiny/vfx/" + name + ".bbmodel"), Files.readAllBytes(dir.resolve(name + ".bbmodel")));
        Path custom = dir.resolve(HunterVfxAssets.SUPER_MODELS.getFirst() + ".bbmodel");
        Files.writeString(custom, "artist-owned");
        assertEquals(0, HunterVfxAssets.install(dir));
        assertEquals("artist-owned", Files.readString(custom));
    }

    @Test
    void thinBeamsResolveTexturesAndKeepAUnitLengthForwardAxis() throws Exception {
        for (String name : new String[]{"solar_trail_h15", "void_link_h15"}) {
            var item = JsonParser.parseString(new String(resource("assets/destiny/items/fx/" + name + ".json"), StandardCharsets.UTF_8)).getAsJsonObject();
            assertEquals("destiny:fx/" + name, item.getAsJsonObject("model").get("model").getAsString());
            var model = JsonParser.parseString(new String(resource("assets/destiny/models/fx/" + name + ".json"), StandardCharsets.UTF_8)).getAsJsonObject();
            assertEquals(48, model.getAsJsonArray("elements").size());
            assertEquals("destiny:item/fx/" + name, model.getAsJsonObject("textures").get("0").getAsString());
            assertTrue(resource("assets/destiny/textures/item/fx/" + name + ".png").length > 0);
            for (int i = 0; i < 16; i++) {
                var cube = model.getAsJsonArray("elements").get(i).getAsJsonObject();
                assertEquals(1, cube.getAsJsonArray("to").get(2).getAsDouble() - cube.getAsJsonArray("from").get(2).getAsDouble(), 1e-7);
            }
        }
    }
}
