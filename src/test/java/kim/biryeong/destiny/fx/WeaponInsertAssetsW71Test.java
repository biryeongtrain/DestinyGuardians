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

/** Sampled rigid-body asset contracts; these do not establish gameplay, hand IK or a source animation rip. */
class WeaponInsertAssetsW71Test {
    private static final Path ROOT = Path.of("src/main/resources/assets/destiny");
    private static final Path ART = Path.of("art/weapons/w71/manifest.json");
    private static final String KEY = "weapon_insert_w71/long_arm";
    private static final String SOURCE = "weapon/scout_rifle/long_arm";
    private static final List<String> PHASES = List.of("initial", "loop", "return");
    private static final List<String> GRIPS = List.of("native", "twohand");
    private static final List<String> FP = List.of("firstperson_righthand", "firstperson_lefthand");
    private static final double EPS = 3e-6;
    // Captured directly from original file bytes while authoring this test, not from manifest values.
    private static final Map<String, String> ORIGINALS = Map.ofEntries(
            Map.entry("src/main/resources/assets/destiny/models/weapon/scout_rifle/long_arm.json",
                    "d166bc28532cf9461c5cb2e568f532bbceba1d3d0d0d7e43afc82408f9390ed0"),
            Map.entry("src/main/resources/assets/destiny/models/weapon/scout_rifle/long_arm_twohand.json",
                    "4878962e665c5d97e9cfa3ec4c2f9746a5112f961722b502d249149d8ea6c435"),
            Map.entry("src/main/resources/assets/destiny/models/weapon/scout_rifle/long_arm_ads.json",
                    "0b1b8d89a896157680ea6ac204579fdaff30c78c2e44c6bbe8c5fbb1b965a6bc"),
            Map.entry("src/main/resources/assets/destiny/models/weapon/scout_rifle/long_arm_ads_twohand.json",
                    "426b184d4d4631771d52647829048478cadccdb0a9084cf4b728ed233fef5067"),
            Map.entry("src/main/resources/assets/destiny/models/weapon/scout_rifle/long_arm_inspect.json",
                    "5a5838c443d600cabe8b05b20dbe08e3e3780e13e27c8e7e7fdd767ef2ba7514"),
            Map.entry("src/main/resources/assets/destiny/models/weapon/scout_rifle/long_arm_inspect_twohand.json",
                    "1816054f55bd624d34af035e48034518edc66004df85ce4fd692b53572832c2a"),
            Map.entry("src/main/resources/assets/destiny/items/weapon/long_arm.json",
                    "618586f543c4f3f14b98ebbd13baf4d4b9196621315ed940f74b4c13f0626f4b"),
            Map.entry("src/main/resources/assets/destiny/textures/item/weapon/w30/long_arm.png",
                    "451805809af885130bcda938e7e86035d0a1d0b188590699f511107bbd090a0e"),
            Map.entry("art/blockbench/weapons/w30/long_arm.bbmodel",
                    "f0af312b159d8a8a5558dcec7049789cdfea59cad25257c74657524cb01d091f"),
            Map.entry("scripts/build_weapons_w30.py",
                    "e087fca588231486505691e97b5c2b581382c1055c76d64300dbc24118bf1d83"));

