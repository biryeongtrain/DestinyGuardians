package kim.biryeong.destiny.fx;

import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.serialization.JsonOps;
import net.minecraft.client.color.item.ItemTintSources;
import net.minecraft.client.renderer.item.ItemModels;
import net.minecraft.client.resources.model.cuboid.CuboidModel;
import net.minecraft.world.item.ItemDisplayContext;
import org.joml.Matrix4d;
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

/** W101 asset contracts only. Matrix equality cannot establish on-screen visibility. */
class RecluseFramingW101Test {
    private static final Path ROOT = Path.of("src/main/resources/assets/destiny");
    private static final Path MANIFEST = Path.of("art/weapons/w101/manifest.json");
    private static final String KEY = "weapon_reload_w101/the_recluse";
    private static final String W100 = "weapon_reload_w100/the_recluse";
    private static final String SOURCE = "models/weapon/submachine_gun/the_recluse";
    private static final List<String> PARTS = List.of("body", "magazine");
    private static final List<String> GRIPS = List.of("native", "twohand");
    private static final List<String> CONTEXTS = List.of("firstperson_righthand", "firstperson_lefthand");
    private static final double EPS = 3e-6;
    private static final List<Integer> MAGAZINE_INDICES = List.of(
            2, 3, 4, 44, 56, 62, 63, 65, 72, 77, 78, 81, 83, 84,
            141, 144, 156, 161, 162, 163, 167, 173, 178, 183);

    // Independent pre-W101 literals: changing a manifest alongside a source must still fail.
    private static final Map<String, String> ORIGINAL_PINS = Map.ofEntries(
            Map.entry(SOURCE + ".json", "b338c341d40234e39356ca70f47594e5d625c6521f102ea417a06956d33f73ae"),
            Map.entry(SOURCE + "_twohand.json", "cfcb4ffe8ab00cdff8d43e89421513033018294c8b25021c82def1fd5bc0ba32"),
            Map.entry(SOURCE + "_ads.json", "7704b4118c8d119bd5f6143a3ba1b81307567e5580d8db719fa9dbab9dce95ba"),
            Map.entry(SOURCE + "_ads_twohand.json", "164d204387f178bf6080a804a3931312c640493b8fdb60df9f9191c9fcc5da4b"),
            Map.entry(SOURCE + "_inspect.json", "ad838bf2766050006c06d6327703cb653044c3bc8ec49842844c5fc7776ead51"),
            Map.entry(SOURCE + "_inspect_twohand.json", "a316abfddee965dc1842ba7930b75dc8420f0f1754fe2b64874e70a590e8808e"),
            Map.entry("items/weapon/the_recluse.json", "74132a108fd993aff0a5e2904889372ac3e9e0f584420ddf4e06e852e79c7d00"),
            Map.entry("textures/item/weapon/w30/the_recluse.png", "f3aad8fd07a4af6d7a368f02baf5ea695f15f7a6bedb4b41ed4af6c12ae357a3"));
    private static final Map<String, String> ORIGINAL_SOURCE_PINS = Map.of(
            "art/blockbench/weapons/w30/the_recluse.bbmodel", "9d922885fd0055eba9ae83974df9938cceade443ae2a349e8afc7c610331f3a0",
            "scripts/build_weapons_w30.py", "e087fca588231486505691e97b5c2b581382c1055c76d64300dbc24118bf1d83",
            "scripts/generate_reload_models_w69.py", "ac4b51364886b790a9a60fd01b53a9247249a9f592584f9865f4136de286cb4c");
    private static final Map<String, String> PARENT_PINS = Map.of(
            "body", "74d624d9329cd6becf763bf53781269fd072c1c718d097c3a57d578b6cd3b641",
            "magazine", "1e8b5044599909a46cb68adb22c3b516b42ae2cd83ee648de9155f9951094103");
    private static final Map<String, String> BASELINE_PINS = Map.of(
            "scripts/generate_reload_models_w100.py", "aef69a0be0a2b4f84c87ff33ce4ca56faf637dcb24b34806293b34b4ea21e97c",
            "art/weapons/w100/manifest.json", "f4ddf971ef78211072931a73448e6ec3fd3f2431075d07743685dbaa62b19713");
    // Master froze these candidate values for this bounded stage on 2026-10-25.
    // Authored view composition; native visibility remains unaccepted/pending.
    // Columns: progress, body rotation delta, body translation delta, local magazine offset.
    private static final String AUTHORED_KEYS = """
            [
              [0,    [0,0,0],      [0,0,0],        [0,0,0]],
              [0.12, [4,-10,-14],  [-2,4,-1],      [0,0,0]],
              [0.24, [8,-20,-28],  [-4.5,8,-2],    [0.3,-1.5,0]],
              [0.40, [8,-22,-32],  [-4.5,8,-2],    [0.5,-4.2,0.3]],
              [0.52, [7,-20,-30],  [-4.5,8,-2],    [0.5,-4.2,0.3]],
              [0.68, [6,-18,-28],  [-4.5,8,-2],    [0.2,-1.8,0.1]],
              [0.78, [8,-16,-26],  [-4.2,7.5,-1.8],[0,0,0]],
              [0.86, [5,-10,-16],  [-2.5,4.5,-1],  [0,0,0]],
              [1,    [0,0,0],      [0,0,0],        [0,0,0]]
            ]
            """;

