package kim.biryeong.destiny.fx;

import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import com.mojang.serialization.JsonOps;
import net.minecraft.client.color.item.ItemTintSources;
import net.minecraft.client.renderer.item.ItemModels;
import net.minecraft.client.resources.model.cuboid.CuboidModel;
import net.minecraft.world.item.ItemDisplayContext;
import org.joml.Matrix4d;
import org.joml.Quaterniond;
import org.joml.Vector3d;
import org.junit.jupiter.api.Test;

import java.io.StringReader;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.HashSet;
import java.util.HexFormat;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Set;

import static org.junit.jupiter.api.Assertions.*;
import static kim.biryeong.destiny.weapon.RenderContractsW163Support.*;

/** Ammit-only asset contracts using native 26.3 parsers; no client launch or gameplay claims. */
class AutoRifleReloadW69Test {
    private static final Path ROOT = Path.of("src/main/resources/assets/destiny");
    private static final Path ART = Path.of("art/weapons/w69/manifest.json");
    private static final String KEY = "weapon_reload_w69/ammit_ar2";
    private static final String SOURCE = "models/weapon/auto_rifle/ammit_ar2";
    private static final List<String> CONTEXTS = List.of("firstperson_righthand", "firstperson_lefthand");
    private static final List<String> PARTS = List.of("body", "magazine");
    private static final List<String> GRIPS = List.of("native", "twohand");
    private static final double EPS = 3e-6;
    // Computed directly from current originals before W69 assets arrived, independently of the manifest.
    private static final Map<String, String> ORIGINALS = Map.of(
            "src/main/resources/assets/destiny/models/weapon/auto_rifle/ammit_ar2.json",
            "07baa6310f8563c21fe6276975830b64c2052e3cd06dd9015855d78956b47673",
            "src/main/resources/assets/destiny/models/weapon/auto_rifle/ammit_ar2_twohand.json",
            "0c71893a4c065d17d0f6b3d936cd6410e29b9f2182cf5845e62228abc41c2c2b",
            "src/main/resources/assets/destiny/items/weapon/ammit_ar2.json",
            "e029d018bbb12dba3a5b941afa36e2d408a6b93c387d64bcef3ebb4f7dad43a4",
            "src/main/resources/assets/destiny/textures/item/weapon/w30/ammit_ar2.png",
            "c28a623888c57a9527038d7975b230081b882e61ffbebf4ce82865998cc6c1f1",
            "art/blockbench/weapons/w30/ammit_ar2.bbmodel",
            "e98d7cb58b352e428b7f134d5092f991f70e421d992e9813b7d4fc87c58da726",
            "scripts/build_weapons_w30.py",
            "e087fca588231486505691e97b5c2b581382c1055c76d64300dbc24118bf1d83");

    @Test void exactly87AssetsMatchInventoryHashesAndIndependentOriginalPins() throws Exception {
        var manifest = json(ART);
        assertEquals("W69", manifest.get("stage").getAsString());
        assertEquals("scripts/generate_reload_models_w69.py", manifest.get("generator").getAsString());
        assertEquals(List.of("ammit_ar2"), strings(manifest.getAsJsonArray("ids")));
        assertEquals(21, manifest.get("frames").getAsInt());
        assertEquals(1, manifest.get("progressFloatIndex").getAsInt());
        assertEquals(CONTEXTS, strings(manifest.getAsJsonArray("firstPersonContexts")));
        assertTrue(manifest.get("originalsUnchanged").getAsBoolean());
        var expected = expectedAssets();
        assertEquals(87, expected.size());
        var hashes = manifest.getAsJsonObject("sha256");
        assertEquals(expected, hashes.keySet());
        Set<String> disk = new HashSet<>();
        for (String type : List.of("items", "models")) {
            try (var files = Files.walk(ROOT.resolve(type + "/weapon_reload_w69"))) {
                disk.addAll(files.filter(Files::isRegularFile).map(Path::toString).toList());
            }
        }
        assertEquals(expected, disk, "No missing, extra, or other-weapon asset");
        for (var entry : hashes.entrySet())
            assertEquals(entry.getValue().getAsString(), historicalSha(Path.of(entry.getKey())), entry.getKey());
        for (var entry : ORIGINALS.entrySet())
            assertEquals(entry.getValue(), historicalSha(Path.of(entry.getKey())), "Independent pin: " + entry.getKey());
        var sources = manifest.getAsJsonObject("sourceSha256");
        assertTrue(sources.keySet().containsAll(Set.of(ROOT.resolve(SOURCE + ".json").toString(),
                ROOT.resolve("items/weapon/ammit_ar2.json").toString(), "scripts/build_weapons_w30.py")));
        for (var entry : sources.entrySet()) {
            assertTrue(ORIGINALS.containsKey(entry.getKey()), "Unpinned original: " + entry.getKey());
            assertEquals(ORIGINALS.get(entry.getKey()), entry.getValue().getAsString(), entry.getKey());
        }
    }

