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
import org.joml.Vector3d;
import org.junit.jupiter.api.Test;

import java.io.StringReader;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.HexFormat;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Set;

import static org.junit.jupiter.api.Assertions.*;

/** W50 ordinary-bow assets against native 26.3 parsers and independent source/geometry contracts. */
class WeaponBowAssetsW50Test {
    private static final Path ROOT = Path.of("src/main/resources/assets/destiny");
    private static final Path ART = Path.of("art/weapons/w50");
    private static final List<String> POSES = List.of("hip", "ads", "inspect");
    private static final List<String> HELD = List.of("firstperson_righthand", "firstperson_lefthand",
            "thirdperson_righthand", "thirdperson_lefthand");
    private static final double EPS = 3e-6; // JSON coordinates and angles are rounded to six decimals.

    private record Bow(String id, int sourceCubes, int bodyCubes, int stringIndex, List<Integer> arrowIndices,
                       int shaftIndex, double fullPull, List<List<Double>> bridges) {
        int loadedCubes() { return bodyCubes + 2 + arrowIndices.size() + bridges.size(); }
    }

    // Reviewed source indices and pull distances, deliberately independent of generated manifest/config reads.
    private static final List<Bow> BOWS = List.of(
            new Bow("biting_winds", 250, 229, 128,
                    List.of(86, 87, 88, 89, 90, 156, 157, 158, 159, 160, 161, 162, 163, 164, 165, 166, 203, 204, 220, 221),
                    161, 4.8, List.of(List.of(6.378126, 8.803671))),
            new Bow("whispering_slab", 200, 190, 114,
                    List.of(67, 68, 70, 139, 140, 141, 142, 180, 181),
                    140, 3.4, List.of(List.of(2.486954, 2.944633), List.of(3.173472, 4.775347))));

    // Computed directly from original files: editing an original AND the manifest must still fail.
    private static final Map<String, String> ORIGINALS = Map.ofEntries(
            Map.entry("src/main/resources/assets/destiny/models/weapon/bow/biting_winds.json",
                    "6e3146acd14e4e5d04332eea1b0ad2e89d9c88abf65b85fc1a894f73f05b4c6e"),
            Map.entry("src/main/resources/assets/destiny/models/weapon/bow/biting_winds_ads.json",
                    "054ee97ca4d8b1d14a0e87e820ba7fec923e9897ff436eb397b88d9abe32cfcd"),
            Map.entry("src/main/resources/assets/destiny/models/weapon/bow/biting_winds_inspect.json",
                    "b2becda5f2f0f8f2cd9b1699dafc4a49cb2f98a131d2fe817eec0b6efddbd1f7"),
            Map.entry("src/main/resources/assets/destiny/items/weapon/biting_winds.json",
                    "d7a5df22b93b89fc3232c98da5f2603897a3de99dcf23e4d6d9bd8539bf70a33"),
            Map.entry("art/blockbench/weapons/w30/biting_winds.bbmodel",
                    "657be7f10b3c91c74fe8df917c561d61a9baf65741f321ba65410b35f58e401b"),
            Map.entry("src/main/resources/assets/destiny/textures/item/weapon/w30/biting_winds.png",
                    "7d82bb7dd39dc31595b040772d11c452a3c3cf53ef807920835f2217534dfe53"),
            Map.entry("src/main/resources/assets/destiny/models/weapon/bow/whispering_slab.json",
                    "e4b262f49e49adb4266b100afb51a7f85e3a88daa1e55ec2a5421e9a7643510a"),
            Map.entry("src/main/resources/assets/destiny/models/weapon/bow/whispering_slab_ads.json",
                    "66b2f7e027bc6a556d04975a727c56dab9c46b0ecbc8b3da26f5626e60f474e1"),
            Map.entry("src/main/resources/assets/destiny/models/weapon/bow/whispering_slab_inspect.json",
                    "04a9e7861720977efcbc8d57be6a5c070c8015a81af00230da4a9a3855521634"),
            Map.entry("src/main/resources/assets/destiny/items/weapon/whispering_slab.json",
                    "32115e96a8ae4d2262d63f9a49822bd01e15b25401cf162afc6fd6d9bb8daed6"),
            Map.entry("art/blockbench/weapons/w30/whispering_slab.bbmodel",
                    "6cb11fd553442618830c2cdde147209ba74c02352f5c9374e5b872e27faa43e9"),
            Map.entry("src/main/resources/assets/destiny/textures/item/weapon/w30/whispering_slab.png",
                    "e3ba1a407db10380a8b2abc72ee33af9288df956fca4f027177ad9aa04115c03"));

