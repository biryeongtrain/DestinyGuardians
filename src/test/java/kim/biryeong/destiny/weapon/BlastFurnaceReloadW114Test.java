package kim.biryeong.destiny.weapon;

import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import com.mojang.serialization.JsonOps;
import com.mojang.blaze3d.vertex.PoseStack;
import net.minecraft.world.item.ItemDisplayContext;
import net.minecraft.client.renderer.item.ItemModels;
import net.minecraft.client.resources.model.cuboid.CuboidModel;
import org.joml.Matrix4d;
import org.joml.Vector3d;
import org.junit.jupiter.api.BeforeAll;
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

/** Independent native 26.3 asset tests. Master runs these; no client/GT claim. */
class BlastFurnaceReloadW114Test {
    private static final Path ROOT = Path.of("src/main/resources/assets/destiny");
    private static final Path ART = Path.of("art/weapons/w114/blast_furnace");
    private static final String KEY = "weapon_reload_w114_blast_furnace/blast_furnace";
    private static final String BASE = "models/weapon/pulse_rifle/blast_furnace";
    private static final List<String> PARTS = List.of("body", "magazine");
    private static final List<String> FP = List.of("firstperson_righthand", "firstperson_lefthand");
    private static final Set<Integer> MAG = Set.of(54,110,112,113,116,118,120,124,132,139,143,149);

    @BeforeAll static void bootstrapCodecsIndependently() {
        net.minecraft.SharedConstants.tryDetectVersion();
        net.minecraft.server.Bootstrap.bootStrap();
        ItemModels.bootstrap();
        net.minecraft.client.color.item.ItemTintSources.bootstrap();
        net.minecraft.client.renderer.item.properties.select.SelectItemModelProperties.bootstrap();
        net.minecraft.client.renderer.item.properties.conditional.ConditionalItemModelProperties.bootstrap();
        net.minecraft.client.renderer.item.properties.numeric.RangeSelectItemModelProperties.bootstrap();
    }

    @Test void nativeCodecsDecodeExactly87AssetsAndRejectBrokenControls() throws Exception {
        var expected = expectedAssets();
        Set<Path> actual = new HashSet<>();
        for (String kind : List.of("models", "items")) {
            try (var paths = Files.list(ROOT.resolve(kind + "/weapon_reload_w114_blast_furnace"))) {
                paths.filter(Files::isRegularFile).forEach(actual::add);
            }
        }
        assertEquals(87, expected.size()); assertEquals(expected, actual);
        for (Path path : actual) {
            if (path.toString().contains("/items/")) {
                var decoded = ItemModels.CODEC.parse(JsonOps.INSTANCE, json(path).get("model"));
                assertTrue(decoded.isSuccess(), path + ": " + decoded.error());
            } else assertNotNull(CuboidModel.fromStream(new StringReader(Files.readString(path))), path.toString());
        }
        var invalid = item().getAsJsonObject("model").deepCopy();
        invalid.getAsJsonArray("cases").get(0).getAsJsonObject().addProperty("when", "first_person_right_hand");
        assertFalse(ItemModels.CODEC.parse(JsonOps.INSTANCE, invalid).isSuccess());
        var broken = json(ROOT.resolve(BASE + ".json"));
        broken.getAsJsonArray("elements").get(0).getAsJsonObject().add("from", JsonParser.parseString("[0,0]"));
        assertThrows(com.google.gson.JsonParseException.class,
            () -> CuboidModel.fromStream(new StringReader(broken.toString())));
    }

