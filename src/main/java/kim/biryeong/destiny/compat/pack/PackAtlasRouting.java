package kim.biryeong.destiny.compat.pack;

import com.google.gson.*;
import eu.pb4.polymer.resourcepack.api.PackResource;
import eu.pb4.polymer.resourcepack.api.ResourcePackBuilder;
import kim.biryeong.destiny.DestinyGuardians;
import java.nio.charset.StandardCharsets;
import java.security.*;
import java.util.*;
import java.util.regex.Pattern;

/** Lossless, content-addressed atlas placement for large generated model textures.
 * Generated sprite names may change on every pack build; texture bytes are never modified.
 */
public final class PackAtlasRouting {
    private static final String CATALOG = "/destiny/pack/atlas_routes.json";
    public record Route(String sha256, String texturePrefix, String from, String to) {
        public Route {
            if (!sha256.matches("[a-f0-9]{64}") || !texturePrefix.matches("assets/[a-z0-9_.-]+/textures/[a-z0-9_./-]*")
                    || !from.matches("[a-z0-9_.-]+:[a-z0-9_./-]+") || !to.matches("[a-z0-9_.-]+:[a-z0-9_./-]+")
                    || from.equals(to)) throw new IllegalArgumentException("Invalid atlas route");
        }
    }
    public record Result(Map<String, PackResource> updates, List<String> sprites, Set<String> missingHashes) { }
    private PackAtlasRouting() { }

    /** Polymer merges atlas definitions BEFORE pre-finish tasks. Seed these output paths early. */
    static void prepare(ResourcePackBuilder builder) {
        var atlases = new LinkedHashSet<String>();
        for (var route : catalog()) { atlases.add(route.from()); atlases.add(route.to()); }
        for (String atlas : atlases) builder.addData(atlasPath(atlas), PackResource.fromString("{\"sources\":[]}"));
    }
    static void apply(ResourcePackBuilder builder, Map<String, PackResource> files) {
        List<Route> routes = catalog();
        var result = route(files, routes);
        // addData(atlas) here would append to an already-consumed merger and vanish from the ZIP.
        // The early seed guarantees the paths exist; a converter replaces the final merged bytes.
        for (String path : result.updates().keySet()) if (!files.containsKey(path))
            throw new IllegalStateException("Atlas output was not prepared before merge: " + path);
        builder.addResourceConverter((path, resource) -> result.updates().getOrDefault(path, resource));
        files.putAll(result.updates());
        if (!result.sprites().isEmpty()) DestinyGuardians.LOGGER.info("Large model atlas routing: {}", result.sprites());
        if (!result.missingHashes().isEmpty()) DestinyGuardians.LOGGER.warn("Atlas routes absent from generated pack (model missing or externally overridden): {}", result.missingHashes());
    }
    static List<Route> catalog() {
        try (var in = PackAtlasRouting.class.getResourceAsStream(CATALOG)) {
            if (in == null) throw new IllegalStateException("Missing atlas route catalog");
            var root = JsonParser.parseString(new String(in.readAllBytes(), StandardCharsets.UTF_8)).getAsJsonObject();
            var routes = new ArrayList<Route>();
            for (var value : root.getAsJsonArray("routes")) {
                var r = value.getAsJsonObject();
                routes.add(new Route(r.get("sha256").getAsString(), r.get("texturePrefix").getAsString(),
                        r.get("from").getAsString(), r.get("to").getAsString()));
            }
            return List.copyOf(routes);
        } catch (java.io.IOException e) { throw new IllegalStateException("Cannot read atlas routes", e); }
    }
    static Result route(Map<String, PackResource> files, List<Route> routes) {
        var updates = new LinkedHashMap<String, JsonObject>();
        var routed = new ArrayList<String>();
        var missing = new LinkedHashSet<String>();
        for (var r : routes) missing.add(r.sha256());
        var destinations = new HashMap<String, String>();
        for (String path : new TreeSet<>(files.keySet())) {
            if (!path.endsWith(".png") || routes.stream().noneMatch(r -> path.startsWith(r.texturePrefix()))) continue;
            String hash = sha256(files.get(path).readAllBytes());
            for (var r : routes) if (path.startsWith(r.texturePrefix()) && hash.equals(r.sha256())) {
                String[] parts = path.split("/", 4);
                String sprite = parts[1] + ":" + parts[3].substring(0, parts[3].length() - 4);
                String old = destinations.putIfAbsent(sprite, r.from() + ">" + r.to());
                if (old != null && !old.equals(r.from() + ">" + r.to())) throw new IllegalStateException("Conflicting atlas routes: " + sprite);
                var filter = new JsonObject(); filter.addProperty("type", "minecraft:filter");
                // Native IdentifierPattern uses Pattern.asPredicate (find), so quote alone also removes _hud siblings.
                var pattern = new JsonObject(); pattern.addProperty("namespace", "^" + Pattern.quote(parts[1]) + "$");
                pattern.addProperty("path", "^" + Pattern.quote(sprite.substring(sprite.indexOf(':') + 1)) + "$"); filter.add("pattern", pattern);
                append(updates, files, r.from(), filter);
                var single = new JsonObject(); single.addProperty("type", "minecraft:single");
                single.addProperty("resource", sprite); single.addProperty("sprite", sprite);
                append(updates, files, r.to(), single);
                if (old == null) routed.add(sprite);
                missing.remove(hash);
            }
        }
        var output = new LinkedHashMap<String, PackResource>();
        updates.forEach((p, j) -> output.put(p, PackResource.fromString(j.toString())));
        return new Result(Map.copyOf(output), List.copyOf(routed), Set.copyOf(missing));
    }
    private static void append(Map<String, JsonObject> updates, Map<String, PackResource> files, String atlas, JsonObject source) {
        String path = atlasPath(atlas);
        var root = updates.computeIfAbsent(path, p -> files.containsKey(p)
                ? JsonParser.parseString(files.get(p).asString()).getAsJsonObject() : new JsonObject());
        if (!root.has("sources")) root.add("sources", new JsonArray());
        var sources = root.getAsJsonArray("sources");
        if (!sources.contains(source)) sources.add(source);
    }
    private static String atlasPath(String atlas) { return "assets/" + atlas.replace(":", "/atlases/") + ".json"; }
    static String sha256(byte[] bytes) {
        try { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)); }
        catch (NoSuchAlgorithmException e) { throw new IllegalStateException(e); }
    }
}
