package kim.biryeong.destiny.fx;

import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import net.minecraft.client.resources.model.cuboid.CuboidModel;
import org.junit.jupiter.api.Test;

import javax.imageio.ImageIO;
import java.io.ByteArrayInputStream;
import java.io.StringReader;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Base64;
import java.util.HashSet;
import java.util.List;

import static org.junit.jupiter.api.Assertions.*;

/** Asset contracts only: native parser, normalized geometry, editable sources and opaque UVs. */
class SuperEnergyAssetsH25Test {
    private static final List<String> NAMES = List.of(
            "arc_filament_h25", "void_filament_h25", "void_spark_h25");
    private static final List<String> SIDES = List.of("north", "east", "south", "west", "up", "down");
    private static final double EPSILON = 1e-7;

    private byte[] bytes(String relative) throws Exception {
        try (var stream = getClass().getResourceAsStream("/assets/destiny/" + relative)) {
            assertNotNull(stream, relative);
            return stream.readAllBytes();
        }
    }

    private JsonObject resource(String relative) throws Exception {
        return JsonParser.parseString(new String(bytes(relative), StandardCharsets.UTF_8)).getAsJsonObject();
    }

    private JsonObject model(String name) throws Exception {
        return resource("models/fx/" + name + ".json");
    }

    private double coordinate(JsonObject element, String key, int axis) {
        return element.getAsJsonArray(key).get(axis).getAsDouble();
    }

    private JsonObject named(JsonArray elements, String name) {
        for (var value : elements) {
            var element = value.getAsJsonObject();
            if (name.equals(element.get("name").getAsString())) return element;
        }
        throw new AssertionError("Missing cuboid " + name);
    }

    /** Apply the native single-axis rotation, including its origin, to a raw model point. */
    private double[] rotate(JsonObject element, double[] point) {
        if (!element.has("rotation")) return point;
        var rotation = element.getAsJsonObject("rotation");
        int axis = "xyz".indexOf(rotation.get("axis").getAsString());
        assertTrue(axis >= 0);
        int u = (axis + 1) % 3;
        int v = (axis + 2) % 3;
        var origin = rotation.getAsJsonArray("origin");
        double x = point[u] - origin.get(u).getAsDouble();
        double y = point[v] - origin.get(v).getAsDouble();
        double angle = Math.toRadians(rotation.get("angle").getAsDouble());
        point[u] = origin.get(u).getAsDouble() + x * Math.cos(angle) - y * Math.sin(angle);
        point[v] = origin.get(v).getAsDouble() + x * Math.sin(angle) + y * Math.cos(angle);
        return point;
    }

    private double[] capCenter(JsonObject element, boolean high) {
        return rotate(element, new double[]{
                (coordinate(element, "from", 0) + coordinate(element, "to", 0)) / 2,
                (coordinate(element, "from", 1) + coordinate(element, "to", 1)) / 2,
                coordinate(element, high ? "to" : "from", 2)});
    }

    @Test void allThreeItemsResolveThroughTheNativeCuboidParserWithIdentityFixedDisplay() throws Exception {
        for (String name : NAMES) {
            var model = model(name);
            assertEquals("1.21.11", model.get("format_version").getAsString());
            assertNotNull(CuboidModel.fromStream(new StringReader(model.toString())), name);
            var item = resource("items/fx/" + name + ".json").getAsJsonObject("model");
            assertEquals("minecraft:model", item.get("type").getAsString());
            assertEquals("destiny:fx/" + name, item.get("model").getAsString());
            assertFalse(model.has("parent"));
            assertFalse(model.get("ambientocclusion").getAsBoolean());
            var fixed = model.getAsJsonObject("display").getAsJsonObject("fixed");
            for (int axis = 0; axis < 3; axis++) {
                assertEquals(0, fixed.getAsJsonArray("rotation").get(axis).getAsDouble());
                assertEquals(0, fixed.getAsJsonArray("translation").get(axis).getAsDouble());
                assertEquals(1, fixed.getAsJsonArray("scale").get(axis).getAsDouble());
            }
        }
    }

