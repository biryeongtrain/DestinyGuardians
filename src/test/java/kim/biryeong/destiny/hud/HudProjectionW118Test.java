package kim.biryeong.destiny.hud;

import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import net.minecraft.client.resources.model.ModelDebugName;
import net.minecraft.client.resources.model.cuboid.CuboidModel;
import net.minecraft.client.resources.model.cuboid.CuboidModelElement;
import net.minecraft.client.resources.model.cuboid.FaceBakery;
import net.minecraft.client.resources.model.cuboid.UnbakedCuboidGeometry;
import net.minecraft.client.resources.model.sprite.TextureSlots;
import org.joml.Matrix4f;
import org.joml.Matrix4fc;
import org.joml.Vector3f;
import org.joml.Vector3fc;
import org.junit.jupiter.api.Test;

import java.io.StringReader;
import java.lang.reflect.Method;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.HexFormat;
import java.util.List;
import java.util.Set;

import static org.junit.jupiter.api.Assertions.*;

/** Installed 26.3 ELEMENT parser and FaceBakery vertex path versus Python fixtures.
 * No ItemTransform approximation, graphics context, client, or native gameplay claim.
 * The private vertex helper is the exact method invoked by FaceBakery.bakeVertex;
 * reflection intentionally fails if the installed engine changes that contract. */
class HudProjectionW118Test {
    private static final Path FIXTURE = Path.of("src/test/resources/weapon_hud_w118/rotation-fixtures.json");
    private static final String ASSETS = "src/main/resources/assets/destiny/";
    private static final ModelDebugName DEBUG = () -> "W118 HUD texture resolution";

    private static JsonObject object(Path path) throws Exception {
        return JsonParser.parseString(Files.readString(path)).getAsJsonObject();
    }

    private static JsonObject fixture() throws Exception { return object(FIXTURE); }

    private static Vector3f vector(JsonArray xyz) {
        return new Vector3f(xyz.get(0).getAsFloat(), xyz.get(1).getAsFloat(), xyz.get(2).getAsFloat());
    }

    private static CuboidModelElement element(JsonObject data) {
        JsonObject model = new JsonObject();
        JsonArray elements = new JsonArray(); elements.add(data); model.add("elements", elements);
        return ((UnbakedCuboidGeometry) CuboidModel.fromStream(new StringReader(model.toString()))
                .geometry()).elements().getFirst();
    }

    private static List<Vector3f> engineCorners(JsonObject data) throws Exception {
        var e = element(data);
        Method rotate = FaceBakery.class.getDeclaredMethod("rotateVertexBy", Vector3f.class, Vector3fc.class, Matrix4fc.class);
        rotate.setAccessible(true);
        List<Vector3f> points = new ArrayList<>();
        // Same model-unit division, parsed origin and transform, and vertex helper
        // used by FaceBakery.bakeVertex. Preserve itertools.product corner order.
        for (int x = 0; x < 2; x++) for (int y = 0; y < 2; y++) for (int z = 0; z < 2; z++) {
            var p = new Vector3f((x == 0 ? e.from() : e.to()).x(),
                    (y == 0 ? e.from() : e.to()).y(), (z == 0 ? e.from() : e.to()).z()).div(16);
            if (e.rotation() != null) rotate.invoke(null, p, e.rotation().origin(), e.rotation().transform());
            points.add(p.mul(16));
        }
        return points;
    }

    private static void matches(JsonObject sample, List<Vector3f> points, double tolerance) {
        assertEquals(8, points.size());
        JsonArray expected = sample.getAsJsonArray("python_corners");
        assertEquals(8, expected.size());
        for (int i = 0; i < 8; i++) {
            var p = points.get(i);
            assertTrue(p.isFinite());
            for (int axis = 0; axis < 3; axis++)
                assertEquals(expected.get(i).getAsJsonArray().get(axis).getAsDouble(), p.get(axis), tolerance,
                        sample.get("name") + " corner " + i + " axis " + axis);
            var gun = sample.getAsJsonArray("gun_yz").get(i).getAsJsonArray();
            assertEquals(gun.get(0).getAsDouble(), p.z(), tolerance);
            assertEquals(gun.get(1).getAsDouble(), -p.y(), tolerance);
            var melee = sample.getAsJsonArray("melee_yz").get(i).getAsJsonArray();
            assertEquals(melee.get(0).getAsDouble(), p.y(), tolerance);
            assertEquals(melee.get(1).getAsDouble(), p.z(), tolerance);
        }
    }

    @Test void pythonCornersAndBothProjectionsMatchInstalledElementBaker() throws Exception {
        var data = fixture();
        double tolerance = data.get("tolerance_model_units").getAsDouble();
        assertEquals(0.00005, tolerance);
        var cases = data.getAsJsonArray("cases");
        assertEquals(105, cases.size()); // 71 product + 10 identity/native + 24 rescale
        for (var sample : cases) {
            var s = sample.getAsJsonObject();
            matches(s, engineCorners(s.getAsJsonObject("element")), tolerance);
        }
        System.out.println("W118 native element corners checked: " + cases.size() * 8 + " (two projection policies)");
    }

