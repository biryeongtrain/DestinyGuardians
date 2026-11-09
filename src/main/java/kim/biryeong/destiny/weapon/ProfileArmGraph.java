package kim.biryeong.destiny.weapon;

import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import net.minecraft.world.item.component.CustomModelData;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Set;

/** Pure projection/evaluation of native item-model selectors for the PROFILE arm carrier.
 * Pass the item definition's {@code model} object, not the enclosing item definition.
 * No registry bootstrap, world, profile lookup, matrix conversion or pack writes are needed. */
public final class ProfileArmGraph {
    private static final String POSES = "destiny:skin_arm_w204/poses/";
    private static final String CMD = "minecraft:custom_model_data";
    private static final String CONTEXT = "minecraft:display_context";
    private static final Set<String> CONTEXTS = Set.of("none", "thirdperson_lefthand", "thirdperson_righthand",
            "firstperson_lefthand", "firstperson_righthand", "head", "gui", "ground", "fixed", "on_shelf");

    private ProfileArmGraph() {}
    /** Weapon-owned W350 pose leaves inherit the same W204 arm geometry and tint contract. */
    public static boolean armPose(String id) {
        return id.startsWith(POSES) || id.startsWith("destiny:weapon_hands_w350/")
                || id.startsWith("destiny:weapon_w350/") && id.contains("/hands/");
    }

    /** Returns a detached, tint-free native graph; rejects unsupported selectors even in dead branches.
     * Thresholds must already be finite and strictly increasing in native Float.compare order.
     * Missing fallbacks project to empty (native's missing-model diagnostic contains no arm poses). */
    public static JsonObject armsOnly(JsonObject source) {
        Objects.requireNonNull(source, "source");
        String type = string(source, "type");
        return switch (type) {
            case "minecraft:empty" -> {
                fields(source, "type", "transformation");
                yield empty();
            }
            case "minecraft:model" -> {
                fields(source, "type", "model", "tints", "transformation");
                String model = string(source, "model");
                if (!armPose(model)) yield empty();
                yield shell(source, "tints");
            }
            case "minecraft:composite" -> composite(source);
            case "minecraft:condition" -> condition(source);
            case "minecraft:select" -> compileSelect(source);
            case "minecraft:range_dispatch" -> range(source);
            default -> throw invalid("Unsupported model type: " + type);
        };
    }

    /** Evaluates a graph produced by armsOnly, retaining composite order and duplicate leaves.
     * flags[8] is virtually true and flags[9] is slim; null data means a missing CMD component.
     * leftHand only chooses firstperson_lefthand; the caller owns native matrix conversion.
     * The returned list is immutable. No input JSON or CMD list is changed. */
    public static List<String> select(JsonObject graph, CustomModelData data, boolean slim, boolean leftHand) {
        Objects.requireNonNull(graph, "graph");
        var result = new ArrayList<String>(4);
        evaluate(graph, data, slim, leftHand, result);
        return List.copyOf(result);
    }

    private static JsonObject composite(JsonObject source) {
        fields(source, "type", "models", "transformation");
        var models = new JsonArray();
        for (var child : array(source, "models")) {
            var compiled = armsOnly(object(child));
            if (isEmpty(compiled)) continue;
            if (string(compiled, "type").equals("minecraft:composite") && !compiled.has("transformation"))
                compiled.getAsJsonArray("models").forEach(models::add);
            else models.add(compiled);
        }
        if (models.isEmpty()) return empty();
        if (models.size() == 1 && !source.has("transformation")) return object(models.get(0));
        var out = shell(source, "models");
        out.add("models", models);
        return out;
    }

    private static JsonObject condition(JsonObject source) {
        fields(source, "type", "property", "index", "on_true", "on_false", "transformation");
        conditionIndex(source);
        var yes = armsOnly(object(source.get("on_true")));
        var no = armsOnly(object(source.get("on_false")));
        if (yes.equals(no) && !source.has("transformation")) return yes;
        var out = shell(source, "on_true", "on_false");
        out.add("on_true", yes);
        out.add("on_false", no);
        return out;
    }

