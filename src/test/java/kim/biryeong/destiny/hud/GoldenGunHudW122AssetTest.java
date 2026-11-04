package kim.biryeong.destiny.hud;

import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import org.junit.jupiter.api.Test;

import javax.imageio.ImageIO;
import java.awt.image.BufferedImage;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.Arrays;
import java.util.HexFormat;
import java.util.Set;

import static org.junit.jupiter.api.Assertions.*;

/** Standalone asset/source contracts; no Minecraft bootstrap or native HUD claim. */
class GoldenGunHudW122AssetTest {
    private static final String A = "src/main/resources/assets/destiny/";
    private static final String ART = "art/weapons/w122/golden_gun_hud/";
    private static final String NAME = "ammo_golden_gun_w122";
    private static final String SOURCE = A + "models/item/golden_gun_h29.json";
    private static final String ITEM = A + "items/golden_gun_h29.json";
    private static final String PRIMITIVE = A + "models/mesh/h29/golden_gun_triangle.json";
    private static final String MESH = "art/mesh/supers/h29/golden_gun.mesh.json";

    private static JsonObject object(String path) throws Exception {
        return JsonParser.parseString(Files.readString(Path.of(path))).getAsJsonObject();
    }
    private static JsonObject manifest() throws Exception { return object(ART + "manifest.json"); }
    private static String hash(byte[] bytes) throws Exception {
        return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes));
    }
    private static BufferedImage image(String name) throws Exception {
        return ImageIO.read(Path.of(A + "textures/item/hud/" + name + ".png").toFile());
    }
    private static byte[] alpha(BufferedImage image) {
        byte[] result = new byte[image.getWidth() * image.getHeight()];
        for (int y = 0; y < image.getHeight(); y++) for (int x = 0; x < image.getWidth(); x++)
            result[y * image.getWidth() + x] = (byte)(image.getRGB(x, y) >>> 24);
        return result;
    }

    @Test void actualHeldPathUsesCompositeNotEmptyMetadataOrUnderlyingAce() throws Exception {
        var m = manifest();
        assertEquals(SOURCE, m.get("source_model").getAsString());
        assertEquals("1c12e34eb47e86500592f62a5fe5a2f359ca8f76d5ae72ad6092c5e8d11027df",
                hash(Files.readAllBytes(Path.of(SOURCE))), "Current requested metadata source");
        assertEquals(m.get("source_sha256").getAsString(), hash(Files.readAllBytes(Path.of(SOURCE))));
        assertEquals(0, object(SOURCE).getAsJsonArray("elements").size());
        assertEquals(ITEM, m.get("runtime_item").getAsString());
        assertEquals(PRIMITIVE, m.get("runtime_primitive").getAsString());
        String visuals = Files.readString(Path.of("src/main/java/kim/biryeong/destiny/fx/SuperVisuals.java"));
        assertTrue(visuals.contains("case SOLAR -> \"golden_gun_h29\""));
        assertTrue(visuals.contains("stack.set(DataComponents.ITEM_MODEL, DestinyGuardians.id(name))"));
        String session = Files.readString(Path.of("src/main/java/kim/biryeong/destiny/ability/hunter/HunterSuper.java"));
        String golden = session.substring(session.indexOf("private final class GoldenGun"));
        assertTrue(golden.contains("handItem(kim.biryeong.destiny.fx.SuperVisuals.item(element()))"));
        var root = object(ITEM).getAsJsonObject("model");
        assertEquals("composite", root.get("type").getAsString());
        assertEquals(2350, root.getAsJsonArray("models").size());
        for (var child : root.getAsJsonArray("models"))
            assertEquals("destiny:mesh/h29/golden_gun_triangle", child.getAsJsonObject().get("model").getAsString());
    }

    @Test void allCurrentInputsAndFourOutputHashesAreExact() throws Exception {
        var m = manifest();
        var inputs = m.getAsJsonObject("inputs_sha256");
        assertEquals(11, inputs.size());
        for (String required : new String[]{SOURCE, ITEM, PRIMITIVE, MESH,
                A + "textures/item/supers/mesh_triangle_h28.png", "scripts/build_weapon_hud_w112.py",
                "scripts/build_golden_gun_hud_w122.py"}) assertTrue(inputs.has(required), required);
        for (var entry : inputs.entrySet())
            assertEquals(entry.getValue().getAsString(), hash(Files.readAllBytes(Path.of(entry.getKey()))), entry.getKey());
        var outputs = m.getAsJsonObject("outputs_sha256");
        assertEquals(Set.of(A + "items/gui/hud/" + NAME + ".json", A + "models/gui/hud/" + NAME + ".json",
                A + "textures/item/hud/" + NAME + ".png", ART + "contact.png"), outputs.keySet());
        for (var entry : outputs.entrySet())
            assertEquals(entry.getValue().getAsString(), hash(Files.readAllBytes(Path.of(entry.getKey()))), entry.getKey());
        var contact = ImageIO.read(Path.of(ART + "contact.png").toFile());
        assertEquals(800, contact.getWidth()); assertEquals(330, contact.getHeight());
    }

    @Test void runtimeMatricesRecoverEveryIndependentSourceMeshVertex() throws Exception {
        var mesh = object(MESH); var vertices = mesh.getAsJsonArray("vertices");
        var source = mesh.getAsJsonArray("triangles"); var actual = object(ITEM).getAsJsonObject("model").getAsJsonArray("models");
        assertEquals(source.size(), actual.size()); assertEquals(2350, source.size());
        double[][] unit = {{0, 0, 0}, {-1, 0, 0}, {0, 1, 0}};
        double maxError = 0;
        for (int i = 0; i < actual.size(); i++) {
            JsonArray matrix = actual.get(i).getAsJsonObject().getAsJsonArray("transformation");
            assertEquals(16, matrix.size());
            for (int j = 0; j < 4; j++) assertEquals(j == 3 ? 1 : 0, matrix.get(12 + j).getAsDouble());
            JsonArray indices = source.get(i).getAsJsonObject().getAsJsonArray("v");
            for (int v = 0; v < 3; v++) for (int axis = 0; axis < 3; axis++) {
                double coord = matrix.get(axis * 4 + 3).getAsDouble();
                for (int k = 0; k < 3; k++) coord += unit[v][k] * matrix.get(axis * 4 + k).getAsDouble();
                double expected = vertices.get(indices.get(v).getAsInt()).getAsJsonArray().get(axis).getAsDouble();
                maxError = Math.max(maxError, Math.abs(coord * 16 - expected));
            }
        }
        assertTrue(maxError < 0.00001, "Actual runtime matrices reconstruct original H29 mesh");
        assertEquals(maxError, manifest().get("max_runtime_mesh_vertex_error").getAsDouble(), 1e-12);
        var element = object(PRIMITIVE).getAsJsonArray("elements").get(0).getAsJsonObject();
        assertEquals("[-16,0,0]", element.getAsJsonArray("from").toString());
        assertEquals("[0,16,0]", element.getAsJsonArray("to").toString());
        assertEquals("[0,0,16,16]", element.getAsJsonObject("faces").getAsJsonObject("north").getAsJsonArray("uv").toString());
        assertEquals("[16,0,0,16]", element.getAsJsonObject("faces").getAsJsonObject("south").getAsJsonArray("uv").toString());
        var atlas = ImageIO.read(Path.of(A + "textures/item/supers/mesh_triangle_h28.png").toFile());
        assertEquals(128, atlas.getWidth()); assertEquals(128, atlas.getHeight());
        for (int y = 0; y < 128; y++) for (int x = 0; x < 128; x++)
            assertEquals(x <= y ? 255 : 0, atlas.getRGB(x, y) >>> 24, "Alpha-cut triangle, never full rectangle");
    }

    @Test void neutralRgbaHasClearPaddingOpaqueCoreAntialiasAndTriggerHole() throws Exception {
        var im = image(NAME); var m = manifest();
        assertEquals(160, im.getWidth()); assertEquals(64, im.getHeight());
        assertTrue(im.getColorModel().hasAlpha()); assertEquals(4, im.getColorModel().getNumComponents());
        int visible = 0, opaque = 0, partial = 0, left = 160, top = 64, right = 0, bottom = 0;
        for (int y = 0; y < 64; y++) for (int x = 0; x < 160; x++) {
            int pixel = im.getRGB(x, y), a = pixel >>> 24;
            assertEquals(0xffffff, pixel & 0xffffff, "No baked gold, including transparent pixels");
            if (x < 4 || x >= 156 || y < 4 || y >= 60) assertEquals(0, a, "W112 padding");
            if (a > 0) {
                visible++; left = Math.min(left, x); top = Math.min(top, y);
                right = Math.max(right, x + 1); bottom = Math.max(bottom, y + 1);
                if (a == 255) opaque++; else partial++;
            }
        }
        assertTrue(visible > 3000 && visible < 4000, "Bounded actual revolver coverage");
        assertTrue(opaque > 2500 && partial > 100, "Solid core with coverage edges");
        assertEquals(m.get("visible_pixels").getAsInt(), visible);
        assertEquals("[" + left + "," + top + "," + right + "," + bottom + "]", m.getAsJsonArray("alpha_bbox").toString());
        assertEquals(m.get("alpha_sha256").getAsString(), hash(alpha(im)));
        // Interior of actual trigger guard, plus barrel-left / grip-bottom-right.
        assertEquals(0, im.getRGB(101, 37) >>> 24);
        assertEquals(255, im.getRGB(30, 12) >>> 24);
        assertEquals(255, im.getRGB(128, 50) >>> 24);
        assertEquals(0, im.getRGB(30, 50) >>> 24);
    }

    private static double edge(double[] a, double[] b, double x, double y) {
        return (b[0] - a[0]) * (y - a[1]) - (b[1] - a[1]) * (x - a[0]);
    }
    private static boolean inside(double[][] p, double x, double y) {
        double a = edge(p[0], p[1], x, y), b = edge(p[1], p[2], x, y), c = edge(p[2], p[0], x, y);
        return (a >= 0 && b >= 0 && c >= 0) || (a <= 0 && b <= 0 && c <= 0);
    }
    private static double iou(boolean[] expected, BufferedImage actual, boolean flipX, boolean flipY) {
        int intersection = 0, union = 0;
        for (int y = 0; y < 64; y++) for (int x = 0; x < 160; x++) {
            boolean a = (actual.getRGB(flipX ? 159 - x : x, flipY ? 63 - y : y) >>> 24) >= 128;
            boolean e = expected[y * 160 + x];
            if (a && e) intersection++; if (a || e) union++;
        }
        return (double)intersection / union;
    }

    @Test void independentSourceMeshCoverageRejectsMirroredOrUpsideDownSilhouette() throws Exception {
        var m = manifest(); var orientation = m.getAsJsonObject("orientation");
        assertEquals("YZ", orientation.get("plane").getAsString());
        assertEquals("-Z", orientation.get("screen_x").getAsString());
        assertEquals("-Y", orientation.get("screen_y").getAsString());
        assertEquals(180, orientation.get("side_rotation_degrees").getAsInt());
        assertEquals("[160,64]", m.getAsJsonArray("texture_size").toString());
        assertEquals("[80,32]", m.getAsJsonArray("selected_quad_size").toString());
        assertEquals(4, m.get("padding_pixels").getAsInt()); assertEquals(8, m.get("supersampling").getAsInt());
        var mesh = object(MESH); var vertices = mesh.getAsJsonArray("vertices");
        assertTrue(mesh.get("coordinate_mapping").getAsString().contains("muzzle+Z"));
        double[][] points = new double[vertices.size()][2];
        double x0 = Double.POSITIVE_INFINITY, y0 = x0, x1 = Double.NEGATIVE_INFINITY, y1 = x1;
        for (int i = 0; i < points.length; i++) {
            var v = vertices.get(i).getAsJsonArray(); points[i] = new double[]{-v.get(2).getAsDouble(), -v.get(1).getAsDouble()};
            x0 = Math.min(x0, points[i][0]); y0 = Math.min(y0, points[i][1]);
            x1 = Math.max(x1, points[i][0]); y1 = Math.max(y1, points[i][1]);
        }
        double scale = Math.min(151 / (x1 - x0), 55 / (y1 - y0));
        assertEquals(scale, m.get("pixels_per_model_unit").getAsDouble(), 0.00001);
        for (double[] p : points) {
            p[0] = (p[0] - x0) * scale + (159 - (x1 - x0) * scale) / 2;
            p[1] = (p[1] - y0) * scale + (63 - (y1 - y0) * scale) / 2;
        }
        // Independent oracle: original source triangles, pixel-center point inclusion.
        // It does not consume generated masks, composite matrices, or manifest bounds.
        boolean[] expected = new boolean[160 * 64];
        for (var entry : mesh.getAsJsonArray("triangles")) {
            JsonArray v = entry.getAsJsonObject().getAsJsonArray("v");
            double[][] p = {points[v.get(0).getAsInt()], points[v.get(1).getAsInt()], points[v.get(2).getAsInt()]};
            if (Math.abs(edge(p[0], p[1], p[2][0], p[2][1])) < 1e-10) continue;
            for (int y = 0; y < 64; y++) for (int x = 0; x < 160; x++)
                if (inside(p, x + .5, y + .5)) expected[y * 160 + x] = true;
        }
        var actual = image(NAME);
        double score = iou(expected, actual, false, false);
        System.out.printf("W122 independent source mesh IoU=%.6f; mirrored=%.6f; upsideDown=%.6f%n",
                score, iou(expected, actual, true, false), iou(expected, actual, false, true));
        assertTrue(score > .97, "Independent source silhouette IoU=" + score);
        assertTrue(iou(expected, actual, true, false) < .7, "Mirrored muzzle negative control");
        assertTrue(iou(expected, actual, false, true) < .7, "Upside-down grip negative control");
    }

    @Test void dedicatedTransportPreservesTintAndOnlySuperSelectedBranchChanges() throws Exception {
        var item = object(A + "items/gui/hud/" + NAME + ".json");
        var model = object(A + "models/gui/hud/" + NAME + ".json");
        var expectedItem = object(A + "items/gui/hud/ammo_weapon_w112_ace_of_spades.json");
        var expectedModel = object(A + "models/gui/hud/ammo_weapon_w112_ace_of_spades.json");
        expectedItem.getAsJsonObject("model").addProperty("model", "destiny:gui/hud/" + NAME);
        expectedModel.getAsJsonObject("textures").addProperty("layer0", "destiny:item/hud/" + NAME);
        assertEquals(expectedItem, item); assertEquals(expectedModel, model);
        var tint = item.getAsJsonObject("model").getAsJsonArray("tints").get(0).getAsJsonObject();
        assertEquals("minecraft:custom_model_data", tint.get("type").getAsString());
        assertEquals(0, tint.get("index").getAsInt()); assertEquals(0xffffff, tint.get("default").getAsInt());
        assertEquals("#layer0", model.getAsJsonObject("textures").get("particle").getAsString());
        for (var element : model.getAsJsonArray("elements")) for (var face : element.getAsJsonObject().getAsJsonObject("faces").entrySet())
            assertEquals(0, face.getValue().getAsJsonObject().get("tintindex").getAsInt());
        String hud = Files.readString(Path.of("src/main/java/kim/biryeong/destiny/hud/AmmoHud.java"));
        assertTrue(hud.contains("String silhouette = state.superWeapon() ? \"" + NAME + "\"\n"
                + "                : \"ammo_weapon_w112_\" + WeaponItems.entry(player.getMainHandItem()).orElseThrow().id();"));
        assertTrue(hud.contains("sprite(player, PREFIX + \"weapon\", silhouette, 336, 948, 80, 32, 2,"));
        assertTrue(hud.contains("state.superWeapon() ? 0xF4D36A : 0xC7CDD4"));
        assertTrue(hud.contains("\"ammo_weapon_w112_\"+equipped.weapon().id(),329,y,50,20,2,0xA9B0B9"));
        assertFalse(Arrays.equals(alpha(image(NAME)), alpha(image("ammo_weapon_w112_ace_of_spades"))));
        assertFalse(Arrays.equals(alpha(image(NAME)), alpha(image("ammo_hand_cannon"))));
        String gt = Files.readString(Path.of("src/gametest/java/kim/biryeong/destiny/test/WeaponFeedbackW112GameTests.java"));
        assertTrue(gt.contains(".equals(\"destiny:gui/hud/" + NAME + "\"),\"Golden Gun does not borrow underlying Ace silhouette\""));
    }
}