    @Test void manifestAndDiskContainExactly126PoseChildrenAndOneGraphWithMatchingOutputHashes() throws Exception {
        var manifest = json(ART);
        assertEquals("W71", manifest.get("stage").getAsString());
        assertEquals("scripts/generate_insert_models_w71.py", manifest.get("generator").getAsString());
        assertEquals("long_arm", manifest.get("id").getAsString());
        assertEquals(8293111, manifest.get("bungieHash").getAsInt());
        assertEquals(PHASES, strings(manifest.getAsJsonArray("phases")));
        for (var entry : Map.of("framesPerPhase", 21, "progressFloatIndex", 4, "sourceCubes", 256,
                "compositeCubes", 256, "newGeometry", 0, "newTextures", 0, "returnTicks", 6).entrySet())
            assertEquals(entry.getValue().intValue(), manifest.get(entry.getKey()).getAsInt(), entry.getKey());
        assertTrue(manifest.get("originalsUnchanged").getAsBoolean());
        for (String flag : List.of("returnBlocksGameplay", "exactAnimationRip", "handIK", "nativeGameplayVerified"))
            assertFalse(manifest.get(flag).getAsBoolean(), flag);
        var expected = expectedAssets();
        assertEquals(127, expected.size());
        Set<Path> actual = new HashSet<>();
        for (String type : List.of("items", "models", "textures")) {
            Path directory = ROOT.resolve(type + "/weapon_insert_w71");
            if (Files.exists(directory)) try (var paths = Files.walk(directory)) {
                actual.addAll(paths.filter(Files::isRegularFile).toList());
            }
        }
        assertEquals(expected, actual, "No extra weapon, inline-geometry asset, texture or non-JSON file");
        var hashes = manifest.getAsJsonObject("outputSha256");
        assertEquals(expected, new HashSet<>(hashes.keySet().stream().map(Path::of).toList()));
        for (Path path : expected) assertEquals(hashes.get(path.toString()).getAsString(), sha(path), path.toString());
    }

    @Test void independentPinsProtectEveryOriginalLongArmModelGraphTextureBlockbenchAndGeneratorInput() throws Exception {
        assertEquals(10, ORIGINALS.size());
        for (var entry : ORIGINALS.entrySet())
            assertEquals(entry.getValue(), sha(Path.of(entry.getKey())), "Independent original pin: " + entry.getKey());
        var inputs = json(ART).getAsJsonObject("inputSha256");
        assertEquals(Set.of(ROOT.resolve("models/" + SOURCE + ".json").toString(),
                ROOT.resolve("items/weapon/long_arm.json").toString(), "scripts/build_weapons_w30.py"), inputs.keySet());
        for (var entry : inputs.entrySet())
            assertEquals(ORIGINALS.get(entry.getKey()), entry.getValue().getAsString(), entry.getKey());
        var blockbench = json(Path.of("art/blockbench/weapons/w30/long_arm.bbmodel"));
        assertEquals(256, blockbench.getAsJsonArray("elements").size());
        assertTrue(!blockbench.has("animations") || blockbench.getAsJsonArray("animations").isEmpty());
    }

    @Test void native26_3Parses126CuboidChildrenAndOneItemGraphAndRejectsBadDisplayContext() throws Exception {
        net.minecraft.SharedConstants.tryDetectVersion();
        net.minecraft.server.Bootstrap.bootStrap();
        ItemModels.bootstrap();
        ItemTintSources.bootstrap();
        net.minecraft.client.renderer.item.properties.select.SelectItemModelProperties.bootstrap();
        net.minecraft.client.renderer.item.properties.conditional.ConditionalItemModelProperties.bootstrap();
        net.minecraft.client.renderer.item.properties.numeric.RangeSelectItemModelProperties.bootstrap();
        int children = 0, graphs = 0;
        for (Path path : expectedAssets()) {
            if (path.startsWith(ROOT.resolve("items"))) {
                var graph = json(path).getAsJsonObject("model");
                var decoded = ItemModels.CODEC.parse(JsonOps.INSTANCE, graph);
                assertTrue(decoded.isSuccess(), path + ": " + decoded.error());
                var invalid = graph.deepCopy();
                invalid.getAsJsonArray("cases").get(0).getAsJsonObject().addProperty("when", "first_person_right_hand");
                assertFalse(ItemModels.CODEC.parse(JsonOps.INSTANCE, invalid).isSuccess(), "Context spelling negative control");
                graphs++;
            } else {
                assertNotNull(CuboidModel.fromStream(new StringReader(Files.readString(path))), path.toString());
                children++;
            }
        }
        assertEquals(126, children);
        assertEquals(1, graphs);
    }

