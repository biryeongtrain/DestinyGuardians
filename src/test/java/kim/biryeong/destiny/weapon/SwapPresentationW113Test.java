package kim.biryeong.destiny.weapon;

import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import com.mojang.serialization.JsonOps;
import net.minecraft.client.renderer.item.ItemModels;
import net.minecraft.client.resources.model.cuboid.CuboidModel;
import org.joml.Matrix4d;
import org.joml.Vector3d;
import org.junit.jupiter.api.Test;

import java.io.StringReader;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

import static org.junit.jupiter.api.Assertions.*;
import static kim.biryeong.destiny.weapon.RenderContractsW163Support.*;

/** Native asset codecs and real model graphs. These checks are not framebuffer evidence. */
class SwapPresentationW113Test {
    private static final Path ROOT = Path.of("src/main/resources/assets/destiny");
    private static final List<String> PAIR = List.of("austringer", "beloved", "ammit_ar2", "the_recluse");
    private static final List<String> FP = List.of("firstperson_righthand", "firstperson_lefthand");

    @Test void onlyTheTwelveDistinctCatalogDirectionsAreSupported() {
        int supported = 0;
        for (var from : WeaponCatalog.all()) for (var to : WeaponCatalog.all()) {
            boolean expected = PAIR.contains(from.id()) && PAIR.contains(to.id()) && !from.id().equals(to.id());
            assertEquals(expected, WeaponSwapPresentation.supports(from, to), from.id() + " -> " + to.id());
            if (expected) supported++;
        }
        assertEquals(12, supported);
        assertFalse(WeaponSwapPresentation.supports(null, WeaponCatalog.find("beloved").orElseThrow()));
        assertFalse(WeaponSwapPresentation.supports(WeaponCatalog.find("austringer").orElseThrow(), null));
        assertEquals(5, WeaponSwapPresentation.SELECTOR_INDEX);
        assertEquals(20, WeaponSwapPresentation.STEPS);
    }

    @Test void pairGraphsPreserveIncomingFallbackAndDecodeAllPhaseAndCarrierModels() throws Exception {
        bootstrapCodecs();
        var references = new HashSet<Path>();
        for (String from : PAIR) for (String to : PAIR) {
            if (from.equals(to) || legacy(from, to)) continue;
            var item = json("items/weapon_swap_w113/" + from + "_to_" + to);
            var original = json("items/weapon/" + to);
            var decoded = ItemModels.CODEC.parse(JsonOps.INSTANCE, item.get("model"));
            assertTrue(decoded.isSuccess(), decoded.error().toString());
            var metadata = item.deepCopy(); metadata.add("model", original.get("model"));
            assertEquals(original, metadata, "Original incoming metadata including equip animation policy");
            var wrapper = item.getAsJsonObject("model");
            assertEquals("minecraft:select", wrapper.get("type").getAsString());
            assertEquals("minecraft:display_context", wrapper.get("property").getAsString());
            assertEquals(original.get("model"), wrapper.get("fallback"), "GUI/third person keep actual selected weapon");
            assertEquals(1, wrapper.getAsJsonArray("cases").size());
            var first = wrapper.getAsJsonArray("cases").get(0).getAsJsonObject();
            assertEquals(FP, first.getAsJsonArray("when").asList().stream().map(JsonElement::getAsString).toList());
            var range = first.getAsJsonObject("model");
            assertEquals("minecraft:range_dispatch", range.get("type").getAsString());
            assertEquals("minecraft:custom_model_data", range.get("property").getAsString());
            assertEquals(5, range.get("index").getAsInt());
            assertEquals(historicalNormalGraph(original.get("model")), range.get("fallback"), "W161 preserves animated FP fallback exactly");
            assertEquals(42, range.getAsJsonArray("entries").size());
            for (int phase = 0; phase < 2; phase++) for (int sample = 0; sample <= 20; sample++) {
                var frame = range.getAsJsonArray("entries").get(phase * 21 + sample).getAsJsonObject();
                assertEquals(phase * 2 + sample / 20.0, frame.get("threshold").getAsDouble(), 1e-7);
                var grip = frame.getAsJsonObject("model");
                assertEquals("minecraft:condition", grip.get("type").getAsString());
                assertEquals("minecraft:custom_model_data", grip.get("property").getAsString());
                assertEquals(0, grip.get("index").getAsInt(), "Flag0 belongs to actual wire carrier");
                String rendered = phase == 0 ? from : to;
                var nativeDisplay = child(grip.getAsJsonObject("on_false"), rendered, false, references);
                var twoDisplay = child(grip.getAsJsonObject("on_true"), rendered, true, references);
                compensate(nativeDisplay, twoDisplay);
                if (phase == 0 && sample == 0 || phase == 1 && sample == 20) {
                    assertEquals(base(rendered, false).get("display"), nativeDisplay, "Exact HIP endpoint " + rendered);
                    assertEquals(base(rendered, true).get("display"), twoDisplay, "Exact twohand HIP endpoint " + rendered);
                }
            }
        }
        assertEquals(840, references.size(), "Ten new directions, both phases, 21 samples and both current carriers");
        try (var files = Files.walk(ROOT.resolve("models/item/weapon_swap_w113"))) {
            assertEquals(references, files.filter(Files::isRegularFile).collect(java.util.stream.Collectors.toSet()));
        }
        try (var files = Files.list(ROOT.resolve("items/weapon_swap_w113"))) {
            var expected = new HashSet<String>();
            for (String from : PAIR) for (String to : PAIR)
                if (!from.equals(to) && !legacy(from, to)) expected.add(from + "_to_" + to + ".json");
            assertEquals(expected, files.filter(Files::isRegularFile).map(p -> p.getFileName().toString())
                            .collect(java.util.stream.Collectors.toSet()));
        }
    }

