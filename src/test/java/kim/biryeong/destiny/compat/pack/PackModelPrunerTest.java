package kim.biryeong.destiny.compat.pack;

import eu.pb4.polymer.resourcepack.api.PackResource;
import org.junit.jupiter.api.Test;

import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;

class PackModelPrunerTest {
    private static final String PREFIX = "assets/destiny/models/weapon_reload_w257/";

    @Test
    void retainsEveryItemBranchSpecialBaseAndTransitiveParentAcrossNamespaces() {
        var files = models("yes", "no", "case", "fallback", "base", "parent", "dead");
        put(files, "assets/foreign/items/route.json", """
                {"model":{"type":"composite","models":[
                  {"type":"minecraft:condition","on_true":{"type":"model","model":"destiny:weapon_reload_w257/yes"},
                   "on_false":{"type":"minecraft:model","model":"destiny:weapon_reload_w257/no"}},
                  {"type":"select","cases":[{"when":"gui","model":{"type":"minecraft:model","model":"destiny:weapon_reload_w257/case"}}],
                   "fallback":{"type":"model","model":"destiny:weapon_reload_w257/fallback"}},
                  {"type":"special","base":"destiny:weapon_reload_w257/base","model":{"type":"player_head"}}
                ]}}
                """);
        put(files, model("yes"), "{\"parent\":\"foreign:bridge\"}");
        put(files, "assets/foreign/models/bridge.json", "{\"parent\":\"destiny:weapon_reload_w257/parent\"}");
        var before = contents(files);
        var omitted = new HashSet<String>();
        PackModelPruner.prune(Map.copyOf(files), omitted);
        assertEquals(Set.of(model("dead")), omitted);
        assertEquals(before, contents(files), "Snapshot resources must remain byte-for-byte unchanged");
    }

    @Test
    void retainsWeightedVariantsMultipartAndLegacyOverrideDependencies() {
        var files = models("variant", "weighted", "multipart", "override", "dead");
        put(files, "assets/minecraft/blockstates/test.json", """
                {"variants":{"axis=y":[{"model":"destiny:weapon_reload_w257/variant"},
                  {"model":"destiny:weapon_reload_w257/weighted","weight":2}]},
                 "multipart":[{"when":{"lit":"true"},"apply":[{"model":"destiny:weapon_reload_w257/multipart"}]}]}
                """);
        put(files, model("variant"), """
                {"overrides":[{"predicate":{"custom_model_data":1},"model":"destiny:weapon_reload_w257/override"}]}
                """);
        var omitted = new HashSet<String>();
        PackModelPruner.prune(files, omitted);
        assertEquals(Set.of(model("dead")), omitted);
    }

    @Test
    void preservesForeignAndOutOfScopeDynamicRootsAndTheirParents() {
        var files = models("foreign_parent", "dynamic_parent", "dead");
        put(files, "assets/other/models/unreferenced.json", "{\"parent\":\"destiny:weapon_reload_w257/foreign_parent\"}");
        put(files, "assets/destiny/models/weapon/custom.json", "{\"parent\":\"destiny:weapon_reload_w257/dynamic_parent\"}");
        for (String path : Set.of("assets/destiny/models/profile_arm.json",
                "assets/destiny/models/gui/hud/icon.json", "assets/destiny/models/weapon_future/custom.json",
                "assets/other/models/weapon_reload_w257/dead.json",
                "assets/destiny/textures/weapon_reload_w257/dead.json",
                "assets/destiny/models/first_person_framing_w205_extra/dead.json")) put(files, path, "{}");
        var omitted = new HashSet<String>();
        PackModelPruner.prune(files, omitted);
        assertEquals(Set.of(model("dead")), omitted);
    }

    @Test
    void customJsonRegistryAndExplicitExternalRootsProtectDynamicModels() {
        var files = models("metadata", "registry_key", "explicit", "parent", "full_path", "dead");
        put(files, "assets/other/custom/renderer.json", """
                {"dynamic_models":["destiny:weapon_reload_w257/metadata"],
                 "registry":{"destiny:weapon_reload_w257/registry_key":true}}
                """);
        put(files, model("explicit"), "{\"parent\":\"destiny:weapon_reload_w257/parent\"}");
        var omitted = new HashSet<String>();
        PackModelPruner.prune(files, omitted, Set.of("destiny:weapon_reload_w257/explicit", model("full_path")));
        assertEquals(Set.of(model("dead")), omitted);
    }

    @Test
    void defaultMinecraftNamespaceAndUnknownModelTypesAreConservativelyTraversed() {
        var files = models("parent", "unknown", "dead");
        put(files, "assets/minecraft/models/item/stick.json", "{\"parent\":\"destiny:weapon_reload_w257/parent\"}");
        put(files, "assets/other/items/a.json", """
                {"model":{"type":"future:renderer","models":["item/stick","destiny:weapon_reload_w257/unknown"]}}
                """);
        var omitted = new HashSet<String>();
        PackModelPruner.prune(files, omitted);
        assertEquals(Set.of(model("dead")), omitted);
    }