    @Test void native26_3ItemCodecAndCuboidParserAcceptAll87Assets() throws Exception {
        net.minecraft.SharedConstants.tryDetectVersion();
        net.minecraft.server.Bootstrap.bootStrap();
        ItemModels.bootstrap();
        ItemTintSources.bootstrap();
        net.minecraft.client.renderer.item.properties.select.SelectItemModelProperties.bootstrap();
        net.minecraft.client.renderer.item.properties.conditional.ConditionalItemModelProperties.bootstrap();
        net.minecraft.client.renderer.item.properties.numeric.RangeSelectItemModelProperties.bootstrap();
        int parsed = 0;
        for (String path : expectedAssets()) {
            if (path.contains("/items/")) {
                var model = json(Path.of(path)).getAsJsonObject("model");
                var decoded = ItemModels.CODEC.parse(JsonOps.INSTANCE, model);
                assertTrue(decoded.isSuccess(), path + ": " + decoded.error());
                var invalid = model.deepCopy();
                invalid.getAsJsonArray("cases").get(0).getAsJsonObject()
                        .addProperty("when", "first_person_right_hand");
                assertFalse(ItemModels.CODEC.parse(JsonOps.INSTANCE, invalid).isSuccess(),
                        "Negative control rejects incorrect context spelling");
            } else {
                assertNotNull(CuboidModel.fromStream(new StringReader(Files.readString(Path.of(path)))), path);
            }
            parsed++;
        }
        assertEquals(87, parsed);
    }

    @Test void wrapperKeepsExactOriginalMetadataAndInactiveAndEveryOtherContextFallback() throws Exception {
        var source = json(ROOT.resolve("items/weapon/ammit_ar2.json"));
        var reload = item();
        var restored = reload.deepCopy();
        restored.add("model", source.get("model").deepCopy());
        assertEquals(source, restored, "Preserve hand_animation_on_swap and all original metadata");
        var select = reload.getAsJsonObject("model");
        assertEquals(Set.of("type", "property", "cases", "fallback"), select.keySet());
        assertEquals("minecraft:select", select.get("type").getAsString());
        assertEquals("minecraft:display_context", select.get("property").getAsString());
        assertEquals(source.get("model"), select.get("fallback"), "Full original HIP/ADS/inspect/grip graph");
        assertEquals(1, select.getAsJsonArray("cases").size());
        var branch = select.getAsJsonArray("cases").get(0).getAsJsonObject();
        assertEquals(Set.of("when", "model"), branch.keySet());
        assertEquals(CONTEXTS, strings(branch.getAsJsonArray("when")));
        for (ItemDisplayContext context : ItemDisplayContext.values()) {
            if (CONTEXTS.contains(context.getSerializedName())) continue;
            assertFalse(strings(branch.getAsJsonArray("when")).contains(context.getSerializedName()));
            assertEquals(source.get("model"), select.get("fallback"), "Exact fallback in " + context);
        }
        var range = branch.getAsJsonObject("model");
        assertEquals(Set.of("type", "property", "index", "entries", "fallback"), range.keySet());
        assertEquals("minecraft:range_dispatch", range.get("type").getAsString());
        assertEquals("minecraft:custom_model_data", range.get("property").getAsString());
        assertEquals(1, range.get("index").getAsInt(), "Progress uses float 1");
        assertEquals(historicalNormalGraph(source.get("model")), range.get("fallback"), "Inactive FP progress preserves pre-W161 graph; outer fallback retains crouch routing");
    }

