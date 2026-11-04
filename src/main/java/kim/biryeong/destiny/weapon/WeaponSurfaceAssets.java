package kim.biryeong.destiny.weapon;

import com.google.gson.JsonParser;
import com.google.gson.JsonArray;
import eu.pb4.polymer.resourcepack.api.PackResource;
import eu.pb4.polymer.resourcepack.api.PolymerResourcePackUtils;
import eu.pb4.polymer.resourcepack.api.ResourcePackBuilder;

import java.io.ByteArrayInputStream;
import java.io.IOException;
import java.awt.image.BufferedImage;
import java.util.Arrays;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.HexFormat;
import java.util.List;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Set;

/** W115 art-direction migration at pack output only. Historical editable source
 * assets, canonical item IDs, display transforms, gameplay and owner admission stay intact.
 * Exactly two bodies and their five reload parts are replaced, never whole directories.
 */
public final class WeaponSurfaceAssets {
    static final String MANIFEST = "weapon_surface_w115/manifest.json";
    static final Set<String> TARGETS = Set.of(
            "assets/destiny/models/weapon/pulse_rifle/blast_furnace.json",
            "assets/destiny/models/weapon/machine_gun/hammerhead.json",
            "assets/destiny/models/weapon_reload_w114_blast_furnace/blast_furnace_body.json",
            "assets/destiny/models/weapon_reload_w114_blast_furnace/blast_furnace_magazine.json",
            "assets/destiny/models/weapon_reload_w114_hammerhead/hammerhead_body.json",
            "assets/destiny/models/weapon_reload_w114_hammerhead/hammerhead_magazine.json",
            "assets/destiny/models/weapon_reload_w114_hammerhead/hammerhead_cover.json");
    private static final Map<String, String> OPACITY_PATHS = Map.of(
            "destiny:item/weapon/w115/blast_furnace", "assets/destiny/textures/item/weapon/w115/blast_furnace.png",
            "destiny:item/weapon/w115/hammerhead", "assets/destiny/textures/item/weapon/w115/hammerhead.png");
    private static boolean initialized;

    private WeaponSurfaceAssets() {}

    public static synchronized void init() {
        if (initialized) return;
        PolymerResourcePackUtils.RESOURCE_PACK_CREATION_EVENT.register(WeaponSurfaceAssets::configure);
        initialized = true;
    }

    static void configure(ResourcePackBuilder builder) {
        // Load/verify the complete replacement set before installing either callback.
        // Separate opt-in: the W118 art/manifest remains the immutable input.
        // Only output bytes are optimized; no cross-moving-part occlusion.
        var opacity = Boolean.getBoolean("destiny.weapon.surface.cull.w119")
                ? opacityInputs() : Map.<String, OpacityInput>of();
        var rules = opacity.isEmpty() ? rules() : optimizeRules(rules(), opacity).rules();
        builder.addResourceConverter((path, resource) -> convert(path, resource, rules));
        // Creation event runs before asset copying; validate emitted inputs at pre-finish.
        // A missing target cannot silently leave one old noisy part in an animation.
        builder.addPreFinishTask(pack -> {
            verifyOpacity(pack, opacity);
            prepare(pack, rules);
        });
    }

    static void prepare(ResourcePackBuilder builder, Map<String, Rule> rules) {
        for (String path : TARGETS) {
            PackResource resource = builder.getResource(path);
            if (resource == null) throw incompatible(path, "missing emitted model");
            convert(path, resource, rules);
        }
    }

    record Rule(String sourceSha256, String replacementSha256, String replacementPath, String replacement) {}

    record Optimization(Map<String, Rule> rules, Map<String, List<InteriorSurfaceCuller.Removal>> parts) {}

    // Private snapshot: culling and prefinish use the same classpath bytes, never
    // a new image decoded from mutable server/pack resources after callbacks run.
    private record OpacityInput(byte[] bytes, BufferedImage image) {}