    private static JsonObject json(Path path) throws Exception {
        return JsonParser.parseString(Files.readString(path)).getAsJsonObject();
    }

    private static JsonObject original(Bow bow) throws Exception {
        return json(ROOT.resolve("models/weapon/bow/" + bow.id() + ".json"));
    }

    private static JsonObject originalItem(Bow bow) throws Exception {
        return json(ROOT.resolve("items/weapon/" + bow.id() + ".json"));
    }

    private static JsonObject item(Bow bow) throws Exception {
        return json(ROOT.resolve("items/weapon_bow_w50/" + bow.id() + ".json"));
    }

    private static String key(Bow bow, String part, String pose) {
        return "weapon_bow_w50/" + bow.id() + "_" + part + "_" + pose;
    }

    private static JsonObject model(Bow bow, String part, String pose) throws Exception {
        return json(ROOT.resolve("models/" + key(bow, part, pose) + ".json"));
    }

    private static String frame(String stage, int frame) {
        return stage + "_" + String.format(Locale.ROOT, "%02d", frame);
    }

    private static List<String> states() {
        List<String> states = new ArrayList<>(List.of("empty", "loaded"));
        for (String stage : List.of("draw", "nock"))
            for (int i = 0; i <= 20; i++) states.add(frame(stage, i));
        return states;
    }

    private static List<String> parts() {
        List<String> parts = new ArrayList<>(List.of("body"));
        parts.addAll(states());
        return parts;
    }

    private static Set<String> expectedAssets() {
        Set<String> paths = new HashSet<>();
        for (Bow bow : BOWS) {
            paths.add(ROOT.resolve("items/weapon_bow_w50/" + bow.id() + ".json").toString());
            for (String part : parts()) for (String pose : POSES)
                paths.add(ROOT.resolve("models/" + key(bow, part, pose) + ".json").toString());
        }
        return paths;
    }

