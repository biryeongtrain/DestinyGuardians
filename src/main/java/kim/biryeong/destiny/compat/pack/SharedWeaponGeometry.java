package kim.biryeong.destiny.compat.pack;

import com.google.gson.*;
import com.mojang.math.Transformation;
import com.mojang.serialization.JsonOps;
import eu.pb4.polymer.resourcepack.api.PackResource;
import eu.pb4.polymer.resourcepack.api.ResourcePackBuilder;
import net.minecraft.util.ExtraCodecs;
import org.joml.Matrix4f;
import java.util.*;

/** Shares geometry of display-only weapon poses. All pose frames and materials remain intact. */
final class SharedWeaponGeometry {
    static final List<String> CONTEXTS = List.of("thirdperson_righthand", "thirdperson_lefthand",
            "firstperson_righthand", "firstperson_lefthand", "head", "gui", "ground", "fixed", "on_shelf");
    private final Map<String, PackResource> files;
    private int replaced;

    SharedWeaponGeometry(Map<String, PackResource> files) { this.files = files; }

    static int compact(ResourcePackBuilder builder, Map<String, PackResource> files, Set<String> omitted) {
        var sharing = new SharedWeaponGeometry(files);
        for (String path : new TreeSet<>(files.keySet())) {
            if (!path.startsWith("assets/destiny/items/") || !path.endsWith(".json") || omitted.contains(path)) continue;
            var item = JsonParser.parseString(files.get(path).asString()).getAsJsonObject();
            if (!item.has("model")) continue;
            int before = sharing.replaced;
            item.add("model", sharing.rewrite(item.getAsJsonObject("model")));
            if (sharing.replaced == before) continue;
            item.add("model", WeaponPackOptimizer.specialize(item.getAsJsonObject("model")));
            var resource = PackResource.fromString(item.toString());
            files.put(path, resource); builder.addData(path, resource);
        }
        return sharing.replaced;
    }

    JsonObject rewrite(JsonObject node) {
        String type = node.has("type") ? node.get("type").getAsString() : "";
        if (type.equals("minecraft:model")) return leaf(node);
        // An ancestor matrix precedes the leaf matrix. Do not commute it through a display transform.
        if (node.has("transformation")) return node;
        for (String key : List.of("fallback", "on_true", "on_false"))
            if (node.has(key)) node.add(key, rewrite(node.getAsJsonObject(key)));
        for (String key : List.of("entries", "cases")) if (node.has(key))
            for (var raw : node.getAsJsonArray(key)) {
                var entry = raw.getAsJsonObject(); entry.add("model", rewrite(entry.getAsJsonObject("model")));
            }
        if (type.equals("minecraft:composite")) {
            var children = new JsonArray();
            for (var child : node.getAsJsonArray("models")) children.add(rewrite(child.getAsJsonObject()));
            node.add("models", children);
        }
        return node;
    }

    private JsonObject leaf(JsonObject node) {
        String id = node.get("model").getAsString();
        if (!id.startsWith("destiny:weapon") && !id.startsWith("destiny:first_person_framing_w205/")) return node;
        var chain = new ArrayList<JsonObject>();
        var seen = new HashSet<String>();
        String root = id;
        while (seen.add(root)) {
            var resource = files.get(WeaponPackOptimizer.modelPath(root));
            if (resource == null) return node;
            var model = JsonParser.parseString(resource.asString()).getAsJsonObject();
            chain.add(model);
            if (!model.has("parent") || !Set.of("parent", "display", "credit").containsAll(model.keySet())) break;
            root = model.get("parent").getAsString();
        }
        if (root.equals(id) || !root.startsWith("destiny:") || chain.size() < 2) return node;
        var base = chain.getLast();
        // Resolve only self-contained vanilla cube roots, never custom loaders or unknown parents.
        if (base.has("parent") || !base.has("elements") || !Set.of("elements", "textures", "display", "credit",
                "ambientocclusion", "gui_light", "texture_size").containsAll(base.keySet())) return node;
        Matrix4f original = new Matrix4f();
        if (node.has("transformation")) {
            var parsed = Transformation.EXTENDED_CODEC.parse(JsonOps.INSTANCE, node.get("transformation")).result();
            if (parsed.isEmpty()) return node;
            original.set(parsed.get().getMatrix());
        }
        var cases = new JsonArray();
        for (String context : CONTEXTS) {
            var from = matrix(List.of(base), context);
            var target = matrix(chain, context);
            if (!Float.isFinite(from.determinant()) || Math.abs(from.determinant()) < 1e-8f) return node;
            var local = new Matrix4f(from).invert().mul(target).mul(original);
            if (!local.isFinite() || !new Matrix4f(from).mul(local).equals(new Matrix4f(target).mul(original), .00005f)) return node;
            var value = node.deepCopy(); value.addProperty("model", root);
            value.add("transformation", ExtraCodecs.MATRIX4F.encodeStart(JsonOps.INSTANCE, local).getOrThrow());
            var entry = new JsonObject(); entry.addProperty("when", context); entry.add("model", value); cases.add(entry);
        }
        // NONE has no model display transform on either side; keep the existing local matrix exactly.
        var fallback = node.deepCopy(); fallback.addProperty("model", root);
        var result = new JsonObject(); result.addProperty("type", "minecraft:select");
        result.addProperty("property", "minecraft:display_context"); result.add("cases", cases); result.add("fallback", fallback);
        replaced++; return result;
    }

    static Matrix4f matrix(List<JsonObject> chain, String context) {
        for (var model : chain) {
            var display = model.getAsJsonObject("display");
            if (display == null) continue;
            String key = context;
            // Vanilla fills a missing left-hand transform from this model's right hand before inheritance.
            if (!display.has(key) && key.endsWith("_lefthand")) key = key.replace("_lefthand", "_righthand");
            if (display.has(key)) return SharedArmGeometry.displayMatrix(display.getAsJsonObject(key), context.endsWith("_lefthand"));
        }
        return new Matrix4f().translation(-.5f, -.5f, -.5f);
    }
}