    @Test void wrapperPreservesMetadataAndExactOldGraphForEveryNonFirstPersonContextAndInactiveProgress() throws Exception {
        var original = json(ROOT.resolve("items/weapon/long_arm.json"));
        var wrapper = item();
        var restored = wrapper.deepCopy();
        restored.add("model", original.get("model").deepCopy());
        assertEquals(original, restored, "All original metadata survives");
        assertFalse(wrapper.get("hand_animation_on_swap").getAsBoolean());
        var select = wrapper.getAsJsonObject("model");
        assertEquals(Set.of("type", "property", "cases", "fallback"), select.keySet());
        assertEquals("minecraft:select", select.get("type").getAsString());
        assertEquals("minecraft:display_context", select.get("property").getAsString());
        assertEquals(original.get("model"), select.get("fallback"), "Complete original ADS/inspect/HIP/grip graph");
        assertEquals(1, select.getAsJsonArray("cases").size());
        var branch = select.getAsJsonArray("cases").get(0).getAsJsonObject();
        assertEquals(Set.of("when", "model"), branch.keySet());
        assertEquals(FP, strings(branch.getAsJsonArray("when")));
        var range = range();
        assertEquals(Set.of("type", "property", "index", "entries", "fallback"), range.keySet());
        assertEquals("minecraft:range_dispatch", range.get("type").getAsString());
        assertEquals("minecraft:custom_model_data", range.get("property").getAsString());
        assertEquals(4, range.get("index").getAsInt(), "Reload float 1, bow float 2 and ADS float 3 remain independent");
        assertEquals(original.get("model"), range.get("fallback"));
        for (ItemDisplayContext context : ItemDisplayContext.values()) {
            boolean fp = FP.contains(context.getSerializedName());
            JsonElement selected = strings(branch.getAsJsonArray("when")).contains(context.getSerializedName())
                    ? branch.get("model") : select.get("fallback");
            assertEquals(fp ? range : original.get("model"), selected, context.toString());
        }
        for (float progress : new float[]{-1, -.05f, Math.nextDown(0f)})
            assertEquals(original.get("model"), dispatch(range, progress), "Inactive float 4: " + progress);
    }

    @Test void all63ThresholdsSelectDistinctNativeAndTwohandModelsUsingOnlyFloat4AndGripFlag0() throws Exception {
        var range = range();
        var entries = range.getAsJsonArray("entries");
        assertEquals(63, entries.size());
        Set<Path> referenced = new HashSet<>();
        float previous = -1;
        for (int phase = 0; phase < PHASES.size(); phase++) for (int frame = 0; frame <= 20; frame++) {
            int index = phase * 21 + frame;
            var entry = entries.get(index).getAsJsonObject();
            assertEquals(Set.of("threshold", "model"), entry.keySet());
            assertEquals(phase * 2 + frame / 20.0, entry.get("threshold").getAsDouble(), 1e-9);
            float threshold = entry.get("threshold").getAsFloat();
            assertTrue(threshold > previous);
            previous = threshold;
            var condition = entry.getAsJsonObject("model");
            assertEquals(Set.of("type", "property", "index", "on_true", "on_false"), condition.keySet());
            assertEquals("minecraft:condition", condition.get("type").getAsString());
            assertEquals("minecraft:custom_model_data", condition.get("property").getAsString());
            assertEquals(0, condition.get("index").getAsInt(), "Boolean grip flag 0, not a progress float");
            for (String grip : GRIPS) {
                var leaf = condition.getAsJsonObject(grip.equals("twohand") ? "on_true" : "on_false");
                assertEquals(Set.of("type", "model"), leaf.keySet());
                assertEquals("minecraft:model", leaf.get("type").getAsString());
                assertEquals("destiny:" + poseKey(PHASES.get(phase), frame, grip), leaf.get("model").getAsString());
                Path path = ROOT.resolve("models/" + leaf.get("model").getAsString().substring(8) + ".json");
                assertTrue(referenced.add(path), "No path alias between phase/frame/grip");
                assertTrue(Files.isRegularFile(path));
            }
            assertEquals(condition, dispatch(range, threshold), "Exact native float threshold " + index);
            assertEquals(condition, dispatch(range, Math.nextUp(threshold)), "Immediately after " + index);
            assertEquals(index == 0 ? range.get("fallback") : entries.get(index - 1).getAsJsonObject().get("model"),
                    dispatch(range, Math.nextDown(threshold)), "Immediately before " + index);
        }
        var expected = expectedAssets();
        expected.remove(ROOT.resolve("items/" + KEY + ".json"));
        assertEquals(126, referenced.size());
        assertEquals(expected, referenced, "Every generated child is reachable exactly once");
        assertEquals(entries.get(20).getAsJsonObject().get("model"), dispatch(range, 1.5f));
        assertEquals(entries.get(41).getAsJsonObject().get("model"), dispatch(range, 3.5f));
        assertEquals(entries.get(62).getAsJsonObject().get("model"), dispatch(range, 7f));
    }

