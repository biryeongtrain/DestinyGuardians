package kim.biryeong.destiny.fx;

import com.google.gson.*;
import com.mojang.serialization.JsonOps;
import net.minecraft.client.color.item.ItemTintSources;
import net.minecraft.client.renderer.item.ItemModels;
import net.minecraft.client.resources.model.cuboid.CuboidModel;
import org.junit.jupiter.api.Test;
import java.io.*;
import java.nio.file.*;
import java.util.*;
import static org.junit.jupiter.api.Assertions.*;

class SuperMeshH28Test {
    static JsonObject read(String path) throws IOException {
        return JsonParser.parseString(Files.readString(Path.of(path))).getAsJsonObject();
    }
    static JsonObject asset(String path) throws IOException {
        return read("src/main/resources/assets/destiny/" + path + ".json");
    }
    static double value(JsonArray a, int i) { return a.get(i).getAsDouble(); }

    @Test void nativeItemCodecReadsCompositeMatricesAndConstantTints() throws Exception {
        ItemModels.bootstrap();
        ItemTintSources.bootstrap();
        for (String n : List.of("arc_staff_h28", "shadow_bow_h28_drawn", "shadow_bow_h28")) {
            var root = asset("items/" + n).getAsJsonObject("model");
            assertTrue(ItemModels.CODEC.parse(JsonOps.INSTANCE, root).isSuccess(), n);
        }
        for (String kind : List.of("arc", "bow")) {
            var primitive = asset("models/mesh/h28/" + kind + "_triangle");
            assertNotNull(CuboidModel.fromStream(new StringReader(primitive.toString())));
            assertEquals(2, primitive.getAsJsonArray("elements").get(0).getAsJsonObject().getAsJsonObject("faces").size());
        }
    }

    @Test void everySourceTriangleSurvivesAtTheSameRawItemCoordinates() throws Exception {
        for (String kind : List.of("arc", "bow")) {
            var source = read("art/mesh/supers/h28/" + kind + ".mesh.json");
            var vertices = source.getAsJsonArray("vertices");
            var triangles = source.getAsJsonArray("triangles");
            assertTrue(triangles.size() <= 2400);
            var parts = asset("items/" + (kind.equals("arc") ? "arc_staff_h28" : "shadow_bow_h28_drawn"))
                    .getAsJsonObject("model").getAsJsonArray("models");
            assertEquals(triangles.size() + (kind.equals("bow") ? 1 : 0), parts.size());
            for (int i = 0; i < triangles.size(); i++) {
                var triangle = triangles.get(i).getAsJsonObject();
                List<double[]> corners = new ArrayList<>();
                {
                    var leaf = parts.get(i).getAsJsonObject();
                    assertEquals("destiny:mesh/h28/" + kind + "_triangle", leaf.get("model").getAsString());
                    assertEquals(triangle.get("color").getAsInt() & 0xffffff,
                            leaf.getAsJsonArray("tints").get(0).getAsJsonObject().get("value").getAsInt() & 0xffffff);
                    JsonArray m = leaf.getAsJsonArray("transformation");
                    assertEquals(16, m.size());
                    for (var number : m) assertTrue(Double.isFinite(number.getAsDouble()));
                    for (double[] point : new double[][]{{-1, 0}, {0, 1}, {0, 0}}) {
                        double x = point[0], y = point[1];
                        // Native matrix JSON is row-major, before ItemTransform's -.5 centering.
                        double[] v = new double[3];
                        for (int axis = 0; axis < 3; axis++) {
                            v[axis] = (value(m, axis * 4) * x + value(m, axis * 4 + 1) * y
                                    + value(m, axis * 4 + 3) - .5) * 16 + 8;
                        }
                        corners.add(v);
                    }
                }
                for (var index : triangle.getAsJsonArray("v")) {
                    var expected = vertices.get(index.getAsInt()).getAsJsonArray();
                    double closest = corners.stream().mapToDouble(v -> {
                        double d = 0; for (int a = 0; a < 3; a++) d += Math.pow(v[a] - value(expected, a), 2);
                        return Math.sqrt(d);
                    }).min().orElseThrow();
                    assertTrue(closest < .0001, kind + " triangle " + i + " displaced: " + closest);
                }
            }
        }
    }

