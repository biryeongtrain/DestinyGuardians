package kim.biryeong.destiny.weapon;

import com.google.gson.JsonArray;
import com.google.gson.JsonParser;
import eu.pb4.polymer.resourcepack.api.PackResource;
import eu.pb4.polymer.resourcepack.api.ResourcePackBuilder;
import org.junit.jupiter.api.Test;

import javax.imageio.ImageIO;
import java.lang.reflect.Proxy;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.function.Consumer;

import static org.junit.jupiter.api.Assertions.*;

/** Small pack-integration smoke; not an all-angle fidelity or FPS certification. */
class WeaponSurfaceW123Test {
    static final Path RES = Path.of("src/main/resources");

    @Test void convertsOnlyScopedModelsAndKeepsAcceptedDisplayPoses() throws Exception {
        var rules = WeaponSurfaceW123Assets.rules();
        assertEquals(WeaponSurfaceW123Assets.TARGETS, rules.keySet());
        for (String path : rules.keySet()) {
            String original = Files.readString(RES.resolve(path));
            var output = WeaponSurfaceW123Assets.convert(path, PackResource.fromString(original), rules);
            assertNotEquals(original, output.asString());
            assertEquals(JsonParser.parseString(original).getAsJsonObject().get("display"),
                    JsonParser.parseString(output.asString()).getAsJsonObject().get("display"));
            assertSame(output, WeaponSurfaceW123Assets.convert(path, output, rules));
        }
        var other = PackResource.fromString("untouched");
        assertSame(other, WeaponSurfaceW123Assets.convert("assets/destiny/sounds.json", other, rules));
    }

    @Test void fullModelsAndExistingMovingPartsUseTheSameLoadedTexture() throws Exception {
        for (String id : List.of("retraced_path", "line_in_the_sand", "stormchaser", "bellowing_giant", "pyroclastic_flow", "canis_major", "dimensional_hypotrochoid", "deafening_whisper", "salvager_s_salvo",
                "ammit_ar2", "the_recluse", "beloved", "hammerhead", "blast_furnace", "duke_mk_44",
                "gnawing_hunger", "chattering_bone", "dust_rock_blues", "halfdan_d", "austringer", "antiope_d", "patron_of_lost_causes", "erentil_fr4", "bad_omens", "lonesome", "fixed_odds", "code_duello", "distant_relation", "first_in_last_out", "steelfeather_repeater", "bygones", "bite_of_the_fox", "falling_guillotine", "seventh_seraph_officer_revolver", "ikelos_sg_v1_0_1", "retrofit_escapade", "edge_transit", "crown_splitter", "cold_denial", "claws_of_the_wolf", "frontier_justice", "bug_out_bag", "apostate", "abide_the_return", "goldtusk", "temptation_s_hook", "allied_demand", "aishas_embrace", "long_arm", "ikelos_smg_v1_0_1", "farewell", "dead_man_walking_xx7463", "high_albedo", "brass_attacks", "nezarec_s_whisper", "null_composure", "hollow_words", "coriolis_force", "dream_breaker", "parcel_of_stardust_fell_to_earth", "mindbender_s_ambition_adept", "biting_winds", "whispering_slab")) {
            var full = model(id);
            var assembled = new JsonArray();
            for (String part : parts(id)) {
                var piece = model(id + "_" + part);
                assertEquals(full.get("textures"), piece.get("textures"));
                assertFalse(piece.has("display"));
                assertFalse(piece.getAsJsonArray("elements").isEmpty());
                assembled.addAll(piece.getAsJsonArray("elements"));
            }
            // Full-only roots use existing generic reload, not a custom split.
            // Do not require invented/unreferenced moving parts just for this test.
            if (parts(id).isEmpty()) assembled.addAll(full.getAsJsonArray("elements"));
            assertFalse(assembled.isEmpty(), id);
            assertEquals(assembled, full.get("elements"));
            // Full is the same assembled geometry; do not count it twice.
            assertTrue(assembled.size() <= 1000, id + ": cubes + triangle/contour elements > 1000");
            assertNotNull(ImageIO.read(RES.resolve("assets/destiny/textures/item/weapon/w123/" + id + ".png").toFile()));
        }
    }

    @Test void missingOrChangedTargetCannotSilentlyKeepOldGeometry() throws Exception {
        var rules = WeaponSurfaceW123Assets.rules();
        for (String path : rules.keySet()) {
            assertThrows(IllegalStateException.class, () -> WeaponSurfaceW123Assets.convert(path, null, rules));
            assertThrows(IllegalStateException.class, () -> WeaponSurfaceW123Assets.convert(path, PackResource.fromString("{}"), rules));
        }
    }