    @Test void exact85AssetInventoryPassesNative26_3Parsers() throws Exception {
        var manifest = json(MANIFEST);
        assertEquals("W101", manifest.get("stage").getAsString());
        assertEquals(85, manifest.get("assets").getAsInt());
        assertEquals(21, manifest.get("frames").getAsInt());
        assertEquals("scripts/generate_reload_framing_w101.py", manifest.get("generator").getAsString());
        assertEquals(sha256(Path.of("scripts/generate_reload_framing_w101.py")),
                manifest.get("generatorSha256").getAsString());
        var expected = expectedAssets();
        assertEquals(85, expected.size());
        Set<String> disk = new HashSet<>();
        for (String type : List.of("items", "models")) {
            try (var files = Files.walk(ROOT.resolve(type + "/weapon_reload_w101"))) {
                files.filter(Files::isRegularFile).map(Path::toString).forEach(disk::add);
            }
        }
        assertEquals(expected, disk, "Exactly one item and 84 poses; no W101 geometry copies or extra files");
        var hashes = manifest.getAsJsonObject("sha256");
        assertEquals(expected, hashes.keySet());
        net.minecraft.SharedConstants.tryDetectVersion();
        net.minecraft.server.Bootstrap.bootStrap();
        ItemModels.bootstrap();
        ItemTintSources.bootstrap();
        net.minecraft.client.renderer.item.properties.select.SelectItemModelProperties.bootstrap();
        net.minecraft.client.renderer.item.properties.conditional.ConditionalItemModelProperties.bootstrap();
        net.minecraft.client.renderer.item.properties.numeric.RangeSelectItemModelProperties.bootstrap();
        int items = 0, poses = 0;
        for (String name : expected) {
            Path path = Path.of(name);
            assertEquals(hashes.get(name).getAsString(), sha256(path), name);
            if (name.contains("/items/")) {
                var result = ItemModels.CODEC.parse(JsonOps.INSTANCE, json(path).getAsJsonObject("model"));
                assertTrue(result.isSuccess(), name + ": " + result.error());
                items++;
            } else {
                assertNotNull(CuboidModel.fromStream(new StringReader(Files.readString(path))), name);
                poses++;
            }
        }
        assertEquals(1, items);
        assertEquals(84, poses);
        // Negative controls exercise the actual codecs, rather than a JSON-only substitute.
        var invalidItem = item().getAsJsonObject("model").deepCopy();
        invalidItem.getAsJsonArray("cases").get(0).getAsJsonObject()
                .addProperty("when", "first_person_right_hand");
        assertFalse(ItemModels.CODEC.parse(JsonOps.INSTANCE, invalidItem).isSuccess());
        var invalidGeometry = json(ROOT.resolve(SOURCE + ".json"));
        invalidGeometry.getAsJsonArray("elements").get(0).getAsJsonObject()
                .add("from", JsonParser.parseString("[0, 0]"));
        assertThrows(com.google.gson.JsonParseException.class,
                () -> CuboidModel.fromStream(new StringReader(invalidGeometry.toString())));
    }