    private static JsonObject compileSelect(JsonObject source) {
        fields(source, "type", "property", "index", "cases", "fallback", "transformation");
        String property = selectProperty(source);
        var fallback = fallback(source);
        var cases = new JsonArray();
        var seen = new HashSet<String>();
        for (var value : array(source, "cases")) {
            var entry = object(value);
            fields(entry, "when", "model");
            var labels = labels(entry.get("when"));
            for (var label : labels) {
                String key = label.getAsString();
                if (!seen.add(key)) throw invalid("Duplicate select case: " + key);
                if (property.equals(CONTEXT) && !CONTEXTS.contains(key))
                    throw invalid("Unsupported display context: " + key);
            }
            var model = armsOnly(object(entry.get("model")));
            if (model.equals(fallback)) continue;
            JsonObject group = null;
            for (var existing : cases)
                if (object(existing).get("model").equals(model)) { group = object(existing); break; }
            if (group == null) {
                group = new JsonObject();
                group.add("when", labels);
                group.add("model", model);
                cases.add(group);
            } else labels.forEach(group.getAsJsonArray("when")::add);
        }
        if (cases.isEmpty() && !source.has("transformation")) return fallback;
        var out = shell(source, "cases", "fallback");
        out.add("cases", cases);
        out.add("fallback", fallback);
        return out;
    }

    private static JsonObject range(JsonObject source) {
        fields(source, "type", "property", "index", "scale", "entries", "fallback", "transformation");
        rangeIndex(source);
        scale(source);
        var entries = array(source, "entries");
        float[] thresholds = thresholds(entries); // Validate BEFORE dropping redundant branches.
        var fallback = fallback(source);
        var all = new JsonArray();
        var reduced = new JsonArray();
        JsonObject previous = fallback;
        boolean hasZero = false;
        for (int i = 0; i < entries.size(); i++) {
            var entry = object(entries.get(i));
            fields(entry, "threshold", "model");
            var model = armsOnly(object(entry.get("model")));
            var compiled = new JsonObject();
            compiled.addProperty("threshold", thresholds[i]);
            compiled.add("model", model);
            all.add(compiled);
            if (!model.equals(previous)) reduced.add(compiled);
            previous = model;
            hasZero |= thresholds[i] == 0f;
        }
        if (reduced.isEmpty() && !source.has("transformation")) return fallback;
        // Native uses > comparisons below 16 entries, Arrays.binarySearch at 16+.
        // Crossing that boundary changes -0.0 versus +0.0 behavior; retain the original entries.
        if (hasZero && entries.size() >= 16 && reduced.size() < 16) reduced = all;
        var out = shell(source, "entries", "fallback");
        out.add("entries", reduced);
        out.add("fallback", fallback);
        return out;
    }

    private static void evaluate(JsonObject node, CustomModelData data, boolean slim, boolean left,
                                 List<String> result) {
        switch (string(node, "type")) {
            case "minecraft:empty" -> { }
            case "minecraft:model" -> {
                String model = string(node, "model");
                if (armPose(model)) result.add(model);
            }
            case "minecraft:composite" -> {
                for (var child : array(node, "models")) evaluate(object(child), data, slim, left, result);
            }
            case "minecraft:condition" -> {
                int index = conditionIndex(node);
                boolean flag = index == 8 || (index == 9 ? slim
                        : data != null && index < data.flags().size() && Boolean.TRUE.equals(data.flags().get(index)));
                evaluate(object(node.get(flag ? "on_true" : "on_false")), data, slim, left, result);
            }
            case "minecraft:select" -> {
                String property = selectProperty(node);
                String key = property.equals(CONTEXT) ? (left ? "firstperson_lefthand" : "firstperson_righthand")
                        : data == null || data.strings().isEmpty() ? null : data.strings().getFirst();
                JsonObject selected = null;
                for (var value : array(node, "cases")) {
                    var entry = object(value);
                    for (var label : labels(entry.get("when")))
                        if (label.getAsString().equals(key)) selected = object(entry.get("model"));
                }
                if (selected != null) evaluate(selected, data, slim, left, result);
                else evaluateFallback(node, data, slim, left, result);
            }
            case "minecraft:range_dispatch" -> {
                int index = rangeIndex(node);
                float value = data == null || index >= data.floats().size() ? 0f : data.floats().get(index);
                value *= scale(node);
                var entries = array(node, "entries");
                float[] thresholds = thresholds(entries);
                int selected = -1;
                if (!Float.isNaN(value)) {
                    if (thresholds.length < 16) {
                        while (selected + 1 < thresholds.length && !(thresholds[selected + 1] > value)) selected++;
                    } else {
                        int found = Arrays.binarySearch(thresholds, value);
                        selected = found >= 0 ? found : -found - 2;
                    }
                }
                if (selected < 0) evaluateFallback(node, data, slim, left, result);
                else evaluate(object(object(entries.get(selected)).get("model")), data, slim, left, result);
            }
            default -> throw invalid("Unsupported model type: " + string(node, "type"));
        }
    }