    @Test void everyOriginalCubeFaceUvTextureAndOrderSurvivesExactlyOnce() throws Exception {
        var source = json(ROOT.resolve(BASE + ".json"));
        assertEquals(249, source.getAsJsonArray("elements").size());
        JsonArray restored = new JsonArray();
        int bodyIndex = 0, magazineIndex = 0;
        var body = json(ROOT.resolve("models/" + KEY + "_body.json"));
        var mag = json(ROOT.resolve("models/" + KEY + "_magazine.json"));
        assertEquals(237, body.getAsJsonArray("elements").size());
        assertEquals(12, mag.getAsJsonArray("elements").size());
        for (int i = 0; i < 249; i++) restored.add(MAG.contains(i)
            ? mag.getAsJsonArray("elements").get(magazineIndex++) : body.getAsJsonArray("elements").get(bodyIndex++));
        assertEquals(source.get("elements"), restored);
        var metadata = source.deepCopy(); metadata.remove("elements"); metadata.remove("display");
        for (var geometry : List.of(body, mag)) {
            var actual = geometry.deepCopy(); actual.remove("elements");
            assertEquals(metadata, actual, "Original textures and all metadata remain exact");
        }
        assertEquals(249, bodyIndex + magazineIndex); assertTrue(bodyIndex + magazineIndex <= 256);
        var audit = json(ART.resolve("partition-audit.json"));
        assertEquals(681, audit.get("magazineTriangles").getAsInt());
        assertEquals(270, audit.getAsJsonArray("sourceComponents").size());
        var indices = audit.getAsJsonObject("parts").getAsJsonArray("magazine").asList().stream()
            .map(JsonElement::getAsInt).collect(java.util.stream.Collectors.toSet());
        assertEquals(MAG, indices);
    }

    @Test void fullOriginalGraphFallbackAndMetadataSurviveInEveryOtherContext() throws Exception {
        var original = json(ROOT.resolve("items/weapon/blast_furnace.json")); var reload = item();
        var metadata = reload.deepCopy(); metadata.add("model", original.get("model"));
        assertEquals(original, metadata);
        var select = reload.getAsJsonObject("model");
        assertEquals("minecraft:display_context", select.get("property").getAsString());
        assertEquals(original.get("model"), select.get("fallback"));
        assertEquals(1, select.getAsJsonArray("cases").size());
        var first = select.getAsJsonArray("cases").get(0).getAsJsonObject();
        assertEquals(FP, first.getAsJsonArray("when").asList().stream().map(JsonElement::getAsString).toList());
        var range = first.getAsJsonObject("model");
        assertEquals("minecraft:custom_model_data", range.get("property").getAsString());
        assertEquals(1, range.get("index").getAsInt());
        assertEquals(original.get("model"), range.get("fallback"));
    }

    @Test void all21FloatSamplesSelectDistinctNativeAndTwohandComposites() throws Exception {
        var range = item().getAsJsonObject("model").getAsJsonArray("cases").get(0).getAsJsonObject().getAsJsonObject("model");
        var entries = range.getAsJsonArray("entries"); assertEquals(21, entries.size());
        Set<String> references = new HashSet<>();
        assertEquals(-1, select(entries, -1)); assertEquals(-1, select(entries, -.001f));
        for (int i = 0; i <= 20; i++) {
            var row = entries.get(i).getAsJsonObject(); assertEquals(i / 20.0, row.get("threshold").getAsDouble(), 1e-9);
            for (float offset : new float[] {0, .0001f, .000999f, .001f}) assertEquals(i, select(entries, i/20f + offset));
            if (i > 0) assertEquals(i-1, select(entries, Math.nextDown(i/20f)));
            var condition = row.getAsJsonObject("model");
            assertEquals("minecraft:custom_model_data", condition.get("property").getAsString());
            assertEquals(0, condition.get("index").getAsInt());
            for (String grip : List.of("native", "twohand")) {
                var composite = condition.getAsJsonObject(grip.equals("native") ? "on_false" : "on_true");
                assertEquals("minecraft:composite", composite.get("type").getAsString());
                assertEquals(2, composite.getAsJsonArray("models").size());
                for (int p = 0; p < 2; p++) {
                    String expected = "destiny:" + KEY + "_" + String.format(java.util.Locale.ROOT, "%02d", i) + "_" + PARTS.get(p) + "_" + grip;
                    var leaf = composite.getAsJsonArray("models").get(p).getAsJsonObject();
                    assertEquals("minecraft:model", leaf.get("type").getAsString());
                    assertEquals(expected, leaf.get("model").getAsString()); assertTrue(references.add(expected));
                }
            }
        }
        assertEquals(84, references.size()); assertEquals(20, select(entries, 1.001f));
    }

