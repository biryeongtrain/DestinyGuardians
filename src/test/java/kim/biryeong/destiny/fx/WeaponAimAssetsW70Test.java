package kim.biryeong.destiny.fx;

import com.google.gson.*;
import kim.biryeong.destiny.weapon.WeaponCatalogTest;
import com.mojang.serialization.JsonOps;
import net.minecraft.client.color.item.ItemTintSources;
import net.minecraft.client.renderer.item.ItemModels;
import net.minecraft.client.resources.model.cuboid.CuboidModel;
import org.joml.Matrix4d;
import org.joml.Vector3d;
import org.junit.jupiter.api.Test;

import java.io.StringReader;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.*;

import static org.junit.jupiter.api.Assertions.*;
import static kim.biryeong.destiny.weapon.RenderContractsW163Support.*;

/** Static sampled-pose contracts, not render-frame interpolation, live routing, gameplay or hand IK. */
class WeaponAimAssetsW70Test {
    private static final Path ROOT = Path.of("src/main/resources/assets/destiny");
    private static final Path ART = Path.of("art/weapons/w70/manifest.json");
    private static final String KEY = "weapon_aim_w70/";
    private static final List<String> FP = List.of("firstperson_righthand", "firstperson_lefthand");
    private static final Set<String> LFR = Set.of("line_in_the_sand", "stormchaser");
    private static final Set<String> SNIPERS = Set.of("bite_of_the_fox", "beloved", "apostate");
    private static final Set<String> BOWS = Set.of("biting_winds", "whispering_slab");
    private static final double EPS = 3e-6;
    // SHA-256 of sorted UTF-8 path + NUL + current file SHA-256 + LF, captured directly
    // from original bytes before writing this test; neither constant comes from a manifest hash.
    private static final String INPUT_PIN = "ebca33b54ceee244c8402bf0641edf776b70a22deeb07de0d4d67d22662a7f25";
    private static final String ORIGINAL_ASSET_PIN = "af743a9f3aeb8c307e38c615d61fc6b0982991f393013beba03484bd5c47480e";

    @Test void catalogManifestAndActualInventoryContainExactly57Ranged59GraphsAnd4427Assets() throws Exception {
        var manifest = json(ART);
        assertEquals("W70", manifest.get("stage").getAsString());
        assertEquals("scripts/generate_aim_models_w70.py", manifest.get("generator").getAsString());
        assertEquals(21, manifest.get("frames").getAsInt());
        assertEquals(3, manifest.get("progressFloatIndex").getAsInt());
        for (String flag : List.of("newGeometry", "newTextures")) assertEquals(0, manifest.get(flag).getAsInt());
        assertTrue(manifest.get("originalsUnchanged").getAsBoolean());
        for (String flag : List.of("nativeGameplayVerified", "handIK")) assertFalse(manifest.get(flag).getAsBoolean());
        assertEquals("Linear Euler/translation/scale endpoints at20TPS sampled progress; not render-frame interpolation.",
                manifest.get("interpolation").getAsString());
        Map<String, String> catalog = new HashMap<>(), rows = new HashMap<>();
        for (var v : JsonParser.parseString(Files.readString(Path.of("art/weapons/w30/catalog.json"))).getAsJsonArray()) {
            var e = v.getAsJsonObject(); String family = e.get("family").getAsString();
            if (!Set.of("sword", "glaive").contains(family))
                assertNull(catalog.put(e.get("id").getAsString(), family));
        }
        for (var e : weapons()) {
            String id = id(e);
            assertNull(rows.put(id, e.get("family").getAsString()));
            assertEquals(21, e.get("frames").getAsInt());
            assertEquals(List.of("native", "twohand"), strings(e.getAsJsonArray("grips")));
            assertEquals(BOWS.contains(id) ? 44 : 0, e.get("bowStates").getAsInt());
            assertEquals(LFR.contains(id), e.get("scope").getAsBoolean());
            assertEquals(SNIPERS.contains(id), e.get("opaqueScope").getAsBoolean());
            assertEquals(LFR.contains(id) ? "W45 scope display" : "original W30 ADS display", e.get("endpoint").getAsString());
        }
        assertEquals(57, catalog.size()); assertEquals(catalog, rows);
        var expected = expectedAssets(); var actual = new HashSet<Path>();
        // The W70 manifest/pins describe only the exact original W30 selection.
        var originalIds = WeaponCatalogTest.originalW30Entries().stream().map(e -> e.id()).toList();
        for (String type : List.of("items", "models")) actual.addAll(files(ROOT.resolve(type + "/weapon_aim_w70")).stream()
                .filter(p -> originalIds.stream().anyMatch(id -> p.getFileName().toString().equals(id + ".json")
                        || p.getFileName().toString().startsWith(id + "_"))).toList());
        assertEquals(4427, expected.size()); assertEquals(expected, actual, "No extra files of any extension");
        var hashes = manifest.getAsJsonObject("outputSha256");
        assertEquals(expected, new HashSet<>(hashes.keySet().stream().map(Path::of).toList()));
        Set<Path> referenced = new HashSet<>(); int graphs = 0;
        for (Path path : actual) {
            assertEquals(hashes.get(path.toString()).getAsString(), historicalSha(path), path.toString());
            if (path.startsWith(ROOT.resolve("items"))) { graphs++; references(json(path), referenced); }
            else assertEquals(Set.of("parent", "display"), json(path).keySet(), path.toString());
        }
        assertEquals(59, graphs);
        for (Path path : referenced) assertTrue(Files.isRegularFile(path), "Unresolved reference " + path);
        referenced.removeIf(p -> !p.startsWith(ROOT.resolve("models/weapon_aim_w70")));
        actual.removeIf(p -> !p.startsWith(ROOT.resolve("models")));
        assertEquals(actual, referenced, "Every generated child is referenced; no extraneous model references");
    }