    @Test void everyChildInheritsExactly256OriginalCubesAndPreservesContextsScaleAndBothHandCarrierMatrices() throws Exception {
        var source = json(ROOT.resolve("models/" + SOURCE + ".json"));
        assertEquals(256, source.getAsJsonArray("elements").size(), "Source already consumes the entire 256-cube budget");
        assertEquals(JsonParser.parseString("{\"0\":\"destiny:item/weapon/w30/long_arm\",\"particle\":\"destiny:item/weapon/w30/long_arm\"}"),
                source.get("textures"));
        var hip = source.getAsJsonObject("display");
        var twoHip = json(ROOT.resolve("models/" + SOURCE + "_twohand.json")).getAsJsonObject("display");
        for (String phase : PHASES) for (int frame = 0; frame <= 20; frame++) {
            var nativeDisplay = display(phase, frame, "native");
            var twohand = display(phase, frame, "twohand");
            for (String grip : GRIPS) {
                var child = json(ROOT.resolve("models/" + poseKey(phase, frame, grip) + ".json"));
                assertEquals(Set.of("parent", "display"), child.keySet(), "No inline cubes, textures, cartridge, hands or lever part");
                assertEquals("destiny:" + SOURCE, child.get("parent").getAsString(), "One exact unchanged geometry parent");
                var actual = child.getAsJsonObject("display");
                var base = grip.equals("native") ? hip : twoHip;
                assertEquals(base.keySet(), actual.keySet());
                for (String context : base.keySet()) {
                    var pose = actual.getAsJsonObject(context);
                    assertEquals(Set.of("rotation", "translation", "scale"), pose.keySet());
                    for (String field : List.of("rotation", "translation", "scale")) {
                        var values = vector(pose, field);
                        for (int axis = 0; axis < 3; axis++) {
                            double value = values.get(axis);
                            if (field.equals("translation")) assertTrue(Math.abs(value) <= 80, "No native translation clamp");
                            if (field.equals("scale")) assertTrue(value > 0 && value <= 4, "Positive native scale <= 4");
                        }
                    }
                    assertEquals(base.getAsJsonObject(context).get("scale"), pose.get("scale"), "Rigid, no shrinking/hiding");
                    if (!FP.contains(context)) assertEquals(base.get(context), pose, phase + "/" + frame + "/" + grip + "/" + context);
                }
            }
            for (boolean left : List.of(false, true)) {
                String context = FP.get(left ? 1 : 0);
                double sign = left ? -1 : 1;
                var restored = new Matrix4d().translate(-.641864 * sign, 0, 0).rotateY(Math.toRadians(10) * sign)
                        .mul(transform(twohand.getAsJsonObject(context), left));
                assertTrue(transform(nativeDisplay.getAsJsonObject(context), left).equals(restored, EPS),
                        "Native 26.3 carrier compensation " + phase + "/" + frame + "/" + context);
            }
            for (String field : List.of("rotation", "translation")) {
                var right = vector(nativeDisplay.getAsJsonObject(FP.get(0)), field).sub(vector(hip.getAsJsonObject(FP.get(0)), field));
                var left = vector(nativeDisplay.getAsJsonObject(FP.get(1)), field).sub(vector(hip.getAsJsonObject(FP.get(1)), field));
                assertVector(right, left, "Same body response for both hands " + phase + "/" + frame + "/" + field);
            }
        }
    }