    @Test void bothEndpointsEveryPartAndNonFirstPersonDisplayRemainExact() throws Exception {
        for (String grip : List.of("native", "twohand")) {
            var base = json(ROOT.resolve(BASE + (grip.equals("native") ? "" : "_twohand") + ".json")).getAsJsonObject("display");
            for (int frame = 0; frame <= 20; frame++) for (String part : PARTS) {
                var child = pose(frame, part, grip); assertEquals(Set.of("parent", "display"), child.keySet());
                assertEquals("destiny:" + KEY + "_" + part, child.get("parent").getAsString());
                var display = child.getAsJsonObject("display"); assertEquals(base.keySet(), display.keySet());
                if (frame == 0 || frame == 20) assertEquals(base, display, frame + "/" + part + "/" + grip);
                for (String context : base.keySet()) {
                    if (!FP.contains(context)) assertEquals(base.get(context), display.get(context));
                    for (String field : List.of("rotation", "translation", "scale")) vector(display.getAsJsonObject(context), field);
                }
            }
        }
    }

    @Test void weaponSpecificRaiseMagazineDepartureAndBothHandCarrierInverseHold() throws Exception {
        for (int frame = 0; frame <= 20; frame++) for (String part : PARTS) {
            var n = pose(frame, part, "native").getAsJsonObject("display");
            var t = pose(frame, part, "twohand").getAsJsonObject("display");
            for (boolean left : List.of(false, true)) {
                String context = FP.get(left ? 1 : 0); double sign = left ? -1 : 1;
                var parsedNative = CuboidModel.fromStream(new StringReader(pose(frame,part,"native").toString()));
                var parsedTwohand = CuboidModel.fromStream(new StringReader(pose(frame,part,"twohand").toString()));
                ItemDisplayContext nativeContext = left ? ItemDisplayContext.FIRST_PERSON_LEFT_HAND : ItemDisplayContext.FIRST_PERSON_RIGHT_HAND;
                var nativeApplied = applied(parsedNative,nativeContext,left);
                var twoApplied = applied(parsedTwohand,nativeContext,left);
                assertTrue(transform(n.getAsJsonObject(context),left).translate(-.5,-.5,-.5).equals(nativeApplied,3e-6));
                assertTrue(transform(t.getAsJsonObject(context),left).translate(-.5,-.5,-.5).equals(twoApplied,3e-6));
                assertTrue(nativeApplied.equals(new Matrix4d().translate(-.641864*sign,0,0).rotateY(Math.toRadians(10)*sign).mul(twoApplied),3e-6));
                var restored = new Matrix4d().translate(-.641864*sign, 0, 0).rotateY(Math.toRadians(10)*sign)
                    .mul(transform(t.getAsJsonObject(context), left));
                assertTrue(transform(n.getAsJsonObject(context), left).equals(restored, 3e-6), frame + "/" + context + "/" + part);
            }
        }
        for (String context : FP) {
            var b = pose(8,"body","native").getAsJsonObject("display").getAsJsonObject(context);
            var m = pose(8,"magazine","native").getAsJsonObject("display").getAsJsonObject(context);
            assertTrue(vector(b,"rotation").x > 60, "Observed steep muzzle-up phase");
            assertEquals(b.get("rotation"),m.get("rotation")); assertEquals(b.get("scale"),m.get("scale"));
            var local = vector(m,"translation").sub(vector(b,"translation"));
            transform(b,false).invert().transformDirection(local);
            assertTrue(local.distance(new Vector3d(.2,-5.8,.35)) < 3e-6, "Authored local lower-magazine travel");
        }
        assertEquals(pose(15,"body","native").get("display"),pose(15,"magazine","native").get("display"),"Reseated before ready return");
    }

