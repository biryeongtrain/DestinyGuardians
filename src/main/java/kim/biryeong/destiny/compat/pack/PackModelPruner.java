package kim.biryeong.destiny.compat.pack;

import com.google.gson.JsonElement;
import com.google.gson.JsonParser;
import eu.pb4.polymer.resourcepack.api.PackResource;

import java.util.ArrayDeque;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;
import java.util.regex.Pattern;

/** Output-only reachability pruning of versioned Destiny weapon models. */
public final class PackModelPruner {
    private static final Pattern MODEL = Pattern.compile("assets/[^/]+/models/.+\\.json");
    private static final Pattern WEAPON = Pattern.compile(
            "assets/destiny/models/(?:item/)?weapon_[a-z0-9_]+_w[0-9]+(?:_[a-z0-9_]+)?/.+\\.json");
    private static final Set<String> MODEL_REFERENCE_KEYS = Set.of("parent", "model", "base");
    private static final String FRAMING = "assets/destiny/models/first_person_framing_w205/";

    private PackModelPruner() {}

    /**
     * Adds unreachable model paths to {@code omitted}; never edits resources or removes exclusions.
     * Call after item/model rewrites, with their updated resources in {@code files}, and before
     * freezing the converter's exclusion set. Already omitted resources do not act as roots.
     * Every retained JSON (all namespaces, all item branches and blockstates) contributes references.
     * Models outside the narrow weapon scope remain roots, including foreign and unversioned models.
     *
     * <p>Consumers loading versioned weapon IDs outside pack JSON must use the overload to pin them.
     * Unknown/non-JSON model loaders cannot be inferred from this snapshot. Malformed retained JSON,
     * an unresolved explicit Destiny model reference, or a reachable already-omitted model causes
     * no new exclusions, rather than partial pruning.
     */
    public static void prune(Map<String, PackResource> files, Set<String> omitted) {
        prune(files, omitted, Set.of());
    }

    /** External roots may be resource IDs (default namespace minecraft) or full model JSON paths. */
    public static void prune(Map<String, PackResource> files, Set<String> omitted,
                             Set<String> externalModelRoots) {
        var models = new HashSet<String>();
        for (String path : files.keySet()) if (MODEL.matcher(path).matches()) models.add(path);
        var reachable = new HashSet<String>();
        for (String path : models)
            if (!omitted.contains(path) && !candidate(path)) reachable.add(path);
        for (String root : externalModelRoots) {
            String path = modelPath(root);
            if (!models.contains(path) || omitted.contains(path)) return;
            reachable.add(path);
        }

        var edges = new HashMap<String, Set<String>>();
        // Retain only edges, not the parsed geometry/item trees, across files.
        for (var entry : files.entrySet()) {
            String path = entry.getKey();
            if (omitted.contains(path) || !(path.endsWith(".json") || path.endsWith(".mcmeta"))) continue;
            var references = new HashSet<String>();
            try {
                var json = JsonParser.parseString(entry.getValue().asString());
                boolean definition = models.contains(path) || path.matches("assets/[^/]+/(items|blockstates)/.+\\.json");
                if (json.isJsonNull() || (definition && !json.isJsonObject())) return;
                collect(json, models, references);
            } catch (RuntimeException invalidOrUnreadable) {
                return; // No mutation until the complete graph is known.
            }
            if (models.contains(path)) edges.put(path, references);
            else reachable.addAll(references);
        }

        var queue = new ArrayDeque<>(reachable);
        while (!queue.isEmpty()) {
            String path = queue.removeFirst();
            if (omitted.contains(path)) return; // Caller must repair stale rewrites/exclusions first.
            for (String target : edges.getOrDefault(path, Set.of()))
                if (reachable.add(target)) queue.addLast(target);
        }
        var additions = new HashSet<String>();
        for (String path : models)
            if (candidate(path) && !reachable.contains(path) && !omitted.contains(path)) additions.add(path);
        omitted.addAll(additions);
    }

    private static boolean candidate(String path) {
        return WEAPON.matcher(path).matches() || (path.startsWith(FRAMING) && path.endsWith(".json"));
    }

    private static String modelPath(String reference) {
        if (MODEL.matcher(reference).matches()) return reference;
        int colon = reference.indexOf(':');
        String namespace = colon < 0 ? "minecraft" : reference.substring(0, colon);
        String path = colon < 0 ? reference : reference.substring(colon + 1);
        return "assets/" + namespace + "/models/" + path + ".json";
    }

    private static void collect(JsonElement json, Set<String> models, Set<String> references) {
        if (json.isJsonObject()) {
            for (var entry : json.getAsJsonObject().entrySet()) {
                // Also protect registry keys and custom renderer metadata, without assuming a type.
                reference(entry.getKey(), models, references);
                var value = entry.getValue();
                if (MODEL_REFERENCE_KEYS.contains(entry.getKey())
                        && value.isJsonPrimitive() && value.getAsJsonPrimitive().isString()
                        && value.getAsString().startsWith("destiny:")
                        && !models.contains(modelPath(value.getAsString()))) {
                    throw new IllegalArgumentException("Unresolved Destiny model: " + value.getAsString());
                }
                collect(value, models, references);
            }
        } else if (json.isJsonArray()) {
            for (var child : json.getAsJsonArray()) collect(child, models, references);
        } else if (json.isJsonPrimitive() && json.getAsJsonPrimitive().isString()) {
            reference(json.getAsString(), models, references);
        }
    }

    private static void reference(String value, Set<String> models, Set<String> references) {
        String path = modelPath(value);
        if (models.contains(path)) references.add(path);
    }
}