    @Test void packHooksConvertAndCheckAllScopedEmittedModels() throws Exception {
        var resources = new HashMap<String, PackResource>();
        for (String path : WeaponSurfaceW123Assets.TARGETS)
            resources.put(path, PackResource.fromString(Files.readString(RES.resolve(path))));
        var converters = new ArrayList<ResourcePackBuilder.ResourceConverter>();
        var finish = new ArrayList<Consumer<ResourcePackBuilder>>();
        var builder = (ResourcePackBuilder) Proxy.newProxyInstance(ResourcePackBuilder.class.getClassLoader(),
                new Class<?>[]{ResourcePackBuilder.class}, (proxy, method, args) -> switch (method.getName()) {
                    case "addResourceConverter" -> { converters.add((ResourcePackBuilder.ResourceConverter) args[0]); yield null; }
                    case "addPreFinishTask" -> { finish.add((Consumer<ResourcePackBuilder>) args[0]); yield null; }
                    case "getResource" -> resources.get((String) args[0]);
                    default -> throw new UnsupportedOperationException(method.getName());
                });
        WeaponSurfaceW123Assets.configure(builder, false);
        assertEquals(1, converters.size());
        assertEquals(1, finish.size());
        // Exercise the exact callback (rather than only the helper) as resources enter a pack.
        for (String path : List.copyOf(resources.keySet()))
            resources.put(path, converters.getFirst().convert(path, resources.get(path)));
        finish.getFirst().accept(builder);
        resources.remove(WeaponSurfaceW123Assets.TARGETS.iterator().next());
        assertThrows(IllegalStateException.class, () -> finish.getFirst().accept(builder));
    }