    @Test void independentPinsProtectAll362InputsAnd858OriginalModelsGraphsTexturesAndBlockbenchFiles() throws Exception {
        var inputs = json(ART).getAsJsonObject("inputSha256");
        assertEquals(362, inputs.size());
        assertEquals(INPUT_PIN, pin(inputs.keySet().stream().map(Path::of).toList()));
        for (var e : inputs.entrySet()) assertEquals(e.getValue().getAsString(), historicalSha(Path.of(e.getKey())), e.getKey());
        List<Path> originals = new ArrayList<>();
        for (var e : WeaponCatalogTest.originalW30Entries()) {
            originals.add(ROOT.resolve("items/weapon/" + e.id() + ".json"));
            for (String suffix : List.of("", "_ads", "_inspect", "_twohand", "_ads_twohand", "_inspect_twohand"))
                originals.add(ROOT.resolve("models/weapon/" + e.family() + "/" + e.id() + suffix + ".json"));
            originals.add(ROOT.resolve("textures/item/weapon/w30/" + e.id() + ".png"));
            originals.add(Path.of("art/blockbench/weapons/w30/" + e.id() + ".bbmodel"));
        }
        // W70 pins the eleven original W45 assets. W162's separately reviewed Izanagi
        // wrapper is an additive exotic, outside the original W30/W70 inventory.
        var scopePaths = json(Path.of("art/weapons/w45-models/manifest.json")).getAsJsonObject("sha256");
        assertEquals(11, scopePaths.size());
        originals.addAll(scopePaths.keySet().stream().map(Path::of).toList());
        for (String root : List.of("models/weapon_bow_w50", "items/weapon_bow_w50")) originals.addAll(files(ROOT.resolve(root)));
        originals.addAll(files(ROOT.resolve("textures/item/hud")).stream()
                .filter(p -> p.getFileName().toString().startsWith("scope_w45")).toList());
        assertEquals(858, originals.size()); assertEquals(ORIGINAL_ASSET_PIN, pin(originals));
    }

    @Test void native26_3ItemModelsCodecAccepts59WrappersAndCuboidParserAccepts4368Children() throws Exception {
        net.minecraft.SharedConstants.tryDetectVersion(); net.minecraft.server.Bootstrap.bootStrap();
        ItemModels.bootstrap(); ItemTintSources.bootstrap();
        net.minecraft.client.renderer.item.properties.select.SelectItemModelProperties.bootstrap();
        net.minecraft.client.renderer.item.properties.conditional.ConditionalItemModelProperties.bootstrap();
        net.minecraft.client.renderer.item.properties.numeric.RangeSelectItemModelProperties.bootstrap();
        int graphs = 0, children = 0;
        for (Path path : expectedAssets()) {
            if (path.startsWith(ROOT.resolve("items"))) {
                var graph = json(path).getAsJsonObject("model");
                var parsed = ItemModels.CODEC.parse(JsonOps.INSTANCE, graph);
                assertTrue(parsed.isSuccess(), path + ": " + parsed.error()); graphs++;
                var invalid = graph.deepCopy();
                invalid.getAsJsonArray("cases").get(0).getAsJsonObject().addProperty("when", "first_person_right_hand");
                assertFalse(ItemModels.CODEC.parse(JsonOps.INSTANCE, invalid).isSuccess(), "Context spelling negative control");
            } else {
                assertNotNull(CuboidModel.fromStream(new StringReader(Files.readString(path))), path.toString()); children++;
            }
        }
        assertEquals(59, graphs); assertEquals(4368, children);
    }

