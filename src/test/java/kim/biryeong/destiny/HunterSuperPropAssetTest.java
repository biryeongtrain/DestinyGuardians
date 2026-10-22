package kim.biryeong.destiny;

import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import org.junit.jupiter.api.Test;

import javax.imageio.ImageIO;
import java.io.ByteArrayInputStream;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.Base64;
import java.util.HashSet;
import java.util.HexFormat;
import java.util.Map;
import java.util.Set;

import static org.junit.jupiter.api.Assertions.*;

/** H15 pack/source contract; visual and gameplay verification remain separate. */
class HunterSuperPropAssetTest {
    private static final String[] NAMES = {"arc_staff", "golden_gun", "shadow_bow", "shadow_arrow"};

    private byte[] resource(String path) throws Exception {
        try (var stream = getClass().getClassLoader().getResourceAsStream("assets/destiny/" + path)) {
            assertNotNull(stream, path);
            return stream.readAllBytes();
        }
    }

    private JsonObject json(String path) throws Exception {
        return JsonParser.parseString(new String(resource(path), StandardCharsets.UTF_8)).getAsJsonObject();
    }

    private JsonObject source(String name) throws Exception {
        return JsonParser.parseString(Files.readString(Path.of("art/blockbench/supers/" + name + ".bbmodel"))).getAsJsonObject();
    }

    private JsonArray elements(String name) throws Exception {
        return json("models/item/" + name + ".json").getAsJsonArray("elements");
    }

    private static double axis(JsonObject obj, String key, int axis) {
        return obj.getAsJsonArray(key).get(axis).getAsDouble();
    }

    private static boolean unrotated(JsonObject cube) {
        return !cube.has("rotation") || cube.getAsJsonObject("rotation").get("angle").getAsDouble() == 0;
    }

    private static boolean occupied(JsonArray elements, double x, double y, double z) {
        for (var element : elements) {
            var c = element.getAsJsonObject();
            if (!unrotated(c)) continue;
            if (x > axis(c, "from", 0) && x < axis(c, "to", 0)
                    && y > axis(c, "from", 1) && y < axis(c, "to", 1)
                    && z > axis(c, "from", 2) && z < axis(c, "to", 2)) return true;
        }
        return false;
    }

    @Test
    void existingRoutesAndProjectileResolveDetailedPortableGeometryAndOwnTextures() throws Exception {
        Set<String> atlasPaths = new HashSet<>();
        for (String name : NAMES) {
            var item = json("items/" + name + ".json").getAsJsonObject("model");
            assertEquals("minecraft:model", item.get("type").getAsString());
            assertEquals("destiny:item/" + name, item.get("model").getAsString());
            var model = json("models/item/" + name + ".json");
            var tex = model.getAsJsonObject("textures");
            assertEquals("destiny:item/supers/" + name, tex.get("0").getAsString());
            assertEquals(tex.get("0"), tex.get("particle"));
            assertTrue(atlasPaths.add(tex.get("0").getAsString()));
            var cubes = model.getAsJsonArray("elements");
            int minimum = name.equals("shadow_arrow") ? 24 : 160;
            int maximum = name.equals("shadow_arrow") ? 96 : 384;
            assertTrue(cubes.size() >= minimum && cubes.size() <= maximum, name + " detail/performance budget");
            for (var element : cubes) {
                var c = element.getAsJsonObject();
                for (int i = 0; i < 3; i++) {
                    assertTrue(Double.isFinite(axis(c, "from", i)) && Double.isFinite(axis(c, "to", i)));
                    assertTrue(axis(c, "from", i) >= -16 && axis(c, "to", i) <= 32, name + " Java bounds");
                    assertTrue(axis(c, "to", i) > axis(c, "from", i), name + " nonzero cube");
                }
                if (c.has("rotation")) {
                    var r = c.getAsJsonObject("rotation");
                    double angle = r.get("angle").getAsDouble();
                    assertTrue(Math.abs(angle) <= 45 && angle % 22.5 == 0, "Portable Java rotation");
                    assertTrue(Set.of("x", "y", "z").contains(r.get("axis").getAsString()));
                }
                assertEquals(6, c.getAsJsonObject("faces").size());
                for (var face : c.getAsJsonObject("faces").asMap().values()) {
                    assertEquals("#0", face.getAsJsonObject().get("texture").getAsString());
                    for (var uv : face.getAsJsonObject().getAsJsonArray("uv"))
                        assertTrue(uv.getAsDouble() >= 0 && uv.getAsDouble() <= 16);
                }
            }
            var image = ImageIO.read(new ByteArrayInputStream(resource("textures/item/supers/" + name + ".png")));
            assertNotNull(image); assertEquals(256, image.getWidth()); assertEquals(128, image.getHeight());
            Set<Integer> colors = new HashSet<>();
            for (int y = 0; y < 128; y++) for (int x = 0; x < 256; x++) {
                assertEquals(255, image.getRGB(x, y) >>> 24, "Opaque cutout atlas avoids blend sorting");
                colors.add(image.getRGB(x, y));
            }
            assertTrue(colors.size() >= 64, "Atlas includes material shading and etched details");
        }
    }