    @Test void activeHipAimAndReloadGraphsInheritTheReplacementRatherThanOldCopies() throws Exception {
        var rules = WeaponSurfaceW123Assets.rules();
        var roots = new HashSet<String>();
        for (String item : List.of("weapon/retraced_path", "weapon_aim_w70/retraced_path", "weapon/line_in_the_sand", "weapon_aim_w70/line_in_the_sand", "weapon/stormchaser", "weapon_aim_w70/stormchaser", "weapon/bellowing_giant", "weapon_aim_w70/bellowing_giant", "weapon/pyroclastic_flow", "weapon_aim_w70/pyroclastic_flow", "weapon_scope_w45/line_in_the_sand", "weapon_scope_w45/stormchaser", "weapon/canis_major", "weapon_aim_w70/canis_major", "weapon/dimensional_hypotrochoid", "weapon_aim_w70/dimensional_hypotrochoid", "weapon/deafening_whisper", "weapon_aim_w70/deafening_whisper", "weapon/salvager_s_salvo", "weapon_aim_w70/salvager_s_salvo",
                "weapon/ammit_ar2", "weapon/the_recluse", "weapon/beloved",
                "weapon_aim_w70/ammit_ar2", "weapon_aim_w70/the_recluse",
                "weapon_aim_w70/beloved", "weapon_scope_w45/beloved",
                "weapon_reload_w69/ammit_ar2", "weapon_reload_w100/the_recluse",
                "weapon_reload_w101/the_recluse", "weapon_reload_w47/beloved",
                "weapon_swap_w113/ammit_ar2_to_beloved",
                "weapon_swap_w113/the_recluse_to_ammit_ar2",
                "weapon/hammerhead", "weapon/blast_furnace", "weapon/duke_mk_44",
                "weapon_aim_w70/hammerhead", "weapon_aim_w70/blast_furnace", "weapon_aim_w70/duke_mk_44",
                "weapon_reload_w114_hammerhead/hammerhead", "weapon_reload_w114_blast_furnace/blast_furnace",
                "weapon_reload_w64/duke_mk_44",
                "weapon/gnawing_hunger", "weapon/chattering_bone", "weapon/dust_rock_blues",
                "weapon_aim_w70/gnawing_hunger", "weapon_aim_w70/chattering_bone", "weapon_aim_w70/dust_rock_blues",
                "weapon/halfdan_d", "weapon/austringer", "weapon/antiope_d",
                "weapon_aim_w70/halfdan_d", "weapon_aim_w70/austringer", "weapon_aim_w70/antiope_d",
                "weapon/patron_of_lost_causes", "weapon/erentil_fr4", "weapon/bad_omens", "weapon/lonesome",
                "weapon_aim_w70/patron_of_lost_causes", "weapon_aim_w70/erentil_fr4", "weapon_aim_w70/bad_omens", "weapon_aim_w70/lonesome",
                "weapon/fixed_odds", "weapon/code_duello", "weapon/distant_relation", "weapon/first_in_last_out",
                "weapon_aim_w70/fixed_odds", "weapon_aim_w70/code_duello", "weapon_aim_w70/distant_relation", "weapon_aim_w70/first_in_last_out",
                "weapon/steelfeather_repeater", "weapon/bygones", "weapon/bite_of_the_fox", "weapon/falling_guillotine",
                "weapon_aim_w70/steelfeather_repeater", "weapon_aim_w70/bygones", "weapon_aim_w70/bite_of_the_fox",
                "weapon/seventh_seraph_officer_revolver", "weapon/ikelos_sg_v1_0_1", "weapon/retrofit_escapade", "weapon/edge_transit", "weapon/crown_splitter",
                "weapon_aim_w70/seventh_seraph_officer_revolver", "weapon_aim_w70/ikelos_sg_v1_0_1", "weapon_aim_w70/retrofit_escapade", "weapon_aim_w70/edge_transit",
                "weapon/cold_denial", "weapon/claws_of_the_wolf", "weapon/frontier_justice", "weapon/bug_out_bag", "weapon/apostate",
                "weapon_aim_w70/cold_denial", "weapon_aim_w70/claws_of_the_wolf", "weapon_aim_w70/frontier_justice", "weapon_aim_w70/bug_out_bag", "weapon_aim_w70/apostate", "weapon/abide_the_return", "weapon/goldtusk", "weapon/temptation_s_hook", "weapon/allied_demand", "weapon_aim_w70/allied_demand", "weapon/aishas_embrace", "weapon_aim_w70/aishas_embrace", "weapon/long_arm", "weapon_aim_w70/long_arm", "weapon/ikelos_smg_v1_0_1", "weapon_aim_w70/ikelos_smg_v1_0_1", "weapon/farewell", "weapon_aim_w70/farewell", "weapon/dead_man_walking_xx7463", "weapon_aim_w70/dead_man_walking_xx7463", "weapon/high_albedo", "weapon_aim_w70/high_albedo", "weapon/brass_attacks", "weapon_aim_w70/brass_attacks", "weapon/nezarec_s_whisper", "weapon/null_composure", "weapon_aim_w70/null_composure", "weapon/hollow_words", "weapon_aim_w70/hollow_words", "weapon/coriolis_force", "weapon_aim_w70/coriolis_force", "weapon/dream_breaker", "weapon_aim_w70/dream_breaker", "weapon/parcel_of_stardust_fell_to_earth", "weapon/mindbender_s_ambition_adept", "weapon/biting_winds", "weapon/whispering_slab", "weapon_aim_w70/parcel_of_stardust_fell_to_earth", "weapon_aim_w70/mindbender_s_ambition_adept", "weapon_bow_w50/biting_winds", "weapon_bow_w50/whispering_slab")) {
            var graph = JsonParser.parseString(Files.readString(RES.resolve("assets/destiny/items/" + item + ".json")));
            var references = new HashSet<String>();
            collectModelReferences(graph, references);
            assertFalse(references.isEmpty(), item);
            for (String reference : references) {
                String path = "assets/destiny/models/" + reference.substring("destiny:".length()) + ".json";
                var visited = new HashSet<String>();
                while (true) {
                    assertTrue(visited.add(path), "Cyclic model parent: " + path);
                    var original = PackResource.fromString(Files.readString(RES.resolve(path)));
                    var emitted = WeaponSurfaceW123Assets.convert(path, original, rules);
                    var value = JsonParser.parseString(emitted.asString()).getAsJsonObject();
                    if (value.has("elements")) {
                        if (retainedBowMotion(path)) break; // Separate W50 string/arrow, not a stale rigid body.
                        assertTrue(rules.containsKey(path), "Old geometry bypasses the new art: " + path);
                        assertEquals(JsonParser.parseString(rules.get(path).replacement()), value);
                        roots.add(path);
                        break;
                    }
                    assertTrue(value.has("parent"), "Missing inherited geometry: " + path);
                    String parent = value.get("parent").getAsString();
                    assertTrue(parent.startsWith("destiny:"), parent);
                    path = "assets/destiny/models/" + parent.substring("destiny:".length()) + ".json";
                }
            }
        }
        assertEquals(WeaponSurfaceW123Assets.TARGETS, roots);
    }

    private static boolean retainedBowMotion(String path) throws Exception {
        if (!path.matches("assets/destiny/models/weapon_bow_w50/(biting_winds|whispering_slab)_(empty|loaded|draw_(0[0-9]|1[0-9]|20)|nock_(0[0-9]|1[0-9]|20))_hip[.]json")) return false;
        var historical = JsonParser.parseString(Files.readString(Path.of("art/weapons/w50/manifest.json")))
                .getAsJsonObject().getAsJsonObject("sha256");
        var digest = historical.get("src/main/resources/" + path);
        assertNotNull(digest, "Undeclared retained bow motion: " + path);
        assertEquals(digest.getAsString(), java.util.HexFormat.of().formatHex(java.security.MessageDigest.getInstance("SHA-256")
                .digest(Files.readAllBytes(RES.resolve(path)))));
        return true;
    }

