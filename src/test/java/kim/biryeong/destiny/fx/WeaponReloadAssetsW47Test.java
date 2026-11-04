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
import org.joml.Matrix4f;
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
import java.util.Map;
import java.util.Set;

import static org.junit.jupiter.api.Assertions.*;

/** W47 assets against native 26.3 parsers and geometric contracts; no game launch required. */
class WeaponReloadAssetsW47Test {
    private static final Path ROOT = Path.of("src/main/resources/assets/destiny");
    private static final Path ART = Path.of("art/weapons/w47");
    private static final String KEY = "weapon_reload_w47/beloved";
    private static final List<String> CONTEXTS = List.of("firstperson_righthand", "firstperson_lefthand");
    private static final List<String> PARTS = List.of("body", "magazine");
    private static final List<String> GRIPS = List.of("native", "twohand");
    private static final List<Integer> MAGAZINE = List.of(107, 108, 109, 110, 111, 115, 120, 194, 195, 203);
    // Independent pins: changing both the generated manifest and an original must still fail.
    private static final Map<String, String> ORIGINALS = Map.of(
            "src/main/resources/assets/destiny/models/weapon/sniper_rifle/beloved.json",
            "9c404f594392862390288a35c0aa0aa1943e5e5b6cdb3b36e843b8bf45a70bee",
            "src/main/resources/assets/destiny/items/weapon/beloved.json",
            "f94299f5ba4d9790f83ead34eb6a40d823c2c74fa69201ef3afc205b93d4d70c",
            "scripts/build_weapons_w30.py",
            "e087fca588231486505691e97b5c2b581382c1055c76d64300dbc24118bf1d83");

    private static JsonObject json(Path path) throws Exception {
        return JsonParser.parseString(Files.readString(path)).getAsJsonObject();
    }

    private static JsonObject original() throws Exception {
        return json(ROOT.resolve("models/weapon/sniper_rifle/beloved.json"));
    }

    private static JsonObject item() throws Exception {
        return json(ROOT.resolve("items/" + KEY + ".json"));
    }