    @Test
    void omittedItemsAndModelsDoNotKeepDeadDependenciesAliveAndPruningIsIdempotent() {
        var files = models("old", "parent", "dead");
        String route = "assets/destiny/items/old.json";
        put(files, route, "{\"model\":{\"type\":\"model\",\"model\":\"destiny:weapon_reload_w257/old\"}}");
        put(files, model("old"), "{\"parent\":\"destiny:weapon_reload_w257/parent\"}");
        var omitted = new HashSet<>(Set.of(route, model("old"), "unrelated/already-omitted"));
        PackModelPruner.prune(files, omitted);
        assertEquals(Set.of(route, model("old"), model("parent"), model("dead"), "unrelated/already-omitted"), omitted);
        var once = Set.copyOf(omitted);
        PackModelPruner.prune(files, omitted);
        assertEquals(once, omitted);
    }

    @Test
    void consumesRewrittenSnapshotAfterCanonicalizationAndDropsUnusedWrapper() {
        var files = models("canonical", "old_parent");
        String wrapper = "assets/destiny/models/first_person_framing_w205/alias.json";
        put(files, wrapper, "{\"parent\":\"destiny:weapon_reload_w257/old_parent\"}");
        put(files, "assets/destiny/items/rewritten.json", "{\"model\":{\"type\":\"model\",\"model\":\"destiny:weapon_reload_w257/canonical\"}}");
        var omitted = new HashSet<String>();
        PackModelPruner.prune(files, omitted);
        assertEquals(Set.of(wrapper, model("old_parent")), omitted);
        assertFalse(omitted.contains(model("canonical")));
    }

    @Test
    void cyclesTerminateAndOnlyUnreachableCyclesArePruned() {
        var files = models("a", "b", "c", "d");
        put(files, model("a"), "{\"parent\":\"destiny:weapon_reload_w257/b\"}");
        put(files, model("b"), "{\"parent\":\"destiny:weapon_reload_w257/a\"}");
        put(files, model("c"), "{\"parent\":\"destiny:weapon_reload_w257/d\"}");
        put(files, model("d"), "{\"parent\":\"destiny:weapon_reload_w257/c\"}");
        var omitted = new HashSet<String>();
        PackModelPruner.prune(files, omitted, Set.of("destiny:weapon_reload_w257/a"));
        assertEquals(Set.of(model("c"), model("d")), omitted);
    }

    @Test
    void malformedRetainedJsonAndMissingExternalRootsFailClosedWithoutPartialAdditions() {
        for (String bad : Set.of("{broken", "null", "[]")) {
            var files = models("dead");
            put(files, "assets/foreign/models/bad.json", bad);
            var omitted = new HashSet<>(Set.of("existing"));
            PackModelPruner.prune(files, omitted);
            assertEquals(Set.of("existing"), omitted);
        }
        var omitted = new HashSet<>(Set.of("existing"));
        PackModelPruner.prune(models("dead"), omitted, Set.of("destiny:weapon_reload_w257/missing"));
        assertEquals(Set.of("existing"), omitted);
    }

    @Test
    void unresolvedDestinyParentOrConsumerFailsClosedButExternalVanillaParentsAreAllowed() {
        for (String key : Set.of("parent", "model", "base")) {
            var files = models("dead");
            put(files, "assets/foreign/models/consumer.json",
                    "{\"" + key + "\":\"destiny:missing_external_model\"}");
            var omitted = new HashSet<String>();
            PackModelPruner.prune(files, omitted);
            assertEquals(Set.of(), omitted);
        }
        var files = models("dead");
        put(files, "assets/foreign/models/consumer.json", "{\"parent\":\"item/generated\"}");
        var omitted = new HashSet<String>();
        PackModelPruner.prune(files, omitted);
        assertEquals(Set.of(model("dead")), omitted);
    }

    @Test
    void staleRetainedReferenceToAlreadyOmittedModelFailsClosed() {
        var files = models("old", "parent", "dead");
        put(files, model("old"), "{\"parent\":\"destiny:weapon_reload_w257/parent\"}");
        put(files, "assets/destiny/items/stale.json", "{\"model\":{\"type\":\"model\",\"model\":\"destiny:weapon_reload_w257/old\"}}");
        var omitted = new HashSet<>(Set.of(model("old")));
        PackModelPruner.prune(files, omitted);
        assertEquals(Set.of(model("old")), omitted);
    }

    private static String model(String name) { return PREFIX + name + ".json"; }

    private static Map<String, PackResource> models(String... names) {
        var files = new HashMap<String, PackResource>();
        for (String name : names) put(files, model(name), "{}");
        return files;
    }

    private static void put(Map<String, PackResource> files, String path, String json) {
        files.put(path, PackResource.fromString(json));
    }

    private static Map<String, String> contents(Map<String, PackResource> files) {
        var result = new HashMap<String, String>();
        files.forEach((path, resource) -> result.put(path, resource.asString()));
        return result;
    }
}
