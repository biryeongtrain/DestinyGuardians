package kim.biryeong.destiny.compat.pack;

import com.google.gson.*;
import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.serialization.JsonOps;
import eu.pb4.polymer.resourcepack.api.PackResource;
import net.minecraft.client.resources.model.cuboid.ItemTransform;
import net.minecraft.util.ExtraCodecs;
import org.joml.Matrix4f;
import org.junit.jupiter.api.Test;
import java.util.*;
import static org.junit.jupiter.api.Assertions.*;

class SharedArmGeometryTest {
    @Test void matrixMatchesNativeDisplayIncludingLeftHandAndClamping() throws Exception {
        var ctor = Class.forName("net.minecraft.client.resources.model.cuboid.ItemTransform$Deserializer").getDeclaredConstructor();
        ctor.setAccessible(true);
        var gson = new GsonBuilder().registerTypeAdapter(ItemTransform.class, ctor.newInstance()).create();
        for (String json : List.of("{}",
                "{\"rotation\":[52.89388103,50.67622053,-87.31195801],\"scale\":[0.84875097,1.06307559,0.84875097],\"translation\":[7.18762062,1.03499318,-3.50995967]}",
                "{\"rotation\":[179,-77,83],\"scale\":[8,-9,0.5],\"translation\":[900,-700,25]}")) {
            var display = JsonParser.parseString(json).getAsJsonObject();
            var nativeTransform = gson.fromJson(display, ItemTransform.class);
            for (boolean left : List.of(false, true)) {
                var nativePose = new PoseStack(); nativeTransform.apply(left, nativePose.last());
                var computed = SharedArmGeometry.displayMatrix(display, left);
                assertTrue(nativePose.last().pose().equals(computed, 0.000004f), json + " left=" + left);
                // Actual output path: native identity display followed by a matrix decoded with the native codec.
                var encoded = ExtraCodecs.MATRIX4F.encodeStart(JsonOps.INSTANCE,
                        new Matrix4f().translation(.5f,.5f,.5f).mul(computed)).getOrThrow();
                var restored = ExtraCodecs.MATRIX4F.parse(JsonOps.INSTANCE, encoded).getOrThrow();
                var result = new Matrix4f().translation(-.5f,-.5f,-.5f).mul(restored);
                assertTrue(nativePose.last().pose().equals(result, 0.000004f));
            }
        }
    }

    @Test void sharedMeshRetainsPixelTintsAndBothDisplayContexts() {
        var pose = JsonParser.parseString("{\"parent\":\"destiny:skin_arm_w204/right_classic\",\"display\":{\"firstperson_righthand\":{\"translation\":[1,2,3]},\"firstperson_lefthand\":{\"translation\":[-3,2,1]}}}").getAsJsonObject();
        var files = Map.of("assets/destiny/models/skin_arm_w204/poses/test.json", PackResource.fromString(pose.toString()),
                "assets/destiny/models/skin_arm_w204/right_classic.json", PackResource.fromString("{\"elements\":[]}"));
        var leaf = JsonParser.parseString("{\"type\":\"minecraft:model\",\"model\":\"destiny:skin_arm_w204/poses/test\",\"tints\":[{\"type\":\"minecraft:custom_model_data\",\"index\":64,\"default\":16777215}]}").getAsJsonObject();
        var shared = new SharedArmGeometry(files);
        var rewritten = shared.rewrite(leaf);
        assertEquals(1, shared.rewritten);
        assertEquals(1, rewritten.getAsJsonArray("cases").size());
        for (var c : rewritten.getAsJsonArray("cases")) {
            var model = c.getAsJsonObject().getAsJsonObject("model");
            assertEquals("destiny:skin_arm_w204/poses/test", model.get("model").getAsString());
            assertEquals(leaf.get("tints"), model.get("tints"));
            assertTrue(model.has("transformation"));
        }
        assertEquals(leaf, rewritten.get("fallback"));
    }

    @Test void posesShareAnchorOnlyWhenBothHandMatricesAgree() {
        var files = new HashMap<String, PackResource>();
        files.put("assets/destiny/models/skin_arm_w204/right_classic.json", PackResource.fromString("{\"elements\":[]}"));
        for (int frame = 0; frame < 3; frame++) {
            String pose = "{\"parent\":\"destiny:skin_arm_w204/right_classic\",\"display\":{"
                    + "\"firstperson_righthand\":{\"translation\":[" + frame + ",0,0]},"
                    + "\"firstperson_lefthand\":{\"translation\":[" + (-frame + (frame == 2 ? 4 : 0)) + ",0,0]}}}";
            files.put("assets/destiny/models/skin_arm_w204/poses/p" + frame + ".json", PackResource.fromString(pose));
        }
        var shared = new SharedArmGeometry(files);
        for (int frame = 0; frame < 3; frame++) {
            var leaf = new JsonObject(); leaf.addProperty("type", "minecraft:model");
            leaf.addProperty("model", "destiny:skin_arm_w204/poses/p" + frame);
            var result = shared.rewrite(leaf).getAsJsonArray("cases").get(0).getAsJsonObject().getAsJsonObject("model");
            assertEquals("destiny:skin_arm_w204/poses/p" + (frame == 2 ? 2 : 0), result.get("model").getAsString());
            var matrix = ExtraCodecs.MATRIX4F.parse(JsonOps.INSTANCE, result.get("transformation")).getOrThrow();
            var anchor = JsonParser.parseString(files.get(WeaponPackOptimizer.modelPath(result.get("model").getAsString())).asString()).getAsJsonObject();
            var original = JsonParser.parseString(files.get("assets/destiny/models/skin_arm_w204/poses/p" + frame + ".json").asString()).getAsJsonObject();
            for (boolean left : List.of(false, true)) {
                String context = left ? "firstperson_lefthand" : "firstperson_righthand";
                assertTrue(new Matrix4f(SharedArmGeometry.displayMatrix(anchor.getAsJsonObject("display").getAsJsonObject(context), left))
                        .mul(matrix).equals(SharedArmGeometry.displayMatrix(original.getAsJsonObject("display").getAsJsonObject(context), left), 0.00002f));
            }
        }
    }

    @Test void unsupportedGeometryAndExistingTransformsKeepOriginalPath() {
        var files = Map.of("assets/destiny/models/skin_arm_w204/poses/test.json",
                PackResource.fromString("{\"parent\":\"destiny:future_mesh\",\"display\":{}}"));
        var leaf = JsonParser.parseString("{\"type\":\"minecraft:model\",\"model\":\"destiny:skin_arm_w204/poses/test\"}").getAsJsonObject();
        var shared = new SharedArmGeometry(files);
        assertEquals(leaf, shared.rewrite(leaf.deepCopy()));
        assertEquals(0, shared.rewritten);
        leaf.add("transformation", new JsonArray());
        assertEquals(leaf, shared.rewrite(leaf.deepCopy()));
    }
}