    @Test void normalWrappersPreserveMetadataAndExactFallbacksWithIndependentFloat3AndFlag0() throws Exception {
        for (var e : weapons()) {
            String id = id(e); var original = asset("items/weapon/" + id); var item = asset("items/" + KEY + id);
            var scope = LFR.contains(id) || SNIPERS.contains(id) ? asset("items/weapon_scope_w45/" + id).getAsJsonObject("model") : null;
            var fallback = scope == null ? original.getAsJsonObject("model") : scopeSelect(original.getAsJsonObject("model"), scope);
            wrapper(item, original, fallback);
            range(normalRange(id), 3, 21, historicalNormalGraph(original.get("model")));
            for (int f = 0; f <= 20; f++) assertEquals(grip(id, "", f), frame(normalRange(id), f));
        }
    }

    @Test void allNormalFramesLinearlyInterpolateBothHandsRestoreExactEndpointsAndInvertCarrier() throws Exception {
        for (var e : weapons()) {
            String id = id(e), base = "weapon/" + e.get("family").getAsString() + "/" + id;
            var hip = asset("models/" + base).getAsJsonObject("display");
            String end = LFR.contains(id) ? "weapon_scope_w45/" + id + "_native" : base + "_ads";
            var ads = asset("models/" + end).getAsJsonObject("display");
            var twoHip = asset("models/" + base + "_twohand").getAsJsonObject("display");
            var twoAds = asset("models/" + (LFR.contains(id) ? "weapon_scope_w45/" + id + "_twohand" : base + "_ads_twohand"))
                    .getAsJsonObject("display");
            for (int f = 0; f <= 20; f++) {
                var nativeDisplay = child(id + "_" + number(f) + "_native", base);
                var twohand = child(id + "_" + number(f) + "_twohand", base);
                pose(hip, ads, nativeDisplay, f); compensate(nativeDisplay, twohand);
                otherContexts(twoHip, twohand);
                if (f == 0 || f == 20) {
                    assertEquals(f == 0 ? hip : ads, nativeDisplay, id + "/native/" + f);
                    assertEquals(f == 0 ? twoHip : twoAds, twohand, id + "/twohand/" + f);
                }
            }
        }
    }

    @Test void lfrScopeFramesKeepExactW45TintsSourceGeometryAndContinuousPositionAtHalfProgress() throws Exception {
        for (String id : LFR) {
            var old = firstPerson(asset("items/weapon_scope_w45/" + id));
            var fp = firstPerson(asset("items/" + KEY + id)); var scoped = firstCase(fp);
            assertEquals(scopeSelect(normalRange(id), scoped), fp);
            range(scoped, 3, 21, asset("items/weapon_scope_w45/" + id).get("model"));
            String base = "weapon/linear_fusion_rifle/" + id, geometry = "weapon_scope_w45/" + id + "_geometry";
            assertEquals(id.equals("line_in_the_sand")
                    ? "7c556a696e0467775c957523001e68fe2b284d2eac2e17f695a8d82207056ceb"
                    : "7bcc3f90966b7d71b7ede299ad383f26476c8ed07e9412b4b3e1171eaea8a0bd",
                    sha(ROOT.resolve("models/" + geometry + ".json")), "Exact original W45 geometry bytes");
            assertEquals(asset("models/" + base).get("textures"), asset("models/" + geometry).get("textures"));
            for (String branch : List.of("on_false", "on_true"))
                assertEquals(id.equals("line_in_the_sand") ? 0xB777FF : 0xE8C08A,
                        old.getAsJsonObject(branch).getAsJsonArray("tints").get(0).getAsJsonObject().get("value").getAsInt());
            for (int f = 0; f <= 20; f++) {
                var expected = old.deepCopy();
                for (String style : List.of("native", "twohand")) {
                    String branch = style.equals("native") ? "on_false" : "on_true";
                    String key = id + "_scope_" + number(f) + "_" + style;
                    expected.getAsJsonObject(branch).addProperty("model", "destiny:" + KEY + key);
                    var display = child(key, geometry);
                    assertEquals(child(id + "_" + number(f) + "_" + style, base), display,
                            "Same pose on either scope-string branch, including .5: " + id + "/" + f);
                }
                assertEquals(expected, frame(scoped, f), "Only model references may change; exact tints/condition");
            }
        }
    }

