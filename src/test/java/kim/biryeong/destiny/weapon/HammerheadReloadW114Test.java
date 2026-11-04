package kim.biryeong.destiny.weapon;

import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import com.mojang.serialization.JsonOps;
import net.minecraft.client.renderer.item.ItemModels;
import net.minecraft.client.resources.model.cuboid.CuboidModel;
import org.junit.jupiter.api.Test;

import java.io.StringReader;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.HashSet;
import java.util.HexFormat;
import java.util.List;
import java.util.Set;

import static org.junit.jupiter.api.Assertions.*;

/** Independent resource/native-codec contracts; runtime/PLAY-wire/GT belong to master.
 * This worker deliberately does not launch Gradle or claim native visual acceptance. */
class HammerheadReloadW114Test {
    private static final Path ASSETS = Path.of("src/main/resources/assets/destiny");
    private static final Path ART = Path.of("art/weapons/w114/hammerhead");
    private static final String KEY = "weapon_reload_w114_hammerhead/hammerhead";
    private static final List<String> PARTS = List.of("body", "magazine", "cover");
    private static final List<Integer> MAGAZINE = List.of(0,1,2,3,4,5,6,7,87,169,174,175,186,188,210,213,214,215,216,217,218,219,220,221,222);
    private static final List<Integer> COVER = List.of(89,94,95,98,100,101,102,103,104,105,106,183,184,185,207);

    @Test void parsesOneGraphAndAll129CuboidAssetsWithExplicitIndependentBootstrap() throws Exception {
        // Keep this complete in THIS test: no dependency on another class/test order.
        net.minecraft.SharedConstants.tryDetectVersion();
        net.minecraft.server.Bootstrap.bootStrap();
        ItemModels.bootstrap();
        net.minecraft.client.color.item.ItemTintSources.bootstrap();
        net.minecraft.client.renderer.item.properties.select.SelectItemModelProperties.bootstrap();
        net.minecraft.client.renderer.item.properties.conditional.ConditionalItemModelProperties.bootstrap();
        net.minecraft.client.renderer.item.properties.numeric.RangeSelectItemModelProperties.bootstrap();
        var graph = item().getAsJsonObject("model");
        var decoded = ItemModels.CODEC.parse(JsonOps.INSTANCE, graph);
        assertTrue(decoded.isSuccess(), () -> "26.3 codec: " + decoded.error());
        var invalid = graph.deepCopy();
        invalid.getAsJsonArray("cases").get(0).getAsJsonObject().addProperty("when", "first_person_right_hand");
        assertFalse(ItemModels.CODEC.parse(JsonOps.INSTANCE, invalid).isSuccess());
        int models = 0;
        for (String part : PARTS) {
            assertNotNull(CuboidModel.fromStream(new StringReader(model(part).toString()))); models++;
            for (int frame = 0; frame <= 20; frame++) for (String grip : List.of("native", "twohand")) {
                assertNotNull(CuboidModel.fromStream(new StringReader(child(frame, part, grip).toString()))); models++;
            }
        }
        assertEquals(129, models);
        var malformed = original();
        malformed.getAsJsonArray("elements").get(0).getAsJsonObject().add("from", JsonParser.parseString("[0,0]"));
        assertThrows(com.google.gson.JsonParseException.class,
                () -> CuboidModel.fromStream(new StringReader(malformed.toString())));
    }

