package kim.biryeong.destiny.compat.pack;

import com.google.gson.*;
import eu.pb4.polymer.resourcepack.api.*;
import kim.biryeong.destiny.DestinyGuardians;
import kim.biryeong.destiny.weapon.WeaponFirstPersonHands;
import kim.biryeong.destiny.weapon.WeaponPackRoots;
import net.minecraft.resources.Identifier;
import java.util.*;

/** Output-only compaction. Source art, timing, skins and authoritative item state stay intact. */
public final class WeaponPackOptimizer {
    private static boolean initialized;
    private WeaponPackOptimizer() {}

    public static synchronized void init() {
        if (initialized) return;
        PolymerResourcePackUtils.RESOURCE_PACK_CREATION_EVENT.register(builder ->
                builder.addPreFinishTask(WeaponPackOptimizer::compact));
        initialized = true;
    }

    static String itemPath(Identifier id) {
        return "assets/" + id.getNamespace() + "/items/" + id.getPath() + ".json";
    }

    static void compact(ResourcePackBuilder builder) {
        var files = new HashMap<String, PackResource>();
        builder.forEachResource(files::put);
        kim.biryeong.destiny.weapon.WeaponSurfaceProjection.projectOutput(files);
        var active = WeaponPackRoots.active();
        if (kim.biryeong.destiny.weapon.ProfileWeaponView.enabled()) { ProfileArmAssets.compact(builder, files, active); return; }
        var excluded = new HashSet<String>();
        for (var source : WeaponFirstPersonHands.sources()) {
            if (!active.contains(source)) {
                excluded.add(itemPath(source));
                excluded.add(itemPath(WeaponFirstPersonHands.model(source)));
            }
        }
        for (var root : active) {
            if (!files.containsKey(itemPath(root)) || !files.containsKey(itemPath(WeaponFirstPersonHands.model(root))))
                throw new IllegalStateException("Missing active weapon route: " + root);
        }
        var reachable = new HashSet<String>();
        long before = 0, after = 0;
        int rewritten = 0;
        var sharedArms = new SharedArmGeometry(files);
        // Snapshot first: addData mutates the builder. Parse one item at a time, never the whole pack.
        for (var entry : files.entrySet()) {
            String path = entry.getKey();
            if (!path.contains("/items/") || !path.endsWith(".json") || excluded.contains(path)) continue;
            var json = JsonParser.parseString(entry.getValue().asString()).getAsJsonObject();
            if (path.startsWith("assets/destiny/items/weapon_hands_w201/")) {
                byte[] original = entry.getValue().readAllBytes();
                json.add("model", specialize(sharedArms.rewrite(json.getAsJsonObject("model"))));
                var output = PackResource.fromString(json.toString());
                builder.addData(path, output);
                entry.setValue(output);
                before += original.length;
                after += output.readAllBytes().length;
                rewritten++;
            }
            references(json, reachable);
        }
        // Every non-pose model is retained and may itself inherit a generated pose.
        for (String path : files.keySet())
            if (path.contains("/models/") && path.endsWith(".json") && !generatedPose(path)) reachable.add(path);
        var queue = new ArrayDeque<>(reachable);
        while (!queue.isEmpty()) {
            var path = queue.removeFirst();
            var resource = files.get(path);
            if (resource == null) continue; // Vanilla parents live in the client's base resources.
            var json = JsonParser.parseString(resource.asString()).getAsJsonObject();
            if (json.has("parent")) {
                String parent = modelPath(json.get("parent").getAsString());
                if (reachable.add(parent)) queue.add(parent);
            }
        }
        for (String path : files.keySet())
            if (generatedPose(path) && !reachable.contains(path)) excluded.add(path);
        int sharedModels = PackModelDeduplicator.compact(builder, files, excluded);
        int previousOmitted = excluded.size();
        PackModelPruner.prune(files, excluded);
        DestinyGuardians.LOGGER.info("Weapon model sharing: {} exact aliases, {} additional unused models omitted",
                sharedModels, excluded.size() - previousOmitted);
        int removedTextures = Boolean.getBoolean("destiny.weapon.surface.w115") ? 0
                : PackWeaponTexturePruner.prune(files, excluded);
        DestinyGuardians.LOGGER.info("Weapon textures: {} unused versioned PNGs omitted without resampling", removedTextures);
        var omitted = Set.copyOf(excluded);
        builder.addResourceConverter((path, resource) -> omitted.contains(path) ? null : resource);
        DestinyGuardians.LOGGER.info("Weapon pack compacted: {} active routes, {} omitted files, {} hand graphs: {} -> {} bytes",
                active.size(), omitted.size(), rewritten, before, after);
        DestinyGuardians.LOGGER.info("Shared native arm geometry: {} pose leaves replaced", sharedArms.rewritten);
    }