    @Test void opaqueSnipersKeepExactOldScopeConditionalAndNonFirstPersonFallback() throws Exception {
        // The live Polymer getter selects W45 once scoped; this asset test does not prove that routing.
        for (String id : SNIPERS) {
            var old = asset("items/weapon_scope_w45/" + id); var original = asset("items/weapon/" + id);
            var expected = scopeSelect(original.getAsJsonObject("model"), old.getAsJsonObject("model"));
            assertEquals(expected, asset("items/" + KEY + id).getAsJsonObject("model").get("fallback"));
            assertEquals(JsonParser.parseString("{\"type\":\"minecraft:empty\"}"), firstPerson(old));
            var ads = original.getAsJsonObject("model").getAsJsonArray("cases").asList().stream()
                    .map(JsonElement::getAsJsonObject).filter(c -> c.get("when").getAsString().equals("ads"))
                    .findFirst().orElseThrow().get("model");
            assertEquals(ads, old.getAsJsonObject("model").get("fallback"), "Original ADS/grip graph in other contexts");
            assertEquals("minecraft:range_dispatch", firstPerson(asset("items/" + KEY + id)).get("type").getAsString());
        }
    }

    @Test void liveBowsKeep44ExactDrawStatesAcross21IndependentAimFramesAndByteEquivalentOldFallback() throws Exception {
        var states = parts().subList(1, 45);
        for (String id : BOWS) {
            var old = asset("items/weapon_bow_w50/" + id); var item = asset("items/" + KEY + id + "_bow");
            wrapper(item, old, old.getAsJsonObject("model"));
            assertArrayEquals(old.get("model").toString().getBytes(StandardCharsets.UTF_8),
                    item.getAsJsonObject("model").get("fallback").toString().getBytes(StandardCharsets.UTF_8));
            var aim = firstPerson(item); range(aim, 3, 21, old.get("model"));
            var sourceDraw = firstPerson(old).getAsJsonObject("fallback");
            for (int f = 0; f <= 20; f++) {
                var draw = frame(aim, f); range(draw, 2, 44, grip(id, "", f));
                for (int s = 0; s < 44; s++) {
                    int threshold = s < 23 ? s : s + 9;
                    assertEquals(threshold, sourceDraw.getAsJsonArray("entries").get(s).getAsJsonObject().get("threshold").getAsInt());
                    assertEquals(threshold, draw.getAsJsonArray("entries").get(s).getAsJsonObject().get("threshold").getAsInt());
                    assertEquals(composite("weapon_bow_w50/" + id + "_body_hip", "weapon_bow_w50/" + id + "_" + states.get(s) + "_hip"),
                            frame(sourceDraw, s), "Exact old composite draw paths");
                    assertEquals(composite(KEY + id + "_bow_body_" + number(f), KEY + id + "_bow_" + states.get(s) + "_" + number(f)), frame(draw, s));
                }
                for (String part : parts()) {
                    String parent = "weapon_bow_w50/" + id + "_" + part;
                    var hip = asset("models/" + parent + "_hip");
                    assertTrue(hip.has("elements"), "Geometry stays in original W50 parent");
                    pose(hip.getAsJsonObject("display"), asset("models/" + parent + "_ads").getAsJsonObject("display"),
                            child(id + "_bow_" + part + "_" + number(f), parent + "_hip"), f);
                }
            }
        }
    }