    @Test void all21OrderedFramesUseFlagZeroAnd84DistinctExistingPartPaths() throws Exception {
        var entries = item().getAsJsonObject("model").getAsJsonArray("cases").get(0).getAsJsonObject()
                .getAsJsonObject("model").getAsJsonArray("entries");
        assertEquals(21, entries.size());
        Set<String> references = new HashSet<>();
        for (int frame = 0; frame <= 20; frame++) {
            var entry = entries.get(frame).getAsJsonObject();
            assertEquals(Set.of("threshold", "model"), entry.keySet());
            assertEquals(frame / 20.0, entry.get("threshold").getAsDouble(), 1e-9);
            var condition = entry.getAsJsonObject("model");
            assertEquals(Set.of("type", "property", "index", "on_true", "on_false"), condition.keySet());
            assertEquals("minecraft:condition", condition.get("type").getAsString());
            assertEquals("minecraft:custom_model_data", condition.get("property").getAsString());
            assertEquals(0, condition.get("index").getAsInt(), "Grip uses boolean flag 0");
            for (String grip : GRIPS) {
                var composite = condition.getAsJsonObject(grip.equals("twohand") ? "on_true" : "on_false");
                assertEquals(Set.of("type", "models"), composite.keySet());
                assertEquals("minecraft:composite", composite.get("type").getAsString());
                var parts = composite.getAsJsonArray("models");
                assertEquals(2, parts.size());
                for (int i = 0; i < PARTS.size(); i++) {
                    var part = parts.get(i).getAsJsonObject();
                    assertEquals(Set.of("type", "model"), part.keySet());
                    assertEquals("minecraft:model", part.get("type").getAsString());
                    String key = poseKey(frame, PARTS.get(i), grip);
                    assertEquals("destiny:" + key, part.get("model").getAsString());
                    assertTrue(references.add(key), "No aliased frame paths");
                    assertTrue(Files.isRegularFile(ROOT.resolve("models/" + key + ".json")), key);
                }
            }
        }
        assertEquals(84, references.size());
    }

    @Test void manifestPartitionReconstructsAll199OriginalElementsExactlyWithin256CubeBudget() throws Exception {
        var manifest = json(ART);
        var source = original();
        var cubes = source.getAsJsonArray("elements");
        assertEquals(199, cubes.size());
        Set<Integer> indices = new HashSet<>();
        for (var index : manifest.getAsJsonArray("magazineIndices")) {
            int value = index.getAsInt();
            assertEquals((double) value, index.getAsDouble(), 0, "Integral source index");
            assertTrue(value >= 0 && value < cubes.size(), "Source index in range");
            assertTrue(indices.add(value), "No duplicate magazine index");
        }
        assertTrue(!indices.isEmpty() && indices.size() < cubes.size(), "Both rigid parts must be nonempty");
        JsonArray body = new JsonArray(), magazine = new JsonArray();
        for (int i = 0; i < cubes.size(); i++) (indices.contains(i) ? magazine : body).add(cubes.get(i));
        for (var count : Map.of("sourceCubes", 199, "bodyCubes", body.size(),
                "magazineSourceCubes", magazine.size(), "compositeCubes", 199).entrySet())
            assertEquals(count.getValue().intValue(), manifest.get(count.getKey()).getAsInt(), count.getKey());
        for (String part : PARTS) {
            var expected = source.deepCopy();
            expected.remove("display");
            expected.add("elements", part.equals("body") ? body : magazine);
            assertEquals(expected, json(ROOT.resolve("models/" + KEY + "_" + part + ".json")),
                    "Exact original elements, order, UV, texture and metadata: " + part);
        }
        assertEquals(199, body.size() + magazine.size());
        assertTrue(body.size() + magazine.size() <= 256);
        for (int frame = 0; frame <= 20; frame++) for (String grip : GRIPS) for (String part : PARTS) {
            var child = pose(frame, part, grip);
            assertEquals(Set.of("parent", "display"), child.keySet(), "Only inherited geometry and pose");
            assertEquals("destiny:" + KEY + "_" + part, child.get("parent").getAsString());
            assertEquals(source.getAsJsonObject("display").keySet(), child.getAsJsonObject("display").keySet());
        }
    }

    @Test void bothEndpointsExactlyRestoreOriginalNativeAndCompensatedTwohandDisplays() throws Exception {
        for (String grip : GRIPS) {
            var hip = json(ROOT.resolve(SOURCE + (grip.equals("twohand") ? "_twohand" : "") + ".json"))
                    .getAsJsonObject("display");
            for (int frame : List.of(0, 20)) for (String part : PARTS)
                assertEquals(hip, pose(frame, part, grip).get("display"), frame + "/" + part + "/" + grip);
        }
    }