    private static void evaluateFallback(JsonObject node, CustomModelData data, boolean slim, boolean left,
                                         List<String> result) {
        if (node.has("fallback")) evaluate(object(node.get("fallback")), data, slim, left, result);
    }

    private static int conditionIndex(JsonObject node) {
        cmd(node);
        int index = index(node);
        if (index != 0 && index != 1 && index != 8 && index != 9)
            throw invalid("Unsupported CMD flag index: " + index);
        return index;
    }

    private static int rangeIndex(JsonObject node) {
        cmd(node);
        int index = index(node);
        if (index < 1 || index > 6) throw invalid("Unsupported CMD float index: " + index);
        return index;
    }

    private static String selectProperty(JsonObject node) {
        String property = string(node, "property");
        if (property.equals(CMD)) {
            if (index(node) != 0) throw invalid("Only CMD string index 0 is supported");
        } else if (!property.equals(CONTEXT) || node.has("index"))
            throw invalid("Unsupported select property/index: " + property);
        return property;
    }

    private static void cmd(JsonObject node) {
        if (!string(node, "property").equals(CMD)) throw invalid("Expected CMD property");
    }

    private static int index(JsonObject node) {
        if (!node.has("index")) return 0;
        var element = node.get("index");
        if (!element.isJsonPrimitive() || !element.getAsJsonPrimitive().isNumber())
            throw invalid("Expected integer index");
        try { return element.getAsBigDecimal().intValueExact(); }
        catch (ArithmeticException | NumberFormatException e) { throw invalid("Expected integer index"); }
    }

    private static float scale(JsonObject node) {
        return node.has("scale") ? number(node, "scale") : 1f;
    }

    private static float[] thresholds(JsonArray entries) {
        float[] values = new float[entries.size()];
        for (int i = 0; i < values.length; i++) {
            values[i] = number(object(entries.get(i)), "threshold");
            if (!Float.isFinite(values[i])) throw invalid("Expected finite threshold");
            if (i > 0 && Float.compare(values[i - 1], values[i]) >= 0)
                throw invalid("Thresholds must be strictly increasing (including after float conversion)");
        }
        return values;
    }

    private static float number(JsonObject node, String key) {
        var value = node.get(key);
        if (value == null || !value.isJsonPrimitive() || !value.getAsJsonPrimitive().isNumber())
            throw invalid("Expected number: " + key);
        return value.getAsFloat();
    }

    private static JsonArray labels(JsonElement when) {
        var out = new JsonArray();
        if (when != null && when.isJsonArray()) when.getAsJsonArray().forEach(out::add);
        else if (when != null) out.add(when);
        if (out.isEmpty()) throw invalid("Select when must contain at least one string");
        for (var label : out)
            if (!label.isJsonPrimitive() || !label.getAsJsonPrimitive().isString())
                throw invalid("Select when must be a string or array of strings");
        return out.deepCopy();
    }

    private static JsonObject fallback(JsonObject node) {
        return node.has("fallback") ? armsOnly(object(node.get("fallback"))) : empty();
    }

    private static JsonObject shell(JsonObject source, String... excluded) {
        var out = new JsonObject();
        var skip = Set.of(excluded);
        for (var entry : source.entrySet())
            if (!skip.contains(entry.getKey())) out.add(entry.getKey(), entry.getValue().deepCopy());
        return out;
    }

    private static void fields(JsonObject node, String... allowed) {
        var keys = Set.of(allowed);
        for (String key : node.keySet())
            if (!keys.contains(key)) throw invalid("Unsupported field: " + key);
    }

    private static JsonArray array(JsonObject node, String key) {
        var value = node.get(key);
        if (value == null || !value.isJsonArray()) throw invalid("Expected array: " + key);
        return value.getAsJsonArray();
    }

    private static JsonObject object(JsonElement value) {
        if (value == null || !value.isJsonObject()) throw invalid("Expected model/entry object");
        return value.getAsJsonObject();
    }

    private static String string(JsonObject node, String key) {
        var value = node.get(key);
        if (value == null || !value.isJsonPrimitive() || !value.getAsJsonPrimitive().isString())
            throw invalid("Expected string: " + key);
        return value.getAsString();
    }

    private static boolean isEmpty(JsonObject node) { return string(node, "type").equals("minecraft:empty"); }
    private static JsonObject empty() {
        var node = new JsonObject();
        node.addProperty("type", "minecraft:empty");
        return node;
    }
    private static IllegalArgumentException invalid(String message) {
        return new IllegalArgumentException("ProfileArmGraph: " + message);
    }
}