    private static boolean legacy(String from, String to) {
        return Set.of(from, to).equals(Set.of("austringer", "beloved"));
    }

    @Test void originalGeometryTexturesAndW91BytesMatchFrozenInputs() throws Exception {
        var manifest = JsonParser.parseString(Files.readString(Path.of("art/weapons/w113-swap/manifest.json"))).getAsJsonObject();
        assertEquals(840, manifest.get("modelChildren").getAsInt());
        assertEquals(10, manifest.getAsJsonArray("pairs").size());
        assertEquals(858, manifest.getAsJsonArray("ownedPaths").size());
        assertTrue(manifest.get("approximation").getAsBoolean());
        assertFalse(manifest.get("handIK").getAsBoolean());
        assertFalse(manifest.get("measuredSourceFrames").getAsBoolean());
        for (var entry : manifest.getAsJsonObject("originalSha256").entrySet()) {
            assertEquals(entry.getValue().getAsString(), historicalSha(Path.of(entry.getKey())), entry.getKey());
        }
    }

    @Test void float32DispatchCoversRuntimeOffsetsGapAndFallback() throws Exception {
        for (String from : PAIR) for (String to : PAIR) {
            if (from.equals(to)) continue;
            String namespace = legacy(from, to) ? "weapon_swap_w91" : "weapon_swap_w113";
            var item = json("items/" + namespace + "/" + from + "_to_" + to);
            var range = item.getAsJsonObject("model").getAsJsonArray("cases").get(0)
                    .getAsJsonObject().getAsJsonObject("model");
            assertEquals(-1, select(range, -.001f));
            assertEquals(20, select(range, 1.5f));
            assertEquals(41, select(range, 4f));
            for (int phase = 0; phase < 2; phase++) for (int sample = 0; sample <= 20; sample++)
                for (float offset : new float[] {0, .0001f, .0002f, .0003f, .000999f})
                    assertEquals(phase * 21 + sample, select(range, phase * 2 + sample / 20f + offset));
        }
    }
    private static int select(JsonObject range, float value) {
        int selected = -1; float previous = Float.NEGATIVE_INFINITY;
        var entries = range.getAsJsonArray("entries");
        for (int i = 0; i < entries.size(); i++) {
            float threshold = entries.get(i).getAsJsonObject().get("threshold").getAsFloat();
            assertTrue(threshold > previous); previous = threshold;
            if (threshold <= value) selected = i;
        }
        return selected;
    }
    private static void bootstrapCodecs() {
        net.minecraft.SharedConstants.tryDetectVersion();
        net.minecraft.server.Bootstrap.bootStrap();
        ItemModels.bootstrap();
        net.minecraft.client.color.item.ItemTintSources.bootstrap();
        net.minecraft.client.renderer.item.properties.select.SelectItemModelProperties.bootstrap();
        net.minecraft.client.renderer.item.properties.conditional.ConditionalItemModelProperties.bootstrap();
        net.minecraft.client.renderer.item.properties.numeric.RangeSelectItemModelProperties.bootstrap();
    }
    private static JsonObject json(String path) throws Exception {
        return JsonParser.parseString(Files.readString(ROOT.resolve(path + ".json"))).getAsJsonObject();
    }
    private static String basePath(String id) {
        return "weapon/" + WeaponCatalog.find(id).orElseThrow().family() + "/" + id;
    }
    private static JsonObject base(String id, boolean twohand) throws Exception {
        return json("models/" + basePath(id) + (twohand ? "_twohand" : ""));
    }
    private static JsonObject child(JsonObject reference, String id, boolean twohand, Set<Path> references) throws Exception {
        assertEquals("minecraft:model", reference.get("type").getAsString());
        String key = reference.get("model").getAsString();
        assertTrue(key.startsWith("destiny:item/weapon_swap_w113/"), key);
        var path = ROOT.resolve("models/" + key.substring(8) + ".json");
        assertTrue(references.add(path), "Each direction/phase/sample/carrier is auditable: " + path);
        var child = JsonParser.parseString(Files.readString(path)).getAsJsonObject();
        assertEquals(Set.of("parent", "display"), child.keySet(), "Original detailed geometry/baseUV inherited untouched");
        assertEquals("destiny:" + basePath(id), child.get("parent").getAsString());
        assertNotNull(CuboidModel.fromStream(new StringReader(child.toString())));
        var display = child.getAsJsonObject("display");
        var original = base(id, twohand).getAsJsonObject("display");
        // W156's documented ammit_ar2*.json propagation is filename-scoped: every
        // native child of an outgoing-Ammit pair has Rx72, including the incoming
        // ready phase. Other pairs retain Rx90. These contexts are unreachable in
        // the FP-only animation branch; check the exact historical rule before
        // comparing the remaining display fields to the current canonical model.
        if (!twohand) {
            boolean propagated = key.startsWith("destiny:item/weapon_swap_w113/ammit_ar2_to_");
            for (String context : List.of("thirdperson_righthand", "thirdperson_lefthand")) {
                var pose = display.getAsJsonObject(context);
                assertEquals(JsonParser.parseString(propagated ? "[72,0,0]" : "[90,0,0]"), pose.get("rotation"), key);
                pose.add("rotation", original.getAsJsonObject(context).get("rotation").deepCopy());
            }
        }
        assertEquals(original.keySet(), display.keySet());
        for (String context : display.keySet()) {
            if (!FP.contains(context)) assertEquals(original.get(context), display.get(context));
            for (String field : List.of("rotation", "translation", "scale")) vector(display.getAsJsonObject(context), field);
        }
        return display;
    }
    private static Vector3d vector(JsonObject pose, String field) {
        var a = pose.getAsJsonArray(field); assertEquals(3, a.size());
        for (var v : a) {
            assertTrue(Double.isFinite(v.getAsDouble()) && Float.isFinite(v.getAsFloat()));
            if (field.equals("translation")) assertTrue(Math.abs(v.getAsDouble()) <= 80);
            if (field.equals("scale")) assertTrue(v.getAsDouble() > 0 && v.getAsDouble() <= 4);
        }
        return new Vector3d(a.get(0).getAsDouble(), a.get(1).getAsDouble(), a.get(2).getAsDouble());
    }
    private static Matrix4d transform(JsonObject pose, boolean left) {
        var r = vector(pose, "rotation").mul(Math.PI / 180);
        var t = vector(pose, "translation").div(16); var s = vector(pose, "scale");
        double sign = left ? -1 : 1;
        return new Matrix4d().translate(t.x * sign, t.y, t.z).rotateXYZ(r.x, r.y * sign, r.z * sign).scale(s.x, s.y, s.z);
    }
    private static void compensate(JsonObject nativeDisplay, JsonObject twohand) {
        for (boolean left : List.of(false, true)) {
            String context = FP.get(left ? 1 : 0); double sign = left ? -1 : 1;
            var restored = new Matrix4d().translate(-.641864 * sign, 0, 0)
                    .rotateY(Math.toRadians(10) * sign).mul(transform(twohand.getAsJsonObject(context), left));
            assertTrue(transform(nativeDisplay.getAsJsonObject(context), left).equals(restored, 3e-6), context);
        }
    }
}