    @Test void authoredLocalOffsetsGiveRigidSharedRotationAndQuaternionRotatedScaledTranslation() throws Exception {
        var keys = json(ART).getAsJsonArray("keyframes");
        assertTrue(keys.size() >= 2);
        assertEquals(0, keys.get(0).getAsJsonArray().get(0).getAsDouble(), 0);
        assertEquals(1, keys.get(keys.size() - 1).getAsJsonArray().get(0).getAsDouble(), 0);
        double previous = -1;
        for (var value : keys) {
            var key = value.getAsJsonArray();
            assertEquals(4, key.size(), "Progress, body rotation, body translation, local magazineOffset; no local rotation");
            double progress = key.get(0).getAsDouble();
            assertTrue(Double.isFinite(progress) && progress > previous && progress <= 1);
            for (int column = 1; column <= 3; column++) vector(key.get(column).getAsJsonArray());
            previous = progress;
        }
        boolean bodyMoved = false, magazineMoved = false;
        var hip = original().getAsJsonObject("display");
        for (int frame = 0; frame <= 20; frame++) {
            Vector3d rotation = sample(keys, frame / 20.0, 1);
            Vector3d translation = sample(keys, frame / 20.0, 2);
            Vector3d localOffset = sample(keys, frame / 20.0, 3);
            bodyMoved |= rotation.lengthSquared() + translation.lengthSquared() > 1e-4;
            magazineMoved |= localOffset.lengthSquared() > 1e-4;
            if (frame == 0 || frame == 20) assertVector(new Vector3d(), localOffset, EPS, "Seated endpoint");
            for (String context : CONTEXTS) {
                String label = frame + "/" + context;
                var body = pose(frame, "body", "native").getAsJsonObject("display").getAsJsonObject(context);
                var magazine = pose(frame, "magazine", "native").getAsJsonObject("display").getAsJsonObject(context);
                var base = hip.getAsJsonObject(context);
                assertEquals(body.get("rotation"), magazine.get("rotation"), "No independent magazine rotation " + label);
                assertEquals(base.get("scale"), body.get("scale"));
                assertEquals(body.get("scale"), magazine.get("scale"), "No shrink/hide deformation");
                assertVector(vector(base, "rotation").add(rotation), vector(body, "rotation"), EPS, "Body rotation " + label);
                assertVector(vector(base, "translation").add(translation), vector(body, "translation"), EPS, "Body translation " + label);
                Vector3d radians = vector(body, "rotation").mul(Math.PI / 180);
                Vector3d expected = new Quaterniond().rotationXYZ(radians.x, radians.y, radians.z)
                        .transform(new Vector3d(localOffset)).mul(vector(body, "scale"));
                assertVector(expected, vector(magazine, "translation").sub(vector(body, "translation")), EPS,
                        "rotate(localOffset) * scale " + label);
            }
        }
        assertTrue(bodyMoved, "Intermediate rifle motion must exist");
        assertTrue(magazineMoved, "Intermediate magazine removal must exist");
    }

    @Test void everyPoseCompensatesBothHandsPreservesOtherContextsAndStaysFiniteWithinLimits() throws Exception {
        for (String path : expectedAssets()) assertFinite(json(Path.of(path)), path);
        assertFinite(json(ART), "manifest");
        var nativeHip = original().getAsJsonObject("display");
        var twohandHip = json(ROOT.resolve(SOURCE + "_twohand.json")).getAsJsonObject("display");
        for (int frame = 0; frame <= 20; frame++) for (String part : PARTS) {
            var nativeDisplay = pose(frame, part, "native").getAsJsonObject("display");
            var twohand = pose(frame, part, "twohand").getAsJsonObject("display");
            for (var display : List.of(nativeDisplay, twohand)) for (String context : display.keySet()) {
                var values = display.getAsJsonObject(context);
                for (double component : new double[]{vector(values, "translation").x, vector(values, "translation").y,
                        vector(values, "translation").z}) assertTrue(Math.abs(component) <= 80, "No native translation clamping");
                var scale = vector(values, "scale");
                assertTrue(scale.x > 0 && scale.x <= 4 && scale.y > 0 && scale.y <= 4 && scale.z > 0 && scale.z <= 4,
                        "Positive scale within native limits");
                vector(values, "rotation");
            }
            for (boolean left : List.of(false, true)) {
                String context = CONTEXTS.get(left ? 1 : 0);
                var body = pose(frame, "body", "twohand").getAsJsonObject("display").getAsJsonObject(context);
                var magazine = pose(frame, "magazine", "twohand").getAsJsonObject("display").getAsJsonObject(context);
                assertEquals(body.get("rotation"), magazine.get("rotation"), "Shared compensated rotation");
                assertEquals(body.get("scale"), magazine.get("scale"), "Shared compensated scale");
                double sign = left ? -1 : 1;
                var restored = new Matrix4d().translate(-.641864 * sign, 0, 0)
                        .rotateY(Math.toRadians(10) * sign).mul(transform(twohand.getAsJsonObject(context), left));
                assertTrue(transform(nativeDisplay.getAsJsonObject(context), left).equals(restored, EPS),
                        "Native crossbow compensation " + frame + "/" + part + "/" + context);
            }
            for (String context : nativeHip.keySet()) if (!CONTEXTS.contains(context)) {
                assertEquals(nativeHip.get(context), nativeDisplay.get(context), "Original native " + context);
                assertEquals(twohandHip.get(context), twohand.get(context), "Original compensated " + context);
            }
        }
    }