    @Test void preservesEveryOriginalElementUvFaceTextureAndLiteralPartIndices() throws Exception {
        assertEquals("7890eb2e60dc2a6547c7af7278a079b9e28575fd186683769c41f3c725c990bb",
                hash(ASSETS.resolve("models/weapon/machine_gun/hammerhead.json")));
        assertEquals("ba746a0939a251faf3244f177d20063d982b48cc1f9e0418bff25b4380c2e041",
                hash(ASSETS.resolve("textures/item/weapon/w30/hammerhead.png")));
        var source = original(); var sourceElements = source.getAsJsonArray("elements");
        assertEquals(223, sourceElements.size());
        var indices = json(ART.resolve("partition-audit.json")).getAsJsonObject("indices");
        assertEquals(MAGAZINE, ints(indices.getAsJsonArray("magazine")));
        assertEquals(COVER, ints(indices.getAsJsonArray("cover")));
        Set<Integer> seen = new HashSet<>();
        for (String part : PARTS) {
            var geometry = model(part); var elements = geometry.getAsJsonArray("elements");
            assertEquals(source.get("textures"), geometry.get("textures"));
            var selected = indices.getAsJsonArray(part); assertEquals(selected.size(), elements.size());
            for (int i = 0; i < selected.size(); i++) {
                int index = selected.get(i).getAsInt(); assertTrue(seen.add(index));
                assertEquals(sourceElements.get(index), elements.get(i), "whole original cube " + index);
            }
            var metadata = geometry.deepCopy(); metadata.remove("elements");
            var expected = source.deepCopy(); expected.remove("elements"); expected.remove("display");
            assertEquals(expected, metadata);
        }
        assertEquals(223, seen.size()); assertTrue(seen.size() <= 256);
    }

    @Test void bothEndpointsAndAllOtherContextDisplaysMatchOriginalsExactly() throws Exception {
        for (String grip : List.of("native", "twohand")) {
            var base = json(ASSETS.resolve("models/weapon/machine_gun/hammerhead" + (grip.equals("native") ? "" : "_twohand") + ".json")).getAsJsonObject("display");
            for (String part : PARTS) for (int frame = 0; frame <= 20; frame++) {
                var display = child(frame, part, grip).getAsJsonObject("display");
                if (frame == 0 || frame == 20) assertEquals(base, display);
                for (var entry : display.entrySet()) if (!entry.getKey().startsWith("firstperson_"))
                    assertEquals(base.get(entry.getKey()), entry.getValue());
            }
        }
    }

    @Test void graphUsesFloatSlotOneFlagZeroAndExactFullOriginalFallback() throws Exception {
        var source = json(ASSETS.resolve("items/weapon/hammerhead.json")); var wrapper = item();
        var outer = wrapper.getAsJsonObject("model");
        assertEquals("minecraft:display_context", outer.get("property").getAsString());
        assertEquals(source.get("model"), outer.get("fallback"));
        var cases = outer.getAsJsonArray("cases"); assertEquals(1, cases.size());
        assertEquals(JsonParser.parseString("[\"firstperson_righthand\",\"firstperson_lefthand\"]"), cases.get(0).getAsJsonObject().get("when"));
        var range = cases.get(0).getAsJsonObject().getAsJsonObject("model");
        assertEquals("minecraft:custom_model_data", range.get("property").getAsString());
        assertEquals(1, range.get("index").getAsInt()); assertEquals(source.get("model"), range.get("fallback"));
        var entries = range.getAsJsonArray("entries"); assertEquals(21, entries.size());
        Set<String> references = new HashSet<>();
        for (int frame = 0; frame <= 20; frame++) {
            var row = entries.get(frame).getAsJsonObject(); assertEquals(frame / 20f, row.get("threshold").getAsFloat());
            var condition = row.getAsJsonObject("model"); assertEquals(0, condition.get("index").getAsInt());
            assertEquals("minecraft:condition", condition.get("type").getAsString());
            assertEquals("minecraft:custom_model_data", condition.get("property").getAsString());
            for (String grip : List.of("native", "twohand")) {
                var composite = condition.getAsJsonObject(grip.equals("native") ? "on_false" : "on_true");
                assertEquals("minecraft:composite", composite.get("type").getAsString());
                var models = composite.getAsJsonArray("models"); assertEquals(3, models.size());
                for (int i = 0; i < 3; i++) {
                    String expected = "destiny:" + KEY + "_" + String.format(java.util.Locale.ROOT, "%02d", frame) + "_" + PARTS.get(i) + "_" + grip;
                    assertEquals(expected, models.get(i).getAsJsonObject().get("model").getAsString());
                    assertTrue(references.add(expected));
                    assertEquals("destiny:" + KEY + "_" + PARTS.get(i), child(frame, PARTS.get(i), grip).get("parent").getAsString());
                }
            }
        }
        assertEquals(126, references.size());
        wrapper.remove("model"); source.remove("model"); assertEquals(source, wrapper);
    }