    @Test
    void editableSourcesMatchNativeExportsAndEmbeddedPng() throws Exception {
        for (String name : NAMES) {
            var bb = source(name);
            assertEquals("java_block", bb.getAsJsonObject("meta").get("model_format").getAsString());
            assertEquals(256, bb.getAsJsonObject("resolution").get("width").getAsInt());
            assertEquals(128, bb.getAsJsonObject("resolution").get("height").getAsInt());
            assertEquals(elements(name).size(), bb.getAsJsonArray("elements").size());
            assertFalse(bb.getAsJsonArray("outliner").isEmpty());
            String embedded = bb.getAsJsonArray("textures").get(0).getAsJsonObject().get("source").getAsString();
            assertArrayEquals(resource("textures/item/supers/" + name + ".png"),
                    Base64.getDecoder().decode(embedded.substring(embedded.indexOf(',') + 1)));
        }
    }

    private static void vector(JsonObject slot, String key, double[] expected, double fallback) {
        for (int i = 0; i < 3; i++)
            assertEquals(expected[i], slot.has(key) ? axis(slot, key, i) : fallback, 1e-9, key + " axis " + i);
    }

    @Test
    void originalGuiAndThirdPersonTransformsArePreservedWithCodecDefaultElision() throws Exception {
        Map<String, double[]> rotations = Map.of("arc_staff", new double[]{0, 0, -35},
                "golden_gun", new double[]{20, 135, -10}, "shadow_bow", new double[]{0, 20, -20});
        Map<String, Double> scales = Map.of("arc_staff", .6, "golden_gun", 1.2, "shadow_bow", .8);
        for (String name : rotations.keySet()) {
            var display = json("models/item/" + name + ".json").getAsJsonObject("display");
            var gui = display.getAsJsonObject("gui");
            vector(gui, "rotation", rotations.get(name), 0);
            double s = scales.get(name); vector(gui, "scale", new double[]{s, s, s}, 1);
            var hand = display.getAsJsonObject("thirdperson_righthand");
            vector(hand, "rotation", new double[]{0, 0, 0}, 0);
            vector(hand, "translation", new double[]{0, 2, 0}, 0);
            vector(hand, "scale", new double[]{1, 1, 1}, 1);
        }
    }

    @Test
    void lastWordRevolverHasOpenTriggerGuardAndMuzzleAndRoundCylinder() throws Exception {
        var gun = elements("golden_gun");
        assertFalse(occupied(gun, 8, 7.6, 7.4), "Trigger opening stays empty");
        assertFalse(occupied(gun, 8, 10.1, 16.0), "Muzzle opening stays empty");
        assertTrue(occupied(gun, 7.15, 10.1, 16.0), "Muzzle side rim exists");
        assertTrue(occupied(gun, 9.25, 9.93, 6), "Cylinder projects outside frame at equator");
        assertFalse(occupied(gun, 9.25, 11.15, 6), "Round cylinder narrows toward top");
        long slices = 0;
        for (var e : gun) if (e.getAsJsonObject().get("name").getAsString().startsWith("cylinder_round_slice_")) slices++;
        assertTrue(slices >= 16, "Visible cylinder cross section is rounded");
    }