    @Test void drawnAndReleasedBowShareMeshButUseUnchangedStringAndArrowGeometry() throws Exception {
        var drawn = asset("items/shadow_bow_h28_drawn").getAsJsonObject("model").getAsJsonArray("models");
        var rest = asset("items/shadow_bow_h28").getAsJsonObject("model").getAsJsonArray("models");
        assertEquals(drawn.size(), rest.size());
        for (int i = 0; i < drawn.size() - 1; i++) assertEquals(drawn.get(i), rest.get(i));
        for (String n : List.of("shadow_bow_h28_drawn", "shadow_bow_h28")) {
            var tail = asset("models/item/" + n);
            var old = asset("models/item/" + n.replace("h28", "h27"));
            int count = n.endsWith("drawn") ? 5 : 1;
            assertEquals(old.get("display"), tail.get("display"));
            assertEquals(count, tail.getAsJsonArray("elements").size());
            var es = old.getAsJsonArray("elements");
            for (int i = 0; i < count; i++) assertEquals(es.get(es.size() - count + i), tail.getAsJsonArray("elements").get(i));
        }
        assertEquals(asset("models/item/shadow_bow_h27_drawn").get("display"),
                asset("models/mesh/h28/bow_triangle").get("display"));
        assertEquals(asset("models/item/arc_staff_h27").get("display"),
                asset("models/mesh/h28/arc_triangle").get("display"));
    }

    @Test void manifestPinsRuntimeBytesAndEnergyRootsStayOnTheNewBody() throws Exception {
        var manifest = read("art/mesh/supers/h28/manifest.json");
        var hashes = manifest.getAsJsonObject("runtime_sha256");
        for (var e : hashes.entrySet()) {
            byte[] bytes = Files.readAllBytes(Path.of("src/main/resources/assets/destiny/" + e.getKey()));
            assertEquals(e.getValue().getAsString(), HexFormat.of().formatHex(java.security.MessageDigest.getInstance("SHA-256").digest(bytes)));
        }
        var strands = SuperEnergyGeometry.bow(0);
        assertEquals(7.35, strands.get(0).from().x);
        assertEquals(7.35, strands.get(1).from().x);
        assertEquals(16.24, strands.get(2).to().x);
    }

    @Test void voidMaterialLiftRetainsSourceDiffuseButIsVisiblyViolet() throws Exception {
        var source = read("art/mesh/supers/h28/bow.mesh.json");
        assertTrue(source.has("material_approximation"));
        for (var triangle : source.getAsJsonArray("triangles")) {
            var t = triangle.getAsJsonObject();
            assertTrue(t.has("diffuse_color"));
            int color = t.get("color").getAsInt();
            int r = color >> 16 & 255, g = color >> 8 & 255, b = color & 255;
            assertTrue(b > r && r > g && b >= 140, "Dark diffuse must not become a black/brown void body");
        }
    }

    @Test void triangleCutoutAndMirroredBackFaceDoNotDrawTheFourthCorner() throws Exception {
        var image = javax.imageio.ImageIO.read(Path.of("src/main/resources/assets/destiny/textures/item/supers/mesh_triangle_h28.png").toFile());
        assertEquals(128, image.getWidth()); assertEquals(128, image.getHeight());
        for (int y = 0; y < 128; y++) for (int x = 0; x < 128; x++) {
            assertEquals(x <= y ? 255 : 0, image.getRGB(x, y) >>> 24);
        }
        for (String kind : List.of("arc", "bow")) {
            var e = asset("models/mesh/h28/" + kind + "_triangle").getAsJsonArray("elements").get(0).getAsJsonObject();
            assertEquals(-16, e.getAsJsonArray("from").get(0).getAsInt());
            assertEquals(16, e.getAsJsonArray("to").get(1).getAsInt());
            var north = e.getAsJsonObject("faces").getAsJsonObject("north").getAsJsonArray("uv");
            var south = e.getAsJsonObject("faces").getAsJsonObject("south").getAsJsonArray("uv");
            assertEquals(north.get(0), south.get(2)); assertEquals(north.get(2), south.get(0));
        }
    }
}
