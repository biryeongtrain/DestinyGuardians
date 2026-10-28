package kim.biryeong.destiny.compat.pack;

import com.google.gson.*;
import eu.pb4.polymer.resourcepack.api.PackResource;
import net.minecraft.util.ExtraCodecs;
import com.mojang.serialization.JsonOps;
import org.joml.Matrix4f;
import org.joml.Quaternionf;
import org.joml.Vector3f;
import java.util.*;

/** Share arm geometry using native local matrices; retain both native hand display transforms. */
final class SharedArmGeometry {
    private final Map<String, PackResource> files;
    private final Map<String, JsonObject> replacements = new HashMap<>();
    private record Anchor(String model, Matrix4f right, Matrix4f left) {}
    private final Map<String, List<Anchor>> anchors = new HashMap<>();
    int rewritten;
    SharedArmGeometry(Map<String, PackResource> files) { this.files = files; }

    JsonObject rewrite(JsonObject node) {
        if (node.has("type") && node.get("type").getAsString().equals("minecraft:model") && node.has("model")) {
            String path = WeaponPackOptimizer.modelPath(node.get("model").getAsString());
            if (path.startsWith("assets/destiny/models/skin_arm_w204/poses/") && !node.has("transformation")) {
                var pose = replacements.computeIfAbsent(path, this::pose);
                if (pose.size() == 0) return node; // Future, unsupported source shapes retain their original renderer.
                var leaf = node.deepCopy();
                leaf.add("model", pose.get("model")); leaf.add("transformation", pose.get("transformation"));
                var select = new JsonObject(); select.addProperty("type", "minecraft:select");
                select.addProperty("property", "minecraft:display_context");
                var cases = new JsonArray(); var entry = new JsonObject();
                var contexts = new JsonArray(); contexts.add("firstperson_righthand"); contexts.add("firstperson_lefthand");
                entry.add("when", contexts); entry.add("model", leaf); cases.add(entry);
                select.add("cases", cases);
                // Outside first person the exact original model remains authoritative.
                select.add("fallback", node);
                rewritten++;
                return select;
            }
            return node;
        }
        for (String key : List.of("fallback", "on_true", "on_false"))
            if (node.has(key)) node.add(key, rewrite(node.getAsJsonObject(key)));
        for (String key : List.of("entries", "cases")) if (node.has(key))
            for (var entry : node.getAsJsonArray(key)) {
                var c = entry.getAsJsonObject(); c.add("model", rewrite(c.getAsJsonObject("model")));
            }
        if (node.has("type") && node.get("type").getAsString().equals("minecraft:composite")) {
            var out = new JsonArray();
            for (var child : node.getAsJsonArray("models")) out.add(rewrite(child.getAsJsonObject()));
            node.add("models", out);
        }
        return node;
    }

    private JsonObject pose(String path) {
        var data = files.get(path);
        if (data == null) throw new IllegalStateException("Missing arm pose: " + path);
        var pose = JsonParser.parseString(data.asString()).getAsJsonObject();
        if (pose.size() != 2 || !pose.has("parent") || !pose.has("display")) return new JsonObject();
        String parent = pose.get("parent").getAsString();
        if (!parent.matches("destiny:skin_arm_w204/(left|right)(_upper)?_(classic|slim)")) return new JsonObject();
        var baseResource = files.get(WeaponPackOptimizer.modelPath(parent));
        if (baseResource == null) throw new IllegalStateException("Missing shared skin mesh: " + parent);
        var base = JsonParser.parseString(baseResource.asString()).getAsJsonObject();
        if (base.has("display") || base.has("parent")) return new JsonObject();
        var display = pose.getAsJsonObject("display");
        if (!display.has("firstperson_righthand") || !display.has("firstperson_lefthand")) return new JsonObject();
        var right = displayMatrix(display.getAsJsonObject("firstperson_righthand"), false);
        var left = displayMatrix(display.getAsJsonObject("firstperson_lefthand"), true);
        // C = left * inverse(right) is constant for poses with the same camera framing.
        // Quantization only chooses candidates; BOTH native matrices are checked before reuse.
        var relation = new Matrix4f(left).mul(new Matrix4f(right).invert());
        float[] values = relation.get(new float[16]);
        StringBuilder key = new StringBuilder(parent);
        for (float value : values) key.append(':').append(Math.round(value * 1000));
        var candidates = anchors.computeIfAbsent(key.toString(), k -> new ArrayList<>());
        for (var anchor : candidates) {
            var local = new Matrix4f(anchor.right).invert().mul(right);
            if (new Matrix4f(anchor.right).mul(local).equals(right, 0.00002f)
                    && new Matrix4f(anchor.left).mul(local).equals(left, 0.00002f)) {
                var result = new JsonObject(); result.addProperty("model", anchor.model);
                result.add("transformation", ExtraCodecs.MATRIX4F.encodeStart(JsonOps.INSTANCE, local).getOrThrow());
                return result;
            }
        }
        String model = path.substring("assets/destiny/models/".length(), path.length() - 5);
        candidates.add(new Anchor("destiny:" + model, right, left));
        var result = new JsonObject(); result.addProperty("model", "destiny:" + model);
        result.add("transformation", ExtraCodecs.MATRIX4F.encodeStart(JsonOps.INSTANCE, new Matrix4f()).getOrThrow());
        return result;
    }

    /** Exact 26.3 ItemTransform.Deserializer/apply order, including left-hand signs and clamps. */
    static Matrix4f displayMatrix(JsonObject display, boolean left) {
        var rotation = vector(display, "rotation", 0);
        var translation = vector(display, "translation", 0).mul(1f / 16);
        translation.set(clamp(translation.x, 5), clamp(translation.y, 5), clamp(translation.z, 5));
        var scale = vector(display, "scale", 1);
        scale.set(clamp(scale.x, 4), clamp(scale.y, 4), clamp(scale.z, 4));
        if (left) { translation.x = -translation.x; rotation.y = -rotation.y; rotation.z = -rotation.z; }
        var quaternion = new Quaternionf().rotationXYZ(rotation.x * .017453292f,
                rotation.y * .017453292f, rotation.z * .017453292f);
        return new Matrix4f().translation(translation).rotate(quaternion).scale(scale).translate(-.5f, -.5f, -.5f);
    }

    private static float clamp(float value, float limit) { return Math.max(-limit, Math.min(limit, value)); }
    private static Vector3f vector(JsonObject object, String key, float defaultValue) {
        if (!object.has(key)) return new Vector3f(defaultValue);
        var v = object.getAsJsonArray(key);
        if (v.size() != 3) throw new IllegalArgumentException("Invalid display vector: " + key);
        return new Vector3f(v.get(0).getAsFloat(), v.get(1).getAsFloat(), v.get(2).getAsFloat());
    }
}
