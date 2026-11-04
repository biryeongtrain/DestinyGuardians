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

/** Duke-only W64 contracts against original assets and native 26.3 parsers; no game launch. */
class HandCannonReloadW64Test {
    private static final Path ROOT = Path.of("src/main/resources/assets/destiny");
    private static final Path ART = Path.of("art/weapons/w64");
    private static final String KEY = "weapon_reload_w64/duke_mk_44";
    private static final List<String> CONTEXTS = List.of("firstperson_righthand", "firstperson_lefthand");
    private static final List<String> PARTS = List.of("body", "cylinder");
    private static final List<String> GRIPS = List.of("native", "twohand");
    // Audited source partition, independent of the generator and its manifest.
    private static final List<Integer> CYLINDER = List.of(7, 8, 11, 12, 48, 52, 55, 56, 57, 73,
            80, 82, 83, 164, 178, 179, 181, 182, 183, 186, 230);
    private static final double EPS = 3e-6;
    // Independent geometric samples: closed, opening, loading hold, closing, closed.
    private static final double[] SWING_DEGREES = {0, 0, 0, 0, 560.0 / 27, 1600.0 / 27,
            80, 80, 80, 80, 80, 80, 80, 80, 80, 80, 1600.0 / 27, 12.5, 0, 0, 0};
    // SHA-256 read directly from the baseline current originals, not copied from manifest assertions.
    private static final Map<String, String> ORIGINALS = Map.of(
            "src/main/resources/assets/destiny/models/weapon/hand_cannon/duke_mk_44.json",
            "c933fdbc7abff648419552b326ce028dc9e0ddc389c53e7b1b515e13c90e790b",
            "src/main/resources/assets/destiny/items/weapon/duke_mk_44.json",
            "54c03246a7245c31b88ceeeb0c9f7f8383bb93c8ae2ec9197caca44b4356b2e7",
            "scripts/build_weapons_w30.py",
            "e087fca588231486505691e97b5c2b581382c1055c76d64300dbc24118bf1d83",
            "scripts/generate_reload_models_w47.py",
            "00bb70829765db287a3f412f3aed53cd4defef391fe44c5825fb2c6a58f2d4cf");
    private static final String TWOHAND_SHA = "0885e56d53c6cd399dec518746990b206cf4d42e9637e66c923751caff7c9754";

    @Test void inventoryContainsExactly87DukeAssetsAndOriginalSourcesMatchIndependentPins() throws Exception {
        var manifest = json(ART.resolve("manifest.json"));
        assertEquals("W64", manifest.get("stage").getAsString());
        assertEquals("scripts/generate_reload_models_w64.py", manifest.get("generator").getAsString());
        assertEquals(List.of("duke_mk_44"), strings(manifest.getAsJsonArray("ids")));
        assertEquals(21, manifest.get("frames").getAsInt());
        assertEquals(1, manifest.get("progressFloatIndex").getAsInt());
        assertEquals(CONTEXTS, strings(manifest.getAsJsonArray("firstPersonContexts")));
        for (var count : Map.of("sourceCubes", 232, "bodyCubes", 211, "cylinderSourceCubes", 21,
                "addedYokeCubes", 2, "compositeCubes", 234).entrySet())
            assertEquals(count.getValue().intValue(), manifest.get(count.getKey()).getAsInt(), count.getKey());
        assertEquals(CYLINDER, manifest.getAsJsonArray("cylinderIndices").asList().stream()
                .map(JsonElement::getAsInt).toList());
        assertVector(new Vector3d(8, 10.2, 5.17), vector(manifest, "pivot"), 0, "Independent hinge pin");
        assertTrue(manifest.get("originalsUnchanged").getAsBoolean());
        assertFalse(manifest.get("handIK").getAsBoolean());
        assertFalse(manifest.get("exactAnimationRip").getAsBoolean());

        var hashes = manifest.getAsJsonObject("sha256");
        assertEquals(87, expectedAssets().size());
        assertEquals(expectedAssets(), hashes.keySet(), "No other weapon, missing asset, or extra manifest entry");
        Set<String> disk = new HashSet<>();
        for (String type : List.of("items", "models")) {
            try (var files = Files.walk(ROOT.resolve(type + "/weapon_reload_w64"))) {
                disk.addAll(files.filter(Files::isRegularFile).map(Path::toString).toList());
            }
        }
        assertEquals(expectedAssets(), disk, "Unlisted files must not silently ship");
        for (var entry : hashes.entrySet())
            assertEquals(entry.getValue().getAsString(), sha256(Path.of(entry.getKey())), entry.getKey());
        var sources = manifest.getAsJsonObject("sourceSha256");
        assertEquals(ORIGINALS.keySet(), sources.keySet());
        for (var entry : ORIGINALS.entrySet()) {
            assertEquals(entry.getValue(), sha256(Path.of(entry.getKey())), entry.getKey());
            assertEquals(entry.getValue(), sources.get(entry.getKey()).getAsString(), "Independent source pin");
        }
        assertEquals(TWOHAND_SHA, sha256(ROOT.resolve("models/weapon/hand_cannon/duke_mk_44_twohand.json")));
        verifyFinalDukeReferenceEvidence();
    }