    @Test void pinnedW100ParentsConserveAll217OriginalElementsAndUvs() throws Exception {
        var manifest = json(MANIFEST);
        Set<String> originalPaths = new HashSet<>();
        for (var entry : ORIGINAL_PINS.entrySet()) {
            String name = ROOT.resolve(entry.getKey()).toString();
            originalPaths.add(name);
            assertEquals(entry.getValue(), sha256(Path.of(name)), "Independent original pin: " + name);
            assertEquals(entry.getValue(), manifest.getAsJsonObject("originalPins").get(name).getAsString());
        }
        for (var entry : ORIGINAL_SOURCE_PINS.entrySet()) {
            originalPaths.add(entry.getKey());
            assertEquals(entry.getValue(), sha256(Path.of(entry.getKey())), "Independent original source pin: " + entry.getKey());
            assertEquals(entry.getValue(), manifest.getAsJsonObject("originalPins").get(entry.getKey()).getAsString());
        }
        assertEquals(originalPaths, manifest.getAsJsonObject("originalPins").keySet(), "All eleven original pins");
        assertEquals(BASELINE_PINS.keySet(), manifest.getAsJsonObject("baselinePins").keySet());
        for (var entry : BASELINE_PINS.entrySet()) {
            assertEquals(entry.getValue(), sha256(Path.of(entry.getKey())), entry.getKey());
            assertEquals(entry.getValue(), manifest.getAsJsonObject("baselinePins").get(entry.getKey()).getAsString());
        }
        assertEquals(List.of("destiny:" + W100 + "_body", "destiny:" + W100 + "_magazine"),
                strings(manifest.getAsJsonArray("geometryParents")));
        assertEquals(217, manifest.get("originalCubes").getAsInt());
        var source = json(ROOT.resolve(SOURCE + ".json"));
        var elements = source.getAsJsonArray("elements");
        assertEquals(217, elements.size());
        JsonArray body = new JsonArray(), magazine = new JsonArray();
        for (int i = 0; i < elements.size(); i++)
            (MAGAZINE_INDICES.contains(i) ? magazine : body).add(elements.get(i));
        assertEquals(193, body.size());
        assertEquals(24, magazine.size());
        assertTrue(body.size() + magazine.size() <= 256);
        for (String part : PARTS) {
            Path parent = ROOT.resolve("models/" + W100 + "_" + part + ".json");
            assertEquals(PARENT_PINS.get(part), sha256(parent), "Independent W100 geometry pin: " + part);
            var expected = source.deepCopy();
            expected.remove("display");
            expected.add("elements", part.equals("body") ? body : magazine);
            assertEquals(expected, json(parent), "Exact element order, faces, UVs, textures and metadata: " + part);
        }
        for (int frame = 0; frame <= 20; frame++) for (String grip : GRIPS) for (String part : PARTS) {
            var child = pose(frame, part, grip);
            assertEquals(Set.of("parent", "display"), child.keySet(), "No local geometry/texture/UV override");
            assertEquals("destiny:" + W100 + "_" + part, child.get("parent").getAsString());
        }
    }

