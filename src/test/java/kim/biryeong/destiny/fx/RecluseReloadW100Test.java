package kim.biryeong.destiny.fx;

import com.mojang.blaze3d.vertex.PoseStack;
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

/** Recluse-only asset contracts using native 26.3 parsers; no client launch or gameplay claims. */
class RecluseReloadW100Test {
    private static final Path ROOT = Path.of("src/main/resources/assets/destiny");
    private static final Path ART = Path.of("art/weapons/w100/manifest.json");
    private static final String KEY = "weapon_reload_w100/the_recluse";
    private static final String SOURCE = "models/weapon/submachine_gun/the_recluse";
    private static final List<String> CONTEXTS = List.of("firstperson_righthand", "firstperson_lefthand");
    private static final List<String> PARTS = List.of("body", "magazine");
    private static final List<String> GRIPS = List.of("native", "twohand");
    private static final double EPS = 3e-6;
    // Pre-W100 literal inputs, independently asserted against disk and the manifest.
    // Never derive expected pins, partition membership or authored motion from generated output.
    private static final Map<String, String> ORIGINALS = Map.ofEntries(
            Map.entry("src/main/resources/assets/destiny/models/weapon/submachine_gun/the_recluse.json",
                    "b338c341d40234e39356ca70f47594e5d625c6521f102ea417a06956d33f73ae"),
            Map.entry("src/main/resources/assets/destiny/models/weapon/submachine_gun/the_recluse_ads.json",
                    "7704b4118c8d119bd5f6143a3ba1b81307567e5580d8db719fa9dbab9dce95ba"),
            Map.entry("src/main/resources/assets/destiny/models/weapon/submachine_gun/the_recluse_ads_twohand.json",
                    "164d204387f178bf6080a804a3931312c640493b8fdb60df9f9191c9fcc5da4b"),
            Map.entry("src/main/resources/assets/destiny/models/weapon/submachine_gun/the_recluse_inspect.json",
                    "ad838bf2766050006c06d6327703cb653044c3bc8ec49842844c5fc7776ead51"),
            Map.entry("src/main/resources/assets/destiny/models/weapon/submachine_gun/the_recluse_inspect_twohand.json",
                    "a316abfddee965dc1842ba7930b75dc8420f0f1754fe2b64874e70a590e8808e"),
            Map.entry("src/main/resources/assets/destiny/models/weapon/submachine_gun/the_recluse_twohand.json",
                    "cfcb4ffe8ab00cdff8d43e89421513033018294c8b25021c82def1fd5bc0ba32"),
            Map.entry("src/main/resources/assets/destiny/items/weapon/the_recluse.json",
                    "74132a108fd993aff0a5e2904889372ac3e9e0f584420ddf4e06e852e79c7d00"),
            Map.entry("src/main/resources/assets/destiny/textures/item/weapon/w30/the_recluse.png",
                    "f3aad8fd07a4af6d7a368f02baf5ea695f15f7a6bedb4b41ed4af6c12ae357a3"),
            Map.entry("art/blockbench/weapons/w30/the_recluse.bbmodel",
                    "9d922885fd0055eba9ae83974df9938cceade443ae2a349e8afc7c610331f3a0"),
            Map.entry("scripts/build_weapons_w30.py",
                    "e087fca588231486505691e97b5c2b581382c1055c76d64300dbc24118bf1d83"),
            Map.entry("scripts/generate_reload_models_w69.py",
                    "ac4b51364886b790a9a60fd01b53a9247249a9f592584f9865f4136de286cb4c"));
    private static final List<Integer> MAGAZINE_INDICES = List.of(
            2, 3, 4, 44, 56, 62, 63, 65, 72, 77, 78, 81, 83, 84,
            141, 144, 156, 161, 162, 163, 167, 173, 178, 183);
    private static final String AUTHORED_KEYS = """
            [
              [0,    [0,0,0],     [0,0,0],           [0,0,0]],
              [0.12, [18,-8,12],  [-0.4,-0.1,-0.25], [0,0,0]],
              [0.24, [30,-12,22], [-0.8,0.1,-0.5],   [0.8,-2.8,0.2]],
              [0.40, [33,-14,23], [-0.9,0.25,-0.65], [1.3,-6,0.5]],
              [0.52, [31,-12,21], [-0.9,0.25,-0.65], [1.3,-6,0.5]],
              [0.68, [30,-10,20], [-0.75,0.2,-0.5],  [0.4,-2.4,0.2]],
              [0.78, [34,-9,18],  [-0.65,0.35,-0.4], [0,0,0]],
              [0.86, [25,-6,13],  [-0.4,0.2,-0.3],   [0,0,0]],
              [1,    [0,0,0],     [0,0,0],           [0,0,0]]
            ]
            """;