    @Test void native26_3ItemCodecAndCuboidParserAcceptEveryOneOfThe87Assets() throws Exception {
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
                        "Negative control: codec rejects invalid display context spelling");
            } else {
                assertNotNull(CuboidModel.fromStream(new StringReader(Files.readString(Path.of(path)))), path);
            }
            parsed++;
        }
        assertEquals(87, parsed);
    }

    @Test void wrapperPreservesAllOriginalMetadataAndExactInactiveAndOtherContextGraphs() throws Exception {
        var source = json(ROOT.resolve("items/weapon/duke_mk_44.json"));
        var reload = item();
        var restored = reload.deepCopy();
        restored.add("model", source.get("model").deepCopy());
        assertEquals(source, restored, "Includes hand_animation_on_swap and all other original metadata");
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
            assertEquals(source.get("model"), select.get("fallback"), "Exact original in " + context);
        }
        var range = branch.getAsJsonObject("model");
        assertEquals(Set.of("type", "property", "index", "entries", "fallback"), range.keySet());
        assertEquals("minecraft:range_dispatch", range.get("type").getAsString());
        assertEquals("minecraft:custom_model_data", range.get("property").getAsString());
        assertEquals(1, range.get("index").getAsInt(), "Progress float 1 leaves pose string 0 independent");
        assertEquals(source.get("model"), range.get("fallback"), "Missing/negative inactive progress keeps original graph");
        assertEquals(0, range.getAsJsonArray("entries").get(0).getAsJsonObject().get("threshold").getAsDouble(), 0);
    }

    @Test void all21OrderedFramesSelectTwoRigidPartsForBothBooleanZeroGripsWithoutAliasing() throws Exception {
        var entries = item().getAsJsonObject("model").getAsJsonArray("cases").get(0).getAsJsonObject()
                .getAsJsonObject("model").getAsJsonArray("entries");
        assertEquals(21, entries.size());
        Set<String> references = new HashSet<>();
        Set<JsonObject> intermediatePoses = new HashSet<>();
        for (int frame = 0; frame <= 20; frame++) {
            var entry = entries.get(frame).getAsJsonObject();
            assertEquals(Set.of("threshold", "model"), entry.keySet());
            assertEquals(frame / 20.0, entry.get("threshold").getAsDouble(), 1e-9, "Normalized ordered progress");
            var condition = entry.getAsJsonObject("model");
            assertEquals(Set.of("type", "property", "index", "on_true", "on_false"), condition.keySet());
            assertEquals("minecraft:condition", condition.get("type").getAsString());
            assertEquals("minecraft:custom_model_data", condition.get("property").getAsString());
            assertEquals(0, condition.get("index").getAsInt(), "Two-hand grip uses flag 0");
            for (String grip : GRIPS) {
                var composite = condition.getAsJsonObject(grip.equals("twohand") ? "on_true" : "on_false");
                assertEquals(Set.of("type", "models"), composite.keySet());
                assertEquals("minecraft:composite", composite.get("type").getAsString());
                var parts = composite.getAsJsonArray("models");
                assertEquals(2, parts.size(), "Exactly body plus cylinder/yoke");
                for (int i = 0; i < PARTS.size(); i++) {
                    var part = parts.get(i).getAsJsonObject();
                    assertEquals(Set.of("type", "model"), part.keySet());
                    assertEquals("minecraft:model", part.get("type").getAsString());
                    String expected = "destiny:" + poseKey(frame, PARTS.get(i), grip);
                    assertEquals(expected, part.get("model").getAsString());
                    assertTrue(references.add(expected), "No stage aliases: " + expected);
                }
            }
            if (frame > 0 && frame < 20)
                assertTrue(intermediatePoses.add(pose(frame, "body", "native").getAsJsonObject("display")),
                        "Distinct intermediate body pose " + frame);
        }
        assertEquals(84, references.size());
        assertEquals(19, intermediatePoses.size());
    }

    @Test void partitionPreservesAll232OriginalCubesAndExactUvsWithTwoYokeLinksInsideClosedEnvelope() throws Exception {
        var source = original();
        var cubes = source.getAsJsonArray("elements");
        assertEquals(232, cubes.size(), "Actual source count, not the earlier 216 estimate");
        assertEquals(21, new HashSet<>(CYLINDER).size());
        JsonArray body = new JsonArray(), cylinder = new JsonArray();
        for (int i = 0; i < cubes.size(); i++)
            (CYLINDER.contains(i) ? cylinder : body).add(cubes.get(i).deepCopy());
        assertEquals(211, body.size());
        assertEquals(21, cylinder.size());
        assertEquals(cubes.size(), body.size() + cylinder.size());
        double[][] from = {{7.78, 10.2, 4.97}, {7.78, 12.05, 3.7}};
        double[][] to = {{8.22, 12.25, 5.37}, {8.22, 12.45, 5.37}};
        var min = bounds(cubes, "from", true);
        var max = bounds(cubes, "to", false);
        for (int i = 0; i < 2; i++) {
            var link = cubes.get(120).getAsJsonObject().deepCopy();
            link.add("from", array(from[i]));
            link.add("to", array(to[i]));
            cylinder.add(link);
            // Closed HIP endpoints use original coordinates: added links stay inside the
            // original weapon AABB. This is an envelope check, not an occlusion claim.
            for (Vector3d corner : corners(link)) for (int axis = 0; axis < 3; axis++)
                assertTrue(corner.get(axis) >= min.get(axis) && corner.get(axis) <= max.get(axis),
                        "Closed yoke outside original weapon envelope: " + i + "/" + axis);
            assertEquals(cubes.get(120).getAsJsonObject().get("faces"), link.get("faces"), "Original metal UVs");
        }
        for (String part : PARTS) {
            var expected = source.deepCopy();
            expected.remove("display");
            expected.add("elements", part.equals("body") ? body : cylinder);
            assertEquals(expected, json(ROOT.resolve("models/" + KEY + "_" + part + ".json")),
                    "Exact source order, coordinates, rotations, faces, UVs, textures and metadata: " + part);
        }
        assertEquals(23, cylinder.size());
        assertEquals(234, body.size() + cylinder.size());
        assertTrue(body.size() + cylinder.size() <= 256, "Composite model cube budget");
        for (int frame = 0; frame <= 20; frame++) for (String grip : GRIPS) for (String part : PARTS) {
            var child = pose(frame, part, grip);
            assertEquals(Set.of("parent", "display"), child.keySet(), "Pose assets only transform inherited geometry");
            assertEquals("destiny:" + KEY + "_" + part, child.get("parent").getAsString());
            assertEquals(source.getAsJsonObject("display").keySet(), child.getAsJsonObject("display").keySet());
        }
    }

    @Test void bothEndpointsExactlyRestoreOriginalNativeAndTwohandHipForBodyAndCylinder() throws Exception {
        for (String grip : GRIPS) {
            var hip = json(ROOT.resolve("models/weapon/hand_cannon/duke_mk_44"
                    + (grip.equals("twohand") ? "_twohand" : "") + ".json")).getAsJsonObject("display");
            for (int frame : List.of(0, 20)) for (String part : PARTS)
                assertEquals(hip, pose(frame, part, grip).get("display"),
                        "Exact original HIP endpoint " + frame + "/" + part + "/" + grip);
        }
    }

    @Test void inverseBodyMakesIndependentHingeFixedAndEveryCylinderVertexFollowsRigidPivotRotation() throws Exception {
        var cubes = original().getAsJsonArray("elements");
        for (int frame = 0; frame <= 20; frame++) for (String grip : GRIPS) for (boolean left : List.of(false, true)) {
            String label = frame + "/" + grip + "/" + left;
            Matrix4d relative = relativeCylinder(frame, grip, left);
            Vector3d pivot = modelPoint(new Vector3d(8, 10.2, 5.17), left);
            assertVector(pivot, relative.transformPosition(new Vector3d(pivot)), EPS, "Fixed hinge " + label);
            Matrix4d expected = new Matrix4d().translation(pivot)
                    .rotateZ(Math.toRadians(SWING_DEGREES[frame]) * (left ? -1 : 1))
                    .translate(-pivot.x, -pivot.y, -pivot.z);
            assertTrue(expected.equals(relative, EPS), "Pure pivot rotation, no scale, shear or drift " + label);
            for (int index : CYLINDER) for (Vector3d corner : corners(cubes.get(index).getAsJsonObject())) {
                Vector3d point = modelPoint(corner, left);
                assertVector(expected.transformPosition(new Vector3d(point)), relative.transformPosition(new Vector3d(point)),
                        EPS, "Rigid original cube " + index + "/" + label);
            }
        }
    }

    @Test void measuredSwingOpensLeftTo80DegreesHoldsThenClosesWithoutHidingOrDetachedTranslation() throws Exception {
        var source = original();
        var cubes = source.getAsJsonArray("elements");
        Vector3d center = new Vector3d();
        for (int index : CYLINDER) center.add(vector(cubes.get(index).getAsJsonObject(), "from")
                .add(vector(cubes.get(index).getAsJsonObject(), "to")).mul(.5));
        center.div(CYLINDER.size());
        double previousAngle = 0;
        for (int frame = 0; frame <= 20; frame++) {
            double measuredAngle = Double.NaN;
            for (String grip : GRIPS) for (boolean left : List.of(false, true)) {
                String context = CONTEXTS.get(left ? 1 : 0);
                var body = pose(frame, "body", grip).getAsJsonObject("display").getAsJsonObject(context);
                var cylinder = pose(frame, "cylinder", grip).getAsJsonObject("display").getAsJsonObject(context);
                assertEquals(source.getAsJsonObject("display").getAsJsonObject(context).get("scale"), body.get("scale"));
                assertEquals(body.get("scale"), cylinder.get("scale"), "No shrinking or hiding the drum");
                Vector3d pivot = modelPoint(new Vector3d(8, 10.2, 5.17), left);
                Vector3d closed = modelPoint(new Vector3d(center), left);
                Vector3d opened = relativeCylinder(frame, grip, left).transformPosition(new Vector3d(closed));
                Vector3d a = new Vector3d(closed).sub(pivot), b = new Vector3d(opened).sub(pivot);
                double sign = left ? -1 : 1;
                double angle = Math.toDegrees(Math.atan2(a.x * b.y - a.y * b.x, a.x * b.x + a.y * b.y)) * sign;
                assertTrue(angle >= -1e-3 && angle <= 80.001, "Bounded measured swing " + frame);
                assertEquals(a.length(), b.length(), EPS, "Drum remains attached at fixed radius");
                assertEquals(a.z, b.z, EPS, "No movement along local hinge axis");
                if (Double.isNaN(measuredAngle)) measuredAngle = angle;
                else assertEquals(measuredAngle, angle, 1e-3, "Both hands and grips share physical swing");
                if (frame >= 6 && frame <= 15) {
                    assertEquals(80, angle, 1e-3, "Open loading hold reaches maximum swing");
                    assertTrue((opened.x - closed.x) * sign < -2.0 / 16, "Drum swings to authored local left");
                }
                if (frame <= 3 || frame >= 18)
                    assertVector(closed, opened, EPS, "Drum seated before opening and after closing");
            }
            if (frame >= 4 && frame <= 6) assertTrue(measuredAngle > previousAngle + 1, "Opening advances");
            if (frame >= 16 && frame <= 18) assertTrue(measuredAngle < previousAngle - 1, "Closure advances");
            previousAngle = measuredAngle;
        }
        // Independent body keyframe: muzzle rises and receiver moves left/down during opening.
        for (String context : CONTEXTS) {
            var hip = source.getAsJsonObject("display").getAsJsonObject(context);
            var body = pose(6, "body", "native").getAsJsonObject("display").getAsJsonObject(context);
            assertVector(new Vector3d(62, -16, -14), vector(body, "rotation").sub(vector(hip, "rotation")), EPS, "Body raise");
            assertVector(new Vector3d(-1.8, -4, -.5), vector(body, "translation").sub(vector(hip, "translation")), EPS, "Body displacement");
        }
    }

    @Test void all84PoseAssetsCompensateNativeCrossbowGripAndPreserveUnrelatedDisplayContexts() throws Exception {
        var nativeHip = original().getAsJsonObject("display");
        var twohandHip = json(ROOT.resolve("models/weapon/hand_cannon/duke_mk_44_twohand.json")).getAsJsonObject("display");
        int checkedAssets = 0;
        for (int frame = 0; frame <= 20; frame++) for (String part : PARTS) {
            var nativeDisplay = pose(frame, part, "native").getAsJsonObject("display");
            var twohand = pose(frame, part, "twohand").getAsJsonObject("display");
            for (boolean left : List.of(false, true)) {
                String context = CONTEXTS.get(left ? 1 : 0);
                double sign = left ? -1 : 1;
                var restored = new Matrix4d().translate(-.641864 * sign, 0, 0)
                        .rotateY(Math.toRadians(10) * sign).mul(transform(twohand.getAsJsonObject(context), left));
                assertTrue(transform(nativeDisplay.getAsJsonObject(context), left).equals(restored, 2e-6),
                        "Compensated native transform " + frame + "/" + part + "/" + context);
            }
            for (String context : nativeHip.keySet()) if (!CONTEXTS.contains(context)) {
                assertEquals(nativeHip.get(context), nativeDisplay.get(context), "Native unrelated context " + context);
                assertEquals(twohandHip.get(context), twohand.get(context), "Original twohand context " + context);
            }
            checkedAssets += 2;
        }
        assertEquals(84, checkedAssets);
    }

    private static JsonObject json(Path path) throws Exception {
        return JsonParser.parseString(Files.readString(path)).getAsJsonObject();
    }

    /** Final reference files arrived during this sidecar; assert their actual published schema. */
    private static void verifyFinalDukeReferenceEvidence() throws Exception {
        var reference = json(ART.resolve("references/manifest.json"));
        assertEquals("W64", reference.get("stage").getAsString());
        assertEquals("duke_mk_44", reference.get("target").getAsString());
        assertEquals(2112909414L, reference.get("bungieHash").getAsLong());
        var video = reference.getAsJsonArray("videoSources").asList().stream().map(JsonElement::getAsJsonObject)
                .filter(v -> v.get("id").getAsString().equals("-oS68Bu_sDs")).findFirst().orElseThrow();
        assertEquals("https://www.youtube.com/watch?v=-oS68Bu_sDs", video.get("url").getAsString());
        assertEquals("0da7f343966728f1715bffe93f439e0f861ad2a5dd364f1fb6486d2b48aa9270",
                video.get("privateVideoSha256").getAsString());
        assertEquals("116c938cb22b94077b41a8c39b18ab1a9d62a7570a5abd34b191b3f4491c3936",
                video.get("privateMetadataSha256").getAsString());
        var window = video.getAsJsonArray("reviewedWindowsSeconds").get(0).getAsJsonArray();
        assertEquals(25.4, window.get(0).getAsDouble(), 0);
        assertEquals(28.4, window.get(1).getAsDouble(), 0);
        var files = reference.getAsJsonObject("files");
        for (String path : List.of("art/weapons/w64/reference-notes.md",
                "art/weapons/w64/references/provenance.json", "art/weapons/w64/references/observations.json"))
            assertEquals(files.get(path).getAsString(), sha256(Path.of(path)), path);
        var images = reference.getAsJsonArray("selectedImages").asList().stream().map(JsonElement::getAsJsonObject)
                .filter(v -> v.get("sourceId").getAsString().equals("-oS68Bu_sDs")).toList();
        assertEquals(4, images.size(), "Duke contact sheet plus three selected full frames");
        for (var image : images) {
            String path = image.get("path").getAsString();
            assertEquals(files.get(path), image.get("sha256"));
            assertEquals(image.get("sha256").getAsString(), sha256(Path.of(path)), path);
        }
        var observations = json(ART.resolve("references/observations.json"));
        assertEquals(List.of("duke_mk_44"), strings(observations.getAsJsonArray("implementationTarget")));
        var duke = observations.getAsJsonArray("weapons").asList().stream().map(JsonElement::getAsJsonObject)
                .filter(v -> v.get("id").getAsString().equals("duke_mk_44")).findFirst().orElseThrow();
        assertFalse(duke.getAsJsonObject("sampleType").get("outlawObserved").getAsBoolean());
        assertFalse(duke.getAsJsonObject("sampleType").get("normalBaseStatCertified").getAsBoolean());
        assertFalse(duke.getAsJsonObject("outlawComparison").get("inspected").getAsBoolean());
    }

    private static JsonObject original() throws Exception {
        return json(ROOT.resolve("models/weapon/hand_cannon/duke_mk_44.json"));
    }

    private static JsonObject item() throws Exception {
        return json(ROOT.resolve("items/" + KEY + ".json"));
    }

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

    private static JsonArray array(double[] values) {
        JsonArray result = new JsonArray();
        for (double value : values) result.add(value);
        return result;
    }

    private static Vector3d vector(JsonObject object, String key) {
        var values = object.getAsJsonArray(key);
        assertEquals(3, values.size());
        for (var value : values) assertTrue(Double.isFinite(value.getAsDouble()), "Finite " + key);
        return new Vector3d(values.get(0).getAsDouble(), values.get(1).getAsDouble(), values.get(2).getAsDouble());
    }

    private static Vector3d bounds(JsonArray cubes, String key, boolean minimum) {
        Vector3d result = new Vector3d(minimum ? Double.POSITIVE_INFINITY : Double.NEGATIVE_INFINITY);
        for (var cube : cubes) {
            Vector3d value = vector(cube.getAsJsonObject(), key);
            if (minimum) result.min(value);
            else result.max(value);
        }
        return result;
    }

    private static List<Vector3d> corners(JsonObject cube) {
        var from = vector(cube, "from");
        var to = vector(cube, "to");
        return List.of(new Vector3d(from.x, from.y, from.z), new Vector3d(to.x, from.y, from.z),
                new Vector3d(from.x, to.y, from.z), new Vector3d(to.x, to.y, from.z),
                new Vector3d(from.x, from.y, to.z), new Vector3d(to.x, from.y, to.z),
                new Vector3d(from.x, to.y, to.z), new Vector3d(to.x, to.y, to.z));
    }

    private static void assertVector(Vector3d expected, Vector3d actual, double tolerance, String message) {
        assertEquals(expected.x, actual.x, tolerance, message + "/x");
        assertEquals(expected.y, actual.y, tolerance, message + "/y");
        assertEquals(expected.z, actual.z, tolerance, message + "/z");
    }

    /** Model coordinates are centered on [8,8,8]; left-hand ItemTransform reflects local X. */
    private static Vector3d modelPoint(Vector3d point, boolean left) {
        point.sub(8, 8, 8).div(16);
        if (left) point.x = -point.x;
        return point;
    }

    private static Matrix4d relativeCylinder(int frame, String grip, boolean left) throws Exception {
        String context = CONTEXTS.get(left ? 1 : 0);
        var body = pose(frame, "body", grip).getAsJsonObject("display").getAsJsonObject(context);
        var cylinder = pose(frame, "cylinder", grip).getAsJsonObject("display").getAsJsonObject(context);
        return transform(body, left).invert().mul(transform(cylinder, left));
    }

    /** Same 26.3 ItemTransform order/units as W47, computed independently of Python helpers. */
    private static Matrix4d transform(JsonObject display, boolean left) {
        var r = vector(display, "rotation").mul(Math.PI / 180);
        var t = vector(display, "translation").div(16);
        var s = vector(display, "scale");
        double sign = left ? -1 : 1;
        return new Matrix4d().translate(t.x * sign, t.y, t.z)
                .rotateXYZ(r.x, r.y * sign, r.z * sign).scale(s.x, s.y, s.z);
    }
}