    @Test void wrapperKeepsOriginalFullGraphAndRoutes21FramesTo84DistinctParts() throws Exception {
        var originalItem = json(ROOT.resolve("items/weapon/the_recluse.json"));
        var wrapper = item();
        var restored = wrapper.deepCopy();
        restored.add("model", originalItem.get("model").deepCopy());
        assertEquals(originalItem, restored, "Original item metadata including swap animation");
        var select = wrapper.getAsJsonObject("model");
        assertEquals(Set.of("type", "property", "cases", "fallback"), select.keySet());
        assertEquals("minecraft:select", select.get("type").getAsString());
        assertEquals("minecraft:display_context", select.get("property").getAsString());
        assertEquals(originalItem.get("model"), select.get("fallback"), "Other contexts retain HIP/ADS/inspect and both grips");
        var cases = select.getAsJsonArray("cases");
        assertEquals(1, cases.size());
        var branch = cases.get(0).getAsJsonObject();
        assertEquals(Set.of("when", "model"), branch.keySet());
        assertEquals(CONTEXTS, strings(branch.getAsJsonArray("when")));
        for (ItemDisplayContext context : ItemDisplayContext.values())
            assertEquals(context == ItemDisplayContext.FIRST_PERSON_RIGHT_HAND
                            || context == ItemDisplayContext.FIRST_PERSON_LEFT_HAND,
                    CONTEXTS.contains(context.getSerializedName()), "Context restriction: " + context);
        var range = branch.getAsJsonObject("model");
        assertEquals(Set.of("type", "property", "index", "entries", "fallback"), range.keySet());
        assertEquals("minecraft:range_dispatch", range.get("type").getAsString());
        assertEquals("minecraft:custom_model_data", range.get("property").getAsString());
        assertEquals(1, range.get("index").getAsInt());
        assertEquals(originalItem.get("model"), range.get("fallback"), "Inactive progress below zero retains the full graph");
        var entries = range.getAsJsonArray("entries");
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
            assertEquals(0, condition.get("index").getAsInt());
            for (String grip : GRIPS) {
                var composite = condition.getAsJsonObject(grip.equals("twohand") ? "on_true" : "on_false");
                assertEquals(Set.of("type", "models"), composite.keySet());
                assertEquals("minecraft:composite", composite.get("type").getAsString());
                var models = composite.getAsJsonArray("models");
                assertEquals(2, models.size());
                for (int i = 0; i < PARTS.size(); i++) {
                    var model = models.get(i).getAsJsonObject();
                    assertEquals(Set.of("type", "model"), model.keySet());
                    assertEquals("minecraft:model", model.get("type").getAsString());
                    String key = poseKey(KEY, frame, PARTS.get(i), grip);
                    assertEquals("destiny:" + key, model.get("model").getAsString());
                    assertTrue(references.add(key), "Every frame/part/grip has its own path");
                    assertTrue(Files.isRegularFile(ROOT.resolve("models/" + key + ".json")), key);
                }
            }
        }
        assertEquals(84, references.size());
    }

    @Test void exactHipEndpointsAndEveryOtherDisplayContextRemainW100Identical() throws Exception {
        for (String grip : GRIPS) {
            var hip = json(ROOT.resolve(SOURCE + (grip.equals("twohand") ? "_twohand" : "") + ".json"))
                    .getAsJsonObject("display");
            for (int frame = 0; frame <= 20; frame++) for (String part : PARTS) {
                String label = frame + "/" + part + "/" + grip;
                var display = pose(frame, part, grip).getAsJsonObject("display");
                assertEquals(hip.keySet(), display.keySet(), "No missing/extra contexts: " + label);
                if (frame == 0 || frame == 20) {
                    assertEquals(hip, display, "Exact HIP endpoint: " + label);
                    assertEquals(json(ROOT.resolve("models/" + poseKey(W100, frame, part, grip) + ".json"))
                            .get("display"), display, "Exact W100 endpoint: " + label);
                }
                for (String context : hip.keySet()) {
                    var values = display.getAsJsonObject(context);
                    if (!CONTEXTS.contains(context))
                        assertEquals(hip.get(context), values, "Other context untouched: " + label + "/" + context);
                    assertEquals(hip.getAsJsonObject(context).get("scale"), values.get("scale"),
                            "Original scale at every frame; no shrinking parts");
                    vector(values, "rotation");
                    var translation = vector(values, "translation");
                    for (double value : new double[]{translation.x, translation.y, translation.z})
                        assertTrue(Math.abs(value) <= 80, "Within native translation clamp: " + label);
                    var scale = vector(values, "scale");
                    assertTrue(scale.x > 0 && scale.x <= 4 && scale.y > 0 && scale.y <= 4
                            && scale.z > 0 && scale.z <= 4, "Positive scale within native limits: " + label);
                }
            }
        }
    }

    @Test void nativeApplyMatchesSignedMatricesAndTwohandCarrierForBothHands() throws Exception {
        int comparisons = 0;
        for (int frame = 0; frame <= 20; frame++) for (String part : PARTS) {
            var nativePose = pose(frame, part, "native");
            var twohandPose = pose(frame, part, "twohand");
            var parsedNative = CuboidModel.fromStream(new StringReader(nativePose.toString()));
            var parsedTwohand = CuboidModel.fromStream(new StringReader(twohandPose.toString()));
            for (boolean left : List.of(false, true)) {
                String context = CONTEXTS.get(left ? 1 : 0);
                ItemDisplayContext nativeContext = left ? ItemDisplayContext.FIRST_PERSON_LEFT_HAND
                        : ItemDisplayContext.FIRST_PERSON_RIGHT_HAND;
                String label = frame + "/" + part + "/" + context;
                var nativeMatrix = applied(parsedNative, nativeContext, left);
                var twohandMatrix = applied(parsedTwohand, nativeContext, left);
                assertMatrix(transform(nativePose.getAsJsonObject("display").getAsJsonObject(context), left)
                        .translate(-.5, -.5, -.5), nativeMatrix, "Native apply: " + label);
                assertMatrix(transform(twohandPose.getAsJsonObject("display").getAsJsonObject(context), left)
                        .translate(-.5, -.5, -.5), twohandMatrix, "Twohand apply: " + label);
                assertMatrix(nativeMatrix, carrier(left).mul(twohandMatrix), "Signed crossbow compensation: " + label);
                comparisons++;
            }
        }
        assertEquals(84, comparisons, "21 frames * two parts * both signed hands");
    }

    @Test void literalAuthoredFramingAndRotatedMagazinePathMatchEverySample() throws Exception {
        var keys = JsonParser.parseString(AUTHORED_KEYS).getAsJsonArray();
        var manifest = json(MANIFEST);
        assertEquals(keys, manifest.get("keyframes"), "Independent frozen authored keys, not generated expectations");
        assertTrue(manifest.get("authoredApproximation").getAsBoolean());
        assertFalse(manifest.get("handIK").getAsBoolean());
        assertFalse(manifest.get("gameplayChanged").getAsBoolean());
        assertFalse(manifest.get("nativeVisibilityAccepted").getAsBoolean(),
                "This bounded stage records visibility as unaccepted/pending, regardless of matrix equality");
        var hip = json(ROOT.resolve(SOURCE + ".json")).getAsJsonObject("display");
        boolean distinguishesUnrotatedOffset = false;
        int comparisons = 0;
        for (int frame = 0; frame <= 20; frame++) {
            var rotation = sample(keys, frame / 20.0, 1);
            var translation = sample(keys, frame / 20.0, 2);
            var offset = sample(keys, frame / 20.0, 3);
            for (String grip : GRIPS) {
                var bodyPose = pose(frame, "body", grip);
                var magazinePose = pose(frame, "magazine", grip);
                var body = CuboidModel.fromStream(new StringReader(bodyPose.toString()));
                var magazine = CuboidModel.fromStream(new StringReader(magazinePose.toString()));
                for (boolean left : List.of(false, true)) {
                    String context = CONTEXTS.get(left ? 1 : 0);
                    String label = frame + "/" + grip + "/" + context;
                    ItemDisplayContext nativeContext = left ? ItemDisplayContext.FIRST_PERSON_LEFT_HAND
                            : ItemDisplayContext.FIRST_PERSON_RIGHT_HAND;
                    var expectedDisplay = hip.getAsJsonObject(context).deepCopy();
                    expectedDisplay.add("rotation", array(vector(expectedDisplay, "rotation").add(rotation)));
                    expectedDisplay.add("translation", array(vector(expectedDisplay, "translation").add(translation)));
                    var expectedBody = transform(expectedDisplay, left).translate(-.5, -.5, -.5);
                    // Reflect the local displacement once. Use authored body rotation AND scale,
                    // not the emitted magazine translation, as the independent path oracle.
                    double sign = left ? -1 : 1;
                    var localOffset = new Vector3d(offset.x * sign, offset.y, offset.z).div(16);
                    var displacement = expectedBody.transformDirection(new Vector3d(localOffset));
                    distinguishesUnrotatedOffset |= displacement.distance(localOffset) > .01;
                    var expectedMagazine = new Matrix4d().translate(displacement).mul(expectedBody);
                    var actualBody = applied(body, nativeContext, left);
                    var actualMagazine = applied(magazine, nativeContext, left);
                    if (grip.equals("twohand")) {
                        actualBody = carrier(left).mul(actualBody);
                        actualMagazine = carrier(left).mul(actualMagazine);
                    }
                    assertMatrix(expectedBody, actualBody, "Literal body framing: " + label);
                    assertMatrix(expectedMagazine, actualMagazine, "Literal rotated/scaled magazine path: " + label);
                    var bodyDisplay = bodyPose.getAsJsonObject("display").getAsJsonObject(context);
                    var magazineDisplay = magazinePose.getAsJsonObject("display").getAsJsonObject(context);
                    assertEquals(bodyDisplay.get("rotation"), magazineDisplay.get("rotation"), "No independent part rotation: " + label);
                    assertEquals(bodyDisplay.get("scale"), magazineDisplay.get("scale"), "No independent part scale: " + label);
                    comparisons++;
                }
            }
        }
        assertEquals(84, comparisons, "21 samples * both grips * both signed hands, each checking both parts");
        assertTrue(distinguishesUnrotatedOffset, "An unrotated display-space offset must fail this oracle");
    }

    private static JsonObject json(Path path) throws Exception {
        return JsonParser.parseString(Files.readString(path)).getAsJsonObject();
    }

    private static JsonObject item() throws Exception { return json(ROOT.resolve("items/" + KEY + ".json")); }

    private static String poseKey(String prefix, int frame, String part, String grip) {
        return prefix + "_" + String.format(Locale.ROOT, "%02d", frame) + "_" + part + "_" + grip;
    }

    private static JsonObject pose(int frame, String part, String grip) throws Exception {
        return json(ROOT.resolve("models/" + poseKey(KEY, frame, part, grip) + ".json"));
    }

    private static Set<String> expectedAssets() {
        Set<String> result = new HashSet<>();
        result.add(ROOT.resolve("items/" + KEY + ".json").toString());
        for (int frame = 0; frame <= 20; frame++) for (String part : PARTS) for (String grip : GRIPS)
            result.add(ROOT.resolve("models/" + poseKey(KEY, frame, part, grip) + ".json").toString());
        return result;
    }

    private static List<String> strings(JsonArray values) {
        return values.asList().stream().map(JsonElement::getAsString).toList();
    }

    private static String sha256(Path path) throws Exception {
        return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(path)));
    }

    private static Vector3d vector(JsonObject object, String key) {
        return vector(object.getAsJsonArray(key));
    }

    private static Vector3d vector(JsonArray values) {
        assertEquals(3, values.size(), "Three vector components");
        for (var value : values)
            assertTrue(Double.isFinite(value.getAsDouble()) && Float.isFinite(value.getAsFloat()), "Finite vector");
        return new Vector3d(values.get(0).getAsDouble(), values.get(1).getAsDouble(), values.get(2).getAsDouble());
    }

    private static JsonArray array(Vector3d value) {
        JsonArray result = new JsonArray();
        result.add(value.x);
        result.add(value.y);
        result.add(value.z);
        return result;
    }

    /** Independent smoothstep interpolation of literal keys, without executing/importing the generator. */
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
        throw new AssertionError("Missing authored key for " + progress);
    }

    /** Same native 26.3 API verified by W100; apply already includes model centering. */
    private static Matrix4d applied(CuboidModel model, ItemDisplayContext context, boolean left) {
        PoseStack stack = new PoseStack();
        model.transforms().getTransform(context).apply(left, stack.last());
        return new Matrix4d(stack.last().pose());
    }

    /** Independent double oracle: model units /16, T * Rx * Ry * Rz * S, signed left-hand semantics. */
    private static Matrix4d transform(JsonObject display, boolean left) {
        var r = vector(display, "rotation").mul(Math.PI / 180);
        var t = vector(display, "translation").div(16);
        var s = vector(display, "scale");
        double sign = left ? -1 : 1;
        return new Matrix4d().translate(t.x * sign, t.y, t.z)
                .rotateXYZ(r.x, r.y * sign, r.z * sign).scale(s.x, s.y, s.z);
    }

    private static Matrix4d carrier(boolean left) {
        double sign = left ? -1 : 1;
        return new Matrix4d().translate(-.641864 * sign, 0, 0).rotateY(Math.toRadians(10) * sign);
    }

    private static void assertMatrix(Matrix4d expected, Matrix4d actual, String label) {
        double[] expectedValues = expected.get(new double[16]);
        double[] actualValues = actual.get(new double[16]);
        for (int i = 0; i < 16; i++) {
            assertTrue(Double.isFinite(actualValues[i]), "Finite matrix: " + label + "/" + i);
            assertEquals(expectedValues[i], actualValues[i], EPS, label + "/matrix[" + i + "]");
        }
    }
}