    private static String sha256(Path path) throws Exception {
        return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(path)));
    }

    @Test void all272AssetsHaveAnExactManifestAndDiskInventoryWithMatchingSha256() throws Exception {
        var manifest = json(ART.resolve("manifest.json"));
        assertEquals("scripts/generate_bow_models_w50.py", manifest.get("generator").getAsString());
        assertEquals(20, manifest.get("steps").getAsInt());
        assertEquals(2, manifest.get("selectorFloatIndex").getAsInt());
        assertEquals(HELD, strings(manifest.getAsJsonArray("heldContexts")));
        assertTrue(manifest.get("originalsUnchanged").getAsBoolean());
        var hashes = manifest.getAsJsonObject("sha256");
        assertEquals(272, expectedAssets().size());
        assertEquals(272, hashes.size());
        assertEquals(expectedAssets(), hashes.keySet(), "Independent complete inventory, including all pose children");
        Set<String> disk = new HashSet<>();
        for (String type : List.of("items", "models")) {
            try (var files = Files.walk(ROOT.resolve(type + "/weapon_bow_w50"))) {
                disk.addAll(files.filter(Files::isRegularFile).map(Path::toString).toList());
            }
        }
        assertEquals(expectedAssets(), disk, "Missing and unlisted sidecar files must fail");
        for (var entry : hashes.entrySet())
            assertEquals(entry.getValue().getAsString(), sha256(Path.of(entry.getKey())), entry.getKey());
        var bows = manifest.getAsJsonObject("bows");
        assertEquals(Set.of("biting_winds", "whispering_slab"), bows.keySet());
        for (Bow bow : BOWS) {
            var info = bows.getAsJsonObject(bow.id());
            assertEquals(bow.sourceCubes(), info.get("sourceCubes").getAsInt());
            assertEquals(bow.bodyCubes(), info.get("bodyCubes").getAsInt());
            assertEquals(bow.loadedCubes(), info.get("maxCubes").getAsInt());
            assertEquals(bow.stringIndex(), info.get("stringIndex").getAsInt());
            assertEquals(bow.arrowIndices(), info.getAsJsonArray("arrowIndices").asList().stream().map(JsonElement::getAsInt).toList());
            assertEquals(bow.shaftIndex(), info.get("shaftIndex").getAsInt());
            assertEquals(bow.fullPull(), info.get("authoredFullDrawPull").getAsDouble(), 0);
            assertEquals(JsonParser.parseString(bow.bridges().toString()), info.get("shaftBridges"));
            var entries = info.getAsJsonArray("states");
            assertEquals(44, entries.size());
            for (int i = 0; i < states().size(); i++) {
                assertEquals(states().get(i), entries.get(i).getAsJsonObject().get("name").getAsString());
                assertEquals(selector(i), entries.get(i).getAsJsonObject().get("selector").getAsInt());
            }
        }
    }

    @Test void all12OriginalModelsWrappersDisplaysBlockbenchAndPngFilesMatchIndependentPins() throws Exception {
        var hashes = json(ART.resolve("manifest.json")).getAsJsonObject("sourceSha256");
        assertEquals(12, ORIGINALS.size());
        assertEquals(ORIGINALS.keySet(), hashes.keySet());
        for (var entry : ORIGINALS.entrySet()) {
            assertEquals(entry.getValue(), sha256(Path.of(entry.getKey())), "Original bytes: " + entry.getKey());
            assertEquals(entry.getValue(), hashes.get(entry.getKey()).getAsString(), "Independent pin: " + entry.getKey());
        }
    }

    @Test void native26_3ItemCodecAcceptsBothWrappersAndCuboidParserAcceptsAll270Models() throws Exception {
        net.minecraft.SharedConstants.tryDetectVersion();
        net.minecraft.server.Bootstrap.bootStrap();
        ItemModels.bootstrap();
        ItemTintSources.bootstrap();
        net.minecraft.client.renderer.item.properties.select.SelectItemModelProperties.bootstrap();
        net.minecraft.client.renderer.item.properties.conditional.ConditionalItemModelProperties.bootstrap();
        net.minecraft.client.renderer.item.properties.numeric.RangeSelectItemModelProperties.bootstrap();
        for (Bow bow : BOWS) {
            var wrapper = item(bow).getAsJsonObject("model");
            var decoded = ItemModels.CODEC.parse(JsonOps.INSTANCE, wrapper);
            assertTrue(decoded.isSuccess(), bow.id() + ": 26.3 ItemModels.CODEC: " + decoded.error());
            var invalid = wrapper.deepCopy();
            invalid.getAsJsonArray("cases").get(0).getAsJsonObject().addProperty("when", "first_person_right_hand");
            assertFalse(ItemModels.CODEC.parse(JsonOps.INSTANCE, invalid).isSuccess(), "Reject invalid native context spelling");
        }
        int parsed = 0;
        for (String path : expectedAssets()) if (path.contains("/models/")) {
            assertNotNull(CuboidModel.fromStream(new StringReader(Files.readString(Path.of(path)))), path);
            parsed++;
        }
        assertEquals(270, parsed);
    }

    @Test void wrappersPreserveMetadataAndExactOriginalFallbackOutsideOnlyFourHeldContexts() throws Exception {
        for (Bow bow : BOWS) {
            var source = originalItem(bow);
            var wrapper = item(bow);
            var restored = wrapper.deepCopy();
            restored.add("model", source.get("model").deepCopy());
            assertEquals(source, restored, "Preserve hand_animation_on_swap and every original wrapper field");
            var select = wrapper.getAsJsonObject("model");
            assertEquals(Set.of("type", "property", "cases", "fallback"), select.keySet());
            assertEquals("minecraft:select", select.get("type").getAsString());
            assertEquals("minecraft:display_context", select.get("property").getAsString());
            assertEquals(source.get("model"), select.get("fallback"), "Default retains the full original pose/grip tree");
            assertEquals(1, select.getAsJsonArray("cases").size());
            var branch = select.getAsJsonArray("cases").get(0).getAsJsonObject();
            assertEquals(Set.of("when", "model"), branch.keySet());
            assertEquals(HELD, strings(branch.getAsJsonArray("when")));
            for (ItemDisplayContext context : ItemDisplayContext.values()) {
                var selected = HELD.contains(context.getSerializedName()) ? branch.get("model") : select.get("fallback");
                if (!HELD.contains(context.getSerializedName()))
                    assertEquals(source.get("model"), selected, bow.id() + "/" + context);
            }
            for (String context : List.of("gui", "ground", "head", "fixed")) {
                assertFalse(strings(branch.getAsJsonArray("when")).contains(context));
                assertEquals(source.get("model"), select.get("fallback"), "Exact original in " + context);
            }
        }
    }

    @Test void hipAdsInspectRouteAll44OrderedStatesToExactlyOneBodyAndOneMovingModel() throws Exception {
        for (Bow bow : BOWS) {
            var poseSelect = item(bow).getAsJsonObject("model").getAsJsonArray("cases").get(0)
                    .getAsJsonObject().getAsJsonObject("model");
            assertEquals(Set.of("type", "property", "index", "cases", "fallback"), poseSelect.keySet());
            assertEquals("minecraft:select", poseSelect.get("type").getAsString());
            assertEquals("minecraft:custom_model_data", poseSelect.get("property").getAsString());
            assertEquals(0, poseSelect.get("index").getAsInt(), "Pose remains custom model data string slot 0");
            var cases = poseSelect.getAsJsonArray("cases");
            assertEquals(List.of("ads", "inspect"), cases.asList().stream()
                    .map(v -> v.getAsJsonObject().get("when").getAsString()).toList());
            Set<String> movingRefs = new HashSet<>();
            for (String pose : POSES) {
                var range = pose.equals("hip") ? poseSelect.getAsJsonObject("fallback")
                        : cases.get(POSES.indexOf(pose) - 1).getAsJsonObject().getAsJsonObject("model");
                assertEquals(Set.of("type", "property", "index", "fallback", "entries"), range.keySet());
                assertEquals("minecraft:range_dispatch", range.get("type").getAsString());
                assertEquals("minecraft:custom_model_data", range.get("property").getAsString());
                assertEquals(2, range.get("index").getAsInt(), "Server selector uses float slot 2");
                assertEquals(originalItem(bow).get("model"), range.get("fallback"), "Below-range keeps exact original");
                var entries = range.getAsJsonArray("entries");
                assertEquals(44, entries.size());
                for (int i = 0; i < states().size(); i++) {
                    var entry = entries.get(i).getAsJsonObject();
                    assertEquals(Set.of("threshold", "model"), entry.keySet());
                    assertEquals(selector(i), entry.get("threshold").getAsDouble(), 0, "Ordered discrete selector");
                    var composite = entry.getAsJsonObject("model");
                    assertEquals(Set.of("type", "models"), composite.keySet());
                    assertEquals("minecraft:composite", composite.get("type").getAsString());
                    var models = composite.getAsJsonArray("models");
                    assertEquals(2, models.size());
                    assertModelRef(models.get(0).getAsJsonObject(), key(bow, "body", pose));
                    String moving = key(bow, states().get(i), pose);
                    assertModelRef(models.get(1).getAsJsonObject(), moving);
                    assertTrue(movingRefs.add(moving), "Every state has its own model reference: " + moving);
                }
            }
            assertEquals(132, movingRefs.size());
        }
    }

    @Test void everyPartAndFramePreservesExactOriginalHipAdsInspectDisplays() throws Exception {
        for (Bow bow : BOWS) for (String pose : POSES) {
            var expected = original(bow).getAsJsonObject("display").deepCopy();
            if (!pose.equals("hip")) {
                var variant = json(ROOT.resolve("models/weapon/bow/" + bow.id() + "_" + pose + ".json"));
                for (var entry : variant.getAsJsonObject("display").entrySet())
                    expected.add(entry.getKey(), entry.getValue().deepCopy());
            }
            for (String part : parts()) {
                var actual = model(bow, part, pose);
                assertEquals(expected, actual.get("display"), bow.id() + "/" + part + "/" + pose);
                if (!pose.equals("hip")) {
                    assertEquals(Set.of("parent", "display"), actual.keySet(), "Display-only child inherits exact HIP geometry");
                    assertEquals("destiny:" + key(bow, part, "hip"), actual.get("parent").getAsString());
                }
                for (String context : List.of("gui", "ground", "head", "fixed"))
                    assertEquals(original(bow).getAsJsonObject("display").get(context),
                            actual.getAsJsonObject("display").get(context), "Unchanged non-held display: " + context);
            }
        }
    }

    @Test void bodyContainsEveryNonStringNonArrowSourceCubeExactlyOnceWithUnchangedUvsAndMetadata() throws Exception {
        for (Bow bow : BOWS) {
            var source = original(bow);
            var cubes = source.getAsJsonArray("elements");
            assertEquals(bow.sourceCubes(), cubes.size());
            assertEquals(bow.arrowIndices().size(), new HashSet<>(bow.arrowIndices()).size());
            assertFalse(bow.arrowIndices().contains(bow.stringIndex()));
            JsonArray body = new JsonArray();
            for (int i = 0; i < cubes.size(); i++)
                if (i != bow.stringIndex() && !bow.arrowIndices().contains(i)) body.add(cubes.get(i).deepCopy());
            assertEquals(bow.bodyCubes(), body.size());
            var expected = source.deepCopy();
            expected.add("elements", body);
            assertEquals(expected, model(bow, "body", "hip"),
                    "Exact order, coordinates, faces, UVs, rotations, textures and source metadata: " + bow.id());
            assertEquals(cubes.size(), body.size() + 1 + bow.arrowIndices().size(), "Exhaustive source partition");
        }
    }

    @Test void emptyLoadedAndEveryDrawAndNockFrameStayWithin256CombinedCubesInEveryPose() throws Exception {
        for (Bow bow : BOWS) {
            int maximum = 0;
            var metadata = without(original(bow), "elements", "display");
            for (String state : states()) {
                boolean hasArrow = !state.equals("empty")
                        && !(state.startsWith("nock_") && Integer.parseInt(state.substring(5)) < 6);
                int expectedMoving = 2 + (hasArrow ? bow.arrowIndices().size() + bow.bridges().size() : 0);
                assertEquals(metadata, without(model(bow, state, "hip"), "elements", "display"));
                for (String pose : POSES) {
                    // The display-only child/parent contract is checked independently above.
                    var body = geometry(bow, "body", pose);
                    var moving = geometry(bow, state, pose);
                    assertEquals(bow.bodyCubes(), body.size());
                    assertEquals(expectedMoving, moving.size(), bow.id() + "/" + state + "/" + pose);
                    int combined = body.size() + moving.size();
                    assertTrue(combined <= 256, "Combined body + moving budget: " + bow.id() + "/" + state + "/" + pose);
                    maximum = Math.max(maximum, combined);
                }
            }
            assertEquals(bow.id().equals("biting_winds") ? 252 : 203, maximum, "Independent total, including bridges");
        }
    }

    @Test void bothStringCenterlinesStayOnOriginalTipsAndMeetAtArrowHeightThroughFullPull() throws Exception {
        for (Bow bow : BOWS) {
            var source = original(bow).getAsJsonArray("elements");
            var string = source.get(bow.stringIndex()).getAsJsonObject();
            var lo = vector(string, "from");
            var hi = vector(string, "to");
            var shaft = source.get(bow.shaftIndex()).getAsJsonObject();
            double arrowY = (vector(shaft, "from").y + vector(shaft, "to").y) / 2;
            double x = (lo.x + hi.x) / 2, z = (lo.z + hi.z) / 2;
            assertTrue(arrowY > lo.y && arrowY < hi.y);
            for (String state : states()) {
                double pull = state.startsWith("draw_") ? bow.fullPull() * Integer.parseInt(state.substring(5)) / 20 : 0;
                var moving = model(bow, state, "hip").getAsJsonArray("elements");
                var lower = moving.get(0).getAsJsonObject();
                var upper = moving.get(1).getAsJsonObject();
                String label = bow.id() + "/" + state;
                assertVector(new Vector3d(x, lo.y, z), centerlineEndpoint(lower, false), label + " lower tip");
                assertVector(new Vector3d(x, hi.y, z), centerlineEndpoint(upper, true), label + " upper tip");
                var joint = new Vector3d(x, arrowY, z + pull);
                assertVector(joint, centerlineEndpoint(lower, true), label + " lower nock endpoint");
                assertVector(joint, centerlineEndpoint(upper, false), label + " upper nock endpoint");
                assertVector(centerlineEndpoint(lower, true), centerlineEndpoint(upper, false), label + " connected centerlines");
                for (var segment : List.of(lower, upper)) {
                    var size = vector(segment, "to").sub(vector(segment, "from"));
                    assertEquals(hi.x - lo.x, size.x, EPS, "Original string width");
                    assertEquals(hi.z - lo.z, size.z, EPS, "Original string depth");
                    assertTrue(size.y > 0);
                    assertEquals(without(string, "from", "to", "faces", "rotation"),
                            without(segment, "from", "to", "faces", "rotation"));
                }
            }
        }
    }

    @Test void stringSidesUseTheirRespectiveOriginalUvIntervalsWithAContinuousSplitAndUnchangedCaps() throws Exception {
        for (Bow bow : BOWS) {
            var source = original(bow).getAsJsonArray("elements");
            var string = source.get(bow.stringIndex()).getAsJsonObject();
            var shaft = source.get(bow.shaftIndex()).getAsJsonObject();
            double arrowY = (vector(shaft, "from").y + vector(shaft, "to").y) / 2;
            double fraction = (arrowY - vector(string, "from").y) / (vector(string, "to").y - vector(string, "from").y);
            var faces = string.getAsJsonObject("faces");
            for (String state : states()) {
                var moving = model(bow, state, "hip").getAsJsonArray("elements");
                for (int half = 0; half < 2; half++) {
                    var actual = moving.get(half).getAsJsonObject().getAsJsonObject("faces");
                    assertEquals(faces.keySet(), actual.keySet());
                    for (String face : List.of("north", "south", "west", "east")) {
                        var expectedFace = faces.getAsJsonObject(face);
                        var actualFace = actual.getAsJsonObject(face);
                        assertEquals(without(expectedFace, "uv"), without(actualFace, "uv"), "Face metadata/texture");
                        var uv = expectedFace.getAsJsonArray("uv");
                        var actualUv = actualFace.getAsJsonArray("uv");
                        assertEquals(4, actualUv.size());
                        assertEquals(uv.get(0), actualUv.get(0));
                        assertEquals(uv.get(2), actualUv.get(2));
                        double v0 = uv.get(1).getAsDouble(), v1 = uv.get(3).getAsDouble();
                        double split = v0 + (v1 - v0) * fraction;
                        assertEquals(half == 0 ? v0 : split, actualUv.get(1).getAsDouble(), 6e-7);
                        assertEquals(half == 0 ? split : v1, actualUv.get(3).getAsDouble(), 6e-7);
                        if (half == 0) assertEquals(actualUv.get(3), moving.get(1).getAsJsonObject()
                                .getAsJsonObject("faces").getAsJsonObject(face).getAsJsonArray("uv").get(1), "Continuous UV seam");
                    }
                    for (String face : List.of("up", "down")) assertEquals(faces.get(face), actual.get(face), "Original cap UVs");
                }
            }
        }
    }

    @Test void everyOriginalArrowCubeMovesRigidlyThroughDrawWithUnchangedFacesUvsAndOnlyPinnedShaftBridges() throws Exception {
        for (Bow bow : BOWS) {
            var source = original(bow).getAsJsonArray("elements");
            var loaded = model(bow, "loaded", "hip").getAsJsonArray("elements");
            assertRigidArrow(bow, source, loaded, new Vector3d(), bow.id() + "/loaded");
            assertEquals(loaded, model(bow, "draw_00", "hip").get("elements"), "Draw starts at loaded");
            for (int i = 0; i <= 20; i++) {
                var moving = model(bow, frame("draw", i), "hip").getAsJsonArray("elements");
                assertRigidArrow(bow, source, moving, new Vector3d(0, 0, bow.fullPull() * i / 20), bow.id() + "/draw/" + i);
            }
        }
    }

    @Test void emptyHasNoArrowAndNockHidesItBeforePointThreeThenRigidlyReturnsToLoaded() throws Exception {
        for (Bow bow : BOWS) {
            var source = original(bow).getAsJsonArray("elements");
            var empty = model(bow, "empty", "hip").getAsJsonArray("elements");
            var loaded = model(bow, "loaded", "hip").getAsJsonArray("elements");
            assertEquals(2, empty.size(), "Only two string halves; no arrow or bridges");
            assertEquals(empty.get(0), loaded.get(0));
            assertEquals(empty.get(1), loaded.get(1));
            Vector3d previous = new Vector3d(.8, -5, 1.5);
            for (int i = 0; i <= 20; i++) {
                var moving = model(bow, frame("nock", i), "hip").getAsJsonArray("elements");
                String label = bow.id() + "/nock/" + i;
                if (i < 6) {
                    assertEquals(empty, moving, label + " progress < .3 has no arrow");
                    continue;
                }
                var firstSource = source.get(bow.arrowIndices().getFirst()).getAsJsonObject();
                var offset = vector(moving.get(2).getAsJsonObject(), "from").sub(vector(firstSource, "from"));
                assertRigidArrow(bow, source, moving, offset, label);
                assertEquals(empty.get(0), moving.get(0), "Nocking does not draw lower string");
                assertEquals(empty.get(1), moving.get(1), "Nocking does not draw upper string");
                assertTrue(offset.x >= -EPS && offset.x <= previous.x + EPS, label + " lateral approach");
                assertTrue(offset.y <= EPS && offset.y >= previous.y - EPS, label + " upward approach");
                assertTrue(offset.z >= -EPS && offset.z <= previous.z + EPS, label + " forward approach");
                // Independent authored landmarks; do not import/reimplement the generator's easing function.
                if (i == 6) assertVector(new Vector3d(.8, -5, 1.5), offset, label + " arrow entry");
                if (i == 11) assertVector(new Vector3d(.4, -2.5, .75), offset, label + " approach midpoint");
                if (i >= 16) assertEquals(loaded, moving, label + " exact loaded endpoint from .8 onward");
                previous = offset;
            }
            assertEquals(loaded, model(bow, "nock_20", "hip").get("elements"));
        }
    }

    private static int selector(int stateIndex) {
        // 0 empty, 1 loaded, 2..22 draw; the reserved gap 23..31 is not another stage.
        return stateIndex < 23 ? stateIndex : stateIndex + 9;
    }

    private static List<String> strings(JsonArray array) {
        return array.asList().stream().map(JsonElement::getAsString).toList();
    }

    private static void assertModelRef(JsonObject model, String key) {
        assertEquals(Set.of("type", "model"), model.keySet());
        assertEquals("minecraft:model", model.get("type").getAsString());
        assertEquals("destiny:" + key, model.get("model").getAsString());
    }

    private static JsonObject without(JsonObject value, String... keys) {
        var copy = value.deepCopy();
        for (String key : keys) copy.remove(key);
        return copy;
    }

    private static JsonArray geometry(Bow bow, String part, String pose) throws Exception {
        var value = model(bow, part, pose);
        if (!pose.equals("hip")) {
            assertEquals("destiny:" + key(bow, part, "hip"), value.get("parent").getAsString());
            value = model(bow, part, "hip");
        }
        return value.getAsJsonArray("elements");
    }

    private static Vector3d vector(JsonObject object, String key) {
        var values = object.getAsJsonArray(key);
        assertEquals(3, values.size());
        for (var value : values) assertTrue(Double.isFinite(value.getAsDouble()));
        return new Vector3d(values.get(0).getAsDouble(), values.get(1).getAsDouble(), values.get(2).getAsDouble());
    }

    private static void assertVector(Vector3d expected, Vector3d actual, String label) {
        assertEquals(expected.x, actual.x, EPS, label + " X");
        assertEquals(expected.y, actual.y, EPS, label + " Y");
        assertEquals(expected.z, actual.z, EPS, label + " Z");
    }

    /** Apply the stored cuboid rotation to the two local centerline endpoints, independently of generation. */
    private static Vector3d centerlineEndpoint(JsonObject cube, boolean end) {
        var from = vector(cube, "from");
        var to = vector(cube, "to");
        var rotation = cube.getAsJsonObject("rotation");
        assertEquals(Set.of("origin", "axis", "angle", "rescale"), rotation.keySet());
        assertEquals("x", rotation.get("axis").getAsString());
        assertFalse(rotation.get("rescale").getAsBoolean());
        double angle = rotation.get("angle").getAsDouble();
        assertTrue(Double.isFinite(angle));
        var pivot = vector(rotation, "origin");
        return new Vector3d((from.x + to.x) / 2, end ? to.y : from.y, (from.z + to.z) / 2)
                .sub(pivot).rotateX(Math.toRadians(angle)).add(pivot);
    }

    private static void assertRigidArrow(Bow bow, JsonArray source, JsonArray moving, Vector3d offset, String label) {
        assertEquals(2 + bow.arrowIndices().size() + bow.bridges().size(), moving.size(), label + " no extra arrow cubes");
        for (int i = 0; i < bow.arrowIndices().size(); i++)
            assertTranslatedCube(source.get(bow.arrowIndices().get(i)).getAsJsonObject(),
                    moving.get(2 + i).getAsJsonObject(), offset, label + "/source/" + bow.arrowIndices().get(i));
        for (int i = 0; i < bow.bridges().size(); i++) {
            var shaft = source.get(bow.shaftIndex()).getAsJsonObject().deepCopy();
            shaft.getAsJsonArray("from").set(2, new com.google.gson.JsonPrimitive(bow.bridges().get(i).get(0)));
            shaft.getAsJsonArray("to").set(2, new com.google.gson.JsonPrimitive(bow.bridges().get(i).get(1)));
            assertTranslatedCube(shaft, moving.get(2 + bow.arrowIndices().size() + i).getAsJsonObject(), offset, label + "/bridge/" + i);
        }
    }

    private static void assertTranslatedCube(JsonObject source, JsonObject actual, Vector3d offset, String label) {
        assertEquals(without(source, "from", "to"), without(actual, "from", "to"), label + " exact faces/UVs/rotation/metadata");
        assertVector(vector(source, "from").add(offset), vector(actual, "from"), label + " from");
        assertVector(vector(source, "to").add(offset), vector(actual, "to"), label + " to");
        assertVector(vector(source, "to").sub(vector(source, "from")),
                vector(actual, "to").sub(vector(actual, "from")), label + " rigid dimensions");
    }
}