    static boolean generatedPose(String path) {
        return path.endsWith(".json") && (path.startsWith("assets/destiny/models/skin_arm_w204/poses/")
                || path.startsWith("assets/destiny/models/first_person_framing_w205/")
                || path.startsWith("assets/destiny/models/weapon_hands_w201/poses/"));
    }

    static String modelPath(String reference) {
        var id = Identifier.parse(reference);
        return "assets/" + id.getNamespace() + "/models/" + id.getPath() + ".json";
    }

    static void references(JsonElement element, Set<String> result) {
        if (element.isJsonObject()) {
            var obj = element.getAsJsonObject();
            String type = obj.has("type") && obj.get("type").isJsonPrimitive() ? obj.get("type").getAsString() : "";
            if (type.equals("minecraft:model") && obj.has("model")) result.add(modelPath(obj.get("model").getAsString()));
            if (type.equals("minecraft:special") && obj.has("base")) result.add(modelPath(obj.get("base").getAsString()));
            obj.entrySet().forEach(e -> references(e.getValue(), result));
        } else if (element.isJsonArray()) element.getAsJsonArray().forEach(e -> references(e, result));
    }

    private record Selection(Set<String> allowed, Set<String> denied) {}
    private static final Selection ANY = new Selection(null, Set.of());
    private static final JsonObject EMPTY = JsonParser.parseString("{\"type\":\"minecraft:empty\"}").getAsJsonObject();

    static JsonObject specialize(JsonObject model) { return specialize(model, Map.of(), Map.of()); }

    /** Only discrete, pure selectors are specialized. Float ranges retain native NaN/threshold behavior. */
    private static JsonObject specialize(JsonObject n, Map<String, Selection> selections, Map<String, Boolean> flags) {
        String type = n.has("type") ? n.get("type").getAsString() : "";
        String property = n.has("property") ? n.get("property").getAsString() : "";
        String key = property + ":" + (n.has("index") ? n.get("index").getAsInt() : 0);
        if (type.equals("minecraft:select") && (property.equals("minecraft:display_context") || property.equals("minecraft:custom_model_data"))) {
            var constraint = selections.getOrDefault(key, ANY);
            var cases = new JsonArray();
            var covered = new HashSet<String>();
            var branches = new ArrayList<JsonObject>();
            for (var rawCase : n.getAsJsonArray("cases")) {
                var c = rawCase.getAsJsonObject();
                var values = new LinkedHashSet<String>();
                var when = c.get("when");
                if (when.isJsonArray()) when.getAsJsonArray().forEach(v -> values.add(v.getAsString()));
                else values.add(when.getAsString());
                covered.addAll(values);
                if (constraint.allowed != null) values.retainAll(constraint.allowed);
                values.removeAll(constraint.denied);
                if (values.isEmpty()) continue;
                var env = new HashMap<>(selections);
                env.put(key, new Selection(Set.copyOf(values), constraint.denied));
                var child = specialize(c.getAsJsonObject("model"), env, flags);
                var out = new JsonObject();
                c.entrySet().forEach(e -> out.add(e.getKey(), e.getValue()));
                var narrowed = new JsonArray();
                values.forEach(narrowed::add);
                out.add("when", narrowed);
                out.add("model", child);
                cases.add(out);
                branches.add(child);
            }
            Set<String> remaining = constraint.allowed == null ? null : new HashSet<>(constraint.allowed);
            if (remaining != null) { remaining.removeAll(covered); remaining.removeAll(constraint.denied); }
            JsonObject fallback = EMPTY;
            if (remaining == null || !remaining.isEmpty()) {
                var denied = new HashSet<>(constraint.denied);
                denied.addAll(covered);
                var env = new HashMap<>(selections);
                env.put(key, new Selection(remaining, Set.copyOf(denied)));
                fallback = specialize(n.has("fallback") ? n.getAsJsonObject("fallback") : EMPTY, env, flags);
                branches.add(fallback);
            }
            if (!branches.isEmpty() && branches.stream().allMatch(branches.getFirst()::equals)) return branches.getFirst();
            n.add("cases", cases);
            n.add("fallback", fallback);
            return factor(n);
        }
        if (type.equals("minecraft:condition") && property.equals("minecraft:custom_model_data")) {
            if (flags.containsKey(key)) return specialize(n.getAsJsonObject(flags.get(key) ? "on_true" : "on_false"), selections, flags);
            var on = new HashMap<>(flags); on.put(key, true);
            var off = new HashMap<>(flags); off.put(key, false);
            var yes = specialize(n.getAsJsonObject("on_true"), selections, on);
            var no = specialize(n.getAsJsonObject("on_false"), selections, off);
            if (yes.equals(no)) return yes;
            n.add("on_true", yes); n.add("on_false", no);
            return factor(n);
        }
        // Walk only model edges; tints, transforms and geometry are opaque and untouched.
        for (String child : List.of("fallback", "on_true", "on_false"))
            if (n.has(child)) n.add(child, specialize(n.getAsJsonObject(child), selections, flags));
        for (String list : List.of("entries", "cases")) if (n.has(list))
            for (var e : n.getAsJsonArray(list)) {
                var entry = e.getAsJsonObject();
                entry.add("model", specialize(entry.getAsJsonObject("model"), selections, flags));
            }
        if (type.equals("minecraft:composite")) {
            var children = new JsonArray();
            for (var child : n.getAsJsonArray("models")) {
                var value = specialize(child.getAsJsonObject(), selections, flags);
                if (plainComposite(value)) value.getAsJsonArray("models").forEach(children::add);
                else children.add(value);
            }
            n.add("models", children);
        }
        return factor(n);
    }

