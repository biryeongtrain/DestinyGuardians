package kim.biryeong.destiny.compat.pack;

import com.google.gson.*;
import eu.pb4.polymer.resourcepack.api.PackResource;
import eu.pb4.polymer.resourcepack.api.ResourcePackBuilder;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.*;

/** Redirects byte-identical generated vanilla weapon models before reachability pruning.
 * No pose, geometry, texture, item id or selector threshold is changed. */
final class PackModelDeduplicator {
    private PackModelDeduplicator() {}

    static int compact(ResourcePackBuilder builder, Map<String, PackResource> files, Set<String> omitted) {
        var aliases = aliases(files, omitted);
        if (aliases.isEmpty()) return 0;
        for (String path : new TreeSet<>(files.keySet())) {
            if (omitted.contains(path) || !path.endsWith(".json")) continue;
            boolean model = path.contains("/models/");
            boolean item = path.contains("/items/");
            boolean blockstate = path.contains("/blockstates/");
            if (!model && !item && !blockstate) continue;
            String raw = files.get(path).asString();
            // Most resources do not reference an owned weapon model.
            if (!raw.contains("destiny:")) continue;
            var json = JsonParser.parseString(raw).getAsJsonObject();
            boolean changed = model ? replace(json, "parent", aliases) : rewrite(json, aliases, blockstate);
            if (model && json.has("overrides")) changed |= rewrite(json.get("overrides"), aliases, true);
            if (!changed) continue;
            var resource = PackResource.fromString(json.toString());
            files.put(path, resource);
            builder.addData(path, resource);
        }
        // Leave deletion to the pruner: a retained opaque reference can still keep an alias alive.
        return aliases.size();
    }

    static Map<String,String> aliases(Map<String, PackResource> files, Set<String> omitted) {
        var hashes = new HashMap<String, List<String>>();
        var aliases = new HashMap<String,String>();
        MessageDigest digest;
        try { digest = MessageDigest.getInstance("SHA-256"); }
        catch (NoSuchAlgorithmException e) { throw new AssertionError(e); }
        for (String path : new TreeSet<>(files.keySet())) {
            if (!eligible(path) || omitted.contains(path)) continue;
            byte[] bytes = files.get(path).readAllBytes();
            var model = JsonParser.parseString(new String(bytes, java.nio.charset.StandardCharsets.UTF_8)).getAsJsonObject();
            // Custom loaders may use the resource id as state. Only standard generated models qualify.
            if (!Set.of("parent", "display", "elements", "textures", "credit", "ambientocclusion",
                    "gui_light", "texture_size").containsAll(model.keySet())) continue;
            String hash = HexFormat.of().formatHex(digest.digest(bytes));
            var candidates = hashes.computeIfAbsent(hash, k -> new ArrayList<>());
            String match = null;
            for (String previous : candidates)
                if (Arrays.equals(bytes, files.get(previous).readAllBytes())) { match = previous; break; }
            if (match != null) aliases.put(id(path), id(match));
            else candidates.add(path);
        }
        return aliases;
    }

    private static boolean eligible(String path) {
        return path.endsWith(".json") && (path.startsWith("assets/destiny/models/weapon_")
                || path.startsWith("assets/destiny/models/first_person_framing_w205/"));
    }
    private static String id(String path) {
        return "destiny:" + path.substring("assets/destiny/models/".length(), path.length()-5);
    }

    static boolean rewrite(JsonElement element, Map<String,String> aliases, boolean blockstate) {
        boolean changed = false;
        if (element.isJsonArray()) {
            for (var child : element.getAsJsonArray()) changed |= rewrite(child, aliases, blockstate);
        } else if (element.isJsonObject()) {
            var obj = element.getAsJsonObject();
            String type = obj.has("type") && obj.get("type").isJsonPrimitive() ? obj.get("type").getAsString() : "";
            if (blockstate || type.equals("minecraft:model") || type.equals("model")) changed |= replace(obj, "model", aliases);
            if (type.equals("minecraft:special") || type.equals("special")) changed |= replace(obj, "base", aliases);
            for (var entry : obj.entrySet()) changed |= rewrite(entry.getValue(), aliases, blockstate);
        }
        return changed;
    }

    private static boolean replace(JsonObject obj, String key, Map<String,String> aliases) {
        var value = obj.get(key);
        if (value == null || !value.isJsonPrimitive() || !value.getAsJsonPrimitive().isString()) return false;
        String replacement = aliases.get(value.getAsString());
        if (replacement == null) return false;
        obj.addProperty(key, replacement);
        return true;
    }
}