    private static Map<String, OpacityInput> opacityInputs() {
        var inputs = new LinkedHashMap<String, OpacityInput>();
        for (String path : OPACITY_PATHS.values()) {
            try (var metadata = WeaponSurfaceAssets.class.getResourceAsStream("/" + path + ".mcmeta")) {
                if (metadata != null) throw incompatible(path + ".mcmeta", "unknown classpath texture metadata");
            } catch (IOException failure) {
                throw incompatible(path + ".mcmeta", "classpath metadata read failed");
            }
            try (var stream = WeaponSurfaceAssets.class.getResourceAsStream("/" + path)) {
                if (stream == null) throw incompatible(path, "missing classpath opacity image");
                byte[] bytes = stream.readAllBytes();
                var image = javax.imageio.ImageIO.read(new ByteArrayInputStream(bytes));
                if (image == null) throw incompatible(path, "invalid classpath opacity image");
                inputs.put(path, new OpacityInput(bytes, image));
            } catch (IOException failure) {
                throw incompatible(path, "classpath opacity image read failed");
            }
        }
        return Map.copyOf(inputs);
    }

    private static void verifyOpacity(ResourcePackBuilder builder, Map<String, OpacityInput> inputs) {
        for (var entry : inputs.entrySet()) {
            String path = entry.getKey();
            if (builder.getResource(path + ".mcmeta") != null)
                throw incompatible(path + ".mcmeta", "unknown emitted texture metadata");
            var emitted = builder.getResource(path);
            if (emitted == null) throw incompatible(path, "missing emitted opacity image");
            if (!Arrays.equals(entry.getValue().bytes(), emitted.readAllBytes()))
                throw incompatible(path, "emitted opacity image differs from classpath proof");
        }
    }

    static Optimization optimizeRules(Map<String, Rule> original) {
        return optimizeRules(original, opacityInputs());
    }

    private static Optimization optimizeRules(Map<String, Rule> original, Map<String, OpacityInput> inputs) {
        if (!original.keySet().equals(TARGETS)) throw incompatible(MANIFEST,"optimization needs exact seven targets");
        var optimized=new LinkedHashMap<>(original);
        var audit=new LinkedHashMap<String,List<InteriorSurfaceCuller.Removal>>();
        java.util.function.Function<String, BufferedImage> loader = id -> {
            String path = OPACITY_PATHS.get(id);
            var input = path == null ? null : inputs.get(path);
            return input == null ? null : input.image();
        };
        for (String weapon:List.of("blast_furnace","hammerhead")) {
            var oldAssembly=new JsonArray();var newAssembly=new JsonArray();
            String family=weapon.equals("blast_furnace") ? "pulse_rifle" : "machine_gun";
            String fullPath="assets/destiny/models/weapon/"+family+"/"+weapon+".json";
            var full=verifiedModel(fullPath,original.get(fullPath));
            for (String part:weapon.equals("blast_furnace") ? List.of("body","magazine") : List.of("body","magazine","cover")) {
                String path="assets/destiny/models/weapon_reload_w114_"+weapon+"/"+weapon+"_"+part+".json";
                var rule=original.get(path);var model=verifiedModel(path,rule);
                if (!full.get("textures").equals(model.get("textures"))) throw incompatible(path,"optimization texture mismatch");
                oldAssembly.addAll(model.getAsJsonArray("elements"));
                var result=InteriorSurfaceCuller.cull(model,loader);
                newAssembly.addAll(result.model().getAsJsonArray("elements"));
                optimized.put(path,withOutput(rule,result.model().toString()));
                audit.put(path,result.removals());
            }
            // Never discover occluders on the assembled gun: a fixed body must not
            // erase a magazine/cover that becomes visible during reload.
            if (!oldAssembly.equals(full.getAsJsonArray("elements"))) throw incompatible(fullPath,"optimization assembly mismatch");
            full.add("elements",newAssembly);
            optimized.put(fullPath,withOutput(original.get(fullPath),full.toString()));
        }
        return new Optimization(Map.copyOf(optimized),Map.copyOf(audit));
    }