    @Test void exactHipEndpointsAndHeldSeamsStayContinuousAcrossAllThreePhasesForBothGrips() throws Exception {
        for (String grip : GRIPS) {
            var hip = json(ROOT.resolve("models/" + SOURCE + (grip.equals("twohand") ? "_twohand" : "") + ".json"))
                    .getAsJsonObject("display");
            assertEquals(hip, display("initial", 0, grip), "Exact initial HIP " + grip);
            assertEquals(hip, display("return", 20, grip), "Exact final HIP " + grip);
            var held = display("initial", 20, grip);
            assertNotEquals(hip, held, "Insert completion remains raised");
            assertEquals(held, display("loop", 0, grip));
            assertEquals(held, display("loop", 20, grip), "Repeated cycles never reset to HIP");
            assertEquals(held, display("return", 0, grip));
        }
    }

    @Test void authoredCurveHasIndependentGoldenOffsetsAndSmoothBoundedMonotonicSegments() throws Exception {
        // Literal expected offsets: no generator invocation, KEYS import, or interpolation of manifest values.
        golden("initial", 0, 0, 0, 0, 0, 0, 0);
        golden("initial", 1, 2.074074, -.518519, -1.555556, -.103704, -.025926, -.025926);
        golden("initial", 3, 8, -2, -6, -.4, -.1, -.1);
        golden("initial", 5, 17.504, -4.464, -11.632, -.9632, -.2056, -.2056);
        golden("initial", 8, 35, -9, -22, -2, -.4, -.4);
        golden("initial", 10, 40.185185, -9.740741, -23.481481, -2.296296, -.4, -.4);
        golden("initial", 11, 42, -10, -24, -2.4, -.4, -.4);
        golden("initial", 14, 42.961734, -10.961734, -24.961734, -2.351913, -.207653, -.496173);
        golden("initial", 15, 43.18457, -10.907715, -24.723145, -2.354614, -.181543, -.481543);
        golden("initial", 17, 44.81543, -10.092285, -22.276855, -2.395386, -.018457, -.318457);
        golden("initial", 18, 44.777778, -10, -22.148148, -2.4, -.02963, -.307407);
        golden("initial", 20, 42, -10, -24, -2.4, -.4, -.4);
        golden("loop", 0, 42, -10, -24, -2.4, -.4, -.4);
        golden("loop", 1, 41.792, -9.792, -24.208, -2.3792, -.3896, -.4);
        golden("loop", 5, 40, -8, -26, -2.2, -.3, -.4);
        golden("loop", 8, 41.5, -9.5, -25.5, -2.275, -.25, -.45);
        golden("loop", 11, 43, -11, -25, -2.35, -.2, -.5);
        golden("loop", 16, 45, -10, -22, -2.4, 0, -.3);
        golden("loop", 18, 43.5, -10, -23, -2.4, -.2, -.35);
        golden("loop", 20, 42, -10, -24, -2.4, -.4, -.4);
        golden("return", 0, 42, -10, -24, -2.4, -.4, -.4);
        golden("return", 1, 41.390671, -9.833819, -23.612245, -2.361224, -.394461, -.394461);
        golden("return", 7, 31, -7, -17, -1.7, -.3, -.3);
        golden("return", 10, 22.734694, -5.425656, -12.276968, -1.227697, -.221283, -.221283);
        golden("return", 14, 10, -3, -5, -.5, -.1, -.1);
        golden("return", 17, 5, -1.5, -2.5, -.25, -.05, -.05);
        golden("return", 19, .740741, -.222222, -.37037, -.037037, -.007407, -.007407);
        golden("return", 20, 0, 0, 0, 0, 0, 0);
        // Only shape/bounds and a maximum derivative are checked from these independent authored knots.
        // This deliberately does not duplicate the generator's smoothstep evaluation as an expected-value oracle.
        var knots = Map.of(
                "initial", new double[][]{{0,0,0,0,0,0,0}, {.15,8,-2,-6,-.4,-.1,-.1}, {.4,35,-9,-22,-2,-.4,-.4},
                        {.55,42,-10,-24,-2.4,-.4,-.4}, {.72,43,-11,-25,-2.35,-.2,-.5},
                        {.88,45,-10,-22,-2.4,0,-.3}, {1,42,-10,-24,-2.4,-.4,-.4}},
                "loop", new double[][]{{0,42,-10,-24,-2.4,-.4,-.4}, {.25,40,-8,-26,-2.2,-.3,-.4},
                        {.55,43,-11,-25,-2.35,-.2,-.5}, {.8,45,-10,-22,-2.4,0,-.3}, {1,42,-10,-24,-2.4,-.4,-.4}},
                "return", new double[][]{{0,42,-10,-24,-2.4,-.4,-.4}, {.35,31,-7,-17,-1.7,-.3,-.3},
                        {.7,10,-3,-5,-.5,-.1,-.1}, {1,0,0,0,0,0,0}});
        var metadata = json(ART).getAsJsonObject("keyframes");
        assertEquals(Set.copyOf(PHASES), metadata.keySet());
        for (String phase : PHASES) {
            var curve = knots.get(phase);
            var declared = metadata.getAsJsonArray(phase);
            assertEquals(curve.length, declared.size());
            for (int i = 0; i < curve.length; i++) {
                var key = declared.get(i).getAsJsonArray();
                assertEquals(3, key.size());
                assertEquals(curve[i][0], key.get(0).getAsDouble(), 0);
                for (int axis = 0; axis < 6; axis++) assertEquals(curve[i][axis + 1],
                        key.get(axis / 3 + 1).getAsJsonArray().get(axis % 3).getAsDouble(), 0);
            }
            for (int segment = 1; segment < curve.length; segment++) {
                var a = curve[segment - 1];
                var b = curve[segment];
                double[] previous = null;
                for (int frame = 0; frame <= 20; frame++) {
                    double progress = frame / 20.0;
                    if (progress < a[0] || progress > b[0]) continue;
                    var actual = offsets(phase, frame, FP.get(0));
                    for (int axis = 0; axis < 6; axis++) {
                        double start = a[axis + 1], end = b[axis + 1], value = actual[axis];
                        String label = phase + "/" + segment + "/" + frame + "/" + axis;
                        assertTrue(value >= Math.min(start, end) - EPS && value <= Math.max(start, end) + EPS, "No overshoot " + label);
                        if (previous != null) {
                            double step = value - previous[axis];
                            assertTrue((end - start) * step >= -EPS, "Monotonic within segment " + label);
                            assertTrue(Math.abs(step) <= 1.5 * Math.abs(end - start) / (b[0] - a[0]) / 20 + EPS,
                                    "Bounded smoothstep speed " + label);
                        }
                    }
                    previous = actual;
                }
            }
        }
        for (String phase : PHASES) {
            assertTrue(rotationStep(phase, 0) < rotationStep(phase, 1), "Ease out of phase start: " + phase);
            assertTrue(rotationStep(phase, 19) < rotationStep(phase, 18), "Ease into phase end: " + phase);
        }
    }