    @Test void allFloatTransitionEdgesAndLiveOffsetStayInExpectedSamples() throws Exception {
        var entries = item().getAsJsonObject("model").getAsJsonArray("cases").get(0).getAsJsonObject().getAsJsonObject("model").getAsJsonArray("entries");
        assertEquals(-1, select(entries, -1)); assertEquals(0, select(entries, 0));
        for (int i = 1; i <= 20; i++) {
            float threshold = i / 20f;
            assertEquals(i - 1, select(entries, Math.nextDown(threshold)));
            assertEquals(i, select(entries, threshold)); assertEquals(i, select(entries, Math.nextUp(threshold)));
            if (i < 20) assertEquals(i, select(entries, threshold + .001f));
        }
        assertEquals(20, select(entries, 1.001f));
    }

    @Test void auditedSemanticsAndReferenceEvidenceArePinnedWithoutNativeClaims() throws Exception {
        var audit = json(ART.resolve("original-model-audit.json"));
        assertEquals(25499, audit.get("sourceTriangles").getAsInt());
        var meshes = audit.getAsJsonArray("meshes"); assertEquals(3, meshes.size());
        assertEquals(5084, meshes.get(1).getAsJsonObject().getAsJsonObject("rigidBoneTriangles").get("Magazine").getAsInt());
        assertEquals(2132, meshes.get(2).getAsJsonObject().getAsJsonObject("rigidBoneTriangles").get("Cover").getAsInt());
        var partition = json(ART.resolve("partition-audit.json"));
        assertEquals(19, partition.getAsJsonArray("mixedCubeIndices").size());
        assertEquals(List.of(182, 206, 207), ints(partition.getAsJsonArray("surfaceDisagreementIndices")));
        var manifest = json(ART.resolve("manifest.json"));
        assertFalse(manifest.get("sourceAnimationRecovered").getAsBoolean());
        assertFalse(manifest.get("handIK").getAsBoolean()); assertFalse(manifest.get("nativeGameplayVerified").getAsBoolean());
        assertEquals("destiny:" + KEY, manifest.get("graphId").getAsString());
        assertEquals(130, manifest.getAsJsonObject("assetSha256").size());
        for (var entry : manifest.getAsJsonObject("assetSha256").entrySet())
            assertEquals(entry.getValue().getAsString(), hash(Path.of(entry.getKey())), entry.getKey());
        var frames = json(ART.resolve("gameplay-provenance.json")).getAsJsonArray("frames"); assertEquals(16, frames.size());
        for (JsonElement frame : frames) {
            var row = frame.getAsJsonObject(); assertEquals(row.get("sha256").getAsString(), hash(ART.resolve(row.get("path").getAsString())));
        }
    }

    private static int select(JsonArray entries, float progress) {
        int selected = -1;
        for (int i = 0; i < entries.size(); i++) if (entries.get(i).getAsJsonObject().get("threshold").getAsFloat() <= progress) selected = i;
        return selected;
    }
    private static List<Integer> ints(JsonArray array) {
        return java.util.stream.StreamSupport.stream(array.spliterator(), false).map(JsonElement::getAsInt).toList();
    }
    private static JsonObject json(Path path) throws Exception { return JsonParser.parseString(Files.readString(path)).getAsJsonObject(); }
    private static JsonObject item() throws Exception { return json(ASSETS.resolve("items/" + KEY + ".json")); }
    private static JsonObject original() throws Exception { return json(ASSETS.resolve("models/weapon/machine_gun/hammerhead.json")); }
    private static JsonObject model(String part) throws Exception { return json(ASSETS.resolve("models/" + KEY + "_" + part + ".json")); }
    private static JsonObject child(int frame, String part, String grip) throws Exception {
        return json(ASSETS.resolve("models/" + KEY + "_" + String.format(java.util.Locale.ROOT, "%02d", frame) + "_" + part + "_" + grip + ".json"));
    }
    private static String hash(Path path) throws Exception { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(path))); }
}