    private static boolean plainComposite(JsonObject n) {
        return n.size() == 2 && n.has("models") && n.get("type").getAsString().equals("minecraft:composite");
    }

    /** Distribute a selector over equally ordered composite layers. Invariant skin layers occur once. */
    private static JsonObject factor(JsonObject selector) {
        String type = selector.get("type").getAsString();
        var branches = new ArrayList<JsonObject>();
        if (type.equals("minecraft:condition")) {
            branches.add(selector.getAsJsonObject("on_true")); branches.add(selector.getAsJsonObject("on_false"));
        } else if (type.equals("minecraft:range_dispatch") || type.equals("minecraft:select")) {
            String list = type.equals("minecraft:select") ? "cases" : "entries";
            for (var entry : selector.getAsJsonArray(list)) branches.add(entry.getAsJsonObject().getAsJsonObject("model"));
            if (!selector.has("fallback")) return selector;
            branches.add(selector.getAsJsonObject("fallback"));
        } else return selector;
        if (branches.isEmpty()) return selector;
        if (branches.stream().allMatch(branches.getFirst()::equals)) return branches.getFirst();
        if (!branches.stream().allMatch(WeaponPackOptimizer::plainComposite)) return selector;
        int length = branches.getFirst().getAsJsonArray("models").size();
        if (branches.stream().anyMatch(b -> b.getAsJsonArray("models").size() != length)) return selector;
        boolean invariant = false;
        for (int i = 0; i < length; i++) {
            var candidate = branches.getFirst().getAsJsonArray("models").get(i);
            final int index = i;
            if (branches.stream().allMatch(b -> candidate.equals(b.getAsJsonArray("models").get(index)))) invariant = true;
        }
        if (!invariant) return selector; // Do not expand branches if no repeated layer can be removed.
        var result = new JsonObject(); result.addProperty("type", "minecraft:composite");
        var models = new JsonArray();
        for (int i = 0; i < length; i++) {
            var values = new ArrayList<JsonObject>();
            for (var b : branches) values.add(b.getAsJsonArray("models").get(i).getAsJsonObject());
            if (values.stream().allMatch(values.getFirst()::equals)) models.add(values.getFirst());
            else {
                var split = new JsonObject();
                selector.entrySet().forEach(e -> split.add(e.getKey(), e.getValue()));
                if (type.equals("minecraft:condition")) {
                    split.add("on_true", values.get(0)); split.add("on_false", values.get(1));
                } else {
                    String list = type.equals("minecraft:select") ? "cases" : "entries";
                    var entries = new JsonArray(); int index = 0;
                    for (var entry : selector.getAsJsonArray(list)) {
                        var copy = new JsonObject();
                        entry.getAsJsonObject().entrySet().forEach(e -> copy.add(e.getKey(), e.getValue()));
                        copy.add("model", values.get(index++)); entries.add(copy);
                    }
                    split.add(list, entries); split.add("fallback", values.getLast());
                }
                models.add(factor(split));
            }
        }
        result.add("models", models); return result;
    }
}
