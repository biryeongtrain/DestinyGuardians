package kim.biryeong.destiny.compat.pack;

import com.google.gson.JsonElement;
import com.google.gson.JsonParser;
import eu.pb4.polymer.resourcepack.api.PackResource;

import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;
import java.util.regex.Pattern;

/** Output-only pruning of unreferenced versioned weapon PNGs; never decodes or rewrites images. */
public final class PackWeaponTexturePruner {
    private static final String PREFIX = "assets/destiny/textures/";
    private static final Pattern WEAPON = Pattern.compile(
            "assets/destiny/textures/item/weapon/w[0-9]+/.+\\.png");

    private PackWeaponTexturePruner() {}

    /** Call after model pruning, before freezing exclusions. Returns newly omitted PNG count.
     * All retained JSON/mcmeta values AND keys (including foreign/font/gui/equipment/custom
     * definitions and explicit atlas single sources) protect exact texture IDs and file paths.
     * Atlas directory sources do not make every image a root. Other non-media resources are
     * conservatively searched for literal references, including properties/shaders/custom text.
     * Malformed/unreadable retained resources cause no new exclusions. Dynamic external consumers
     * must pin their textures with the overload; only audited versioned weapon paths are eligible.
     */
    public static int prune(Map<String, PackResource> files, Set<String> omitted) {
        return prune(files, omitted, Set.of());
    }

    public static int prune(Map<String, PackResource> files, Set<String> omitted,
                            Set<String> externalTextureRoots) {
        var candidates = new HashSet<String>();
        var aliases = new HashMap<String, String>();
        for (String path : files.keySet()) {
            if (!WEAPON.matcher(path).matches()) continue;
            candidates.add(path);
            String texture = path.substring(PREFIX.length(), path.length() - 4);
            for (String alias : Set.of("destiny:" + texture, texture,
                    "textures/" + texture, "destiny:textures/" + texture,
                    "destiny/textures/" + texture, PREFIX + texture)) {
                aliases.put(alias, path);
                aliases.put(alias + ".png", path);
            }
        }
        if (candidates.isEmpty()) return 0;
        var retained = new HashSet<String>();
        for (String root : externalTextureRoots) protect(root, aliases, retained);
        for (var entry : files.entrySet()) {
            String path = entry.getKey();
            if (omitted.contains(path) || path.endsWith("/") || path.endsWith(".png") || path.endsWith(".ogg")) continue;
            try {
                String text = entry.getValue().asString();
                if (path.endsWith(".json") || path.endsWith(".mcmeta")) {
                    var json = JsonParser.parseString(text);
                    if (json.isJsonNull()) return 0;
                    collect(json, aliases, retained);
                } else {
                    // Non-JSON custom consumers may quote paths differently: false positives are safe.
                    for (var alias : aliases.entrySet())
                        if (text.contains(alias.getKey())) retained.add(alias.getValue());
                }
            } catch (RuntimeException invalidOrUnreadable) {
                return 0; // Do not partially prune an incomplete reference inventory.
            }
        }
        // A stale caller exclusion is not a license to remove more textures.
        for (String path : retained) if (omitted.contains(path)) return 0;
        int removed = 0;
        for (String path : candidates) {
            if (retained.contains(path) || omitted.contains(path)) continue;
            omitted.add(path);
            if (files.containsKey(path + ".mcmeta")) omitted.add(path + ".mcmeta");
            removed++;
        }
        return removed;
    }

    private static void collect(JsonElement json, Map<String, String> aliases, Set<String> retained) {
        if (json.isJsonObject()) {
            for (var entry : json.getAsJsonObject().entrySet()) {
                protect(entry.getKey(), aliases, retained);
                collect(entry.getValue(), aliases, retained);
            }
        } else if (json.isJsonArray()) {
            for (var value : json.getAsJsonArray()) collect(value, aliases, retained);
        } else if (json.isJsonPrimitive() && json.getAsJsonPrimitive().isString()) {
            protect(json.getAsString(), aliases, retained);
        }
    }

    private static void protect(String reference, Map<String, String> aliases, Set<String> retained) {
        String path = aliases.get(reference);
        if (path != null) retained.add(path);
    }
}
