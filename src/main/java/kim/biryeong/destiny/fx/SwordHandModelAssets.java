package kim.biryeong.destiny.fx;

import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParseException;
import com.google.gson.JsonParser;
import eu.pb4.polymer.resourcepack.api.PackResource;
import eu.pb4.polymer.resourcepack.api.PolymerResourcePackUtils;
import eu.pb4.polymer.resourcepack.api.ResourcePackBuilder;

import java.util.List;

/** Pack-output policy: swords use server third-person presentation, even with a stale hand stack. */
public final class SwordHandModelAssets {
    static final List<String> TARGETS = List.of(
            "assets/destiny/items/weapon/abide_the_return.json",
            "assets/destiny/items/weapon/goldtusk.json",
            "assets/destiny/items/weapon/crown_splitter.json",
            "assets/destiny/items/weapon/falling_guillotine.json",
            "assets/destiny/items/weapon/temptation_s_hook.json");
    private static boolean registered;

    private SwordHandModelAssets() {}

    /** Master calls this during shared initialization; repeated calls register only once. */
    public static synchronized void register() {
        if (registered) return;
        PolymerResourcePackUtils.RESOURCE_PACK_CREATION_EVENT.register(SwordHandModelAssets::configure);
        registered = true;
    }

    static void configure(ResourcePackBuilder builder) {
        builder.addResourceConverter(SwordHandModelAssets::convert);
        // Converters visit emitted resources only. Missing/invalid canonical items must fail loudly.
        builder.addPreFinishTask(pack -> {
            for (String path : TARGETS) convert(path, pack.getResource(path));
        });
    }

    static PackResource convert(String path, PackResource resource) {
        if (!TARGETS.contains(path)) return resource;
        if (resource == null) throw invalid(path, "missing emitted item definition");
        String source = resource.asString();
        String result = transform(path, source);
        return result.equals(source) ? resource : PackResource.fromString(result);
    }

    /** Pure transformation: foreign paths and already wrapped bytes pass through unchanged. */
    static String transform(String path, String source) {
        if (!TARGETS.contains(path)) return source;
        if (source == null) throw invalid(path, "missing item definition");
        final JsonElement parsed;
        try {
            parsed = JsonParser.parseString(source);
        } catch (JsonParseException e) {
            throw new IllegalStateException("W140 sword hand model rejected " + path + ": invalid JSON", e);
        }
        if (!parsed.isJsonObject()) throw invalid(path, "item definition must be an object");
        JsonObject result = wrap(path, parsed.getAsJsonObject());
        return result.equals(parsed) ? source : result.toString();
    }

    /** Copy the root and preserve the complete original model tree, including nested routing. */
    static JsonObject wrap(String path, JsonObject source) {
        if (!TARGETS.contains(path)) return source;
        if (source == null) throw invalid(path, "missing item object");
        JsonObject model = requireModel(path, source.get("model"));
        JsonElement fallback = model.get("fallback");
        if (fallback != null && fallback.isJsonObject()
                && model.equals(firstPersonMask(fallback.getAsJsonObject()))) {
            requireModel(path, fallback);
            return source.deepCopy();
        }
        JsonObject result = source.deepCopy();
        result.add("model", firstPersonMask(model.deepCopy()));
        return result;
    }

    private static JsonObject requireModel(String path, JsonElement element) {
        if (element == null || !element.isJsonObject()) throw invalid(path, "model must be an object");
        JsonObject model = element.getAsJsonObject();
        JsonElement type = model.get("type");
        if (type == null || !type.isJsonPrimitive() || !type.getAsJsonPrimitive().isString()
                || !type.getAsString().matches("(?:[a-z0-9_.-]+:)?[a-z0-9_./-]+")) {
            throw invalid(path, "model must have a valid string type");
        }
        return model;
    }

    private static JsonObject firstPersonMask(JsonObject original) {
        JsonObject select = new JsonObject();
        select.addProperty("type", "minecraft:select");
        select.addProperty("property", "minecraft:display_context");
        JsonArray cases = new JsonArray();
        // 26.3 SelectItemModel.SwitchCase accepts a compact list of ItemDisplayContext names.
        JsonArray hands = new JsonArray();
        hands.add("firstperson_righthand");
        hands.add("firstperson_lefthand");
        JsonObject entry = new JsonObject();
        entry.add("when", hands);
        JsonObject empty = new JsonObject();
        empty.addProperty("type", "minecraft:empty");
        entry.add("model", empty);
        cases.add(entry);
        select.add("cases", cases);
        select.add("fallback", original);
        return select;
    }

    private static IllegalStateException invalid(String path, String reason) {
        return new IllegalStateException("W140 sword hand model rejected " + path + ": " + reason);
    }
}