    private static JsonObject json(Path path) throws Exception {
        return JsonParser.parseString(Files.readString(path)).getAsJsonObject();
    }

    private static JsonObject original() throws Exception { return json(ROOT.resolve(SOURCE + ".json")); }
    private static JsonObject item() throws Exception { return json(ROOT.resolve("items/" + KEY + ".json")); }
    private static List<String> strings(JsonArray values) {
        return values.asList().stream().map(JsonElement::getAsString).toList();
    }

    private static String poseKey(int frame, String part, String grip) {
        return KEY + "_" + String.format(Locale.ROOT, "%02d", frame) + "_" + part + "_" + grip;
    }

    private static JsonObject pose(int frame, String part, String grip) throws Exception {
        return json(ROOT.resolve("models/" + poseKey(frame, part, grip) + ".json"));
    }

    private static Set<String> expectedAssets() {
        Set<String> paths = new HashSet<>();
        paths.add(ROOT.resolve("items/" + KEY + ".json").toString());
        for (String part : PARTS) {
            paths.add(ROOT.resolve("models/" + KEY + "_" + part + ".json").toString());
            for (int frame = 0; frame <= 20; frame++) for (String grip : GRIPS)
                paths.add(ROOT.resolve("models/" + poseKey(frame, part, grip) + ".json").toString());
        }
        return paths;
    }

    private static String sha256(Path path) throws Exception {
        return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(path)));
    }

    private static Vector3d vector(JsonObject object, String key) { return vector(object.getAsJsonArray(key)); }
    private static Vector3d vector(JsonArray values) {
        assertEquals(3, values.size());
        for (var value : values) assertTrue(Double.isFinite(value.getAsDouble()), "Finite vector");
        return new Vector3d(values.get(0).getAsDouble(), values.get(1).getAsDouble(), values.get(2).getAsDouble());
    }

    /** Independent interpolation of the manifest's authored local vectors, not generator execution. */
    private static Vector3d sample(JsonArray keys, double progress, int column) {
        for (int i = 1; i < keys.size(); i++) {
            var a = keys.get(i - 1).getAsJsonArray();
            var b = keys.get(i).getAsJsonArray();
            double end = b.get(0).getAsDouble();
            if (progress > end) continue;
            double start = a.get(0).getAsDouble();
            double t = (progress - start) / (end - start);
            return vector(a.get(column).getAsJsonArray()).lerp(vector(b.get(column).getAsJsonArray()), t * t * (3 - 2 * t));
        }
        throw new AssertionError("Missing keyframe for " + progress);
    }

    private static void assertVector(Vector3d expected, Vector3d actual, double tolerance, String message) {
        assertEquals(expected.x, actual.x, tolerance, message + "/x");
        assertEquals(expected.y, actual.y, tolerance, message + "/y");
        assertEquals(expected.z, actual.z, tolerance, message + "/z");
    }

    private static void assertFinite(JsonElement value, String path) {
        if (value.isJsonObject()) value.getAsJsonObject().entrySet().forEach(e -> assertFinite(e.getValue(), path + "/" + e.getKey()));
        else if (value.isJsonArray()) for (var child : value.getAsJsonArray()) assertFinite(child, path);
        else if (value.isJsonPrimitive() && value.getAsJsonPrimitive().isNumber())
            assertTrue(Double.isFinite(value.getAsDouble()) && Float.isFinite(value.getAsFloat()), "Finite float: " + path);
    }

    /** Native ItemTransform order/units and left-hand reflection, matching the W47/W64 API. */
    private static Matrix4d transform(JsonObject display, boolean left) {
        var r = vector(display, "rotation").mul(Math.PI / 180);
        var t = vector(display, "translation").div(16);
        var s = vector(display, "scale");
        double sign = left ? -1 : 1;
        return new Matrix4d().translate(t.x * sign, t.y, t.z)
                .rotateXYZ(r.x, r.y * sign, r.z * sign).scale(s.x, s.y, s.z);
    }
}