    @Test void rotatedGeometryMeetsEndpointsThinEnvelopesAndCuboidBudgets() throws Exception {
        for (String name : NAMES) {
            var elements = model(name).getAsJsonArray("elements");
            assertTrue(elements.size() > 0 && elements.size() <= 36, name);
            double[] low = {Double.POSITIVE_INFINITY, Double.POSITIVE_INFINITY, Double.POSITIVE_INFINITY};
            double[] high = {Double.NEGATIVE_INFINITY, Double.NEGATIVE_INFINITY, Double.NEGATIVE_INFINITY};
            for (var value : elements) {
                var element = value.getAsJsonObject();
                for (int axis = 0; axis < 3; axis++) {
                    assertTrue(Double.isFinite(coordinate(element, "from", axis)));
                    assertTrue(Double.isFinite(coordinate(element, "to", axis)));
                    assertTrue(coordinate(element, "from", axis) < coordinate(element, "to", axis));
                }
                for (int mask = 0; mask < 8; mask++) {
                    var point = new double[3];
                    for (int axis = 0; axis < 3; axis++) {
                        point[axis] = coordinate(element, (mask & (1 << axis)) == 0 ? "from" : "to", axis);
                    }
                    point = rotate(element, point);
                    for (int axis = 0; axis < 3; axis++) {
                        low[axis] = Math.min(low[axis], point[axis]);
                        high[axis] = Math.max(high[axis], point[axis]);
                    }
                }
            }
            if (name.contains("filament")) {
                for (int axis = 0; axis < 2; axis++) {
                    assertTrue(high[axis] - low[axis] <= 1.6 + EPSILON, "At most .10 blocks laterally");
                    assertTrue(low[axis] >= 7.2 - EPSILON && high[axis] <= 8.8 + EPSILON);
                }
                assertEquals(-8, low[2], EPSILON);
                assertEquals(8, high[2], EPSILON);
                // Both opaque layers form a continuous centerline with exact one-block endpoints.
                for (String layer : List.of("outer", "spine")) {
                    assertArrayEquals(new double[]{8, 8, 8}, capCenter(named(elements, "main_00_" + layer), true), EPSILON);
                    assertArrayEquals(new double[]{8, 8, -8}, capCenter(named(elements, "main_11_" + layer), false), EPSILON);
                    for (int i = 0; i < 11; i++) {
                        assertArrayEquals(capCenter(named(elements, "main_%02d_%s".formatted(i, layer)), false),
                                capCenter(named(elements, "main_%02d_%s".formatted(i + 1, layer)), true), EPSILON);
                    }
                }
                if (name.startsWith("arc")) {
                    assertEquals(32, elements.size());
                    for (int branch = 0; branch < 2; branch++) {
                        for (int segment = 0; segment < 2; segment++) {
                            named(elements, "branch_" + branch + "_" + segment + "_outer");
                        }
                    }
                } else {
                    assertEquals(28, elements.size());
                    named(elements, "fragment_0_shard");
                    named(elements, "fragment_1_shard");
                }
            } else {
                assertEquals(26, elements.size());
                for (int axis = 0; axis < 3; axis++) {
                    assertTrue(high[axis] - low[axis] <= 1.92 + EPSILON, "At most .12 blocks before native scale");
                    assertEquals(8, (low[axis] + high[axis]) / 2, EPSILON);
                }
                assertEquals(1.92, high[0] - low[0], EPSILON);
                assertEquals(1.92, high[1] - low[1], EPSILON);
                for (int edge = 0; edge < 4; edge++) named(elements, "diamond_edge_" + edge + "_outer");
            }
        }
    }