    private static String poseKey(int frame, String part, String grip) {
        return KEY + "_" + String.format(java.util.Locale.ROOT, "%02d", frame) + "_" + part + "_" + grip;
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

    @Test void all87GeneratedAssetsAreInventoriedHashedAndAllOriginalSourcesRemainByteIdentical() throws Exception {
        var manifest = json(ART.resolve("manifest.json"));
        assertEquals(List.of("beloved"), manifest.getAsJsonArray("ids").asList().stream().map(JsonElement::getAsString).toList());
        assertEquals(21, manifest.get("frames").getAsInt());
        assertEquals(253, manifest.get("sourceCubes").getAsInt());
        assertEquals(CONTEXTS, manifest.getAsJsonArray("firstPersonContexts").asList().stream().map(JsonElement::getAsString).toList());
        assertEquals(1, manifest.get("progressFloatIndex").getAsInt());
        assertTrue(manifest.get("originalsUnchanged").getAsBoolean());
        assertEquals(MAGAZINE, manifest.getAsJsonArray("magazineIndices").asList().stream().map(JsonElement::getAsInt).toList());
        assertEquals("scripts/generate_reload_models_w47.py", manifest.get("generator").getAsString());
        var hashes = manifest.getAsJsonObject("sha256");
        assertEquals(87, hashes.size());
        assertEquals(expectedAssets(), hashes.keySet(), "No missing, extra, or other-weapon manifest entries");
        Set<String> disk = new HashSet<>();
        for (String type : List.of("items", "models")) {
            try (var files = Files.walk(ROOT.resolve(type + "/weapon_reload_w47"))) {
                disk.addAll(files.filter(Files::isRegularFile).map(Path::toString).toList());
            }
        }
        assertEquals(expectedAssets(), disk, "Unlisted files must not silently ship");
        for (var entry : hashes.entrySet())
            assertEquals(entry.getValue().getAsString(), sha256(Path.of(entry.getKey())), entry.getKey());
        var sources = manifest.getAsJsonObject("sourceSha256");
        assertEquals(ORIGINALS.keySet(), sources.keySet());
        for (var entry : ORIGINALS.entrySet()) {
            assertEquals(entry.getValue(), sources.get(entry.getKey()).getAsString(), "Independent original pin");
            assertEquals(entry.getValue(), sha256(Path.of(entry.getKey())), entry.getKey());
        }
    }

    @Test void actual26_3ItemCodecAndCuboidParserAcceptEveryGeneratedAsset() throws Exception {
        net.minecraft.SharedConstants.tryDetectVersion();
        net.minecraft.server.Bootstrap.bootStrap();
        ItemModels.bootstrap();
        ItemTintSources.bootstrap();
        net.minecraft.client.renderer.item.properties.select.SelectItemModelProperties.bootstrap();
        net.minecraft.client.renderer.item.properties.conditional.ConditionalItemModelProperties.bootstrap();
        net.minecraft.client.renderer.item.properties.numeric.RangeSelectItemModelProperties.bootstrap();
        var model = item().getAsJsonObject("model");
        var decoded = ItemModels.CODEC.parse(JsonOps.INSTANCE, model);
        assertTrue(decoded.isSuccess(), "26.3 ItemModels.CODEC: " + decoded.error());
        var invalid = model.deepCopy();
        invalid.getAsJsonArray("cases").get(0).getAsJsonObject().addProperty("when", "first_person_right_hand");
        assertFalse(ItemModels.CODEC.parse(JsonOps.INSTANCE, invalid).isSuccess(), "Codec must reject wrong context enum spelling");
        for (String path : expectedAssets()) if (path.contains("/models/"))
            assertNotNull(CuboidModel.fromStream(new StringReader(Files.readString(Path.of(path)))), path);
    }

    @Test void wrapperPreservesOriginalMetadataAndExactFallbackWithOnlyTwoFirstPersonContexts() throws Exception {
        var source = json(ROOT.resolve("items/weapon/beloved.json"));
        var reload = item();
        var metadata = reload.deepCopy();
        metadata.add("model", source.get("model").deepCopy());
        assertEquals(source, metadata, "Includes original hand_animation_on_swap and any future metadata");
        var select = reload.getAsJsonObject("model");
        assertEquals(Set.of("type", "property", "cases", "fallback"), select.keySet());
        assertEquals("minecraft:select", select.get("type").getAsString());
        assertEquals("minecraft:display_context", select.get("property").getAsString());
        assertEquals(source.get("model"), select.get("fallback"), "Keep full original ADS/inspect/grip wrapper");
        assertEquals(1, select.getAsJsonArray("cases").size());
        var branch = select.getAsJsonArray("cases").get(0).getAsJsonObject();
        assertEquals(CONTEXTS, branch.getAsJsonArray("when").asList().stream().map(JsonElement::getAsString).toList());
        for (ItemDisplayContext context : ItemDisplayContext.values()) {
            if (CONTEXTS.contains(context.getSerializedName())) continue;
            assertFalse(branch.getAsJsonArray("when").asList().stream()
                    .anyMatch(v -> v.getAsString().equals(context.getSerializedName())), context.toString());
            assertEquals(source.get("model"), select.get("fallback"), "Exact original in " + context);
        }
        var range = branch.getAsJsonObject("model");
        assertEquals(Set.of("type", "property", "index", "entries", "fallback"), range.keySet());
        assertEquals("minecraft:range_dispatch", range.get("type").getAsString());
        assertEquals("minecraft:custom_model_data", range.get("property").getAsString());
        assertEquals(1, range.get("index").getAsInt(), "Reload progress float slot 1; pose strings 0/grip bool 0 independent");
        assertEquals(source.get("model"), range.get("fallback"), "Below-range values preserve original behavior");
    }

    @Test void all21OrderedStagesSelectDistinctPartReferencesUsingGripBooleanZero() throws Exception {
        var entries = item().getAsJsonObject("model").getAsJsonArray("cases").get(0).getAsJsonObject()
                .getAsJsonObject("model").getAsJsonArray("entries");
        assertEquals(21, entries.size());
        Set<String> references = new HashSet<>();
        Set<JsonObject> intermediatePoses = new HashSet<>();
        for (int frame = 0; frame <= 20; frame++) {
            var entry = entries.get(frame).getAsJsonObject();
            assertEquals(frame / 20.0, entry.get("threshold").getAsDouble(), 1e-9, "Ordered normalized progress");
            var condition = entry.getAsJsonObject("model");
            assertEquals(Set.of("type", "property", "index", "on_true", "on_false"), condition.keySet());
            assertEquals("minecraft:condition", condition.get("type").getAsString());
            assertEquals("minecraft:custom_model_data", condition.get("property").getAsString());
            assertEquals(0, condition.get("index").getAsInt(), "Two-hand grip is boolean slot 0");
            for (String grip : GRIPS) {
                var composite = condition.getAsJsonObject(grip.equals("twohand") ? "on_true" : "on_false");
                assertEquals(Set.of("type", "models"), composite.keySet());
                assertEquals("minecraft:composite", composite.get("type").getAsString());
                var parts = composite.getAsJsonArray("models");
                assertEquals(2, parts.size(), "Exactly one body and one magazine per frame");
                for (int i = 0; i < PARTS.size(); i++) {
                    var part = parts.get(i).getAsJsonObject();
                    assertEquals(Set.of("type", "model"), part.keySet());
                    assertEquals("minecraft:model", part.get("type").getAsString());
                    String expected = "destiny:" + poseKey(frame, PARTS.get(i), grip);
                    assertEquals(expected, part.get("model").getAsString());
                    assertTrue(references.add(expected), "Stage must not alias a different stage: " + expected);
                }
            }
            if (frame > 0 && frame < 20)
                assertTrue(intermediatePoses.add(pose(frame, "body", "native").getAsJsonObject("display")), "Distinct intermediate pose " + frame);
        }
        assertEquals(84, references.size());
        assertEquals(19, intermediatePoses.size());
        // Endpoints deliberately share the HIP pose; their stage references remain distinct.
    }

    @Test void rigidBodyMagazinePartitionReconstructsEveryOriginalCubeExactlyWithinBudget() throws Exception {
        var source = original();
        var cubes = source.getAsJsonArray("elements");
        assertEquals(253, cubes.size());
        JsonArray body = new JsonArray(), magazine = new JsonArray();
        for (int i = 0; i < cubes.size(); i++) (MAGAZINE.contains(i) ? magazine : body).add(cubes.get(i).deepCopy());
        for (String part : PARTS) {
            var expected = source.deepCopy();
            expected.remove("display");
            expected.add("elements", part.equals("body") ? body : magazine);
            assertEquals(expected, json(ROOT.resolve("models/" + KEY + "_" + part + ".json")),
                    "Preserve geometry, order, UVs, rotations, faces, textures and metadata: " + part);
        }
        assertEquals(243, body.size());
        assertEquals(10, magazine.size());
        assertEquals(cubes.size(), body.size() + magazine.size());
        assertTrue(body.size() + magazine.size() <= 256);
        for (int frame = 0; frame <= 20; frame++) for (String grip : GRIPS) for (String part : PARTS) {
            var child = pose(frame, part, grip);
            assertEquals(Set.of("parent", "display"), child.keySet(), "Pose changes transforms only");
            assertEquals("destiny:" + KEY + "_" + part, child.get("parent").getAsString());
            assertEquals(source.getAsJsonObject("display").keySet(), child.getAsJsonObject("display").keySet());
        }
    }

    @Test void bothEndpointsReturnExactlyToOriginalHipForBothPartsAndBothGrips() throws Exception {
        for (String grip : GRIPS) {
            var hip = json(ROOT.resolve("models/weapon/sniper_rifle/beloved" + (grip.equals("twohand") ? "_twohand" : "") + ".json"))
                    .getAsJsonObject("display");
            for (String part : PARTS) for (int frame : List.of(0, 20))
                assertEquals(hip, pose(frame, part, grip).get("display"), "Exact HIP endpoint: " + frame + "/" + part + "/" + grip);
        }
    }

    @Test void magazinePullIsRigidAlongRotatedLocalMinusYWithRemovalAndReseating() throws Exception {
        var hip = original().getAsJsonObject("display");
        double previousPull = 0;
        for (int frame = 0; frame <= 20; frame++) {
            double framePull = -1;
            for (String context : CONTEXTS) {
                var body = pose(frame, "body", "native").getAsJsonObject("display").getAsJsonObject(context);
                var mag = pose(frame, "magazine", "native").getAsJsonObject("display").getAsJsonObject(context);
                assertEquals(body.get("rotation"), mag.get("rotation"), "Magazine does not rotate independently");
                assertEquals(hip.getAsJsonObject(context).get("scale"), body.get("scale"));
                assertEquals(body.get("scale"), mag.get("scale"), "No shrink/hide deformation");
                Vector3d local = vector(mag, "translation").sub(vector(body, "translation")).div(vector(body, "scale"));
                Vector3d rotation = vector(body, "rotation").mul(Math.PI / 180);
                new Quaterniond().rotationXYZ(rotation.x, rotation.y, rotation.z).invert().transform(local);
                assertEquals(0, local.x, 3e-6, "No sideways magazine drift at " + frame + "/" + context);
                assertEquals(0, local.z, 3e-6, "No forward magazine drift at " + frame + "/" + context);
                double pull = -local.y;
                assertTrue(pull >= -3e-6 && pull <= 6.000003, "Local downward pull bounded at " + frame);
                if (framePull < 0) framePull = pull;
                else assertEquals(framePull, pull, 3e-6, "Both hand contexts use the same local pull");
                if (frame <= 3 || frame >= 15) assertEquals(0, pull, 3e-6, "Seated before removal and after replacement");
                if (frame == 10) assertTrue(pull > 5.9, "Magazine is actually pulled out mid-reload");
                if (frame == 8) assertEquals(5.055393586, pull, 3e-6, "Local pull sample at progress .4");
                if (frame == 8) {
                    Vector3d delta = vector(body, "rotation").sub(vector(hip.getAsJsonObject(context), "rotation"));
                    assertTrue(delta.x > 25 && delta.y < -14 && delta.z < -20, "Rifle pitches up and rolls left");
                    assertTrue(vector(body, "translation").x < -2, "Rifle moves left");
                }
            }
            if (frame >= 4 && frame <= 10) assertTrue(framePull >= previousPull - 3e-6, "Removal advances");
            if (frame >= 11 && frame <= 15) assertTrue(framePull <= previousPull + 3e-6, "Replacement reseats");
            previousPull = framePull;
        }
    }

    @Test void everyPoseAndPartCompensatesNativeCrossbowGripForBothHands() throws Exception {
        for (int frame = 0; frame <= 20; frame++) for (String part : PARTS) {
            var nativeDisplay = pose(frame, part, "native").getAsJsonObject("display");
            var twohand = pose(frame, part, "twohand").getAsJsonObject("display");
            for (boolean left : List.of(false, true)) {
                String context = left ? CONTEXTS.get(1) : CONTEXTS.get(0);
                float sign = left ? -1 : 1;
                var restored = new Matrix4f().translate(-.641864f * sign, 0, 0)
                        .rotateY((float) Math.toRadians(10) * sign).mul(transform(twohand.getAsJsonObject(context), left));
                assertTrue(transform(nativeDisplay.getAsJsonObject(context), left).equals(restored, 2e-6f),
                        "Native and compensated transforms agree: " + frame + "/" + part + "/" + context);
            }
            for (String context : List.of("gui", "ground", "fixed", "head"))
                assertEquals(nativeDisplay.get(context), twohand.get(context), "Unrelated display context " + context);
        }
    }

    @Test void gameplayReferencePinsOnlyReportedBelovedVideoAndReviewedWindow() throws Exception {
        var reference = json(ART.resolve("gameplay-references.json"));
        assertEquals(1, reference.getAsJsonArray("references").size());
        var beloved = reference.getAsJsonArray("references").get(0).getAsJsonObject();
        var previous = json(Path.of("art/weapons/w45-models/references.json")).getAsJsonArray("references").asList().stream()
                .map(JsonElement::getAsJsonObject).filter(v -> v.get("weapon").getAsString().equals("beloved")).findFirst().orElseThrow();
        for (String key : List.of("weapon", "url", "title", "uploader", "uploadDate", "formatId", "videoSha256", "infoSha256"))
            assertEquals(previous.get(key), beloved.get(key), "Inherited original-video provenance: " + key);
        assertEquals("https://www.youtube.com/watch?v=xEu_l7vOJBQ", beloved.get("url").getAsString());
        assertEquals("91269f9b4ff94fb7612af527643589d5a195b382a40dfd8c9d1af83e3198c7f5", beloved.get("videoSha256").getAsString());
        assertEquals(23.3, beloved.getAsJsonArray("reviewedSegmentSeconds").get(0).getAsDouble(), 0);
        assertEquals(25.3, beloved.getAsJsonArray("reviewedSegmentSeconds").get(1).getAsDouble(), 0);
        assertFalse(reference.get("exactCurrentTimingClaimed").getAsBoolean());
        assertFalse(reference.get("handIK").getAsBoolean());
        assertFalse(reference.get("exactAnimationRip").getAsBoolean());
    }

    private static Vector3d vector(JsonObject display, String key) {
        var values = display.getAsJsonArray(key);
        assertEquals(3, values.size());
        for (var value : values) assertTrue(Double.isFinite(value.getAsDouble()));
        return new Vector3d(values.get(0).getAsDouble(), values.get(1).getAsDouble(), values.get(2).getAsDouble());
    }

    /** ItemTransform order, including native left-hand reflection and translation units. */
    private static Matrix4f transform(JsonObject display, boolean left) {
        var r = vector(display, "rotation").mul(Math.PI / 180);
        var t = vector(display, "translation").div(16);
        var s = vector(display, "scale");
        float sign = left ? -1 : 1;
        return new Matrix4f().translate((float) t.x * sign, (float) t.y, (float) t.z)
                .rotateXYZ((float) r.x, (float) r.y * sign, (float) r.z * sign)
                .scale((float) s.x, (float) s.y, (float) s.z);
    }
}