    @Test void literalOriginalPinsAndManifestHashesIncludeEveryAssetAndReference() throws Exception {
        assertEquals("f3922a28cc58de8c7a7f965ba3464aeb5841d1a53bde72bf74d58e48aca39706", sha(ROOT.resolve(BASE + ".json")));
        assertEquals("0f252ca03244d8b2d7d5c63e9d67c90dc87e6bbac3faeb402572aacb7df4cd91",sha(ROOT.resolve("textures/item/weapon/w30/blast_furnace.png")));
        var manifest = json(ART.resolve("manifest.json"));
        assertEquals("destiny:" + KEY,manifest.get("graphId").getAsString());
        assertEquals(87,manifest.getAsJsonObject("sha256").size());
        assertFalse(manifest.get("nativeGameplayVerified").getAsBoolean());
        var fidelity = manifest.getAsJsonObject("partitionFidelity");
        assertFalse(fidelity.get("perfectMagazineExtraction").getAsBoolean());
        assertEquals(.5380997968281779,fidelity.get("capturedRawMagazineFraction").getAsDouble(),1e-8);
        assertEquals(.5835779763155177,fidelity.get("capturedClippedMagazineFraction").getAsDouble(),1e-8);
        assertEquals(8,fidelity.getAsJsonArray("mixedSelected").size());
        assertEquals(6,fidelity.getAsJsonArray("retainedMixedIndices").size());
        assertFalse(manifest.get("sourceAnimationRecovered").getAsBoolean()); assertFalse(manifest.get("handIK").getAsBoolean());
        for (String key : List.of("sha256","originalSha256","referenceSha256","evidenceSha256"))
            for (var entry : manifest.getAsJsonObject(key).entrySet()) assertEquals(entry.getValue().getAsString(),sha(Path.of(entry.getKey())),entry.getKey());
        var provenance = json(ART.resolve("gameplay-provenance.json")); assertEquals(16,provenance.getAsJsonArray("frames").size());
        assertEquals(38.7,provenance.getAsJsonArray("frames").get(0).getAsJsonObject().get("seekSeconds").getAsDouble(),1e-8);
        assertEquals(40.95,provenance.getAsJsonArray("frames").get(15).getAsJsonObject().get("seekSeconds").getAsDouble(),1e-8);
        assertTrue(Files.readString(ART.resolve("reference-notes.md")).contains("BRAVE"));
    }

    private static JsonObject json(Path path) throws Exception { return JsonParser.parseString(Files.readString(path)).getAsJsonObject(); }
    private static JsonObject item() throws Exception { return json(ROOT.resolve("items/" + KEY + ".json")); }
    private static JsonObject pose(int frame,String part,String grip) throws Exception {
        return json(ROOT.resolve("models/" + KEY + "_" + String.format(java.util.Locale.ROOT,"%02d",frame) + "_" + part + "_" + grip + ".json"));
    }
    private static Set<Path> expectedAssets() {
        Set<Path> out = new HashSet<>(); out.add(ROOT.resolve("items/" + KEY + ".json"));
        for (String part : PARTS) {
            out.add(ROOT.resolve("models/" + KEY + "_" + part + ".json"));
            for (int i=0;i<=20;i++) for (String grip : List.of("native","twohand"))
                out.add(ROOT.resolve("models/" + KEY + "_" + String.format(java.util.Locale.ROOT,"%02d",i) + "_" + part + "_" + grip + ".json"));
        }
        return out;
    }
    private static int select(JsonArray entries,float progress) {
        int selected=-1;
        for (int i=0;i<entries.size();i++) if(entries.get(i).getAsJsonObject().get("threshold").getAsFloat()<=progress) selected=i;
        return selected;
    }
    private static String sha(Path path) throws Exception { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(path))); }
    private static Vector3d vector(JsonObject pose,String field) {
        var a=pose.getAsJsonArray(field);assertEquals(3,a.size());
        for (var v:a) {
            assertTrue(Double.isFinite(v.getAsDouble()) && Float.isFinite(v.getAsFloat()));
            if(field.equals("translation")) assertTrue(Math.abs(v.getAsDouble())<=80);
            if(field.equals("scale")) assertTrue(v.getAsDouble()>0 && v.getAsDouble()<=4);
        }
        return new Vector3d(a.get(0).getAsDouble(),a.get(1).getAsDouble(),a.get(2).getAsDouble());
    }
    private static Matrix4d applied(CuboidModel model,ItemDisplayContext context,boolean left) {
        PoseStack stack = new PoseStack();model.transforms().getTransform(context).apply(left,stack.last());
        return new Matrix4d(stack.last().pose());
    }
    private static Matrix4d transform(JsonObject pose,boolean left) {
        var r=vector(pose,"rotation").mul(Math.PI/180);var t=vector(pose,"translation").div(16);var s=vector(pose,"scale");
        double sign=left?-1:1;
        return new Matrix4d().translate(t.x*sign,t.y,t.z).rotateXYZ(r.x,r.y*sign,r.z*sign).scale(s.x,s.y,s.z);
    }
}