    private static com.google.gson.JsonObject verifiedModel(String path,Rule rule) {
        if (rule==null || !sha256(rule.replacement()).equals(rule.replacementSha256()))
            throw incompatible(path,"optimization input fingerprint mismatch");
        return JsonParser.parseString(rule.replacement()).getAsJsonObject();
    }

    private static Rule withOutput(Rule rule,String output) {
        return new Rule(rule.sourceSha256(),sha256(output),rule.replacementPath(),output);
    }

    static Map<String, Rule> rules() {
        return parseRules(resource(MANIFEST));
    }

    static Map<String, Rule> parseRules(String source) {
        try {
            var manifest = JsonParser.parseString(source).getAsJsonObject();
            if (manifest.get("schema").getAsInt() != 1 || !"W115".equals(manifest.get("stage").getAsString()))
                throw incompatible(MANIFEST, "unknown schema/stage");
            var rules = new LinkedHashMap<String, Rule>();
            for (var element : manifest.getAsJsonArray("targets")) {
                var row = element.getAsJsonObject();
                String path = row.get("path").getAsString();
                String replacementPath = row.get("replacement").getAsString();
                String sourceSha = row.get("sourceSha256").getAsString();
                String outputSha = row.get("replacementSha256").getAsString();
                String expectedReplacement = "assets/destiny/models/weapon_surface_w115/"
                        + path.substring(path.lastIndexOf('/') + 1);
                if (!TARGETS.contains(path) || !replacementPath.equals(expectedReplacement)
                        || !replacementPath.matches("assets/destiny/models/weapon_surface_w115/[a-z_]+\\.json")
                        || !sourceSha.matches("[0-9a-f]{64}") || !outputSha.matches("[0-9a-f]{64}")
                        || sourceSha.equals(outputSha) || rules.containsKey(path))
                    throw incompatible(path, "invalid/duplicate migration rule");
                String replacement = resource(replacementPath);
                if (!sha256(replacement).equals(outputSha)) throw incompatible(path, "replacement fingerprint mismatch");
                rules.put(path, new Rule(sourceSha, outputSha, replacementPath, replacement));
            }
            if (!rules.keySet().equals(TARGETS)) throw incompatible(MANIFEST, "not the exact seven targets");
            return Map.copyOf(rules);
        } catch (IllegalStateException exception) {
            throw exception;
        } catch (RuntimeException exception) {
            throw incompatible(MANIFEST, "malformed manifest: " + exception.getClass().getSimpleName());
        }
    }

    static PackResource convert(String path, PackResource resource, Map<String, Rule> rules) {
        if (!TARGETS.contains(path)) return resource; // Do not even read unrelated resources.
        var rule = rules.get(path);
        if (resource == null || rule == null) throw incompatible(path, "missing model/rule");
        String current = sha256(resource.asString());
        if (current.equals(rule.replacementSha256())) return resource;
        if (!current.equals(rule.sourceSha256())) throw incompatible(path, "unexpected source SHA-256 " + current);
        // Recheck the bytes, not just a trusted manifest field, even for a caller-supplied rule.
        if (!sha256(rule.replacement()).equals(rule.replacementSha256()))
            throw incompatible(path, "changed replacement");
        return PackResource.fromString(rule.replacement());
    }

    private static String resource(String path) {
        try (var stream = WeaponSurfaceAssets.class.getResourceAsStream("/" + path)) {
            if (stream == null) throw incompatible(path, "missing classpath resource");
            return new String(stream.readAllBytes(), StandardCharsets.UTF_8);
        } catch (IOException exception) {
            throw incompatible(path, "resource read failed");
        }
    }

    static String sha256(String source) {
        try {
            return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256")
                    .digest(source.getBytes(StandardCharsets.UTF_8)));
        } catch (NoSuchAlgorithmException impossible) {
            throw new AssertionError(impossible);
        }
    }

    private static IllegalStateException incompatible(String path, String reason) {
        return new IllegalStateException("W115 weapon surface migration rejected " + path + ": " + reason);
    }
}