    @Test
    void arcStaffAndVoidBowHavePairedForksAndOpenNegativeSpace() throws Exception {
        var staff = elements("arc_staff");
        Set<String> tips = new HashSet<>();
        for (var e : staff) {
            String n = e.getAsJsonObject().get("name").getAsString();
            if (n.startsWith("fork_plate_")) tips.add(n.split("_")[2] + "/" + n.split("_")[3]);
        }
        assertEquals(4, tips.size(), "Two prongs at both staff ends");
        assertFalse(occupied(staff, 8, 29, 8), "Fork gap remains open");
        var bow = elements("shadow_bow");
        long curves = 0, forks = 0;
        for (var e : bow) {
            String n = e.getAsJsonObject().get("name").getAsString();
            if (n.startsWith("curved_limb_")) curves++;
            if (n.startsWith("forked_tip_")) forks++;
        }
        assertTrue(curves >= 40 && forks >= 24, "Curved limbs and fork tips have actual geometry");
        assertFalse(occupied(bow, 9.5, 14, 8), "Space between limb and string stays empty");
        assertTrue(occupied(bow, 11.27, 14, 8), "Fine static string connects the tips");
    }

    @Test
    void projectileIsCenteredAndPointsAlongMinusZ() throws Exception {
        var arrow = elements("shadow_arrow");
        double[] min = {Double.POSITIVE_INFINITY, Double.POSITIVE_INFINITY, Double.POSITIVE_INFINITY};
        double[] max = {Double.NEGATIVE_INFINITY, Double.NEGATIVE_INFINITY, Double.NEGATIVE_INFINITY};
        for (var e : arrow) {
            var c = e.getAsJsonObject();
            assertTrue(unrotated(c), "No baked projectile orientation");
            for (int i = 0; i < 3; i++) { min[i] = Math.min(min[i], axis(c, "from", i)); max[i] = Math.max(max[i], axis(c, "to", i)); }
            String name = c.get("name").getAsString();
            if (name.startsWith("arrowhead_")) assertTrue(axis(c, "to", 2) < 3.5, "Tip at -Z");
            if (name.startsWith("spectral_fletching_")) assertTrue(axis(c, "from", 2) >= 11, "Fletching at +Z");
        }
        for (int i = 0; i < 3; i++) assertEquals(8, (min[i] + max[i]) / 2, 1e-9);
        assertEquals(2.38, max[0] - min[0], 1e-9); assertEquals(2.38, max[1] - min[1], 1e-9);
        assertEquals(14, max[2] - min[2], 1e-9);
    }

    @Test
    void referenceRecordsMatchFetchedFilesWithoutClaimingExtractedMeshes() throws Exception {
        var refs = JsonParser.parseString(Files.readString(Path.of("art/blockbench/supers/references/manifest.json"))).getAsJsonArray();
        assertTrue(refs.size() >= 4);
        for (var entry : refs) {
            var ref = entry.getAsJsonObject();
            assertEquals(200, ref.get("http_status").getAsInt());
            assertTrue(ref.get("page").getAsString().startsWith("https://www.destinypedia.com/"));
            byte[] image = Files.readAllBytes(Path.of(ref.get("file").getAsString()));
            assertEquals(ref.get("sha256").getAsString(), HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(image)));
        }
        var manifest = JsonParser.parseString(Files.readString(Path.of("art/blockbench/supers/manifest.json"))).getAsJsonObject();
        for (var model : manifest.getAsJsonArray("models"))
            assertEquals("original_reference_reconstruction", model.getAsJsonObject().get("design_status").getAsString());
    }
}