    @Test void exactly87AssetsMatchInventoryHashesAndIndependentOriginalPins() throws Exception {
        var manifest = json(ART);
        assertEquals("W100", manifest.get("stage").getAsString());
        assertEquals("scripts/generate_reload_models_w100.py", manifest.get("generator").getAsString());
        assertEquals(List.of("the_recluse"), strings(manifest.getAsJsonArray("ids")));
        assertEquals(21, manifest.get("frames").getAsInt());
        assertEquals(87, manifest.get("assets").getAsInt());
        assertEquals(0, manifest.get("gripBooleanIndex").getAsInt());
        assertEquals(sha256(Path.of("scripts/generate_reload_models_w100.py")),
                manifest.get("generatorSha256").getAsString());
        assertEquals(manifest.getAsJsonObject("sha256"), manifest.getAsJsonObject("assetSha256"));
        assertEquals(1, manifest.get("progressFloatIndex").getAsInt());
        assertEquals(CONTEXTS, strings(manifest.getAsJsonArray("firstPersonContexts")));
        assertTrue(manifest.get("originalsUnchanged").getAsBoolean());
        var expected = expectedAssets();
        assertEquals(87, expected.size());
        var hashes = manifest.getAsJsonObject("sha256");
        assertEquals(expected, hashes.keySet());
        Set<String> disk = new HashSet<>();
        for (String type : List.of("items", "models")) {
            try (var files = Files.walk(ROOT.resolve(type + "/weapon_reload_w100"))) {
                disk.addAll(files.filter(Files::isRegularFile).map(Path::toString).toList());
            }
        }
        assertEquals(expected, disk, "No missing, extra, or other-weapon asset");
        for (var entry : hashes.entrySet())
            assertEquals(entry.getValue().getAsString(), sha256(Path.of(entry.getKey())), entry.getKey());
        for (var entry : ORIGINALS.entrySet())
            assertEquals(entry.getValue(), sha256(Path.of(entry.getKey())), "Independent pin: " + entry.getKey());
        var sources = manifest.getAsJsonObject("sourceSha256");
        assertEquals(ORIGINALS.keySet(), sources.keySet(), "All eleven original pins are required");
        assertTrue(sources.keySet().containsAll(Set.of(ROOT.resolve(SOURCE + ".json").toString(),
                ROOT.resolve("items/weapon/the_recluse.json").toString(), "scripts/build_weapons_w30.py")));
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
        int parsedModels = 0, parsedItems = 0;
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
                parsedItems++;
            } else {
                assertNotNull(CuboidModel.fromStream(new StringReader(Files.readString(Path.of(path)))), path);
                parsedModels++;
            }
        }
        assertEquals(1, parsedItems);
        assertEquals(86, parsedModels);
        var invalidCube = original();
        invalidCube.getAsJsonArray("elements").get(0).getAsJsonObject()
                .add("from", JsonParser.parseString("[0, 0]"));
        assertThrows(com.google.gson.JsonParseException.class,
                () -> CuboidModel.fromStream(new StringReader(invalidCube.toString())),
                "Negative control rejects malformed native cuboid coordinates");
    }

    @Test void wrapperKeepsExactOriginalMetadataAndInactiveAndEveryOtherContextFallback() throws Exception {
        var source = json(ROOT.resolve("items/weapon/the_recluse.json"));
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
        assertEquals(source.get("model"), range.get("fallback"), "Inactive negative progress restores exact graph");
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

    @Test void manifestPartitionReconstructsAll217OriginalElementsExactlyWithin256CubeBudget() throws Exception {
        var manifest = json(ART);
        var source = original();
        var cubes = source.getAsJsonArray("elements");
        assertEquals(217, cubes.size());
        Set<Integer> indices = new HashSet<>();
        for (var index : manifest.getAsJsonArray("magazineIndices")) {
            int value = index.getAsInt();
            assertEquals((double) value, index.getAsDouble(), 0, "Integral source index");
            assertTrue(value >= 0 && value < cubes.size(), "Source index in range");
            assertTrue(indices.add(value), "No duplicate magazine index");
        }
        assertEquals(MAGAZINE_INDICES, manifest.getAsJsonArray("magazineIndices").asList().stream()
                .map(JsonElement::getAsInt).toList(), "Literal reviewed lower-cartridge proxy partition");
        assertEquals(new HashSet<>(MAGAZINE_INDICES), indices);
        assertEquals(24, indices.size());
        JsonArray body = new JsonArray(), magazine = new JsonArray();
        for (int i = 0; i < cubes.size(); i++) (indices.contains(i) ? magazine : body).add(cubes.get(i));
        for (var count : Map.of("sourceCubes", 217, "bodyCubes", body.size(),
                "magazineSourceCubes", magazine.size(), "compositeCubes", 217).entrySet())
            assertEquals(count.getValue().intValue(), manifest.get(count.getKey()).getAsInt(), count.getKey());
        for (String part : PARTS) {
            var expected = source.deepCopy();
            expected.remove("display");
            expected.add("elements", part.equals("body") ? body : magazine);
            assertEquals(expected, json(ROOT.resolve("models/" + KEY + "_" + part + ".json")),
                    "Exact original elements, order, UV, texture and metadata: " + part);
        }
        assertEquals(193, body.size());
        assertEquals(24, magazine.size());
        assertEquals(256, manifest.get("maxCompositeCubes").getAsInt());
        assertEquals(217, body.size() + magazine.size());
        // Explicitly interleave the actual part arrays back into the exact source sequence.
        var actualBody = json(ROOT.resolve("models/" + KEY + "_body.json")).getAsJsonArray("elements");
        var actualMagazine = json(ROOT.resolve("models/" + KEY + "_magazine.json")).getAsJsonArray("elements");
        JsonArray restored = new JsonArray();
        int bodyIndex = 0, magazineIndex = 0;
        for (int i = 0; i < 217; i++) restored.add(indices.contains(i)
                ? actualMagazine.get(magazineIndex++) : actualBody.get(bodyIndex++));
        assertEquals(cubes, restored, "All original faces/UV/texture references/metadata, once and in order");
        assertEquals(193, bodyIndex);
        assertEquals(24, magazineIndex);
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

    @Test void literalAuthoredMotionKeepsSharedRotationScaleAndRotatedMagazineTranslation() throws Exception {
        var keys = authoredKeys();
        assertEquals(keys, json(ART).get("keyframes"), "Authored motion is pinned independently of output");
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
                // ItemTransform is T * Rx * Ry * Rz * S. Uniform original scale
                // lets this matrix oracle independently check rotate(offset) * scale.
                Vector3d expected = transform(body, false).transformDirection(new Vector3d(localOffset));
                assertVector(expected, vector(magazine, "translation").sub(vector(body, "translation")), EPS,
                        "rotate(localOffset) * scale " + label);
            }
        }
        assertTrue(bodyMoved, "Intermediate Recluse motion must exist");
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

    @Test void native26_3ApplyMatchesIndependentSignedMatricesAndBothHandCompensation() throws Exception {
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
                var nativeMatrix = applied(parsedNative, nativeContext, left);
                var twohandMatrix = applied(parsedTwohand, nativeContext, left);
                String label = frame + "/" + part + "/" + context;
                // Native apply uses float vectors/quaternions and ends with model centering.
                // The independent oracle uses doubles and the JSON's original model units.
                assertMatrix(transform(nativePose.getAsJsonObject("display").getAsJsonObject(context), left)
                        .translate(-.5, -.5, -.5), nativeMatrix, "Native apply " + label);
                assertMatrix(transform(twohandPose.getAsJsonObject("display").getAsJsonObject(context), left)
                        .translate(-.5, -.5, -.5), twohandMatrix, "Twohand apply " + label);
                assertMatrix(nativeMatrix, carrier(left).mul(twohandMatrix),
                        "Same authored transform through native charged-crossbow carrier " + label);
                comparisons++;
            }
        }
        assertEquals(84, comparisons, "21 samples * two parts * both signed hands");
    }

    @Test void magazineWorldDisplacementFollowsSharedBodyWithoutAnyIndependentBodyDrift() throws Exception {
        var hip = original().getAsJsonObject("display");
        var magazineCubes = json(ROOT.resolve("models/" + KEY + "_magazine.json")).getAsJsonArray("elements");
        var keys = authoredKeys();
        boolean distinguishesUnrotatedOffset = false;
        for (int frame = 0; frame <= 20; frame++) {
            var rotation = sample(keys, frame / 20.0, 1);
            var translation = sample(keys, frame / 20.0, 2);
            var offset = sample(keys, frame / 20.0, 3);
            for (boolean left : List.of(false, true)) {
                String context = CONTEXTS.get(left ? 1 : 0);
                double sign = left ? -1 : 1;
                var authoredBody = hip.getAsJsonObject(context).deepCopy();
                authoredBody.add("rotation", array(vector(authoredBody, "rotation").add(rotation)));
                authoredBody.add("translation", array(vector(authoredBody, "translation").add(translation)));
                var expectedBody = transform(authoredBody, left);
                // Reflect the local displacement once, using native signed-hand semantics.
                // ItemTransform's rotations then turn that model-space displacement into world space.
                var local = new Vector3d(offset.x * sign, offset.y, offset.z).div(16);
                var expectedDisplacement = expectedBody.transformDirection(new Vector3d(local));
                distinguishesUnrotatedOffset |= expectedDisplacement.distance(local) > .01;
                for (String grip : GRIPS) {
                    String label = frame + "/" + grip + "/" + context;
                    var bodyDisplay = pose(frame, "body", grip).getAsJsonObject("display").getAsJsonObject(context);
                    var magazineDisplay = pose(frame, "magazine", grip).getAsJsonObject("display").getAsJsonObject(context);
                    var body = transform(bodyDisplay, left);
                    var magazine = transform(magazineDisplay, left);
                    if (grip.equals("twohand")) {
                        body = carrier(left).mul(body);
                        magazine = carrier(left).mul(magazine);
                    }
                    assertMatrix(expectedBody, body, "Body follows only authored body motion " + label);
                    // Every original proxy corner has the same rigid displacement, not just the origin.
                    for (var element : magazineCubes) {
                        var cube = element.getAsJsonObject();
                        var from = vector(cube, "from");
                        var to = vector(cube, "to");
                        for (int mask = 0; mask < 8; mask++) {
                            var point = new Vector3d((mask & 1) == 0 ? from.x : to.x,
                                    (mask & 2) == 0 ? from.y : to.y, (mask & 4) == 0 ? from.z : to.z)
                                    .sub(8, 8, 8).div(16);
                            var expectedBodyPoint = expectedBody.transformPosition(new Vector3d(point));
                            var bodyPoint = body.transformPosition(new Vector3d(point));
                            var magazinePoint = magazine.transformPosition(new Vector3d(point));
                            assertVector(expectedBodyPoint, bodyPoint, EPS, "No body drift " + label);
                            assertVector(new Vector3d(expectedBodyPoint).add(expectedDisplacement), magazinePoint,
                                    EPS, "Authored rotated/scaled world displacement " + label);
                            assertVector(expectedDisplacement, magazinePoint.sub(bodyPoint), EPS,
                                    "Same rigid delta at every original corner " + label);
                        }
                    }
                }
            }
        }
        assertTrue(distinguishesUnrotatedOffset, "A raw unrotated display offset must fail this oracle");
    }

    @Test void referencePinsAndPartitionAuditRetainExplicitProxyApproximation() throws Exception {
        var manifest = json(ART);
        var referencePins = Map.of(
                "art/weapons/w100/reference-notes.md",
                "d053f015e48e83e96d880e0ccc1a32108b004475edb8145f351ea75555079da0",
                "art/weapons/w100/references/gameplay-provenance.json",
                "8386d29206ea7a1831a03c45dc6cecc5d731cfcac4dc37841c6f5dabafcaede4");
        for (var entry : referencePins.entrySet()) {
            assertEquals(entry.getValue(), sha256(Path.of(entry.getKey())), "Literal reference pin");
            assertEquals(entry.getValue(), manifest.getAsJsonObject("referenceSha256")
                    .get(entry.getKey()).getAsString());
        }
        for (var entry : manifest.getAsJsonObject("referenceSha256").entrySet())
            assertEquals(entry.getValue().getAsString(), sha256(Path.of(entry.getKey())), entry.getKey());
        var audit = json(Path.of("art/weapons/w100/model-partition-audit.json"));
        assertEquals("art/weapons/w100/model-partition-audit.json", manifest.get("partitionAudit").getAsString());
        assertEquals(manifest.get("magazineIndices"), audit.get("magazineIndices"));
        assertEquals(manifest.get("partitionApproximation"), audit.get("approximation"));
        assertEquals(217, audit.get("sourceCubes").getAsInt());
        assertEquals(193, audit.get("bodyCubes").getAsInt());
        assertEquals(24, audit.get("magazineSourceCubes").getAsInt());
        var source = audit.getAsJsonObject("sourceIdentification");
        assertEquals("Mesh_0007.rip", source.get("magazineMesh").getAsString());
        assertEquals(1, source.get("magazineComponent").getAsInt());
        assertEquals(352, source.get("magazineTriangles").getAsInt());
        assertTrue(audit.getAsJsonObject("approximation").get("wholeCubePartition").getAsBoolean());
        assertTrue(audit.get("partitionStatus").getAsString().contains("proxy"));
        for (var entry : manifest.getAsJsonObject("auditSha256").entrySet())
            assertEquals(entry.getValue().getAsString(), sha256(Path.of(entry.getKey())), entry.getKey());
        // Byte/geometry contracts cannot establish physical magazine identity or visual fidelity.
    }

    private static JsonObject json(Path path) throws Exception {
        return JsonParser.parseString(Files.readString(path)).getAsJsonObject();
    }

    private static JsonArray authoredKeys() { return JsonParser.parseString(AUTHORED_KEYS).getAsJsonArray(); }

    private static JsonArray array(Vector3d value) {
        JsonArray result = new JsonArray();
        result.add(value.x);
        result.add(value.y);
        result.add(value.z);
        return result;
    }

    private static Matrix4d carrier(boolean left) {
        double sign = left ? -1 : 1;
        return new Matrix4d().translate(-.641864 * sign, 0, 0).rotateY(Math.toRadians(10) * sign);
    }

    private static Matrix4d applied(CuboidModel model, ItemDisplayContext context, boolean left) {
        PoseStack stack = new PoseStack();
        model.transforms().getTransform(context).apply(left, stack.last());
        return new Matrix4d(stack.last().pose());
    }

    private static void assertMatrix(Matrix4d expected, Matrix4d actual, String label) {
        double[] expectedValues = expected.get(new double[16]);
        double[] actualValues = actual.get(new double[16]);
        for (int i = 0; i < 16; i++) {
            assertTrue(Double.isFinite(actualValues[i]), "Finite matrix " + label + "/" + i);
            assertEquals(expectedValues[i], actualValues[i], EPS, label + "/matrix[" + i + "]");
        }
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

    /** Independent interpolation of literal authored vectors; no generator execution or manifest oracle. */
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
