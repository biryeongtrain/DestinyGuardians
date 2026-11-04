package kim.biryeong.destiny.compat.pack;

import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import eu.pb4.polymer.resourcepack.api.PackResource;
import eu.pb4.polymer.resourcepack.api.PolymerResourcePackUtils;

import java.util.HashSet;

/** Give standalone HUD/plane models a particle sprite from their actual face.
 * No geometry, UV, tint, item graph, shader or source asset is changed.
 */
public final class ParticleTextureFallbacks {
    private static boolean initialized;

    private ParticleTextureFallbacks() {}

    public static synchronized void init() {
        if (initialized) return;
        PolymerResourcePackUtils.RESOURCE_PACK_CREATION_EVENT.register(builder ->
                builder.addResourceConverter(ParticleTextureFallbacks::convert));
        initialized = true;
    }

    static PackResource convert(String path, PackResource resource) {
        if (resource == null || !(path.startsWith("assets/destiny/models/gui/hud/") && path.endsWith(".json")
                || path.equals("assets/destiny/models/fx/glaive_shield_w41.json"))) return resource;
        var model = JsonParser.parseString(resource.asString()).getAsJsonObject();
        // An inherited model may deliberately get its particle sprite from its parent.
        if (model.has("parent") || !model.has("elements") || !model.has("textures")) return resource;
        var textures = model.getAsJsonObject("textures");
        if (textures.has("particle")) return resource;
        for (var element : model.getAsJsonArray("elements")) {
            var cube = element.getAsJsonObject();
            if (!cube.has("faces")) continue;
            for (var entry : cube.getAsJsonObject("faces").entrySet()) {
                var face = entry.getValue().getAsJsonObject();
                if (!face.has("texture")) continue;
                String sprite = resolve(textures, face.get("texture").getAsString());
                if (sprite == null) continue;
                textures.addProperty("particle", sprite);
                return PackResource.fromString(model.toString());
            }
        }
        return resource; // Unknown aliases are not papered over with an unrelated sprite.
    }

    private static String resolve(JsonObject textures, String reference) {
        var visited = new HashSet<String>();
        while (reference.startsWith("#")) {
            String key = reference.substring(1);
            if (!visited.add(key) || !textures.has(key) || !textures.get(key).isJsonPrimitive()) return null;
            reference = textures.get(key).getAsString();
        }
        return reference.matches("[a-z0-9_.-]+:[a-z0-9_./-]+") ? reference : null;
    }
}