    private static void collectModelReferences(com.google.gson.JsonElement value, Set<String> out) {
        if (value.isJsonArray()) {
            for (var entry : value.getAsJsonArray()) collectModelReferences(entry, out);
        } else if (value.isJsonObject()) {
            var object = value.getAsJsonObject();
            if (object.has("type") && "minecraft:model".equals(object.get("type").getAsString())) {
                String reference = object.get("model").getAsString();
                assertTrue(reference.startsWith("destiny:"), reference);
                out.add(reference);
            }
            for (var entry : object.entrySet()) collectModelReferences(entry.getValue(), out);
        }
    }

    static List<String> parts(String id) {
        return switch (id) {
            case "hammerhead" -> List.of("body", "magazine", "cover");
            case "duke_mk_44" -> List.of("body", "cylinder");
            case "retraced_path", "line_in_the_sand", "stormchaser", "bellowing_giant", "pyroclastic_flow", "canis_major", "dimensional_hypotrochoid", "deafening_whisper", "salvager_s_salvo", "gnawing_hunger", "chattering_bone", "dust_rock_blues", "halfdan_d", "austringer", "antiope_d", "patron_of_lost_causes", "erentil_fr4", "bad_omens", "lonesome", "fixed_odds", "code_duello", "distant_relation", "first_in_last_out", "steelfeather_repeater", "bygones", "bite_of_the_fox", "falling_guillotine", "seventh_seraph_officer_revolver", "ikelos_sg_v1_0_1", "retrofit_escapade", "edge_transit", "crown_splitter", "cold_denial", "claws_of_the_wolf", "frontier_justice", "bug_out_bag", "apostate", "abide_the_return", "goldtusk", "temptation_s_hook", "allied_demand", "aishas_embrace", "long_arm", "ikelos_smg_v1_0_1", "farewell", "dead_man_walking_xx7463", "high_albedo", "brass_attacks", "nezarec_s_whisper", "null_composure", "hollow_words", "coriolis_force", "dream_breaker", "parcel_of_stardust_fell_to_earth", "mindbender_s_ambition_adept", "biting_winds", "whispering_slab" -> List.of();
            default -> List.of("body", "magazine");
        };
    }

    @Test void explicitLegacyW115DoesNotDoubleConvertItsSevenTargets() throws Exception {
        var resources = new HashMap<String, PackResource>();
        for (String path : WeaponSurfaceW123Assets.TARGETS)
            resources.put(path, PackResource.fromString(Files.readString(RES.resolve(path))));
        var converters = new ArrayList<ResourcePackBuilder.ResourceConverter>();
        var finish = new ArrayList<Consumer<ResourcePackBuilder>>();
        var builder = (ResourcePackBuilder) Proxy.newProxyInstance(ResourcePackBuilder.class.getClassLoader(),
                new Class<?>[]{ResourcePackBuilder.class}, (proxy, method, args) -> switch (method.getName()) {
                    case "addResourceConverter" -> { converters.add((ResourcePackBuilder.ResourceConverter) args[0]); yield null; }
                    case "addPreFinishTask" -> { finish.add((Consumer<ResourcePackBuilder>) args[0]); yield null; }
                    case "getResource" -> resources.get((String) args[0]);
                    default -> throw new UnsupportedOperationException(method.getName());
                });
        WeaponSurfaceW123Assets.configure(builder, true);
        var legacyRules = WeaponSurfaceAssets.rules();
        for (String path : List.copyOf(resources.keySet())) {
            var original = resources.get(path);
            var legacy = WeaponSurfaceAssets.convert(path, original, legacyRules);
            var output = converters.getFirst().convert(path, legacy);
            if (WeaponSurfaceAssets.TARGETS.contains(path)) assertSame(legacy, output, path);
            else assertNotEquals(original.asString(), output.asString(), path);
            resources.put(path, output);
        }
        finish.getFirst().accept(builder);
        // Legacy's pre-finish validator must still recognize its own output.
        WeaponSurfaceAssets.prepare(builder, legacyRules);
    }

    static com.google.gson.JsonObject model(String id) throws Exception {
        return JsonParser.parseString(Files.readString(RES.resolve("assets/destiny/models/weapon_surface_w123/" + id + ".json"))).getAsJsonObject();
    }
}