    @Test void editableSourcesMatchEveryCuboidRotationUvAndEmbeddedOriginalPng() throws Exception {
        for (String name : NAMES) {
            var source = JsonParser.parseString(Files.readString(Path.of("art/blockbench/vfx_h25/" + name + ".bbmodel"))).getAsJsonObject();
            assertEquals("java_block", source.getAsJsonObject("meta").get("model_format").getAsString());
            assertEquals("1.21.11", source.get("java_block_version").getAsString());
            var nativeElements = model(name).getAsJsonArray("elements");
            var savedElements = source.getAsJsonArray("elements");
            assertEquals(nativeElements.size(), savedElements.size());
            var ids = new HashSet<String>();
            for (int i = 0; i < savedElements.size(); i++) {
                var nativeElement = nativeElements.get(i).getAsJsonObject();
                var saved = savedElements.get(i).getAsJsonObject();
                for (String key : List.of("name", "from", "to", "shade", "light_emission")) {
                    assertEquals(nativeElement.get(key), saved.get(key), key);
                }
                assertEquals("cube", saved.get("type").getAsString());
                assertTrue(ids.add(saved.get("uuid").getAsString()));
                assertFalse(saved.get("rescale").getAsBoolean());
                for (int axis = 0; axis < 3; axis++) {
                    double expected = 0;
                    if (nativeElement.has("rotation")) {
                        var rotation = nativeElement.getAsJsonObject("rotation");
                        assertEquals(rotation.get("origin"), saved.get("origin"));
                        if ("xyz".indexOf(rotation.get("axis").getAsString()) == axis) {
                            expected = rotation.get("angle").getAsDouble();
                        }
                    }
                    assertEquals(expected, saved.getAsJsonArray("rotation").get(axis).getAsDouble(), EPSILON);
                }
                for (String side : SIDES) {
                    var nativeUv = nativeElement.getAsJsonObject("faces").getAsJsonObject(side).getAsJsonArray("uv");
                    var savedFace = saved.getAsJsonObject("faces").getAsJsonObject(side);
                    assertEquals(0, savedFace.get("texture").getAsInt());
                    for (int uv = 0; uv < 4; uv++) {
                        assertEquals(nativeUv.get(uv).getAsDouble() * 4,
                                savedFace.getAsJsonArray("uv").get(uv).getAsDouble(), EPSILON);
                    }
                }
            }
            var groupIds = new HashSet<String>();
            for (var group : source.getAsJsonArray("groups")) {
                assertTrue(groupIds.add(group.getAsJsonObject().get("uuid").getAsString()));
            }
            for (var group : source.getAsJsonArray("outliner")) {
                assertTrue(groupIds.remove(group.getAsJsonObject().get("uuid").getAsString()));
                for (var id : group.getAsJsonObject().getAsJsonArray("children")) assertTrue(ids.remove(id.getAsString()));
            }
            assertTrue(ids.isEmpty() && groupIds.isEmpty(), "Each source group and cuboid appears exactly once");
            var png = bytes("textures/item/fx/" + name + ".png");
            var texture = source.getAsJsonArray("textures").get(0).getAsJsonObject();
            assertArrayEquals(png, Base64.getDecoder().decode(texture.get("source").getAsString().split(",", 2)[1]));
            assertEquals(64, texture.get("uv_width").getAsInt());
            assertEquals(64, texture.get("uv_height").getAsInt());
        }
    }

    @Test void originalOpaqueAtlasesHaveValidNondegenerateUvsAndFullEmission() throws Exception {
        for (String name : NAMES) {
            var model = model(name);
            var texture = "destiny:item/fx/" + name;
            assertEquals(texture, model.getAsJsonObject("textures").get("0").getAsString());
            assertEquals(texture, model.getAsJsonObject("textures").get("particle").getAsString());
            var image = ImageIO.read(new ByteArrayInputStream(bytes("textures/item/fx/" + name + ".png")));
            assertNotNull(image);
            assertEquals(64, image.getWidth());
            assertEquals(64, image.getHeight());
            var colors = new HashSet<Integer>();
            for (int y = 0; y < 64; y++) {
                for (int x = 0; x < 64; x++) {
                    int color = image.getRGB(x, y);
                    assertEquals(255, color >>> 24);
                    colors.add(color);
                }
            }
            assertTrue(colors.size() > 100, "Procedural surface variation rather than a flat color atlas");
            for (var value : model.getAsJsonArray("elements")) {
                var element = value.getAsJsonObject();
                assertEquals(15, element.get("light_emission").getAsInt());
                assertFalse(element.get("shade").getAsBoolean());
                assertEquals(6, element.getAsJsonObject("faces").size());
                for (String side : SIDES) {
                    var face = element.getAsJsonObject("faces").getAsJsonObject(side);
                    assertEquals("#0", face.get("texture").getAsString());
                    var uv = face.getAsJsonArray("uv");
                    assertEquals(4, uv.size());
                    for (var coordinate : uv) {
                        assertTrue(Double.isFinite(coordinate.getAsDouble()));
                        assertTrue(coordinate.getAsDouble() >= 0 && coordinate.getAsDouble() <= 16);
                    }
                    assertTrue(uv.get(0).getAsDouble() < uv.get(2).getAsDouble());
                    assertTrue(uv.get(1).getAsDouble() < uv.get(3).getAsDouble());
                }
            }
        }
    }
}