    private static JsonObject json(Path path) throws Exception {
        return JsonParser.parseString(Files.readString(path)).getAsJsonObject();
    }
    private static JsonObject item() throws Exception { return json(ROOT.resolve("items/" + KEY + ".json")); }
    private static JsonObject range() throws Exception {
        return item().getAsJsonObject("model").getAsJsonArray("cases").get(0).getAsJsonObject().getAsJsonObject("model");
    }
    private static List<String> strings(JsonArray array) { return array.asList().stream().map(JsonElement::getAsString).toList(); }
    private static String poseKey(String phase, int frame, String grip) {
        return KEY + "_" + phase + "_" + String.format(Locale.ROOT, "%02d", frame) + "_" + grip;
    }
    private static JsonObject display(String phase, int frame, String grip) throws Exception {
        return json(ROOT.resolve("models/" + poseKey(phase, frame, grip) + ".json")).getAsJsonObject("display");
    }
    private static Set<Path> expectedAssets() {
        Set<Path> paths = new HashSet<>();
        paths.add(ROOT.resolve("items/" + KEY + ".json"));
        for (String phase : PHASES) for (int frame = 0; frame <= 20; frame++) for (String grip : GRIPS)
            paths.add(ROOT.resolve("models/" + poseKey(phase, frame, grip) + ".json"));
        return paths;
    }
    /** Native range comparisons use floats; test both adjacent representable values at every threshold. */
    private static JsonElement dispatch(JsonObject range, float progress) {
        JsonElement result = range.get("fallback");
        for (var value : range.getAsJsonArray("entries")) {
            var entry = value.getAsJsonObject();
            if (progress < entry.get("threshold").getAsFloat()) break;
            result = entry.get("model");
        }
        return result;
    }
    private static String sha(Path path) throws Exception {
        return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(path)));
    }
    private static Vector3d vector(JsonObject object, String field) {
        var array = object.getAsJsonArray(field);
        assertEquals(3, array.size());
        for (var value : array) assertTrue(Double.isFinite(value.getAsDouble()) && Float.isFinite(value.getAsFloat()), "Finite " + field);
        return new Vector3d(array.get(0).getAsDouble(), array.get(1).getAsDouble(), array.get(2).getAsDouble());
    }
    private static void assertVector(Vector3d expected, Vector3d actual, String label) {
        assertTrue(expected.equals(actual, EPS), label + ": expected " + expected + ", actual " + actual);
    }
    /** Native ItemTransform translation units, Euler order and left-hand reflection. */
    private static Matrix4d transform(JsonObject pose, boolean left) {
        var r = vector(pose, "rotation").mul(Math.PI / 180);
        var t = vector(pose, "translation").div(16);
        var s = vector(pose, "scale");
        double sign = left ? -1 : 1;
        return new Matrix4d().translate(t.x * sign, t.y, t.z).rotateXYZ(r.x, r.y * sign, r.z * sign).scale(s.x, s.y, s.z);
    }
    private static double[] offsets(String phase, int frame, String context) throws Exception {
        var hip = json(ROOT.resolve("models/" + SOURCE + ".json")).getAsJsonObject("display").getAsJsonObject(context);
        var actual = display(phase, frame, "native").getAsJsonObject(context);
        var rotation = vector(actual, "rotation").sub(vector(hip, "rotation"));
        var translation = vector(actual, "translation").sub(vector(hip, "translation"));
        return new double[]{rotation.x, rotation.y, rotation.z, translation.x, translation.y, translation.z};
    }
    private static void golden(String phase, int frame, double... expected) throws Exception {
        assertEquals(6, expected.length);
        for (String context : FP) assertArrayEquals(expected, offsets(phase, frame, context), 5.1e-7, phase + "/" + frame + "/" + context);
    }
    private static double rotationStep(String phase, int frame) throws Exception {
        var a = offsets(phase, frame, FP.get(0));
        var b = offsets(phase, frame + 1, FP.get(0));
        return new Vector3d(b[0] - a[0], b[1] - a[1], b[2] - a[2]).length();
    }
}