    private static JsonObject json(Path p) throws Exception { return JsonParser.parseString(Files.readString(p)).getAsJsonObject(); }
    private static JsonObject asset(String p) throws Exception { return json(ROOT.resolve(p + ".json")); }
    private static List<JsonObject> weapons() throws Exception {
        return json(ART).getAsJsonArray("weapons").asList().stream().map(JsonElement::getAsJsonObject).toList();
    }
    private static String id(JsonObject e) { return e.get("id").getAsString(); }
    private static String number(int f) { return String.format(Locale.ROOT, "%02d", f); }
    private static List<String> strings(JsonArray a) { return a.asList().stream().map(JsonElement::getAsString).toList(); }
    private static JsonObject firstCase(JsonObject o) { return o.getAsJsonArray("cases").get(0).getAsJsonObject().getAsJsonObject("model"); }
    private static JsonObject firstPerson(JsonObject item) { return firstCase(item.getAsJsonObject("model")); }
    private static JsonObject frame(JsonObject range, int i) { return range.getAsJsonArray("entries").get(i).getAsJsonObject().getAsJsonObject("model"); }
    private static JsonObject normalRange(String id) throws Exception {
        var fp = firstPerson(asset("items/" + KEY + id)); return LFR.contains(id) ? fp.getAsJsonObject("fallback") : fp;
    }
    private static JsonObject scopeSelect(JsonObject ordinary, JsonObject scope) {
        var o = JsonParser.parseString("{\"type\":\"minecraft:select\",\"property\":\"minecraft:custom_model_data\",\"index\":0,\"cases\":[{\"when\":\"scope\"}]}").getAsJsonObject();
        o.getAsJsonArray("cases").get(0).getAsJsonObject().add("model", scope); o.add("fallback", ordinary); return o;
    }
    private static JsonObject model(String key) {
        var o = new JsonObject(); o.addProperty("type", "minecraft:model"); o.addProperty("model", "destiny:" + key); return o;
    }
    private static JsonObject grip(String id, String suffix, int f) {
        var o = JsonParser.parseString("{\"type\":\"minecraft:condition\",\"property\":\"minecraft:custom_model_data\",\"index\":0}").getAsJsonObject();
        for (String style : List.of("native", "twohand")) o.add(style.equals("native") ? "on_false" : "on_true", model(KEY + id + suffix + "_" + number(f) + "_" + style));
        return o;
    }
    private static JsonObject composite(String body, String state) {
        var o = new JsonObject(); o.addProperty("type", "minecraft:composite");
        var a = new JsonArray(); a.add(model(body)); a.add(model(state)); o.add("models", a); return o;
    }
    private static void wrapper(JsonObject item, JsonObject source, JsonObject fallback) {
        var restored = item.deepCopy(); restored.add("model", source.get("model")); assertEquals(source, restored, "All original metadata");
        var select = item.getAsJsonObject("model"); assertEquals(Set.of("type", "property", "cases", "fallback"), select.keySet());
        assertEquals("minecraft:select", select.get("type").getAsString()); assertEquals("minecraft:display_context", select.get("property").getAsString());
        assertEquals(1, select.getAsJsonArray("cases").size()); var c = select.getAsJsonArray("cases").get(0).getAsJsonObject();
        assertEquals(Set.of("when", "model"), c.keySet()); assertEquals(FP, strings(c.getAsJsonArray("when"))); assertEquals(fallback, select.get("fallback"));
    }
    private static void range(JsonObject o, int index, int size, JsonElement fallback) {
        assertEquals(Set.of("type", "property", "index", "entries", "fallback"), o.keySet());
        assertEquals("minecraft:range_dispatch", o.get("type").getAsString()); assertEquals("minecraft:custom_model_data", o.get("property").getAsString());
        assertEquals(index, o.get("index").getAsInt()); assertEquals(fallback, o.get("fallback")); assertEquals(size, o.getAsJsonArray("entries").size());
        for (int i = 0; i < size; i++) {
            var entry = o.getAsJsonArray("entries").get(i).getAsJsonObject(); assertEquals(Set.of("threshold", "model"), entry.keySet());
            assertEquals(index == 3 ? i / 20.0 : i < 23 ? i : i + 9, entry.get("threshold").getAsDouble(), 1e-9);
        }
    }
    private static JsonObject child(String key, String parent) throws Exception {
        var o = asset("models/" + KEY + key); assertEquals(Set.of("parent", "display"), o.keySet());
        assertEquals("destiny:" + parent, o.get("parent").getAsString()); return o.getAsJsonObject("display");
    }
    private static void pose(JsonObject hip, JsonObject ads, JsonObject actual, int f) {
        assertEquals(hip.keySet(), actual.keySet()); otherContexts(hip, actual);
        for (String context : FP) for (String field : List.of("rotation", "translation", "scale")) {
            var expected = vector(hip.getAsJsonObject(context), field).lerp(vector(ads.getAsJsonObject(context), field), f / 20.0);
            assertTrue(expected.equals(vector(actual.getAsJsonObject(context), field), 5.1e-7), context + "/" + field + "/" + f);
        }
        if (f == 0 || f == 20) assertEquals(f == 0 ? hip : ads, actual);
    }
    private static void otherContexts(JsonObject expected, JsonObject actual) {
        assertEquals(expected.keySet(), actual.keySet());
        for (String context : expected.keySet()) if (!FP.contains(context)) assertEquals(expected.get(context), actual.get(context), context);
    }
    private static Vector3d vector(JsonObject o, String field) {
        var a = o.getAsJsonArray(field); assertEquals(3, a.size());
        for (var v : a) { assertTrue(Double.isFinite(v.getAsDouble()) && Float.isFinite(v.getAsFloat()));
            if (field.equals("translation")) assertTrue(Math.abs(v.getAsDouble()) <= 80);
            if (field.equals("scale")) assertTrue(v.getAsDouble() > 0 && v.getAsDouble() <= 4); }
        return new Vector3d(a.get(0).getAsDouble(), a.get(1).getAsDouble(), a.get(2).getAsDouble());
    }
    // Same compact native ItemTransform order/units and reflection helpers as W69.
    private static Matrix4d transform(JsonObject o, boolean left) {
        var r = vector(o, "rotation").mul(Math.PI / 180); var t = vector(o, "translation").div(16); var s = vector(o, "scale");
        double sign = left ? -1 : 1;
        return new Matrix4d().translate(t.x * sign, t.y, t.z).rotateXYZ(r.x, r.y * sign, r.z * sign).scale(s.x, s.y, s.z);
    }
    private static void compensate(JsonObject nativeDisplay, JsonObject twohand) {
        for (boolean left : List.of(false, true)) {
            String context = FP.get(left ? 1 : 0); double sign = left ? -1 : 1;
            var restored = new Matrix4d().translate(-.641864 * sign, 0, 0).rotateY(Math.toRadians(10) * sign)
                    .mul(transform(twohand.getAsJsonObject(context), left));
            assertTrue(transform(nativeDisplay.getAsJsonObject(context), left).equals(restored, EPS), context);
        }
    }
    private static List<String> parts() {
        var p = new ArrayList<>(List.of("body", "empty", "loaded"));
        for (String stage : List.of("draw", "nock")) for (int f = 0; f <= 20; f++) p.add(stage + "_" + number(f)); return p;
    }
    private static Set<Path> expectedAssets() throws Exception {
        Set<Path> paths = new HashSet<>();
        for (var e : weapons()) {
            String id = id(e); paths.add(ROOT.resolve("items/" + KEY + id + ".json"));
            for (int f = 0; f <= 20; f++) {
                for (String suffix : LFR.contains(id) ? List.of("", "_scope") : List.of(""))
                    for (String grip : List.of("native", "twohand")) paths.add(ROOT.resolve("models/" + KEY + id + suffix + "_" + number(f) + "_" + grip + ".json"));
                if (BOWS.contains(id)) for (String part : parts()) paths.add(ROOT.resolve("models/" + KEY + id + "_bow_" + part + "_" + number(f) + ".json"));
            }
            if (BOWS.contains(id)) paths.add(ROOT.resolve("items/" + KEY + id + "_bow.json"));
        }
        return paths;
    }
    private static void references(JsonElement v, Set<Path> refs) {
        if (v.isJsonObject()) for (var e : v.getAsJsonObject().entrySet()) {
            if (e.getKey().equals("model") && e.getValue().isJsonPrimitive()) {
                String key = e.getValue().getAsString(); assertTrue(key.startsWith("destiny:"));
                refs.add(ROOT.resolve("models/" + key.substring(8) + ".json"));
            } else references(e.getValue(), refs);
        } else if (v.isJsonArray()) for (var child : v.getAsJsonArray()) references(child, refs);
    }
    private static List<Path> files(Path root) throws Exception {
        try (var paths = Files.walk(root)) { return paths.filter(Files::isRegularFile).toList(); }
    }
    private static String sha(Path p) throws Exception { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(p))); }
    private static String pin(Collection<Path> paths) throws Exception {
        var digest = MessageDigest.getInstance("SHA-256");
        for (Path p : paths.stream().sorted(Comparator.comparing(Path::toString)).toList())
            digest.update((p + "\0" + historicalSha(p) + "\n").getBytes(StandardCharsets.UTF_8));
        return HexFormat.of().formatHex(digest.digest());
    }
}