    @Test void historicalFixturesCoverEveryCanonicalRotationWithExactSources() throws Exception {
        Set<String> actual = new HashSet<>(), expected = new HashSet<>();
        for (var sample : fixture().getAsJsonArray("cases")) {
            var s = sample.getAsJsonObject();
            if (!s.has("source_model")) continue;
            Path path = Path.of(s.get("source_model").getAsString());
            String hash = HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(path)));
            assertEquals(s.get("source_sha256").getAsString(), hash);
            int index = s.get("source_element").getAsInt();
            assertEquals(object(path).getAsJsonArray("elements").get(index), s.getAsJsonObject("element"));
            assertTrue(actual.add(path + ":" + index));
        }
        var manifest = object(Path.of("art/weapons/w112/hud/manifest.json"));
        for (var weapon : manifest.getAsJsonArray("weapons")) {
            // Pinned W118 baseline remains canonical after W137 remodeling.
            Path path = Path.of(weapon.getAsJsonObject().get("canonical_model").getAsString());
            var elements = object(path).getAsJsonArray("elements");
            for (int i = 0; i < elements.size(); i++)
                if (elements.get(i).getAsJsonObject().has("rotation")) expected.add(path + ":" + i);
        }
        assertEquals(71, expected.size());
        assertEquals(expected, actual);
    }

    @Test void negativeControlRejectsHistoricalRxRyRzForNativeElement() throws Exception {
        JsonObject sample = fixture().getAsJsonArray("cases").get(2).getAsJsonObject();
        JsonObject data = sample.getAsJsonObject("element");
        var e = element(data);
        JsonObject r = data.getAsJsonObject("rotation");
        var wrong = new Matrix4f().rotationXYZ((float) Math.toRadians(r.get("x").getAsDouble()),
                (float) Math.toRadians(r.get("y").getAsDouble()), (float) Math.toRadians(r.get("z").getAsDouble()));
        List<Vector3f> points = new ArrayList<>();
        for (int x = 0; x < 2; x++) for (int y = 0; y < 2; y++) for (int z = 0; z < 2; z++) {
            var p = new Vector3f((x == 0 ? e.from() : e.to()).x(),
                    (y == 0 ? e.from() : e.to()).y(), (z == 0 ? e.from() : e.to()).z());
            var origin = vector(r.getAsJsonArray("origin"));
            wrong.transformPosition(p.sub(origin)).add(origin); points.add(p);
        }
        assertThrows(AssertionError.class, () -> matches(sample, points, 0.00005));
        matches(sample, engineCorners(data), 0.00005);
    }

    @Test void negativeControlRejectsPerturbedPythonFixtureCorner() throws Exception {
        var sample = fixture().getAsJsonArray("cases").get(2).getAsJsonObject();
        var points = engineCorners(sample.getAsJsonObject("element"));
        points.getFirst().add(0.01f, 0.02f, 0.03f);
        assertThrows(AssertionError.class, () -> matches(sample, points, 0.00005));
    }

    private static TextureSlots slots(JsonObject model) {
        var parsed = CuboidModel.fromStream(new StringReader(model.toString()));
        return new TextureSlots.Resolver().addLast(parsed.textureSlots()).resolve(DEBUG);
    }

    @Test void all65ParticleReferencesResolveToExistingLayer0InInstalledEngine() throws Exception {
        var template = object(Path.of(ASSETS + "models/gui/hud/ammo_hand_cannon.json"));
        // Diagnose the old template independently: faces resolve; particle is absent.
        assertNotNull(slots(template).getMaterial("layer0"));
        assertNull(slots(template).getMaterial("particle"));
        int count = 0;
        try (var files = Files.list(Path.of(ASSETS + "models/gui/hud"))) {
            for (var path : files.filter(p -> p.getFileName().toString().startsWith("ammo_weapon_w112_"))
                    .filter(p -> !kim.biryeong.destiny.weapon.WeaponExotics.expansionIds().stream()
                            .anyMatch(id -> p.getFileName().toString().equals("ammo_weapon_w112_"+id+".json"))).toList()) {
                var model = object(path);
                assertEquals("#layer0", model.getAsJsonObject("textures").get("particle").getAsString());
                var resolved = slots(model);
                assertNotNull(resolved.getMaterial("particle"), path.toString());
                assertEquals(resolved.getMaterial("layer0"), resolved.getMaterial("particle"), path.toString());
                var withoutParticle = model.deepCopy();
                withoutParticle.getAsJsonObject("textures").remove("particle");
                assertNull(slots(withoutParticle).getMaterial("particle"));
                assertEquals(resolved.getMaterial("layer0"), slots(withoutParticle).getMaterial("layer0"));
                String texture = model.getAsJsonObject("textures").get("layer0").getAsString();
                assertTrue(Files.isRegularFile(Path.of(ASSETS + "textures/" + texture.split(":")[1] + ".png")));
                count++;
            }
        }
        assertEquals(65, count);
    }
}
