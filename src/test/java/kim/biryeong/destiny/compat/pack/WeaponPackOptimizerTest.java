package kim.biryeong.destiny.compat.pack;

import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import com.google.gson.JsonPrimitive;
import kim.biryeong.destiny.weapon.WeaponCatalog;
import kim.biryeong.destiny.weapon.WeaponFirstPersonHands;
import kim.biryeong.destiny.weapon.WeaponPackRoots;
import net.minecraft.resources.Identifier;
import org.junit.jupiter.api.Test;

import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

import static org.junit.jupiter.api.Assertions.*;

/** Pure synthetic graph semantics plus the real route inventory; no server/client fixture. */
class WeaponPackOptimizerTest {
    private static final String DISPLAY = "minecraft:display_context";
    private static final String CMD = "minecraft:custom_model_data";
    private static final List<String> CONTEXTS = List.of(
            "firstperson_righthand", "firstperson_lefthand", "thirdperson_righthand",
            "thirdperson_lefthand", "gui", "ground", "fixed", "head", "none");

    @Test
    void mixedDisplayCasesNarrowBothHandsAndKeepFallbackExclusions() {
        var firstPerson = select(DISPLAY, -1, model("unreachable_fp_fallback"),
                one("firstperson_righthand", model("right")),
                one("firstperson_lefthand", model("left")),
                one("gui", model("unreachable_fp_gui")));
        var outside = select(DISPLAY, 0, model("outside"),
                one("gui", model("unreachable_fallback_gui")), one("head", model("head")));
        var original = select(DISPLAY, -1, outside,
                many(firstPerson, "firstperson_righthand", "firstperson_lefthand"),
                one("gui", select(DISPLAY, 0, model("unreachable_gui_fallback"),
                        one("gui", model("gui")))));
        var optimized = WeaponPackOptimizer.specialize(original.deepCopy());

        for (String context : CONTEXTS) {
            var input = new Input(context, Map.of(), Map.of());
            assertEquals(evaluate(original, input), evaluate(optimized, input), context);
            String expected = switch (context) {
                case "firstperson_righthand" -> "right";
                case "firstperson_lefthand" -> "left";
                case "gui" -> "gui";
                case "head" -> "head";
                default -> "outside";
            };
            assertEquals(List.of(model(expected)), evaluate(optimized, input), context);
        }
        assertTrue(countType(optimized, "minecraft:select") < countType(original, "minecraft:select"));
        assertFalse(optimized.toString().contains("unreachable_"));
    }

    @Test
    void mixedStringsFlagsAndIndicesPreserveEverySyntheticLeaf() {
        var strings = select(CMD, -1,
                condition(-1,
                        select(CMD, 0, model("other_on"), one("classic", model("unreachable_string"))),
                        condition(0, model("unreachable_flag"), model("other_off"))),
                one("classic", condition(0,
                        condition(0,
                                select(CMD, 1, model("index1_other"), one("slim", model("index1_slim"))),
                                model("unreachable_classic_flag")),
                        condition(1, model("flag1_on"), model("flag1_off")))),
                one("slim", condition(8,
                        condition(9, model("slim_8_9"), model("slim_8")), model("slim_neither"))));
        // A sibling reuses the same keys but must not inherit another sibling's decisions.
        var mixed = composite(strings, condition(0,
                select(CMD, 0, model("sibling_other"), one("classic", model("sibling_classic"))),
                model("sibling_flag_off")));
        var original = select(DISPLAY, -1, mixed.deepCopy(),
                many(select(DISPLAY, 0, model("unreachable_context"),
                                many(mixed.deepCopy(), "firstperson_righthand", "firstperson_lefthand")),
                        "firstperson_righthand", "firstperson_lefthand"));
        var optimized = WeaponPackOptimizer.specialize(original.deepCopy());
        var observations = new HashSet<List<JsonObject>>();
        int comparisons = 0;
        // Flags and strings at equal indices are separate channels. Indices 0/1/8/9
        // are independent; omitted index defaults and explicit zero must agree.
        for (String context : CONTEXTS) for (int bits = 0; bits < 16; bits++) {
            var flags = Map.of(0, (bits & 1) != 0, 1, (bits & 2) != 0,
                    8, (bits & 4) != 0, 9, (bits & 8) != 0);
            for (String zero : List.of("classic", "slim", "unknown", ""))
                for (String one : List.of("classic", "slim", "unknown", "")) {
                    var input = new Input(context, Map.of(0, zero, 1, one), flags);
                    var expected = evaluate(original, input);
                    assertEquals(expected, evaluate(optimized, input), input.toString());
                    observations.add(expected);
                    comparisons++;
                }
        }
        var absent = new Input("gui", Map.of(), Map.of());
        assertEquals(List.of(model("other_off"), model("sibling_flag_off")), evaluate(optimized, absent));
        assertEquals(evaluate(original, absent), evaluate(optimized, absent));
        assertEquals(2304, comparisons);
        assertTrue(observations.size() >= 10, "Exercise genuinely different outcomes");
        assertTrue(countType(optimized, "minecraft:condition") < countType(original, "minecraft:condition"));
        assertFalse(optimized.toString().contains("unreachable_"));
    }

    @Test
    void compositeFactoringSharesInvariantSlotsAndPreservesOrderedLeafMultiplicity() {
        var arm = model("common_arm");
        arm.add("tints", json("""
                {"sources":[{"type":"minecraft:custom_model_data","index":64,"default":16777215}]}
                """).getAsJsonArray("sources"));
        var oppositeArm = model("opposite_arm");
        var repeated = model("same_layer_twice");
        // The changing body lies BETWEEN common layers. Identical final slots
        // deliberately render twice: factoring may share branches, not slots.
        var yes = composite(arm.deepCopy(), model("twohand_body"), oppositeArm.deepCopy(),
                repeated.deepCopy(), repeated.deepCopy());
        var no = composite(arm.deepCopy(), model("onehand_body"), oppositeArm.deepCopy(),
                repeated.deepCopy(), repeated.deepCopy());
        var fallback = composite(arm.deepCopy(), model("fallback_body"), oppositeArm.deepCopy(),
                repeated.deepCopy(), repeated.deepCopy());
        var selectors = List.of(
                condition(0, yes.deepCopy(), no.deepCopy()),
                select(DISPLAY, -1, fallback.deepCopy(),
                        many(yes.deepCopy(), "firstperson_righthand", "firstperson_lefthand"),
                        one("gui", no.deepCopy())),
                select(CMD, 1, fallback.deepCopy(),
                        one("slim", yes.deepCopy()), one("classic", no.deepCopy())));

        for (var original : selectors) {
            var optimized = WeaponPackOptimizer.specialize(original.deepCopy());
            assertEquals("minecraft:composite", optimized.get("type").getAsString());
            var slots = optimized.getAsJsonArray("models");
            assertEquals(5, slots.size());
            assertEquals(arm, slots.get(0), "Keep tinted arm ahead of the body");
            assertEquals(original.get("type"), slots.get(1).getAsJsonObject().get("type"),
                    "Only the variable body slot retains its selector");
            assertEquals(oppositeArm, slots.get(2));
            assertEquals(repeated, slots.get(3));
            assertEquals(repeated, slots.get(4), "Preserve repeated rendered layers and order");
            assertTrue(countType(optimized, "minecraft:model") < countType(original, "minecraft:model"),
                    "Invariant geometry/tints occur once per slot instead of once per branch");
            for (String context : CONTEXTS) for (boolean flag : List.of(false, true))
                for (String string : List.of("slim", "classic", "unknown")) {
                    var input = new Input(context, Map.of(0, "unrelated", 1, string), Map.of(0, flag));
                    var expected = evaluate(original, input);
                    assertEquals(5, expected.size());
                    assertEquals(expected, evaluate(optimized, input), input.toString());
                }
            var absent = new Input("ground", Map.of(), Map.of());
            assertEquals(evaluate(original, absent), evaluate(optimized, absent));
        }

        // Refuse unsafe structural shortcuts: different lengths, reordered
        // layers without an invariant slot, and composites carrying extra data.
        var annotated = yes.deepCopy();
        annotated.addProperty("author_metadata", "must remain attached");
        var guarded = List.of(
                condition(0, composite(arm.deepCopy(), model("body")), composite(arm.deepCopy())),
                condition(0, composite(arm.deepCopy(), oppositeArm.deepCopy()),
                        composite(oppositeArm.deepCopy(), arm.deepCopy())),
                condition(0, annotated, no.deepCopy()));
        for (var original : guarded) {
            var optimized = WeaponPackOptimizer.specialize(original.deepCopy());
            assertEquals("minecraft:condition", optimized.get("type").getAsString());
            for (boolean flag : List.of(false, true)) {
                var input = new Input("gui", Map.of(), Map.of(0, flag));
                assertEquals(evaluate(original, input), evaluate(optimized, input));
            }
        }
    }

    @Test
    void floatRangesRemainOpaqueIncludingNestedSameIndexAndLeafMetadata() {
        var range = json("""
                {"type":"minecraft:range_dispatch","property":"minecraft:custom_model_data",
                 "index":0,"scale":0.5,
                 "fallback":{"type":"minecraft:range_dispatch","property":"minecraft:custom_model_data",
                   "index":0,"scale":2.0,"fallback":{"type":"minecraft:empty"},
                   "entries":[{"threshold":-1.0,"model":{"type":"minecraft:model","model":"destiny:item/negative"}}]},
                 "entries":[
                   {"threshold":-0.0,"model":{"type":"minecraft:model","model":"destiny:item/zero",
                     "tints":[{"type":"minecraft:custom_model_data","index":64,"default":16777215}]}},
                   {"threshold":0.016666666666666666,"model":{"type":"minecraft:model","model":"destiny:item/frame1"}},
                   {"threshold":1.0000001192092896,"model":{"type":"minecraft:special","base":"destiny:item/base",
                     "model":{"type":"minecraft:player_head"}}},
                   {"threshold":2.0,"model":{"type":"minecraft:model","model":"destiny:item/honed"}}]}
                """);
        // A CMD flag at index 0 provides no information about CMD float index 0.
        var original = condition(0,
                condition(0, range.deepCopy(), model("unreachable_flag")), range.deepCopy());
        var optimized = WeaponPackOptimizer.specialize(original.deepCopy());
        assertEquals(range.toString(), optimized.toString(),
                "Keep numeric spelling, signed zero, thresholds, scale, order, tints and special renderer");
        assertEquals(2, countType(optimized, "minecraft:range_dispatch"));
        for (boolean flag : List.of(false, true)) {
            var input = new Input("gui", Map.of(0, "unrelated string"), Map.of(0, flag));
            assertEquals(evaluate(original, input), evaluate(optimized, input));
        }
        // The oracle deliberately does not calculate a float sample or choose a
        // threshold. Exact unchanged range JSON preserves native timing/NaN semantics.
    }

    @Test
    void referencesCollectGeometryAndSpecialBaseWithoutConfusingObjectModelKeys() {
        var item = json("""
                {"model":{"type":"minecraft:select","property":"minecraft:display_context",
                  "cases":[{"when":["gui","ground"],"model":{"type":"minecraft:composite","models":[
                    {"type":"minecraft:model","model":"destiny:item/body","tints":[
                      {"type":"minecraft:constant","value":123,"model":"destiny:not_geometry"}]},
                    {"type":"minecraft:special","base":"other:base/head",
                      "model":{"type":"minecraft:player_head"}},
                    {"type":"minecraft:model","model":"destiny:item/body"}]}}],
                  "fallback":{"type":"minecraft:model","model":"item/stick"}}}
                """);
        var references = new HashSet<String>();
        WeaponPackOptimizer.references(item, references);
        assertEquals(Set.of("assets/destiny/models/item/body.json",
                "assets/other/models/base/head.json", "assets/minecraft/models/item/stick.json"), references);
        assertEquals("assets/other/models/nested/a.json", WeaponPackOptimizer.modelPath("other:nested/a"));
    }

    @Test
    void generatedPoseDeletionIsConfinedToThreeExactOutputDirectories() {
        for (String directory : List.of("skin_arm_w204/poses/", "first_person_framing_w205/",
                "weapon_hands_w201/poses/")) {
            String path = "assets/destiny/models/" + directory + "nested/generated.json";
            assertTrue(WeaponPackOptimizer.generatedPose(path), path);
            assertFalse(WeaponPackOptimizer.generatedPose(path + ".mcmeta"), path);
            assertFalse(WeaponPackOptimizer.generatedPose(path.replace("/destiny/", "/another/")), path);
            assertFalse(WeaponPackOptimizer.generatedPose(path.replace("/models/", "/items/")), path);
        }
        for (String path : List.of(
                "assets/destiny/models/skin_arm_w204/poses_extra/a.json",
                "assets/destiny/models/skin_arm_w204/right.json",
                "assets/destiny/models/first_person_framing_w205_extra/a.json",
                "assets/destiny/models/weapon_hands_w201/poses_extra/a.json",
                "assets/destiny/models/weapon_hands_w201/body.json",
                "assets/destiny/models/item/weapon/a.json",
                "assets/destiny/textures/skin_arm_w204/poses/a.json")) {
            assertFalse(WeaponPackOptimizer.generatedPose(path), path);
        }
    }

    @Test
    void activeRoutesKeepCatalogHandsIzanagiBowAndEveryAuthoredSwapDirection() {
        var active = WeaponPackRoots.active();
        var sources = WeaponFirstPersonHands.sources();
        assertFalse(active.isEmpty());
        for (var entry : WeaponCatalog.all())
            assertTrue(active.contains(Identifier.parse(entry.item_model())), "Catalog base " + entry.id());
        for (var root : active) {
            assertNotNull(getClass().getResource("/" + WeaponPackOptimizer.itemPath(root)), "Source item " + root);
            var wrapped = WeaponFirstPersonHands.model(root);
            if (sources.contains(root)) {
                assertEquals(Identifier.fromNamespaceAndPath(root.getNamespace(), "weapon_hands_w201/" + root.getPath()), wrapped);
                assertNotNull(getClass().getResource("/" + WeaponPackOptimizer.itemPath(wrapped)), "Hands item " + wrapped);
            } else {
                assertEquals(root, wrapped, "Unmapped active routes retain their original item model");
            }
        }
        for (String route : List.of("weapon_izanagi_w91/izanagis_burden",
                "weapon_sight_w159/ace_of_spades", "weapon_sight_w148/biting_winds",
                "weapon_sight_w148/biting_winds_bow", "weapon_bow_w50/whispering_slab"))
            assertTrue(active.contains(Identifier.parse("destiny:" + route)), route);
        var swapIds = List.of("austringer", "beloved", "ammit_ar2", "the_recluse");
        for (String from : swapIds) for (String to : swapIds) if (!from.equals(to)) {
            boolean w91 = Set.of(from, to).equals(Set.of("austringer", "beloved"));
            String route = (w91 ? "weapon_swap_w91/" : "weapon_swap_w113/") + from + "_to_" + to;
            assertTrue(active.contains(Identifier.parse("destiny:" + route)), route);
        }
        assertEquals(12L, active.stream().filter(id -> id.getPath().startsWith("weapon_swap_w")).count());
        var obsoleteAim = Identifier.parse("destiny:weapon_aim_w70/ace_of_spades");
        assertTrue(sources.contains(obsoleteAim), "Generation inventory includes superseded routes");
        assertFalse(active.contains(obsoleteAim), "Use the runtime W159 sight route");
        assertThrows(UnsupportedOperationException.class,
                () -> active.add(Identifier.parse("destiny:not_an_active_route")));
    }

    private record Input(String context, Map<Integer, String> strings, Map<Integer, Boolean> flags) {}
    private record Case(List<String> values, JsonObject model) {}

    /** Independent concrete interpreter: no optimizer constraint propagation. */
    private static List<JsonObject> evaluate(JsonObject node, Input input) {
        return switch (node.get("type").getAsString()) {
            case "minecraft:empty" -> List.of();
            case "minecraft:model", "minecraft:special", "minecraft:range_dispatch" -> List.of(node);
            case "minecraft:composite" -> {
                var leaves = new ArrayList<JsonObject>();
                for (var child : node.getAsJsonArray("models")) leaves.addAll(evaluate(child.getAsJsonObject(), input));
                yield leaves;
            }
            case "minecraft:condition" -> {
                assertEquals(CMD, node.get("property").getAsString());
                boolean value = input.flags().getOrDefault(index(node), false);
                yield evaluate(node.getAsJsonObject(value ? "on_true" : "on_false"), input);
            }
            case "minecraft:select" -> {
                String property = node.get("property").getAsString();
                String value = switch (property) {
                    case DISPLAY -> input.context();
                    case CMD -> input.strings().get(index(node));
                    default -> throw new AssertionError("Unsupported synthetic property: " + property);
                };
                JsonObject chosen = node.has("fallback") ? node.getAsJsonObject("fallback") : empty();
                for (var entry : node.getAsJsonArray("cases")) {
                    var branch = entry.getAsJsonObject();
                    var when = branch.get("when");
                    boolean matches = when.isJsonArray()
                            ? when.getAsJsonArray().asList().stream().anyMatch(v -> v.getAsString().equals(value))
                            : when.getAsString().equals(value);
                    if (matches) {
                        chosen = branch.getAsJsonObject("model");
                        break;
                    }
                }
                yield evaluate(chosen, input);
            }
            default -> throw new AssertionError("Unsupported synthetic model: " + node);
        };
    }

    private static int index(JsonObject node) { return node.has("index") ? node.get("index").getAsInt() : 0; }
    private static Case one(String value, JsonObject model) { return new Case(List.of(value), model); }
    private static Case many(JsonObject model, String... values) { return new Case(List.of(values), model); }
    private static JsonObject json(String text) { return JsonParser.parseString(text).getAsJsonObject(); }
    private static JsonObject empty() { return json("{\"type\":\"minecraft:empty\"}"); }
    private static JsonObject model(String name) {
        var result = new JsonObject();
        result.addProperty("type", "minecraft:model");
        result.addProperty("model", "destiny:item/synthetic/" + name);
        return result;
    }
    private static JsonObject select(String property, int index, JsonObject fallback, Case... branches) {
        var result = new JsonObject();
        result.addProperty("type", "minecraft:select");
        result.addProperty("property", property);
        if (index >= 0) result.addProperty("index", index);
        if (fallback != null) result.add("fallback", fallback);
        var cases = new JsonArray();
        for (var branch : branches) {
            var entry = new JsonObject();
            JsonElement when;
            if (branch.values().size() == 1) when = new JsonPrimitive(branch.values().getFirst());
            else {
                var values = new JsonArray();
                branch.values().forEach(values::add);
                when = values;
            }
            entry.add("when", when);
            entry.add("model", branch.model());
            cases.add(entry);
        }
        result.add("cases", cases);
        return result;
    }
    private static JsonObject condition(int index, JsonObject yes, JsonObject no) {
        var result = new JsonObject();
        result.addProperty("type", "minecraft:condition");
        result.addProperty("property", CMD);
        if (index >= 0) result.addProperty("index", index);
        result.add("on_true", yes);
        result.add("on_false", no);
        return result;
    }
    private static JsonObject composite(JsonObject... models) {
        var result = new JsonObject();
        result.addProperty("type", "minecraft:composite");
        var children = new JsonArray();
        for (var model : models) children.add(model);
        result.add("models", children);
        return result;
    }
    private static int countType(JsonElement element, String type) {
        if (element.isJsonArray()) {
            int count = 0;
            for (var child : element.getAsJsonArray()) count += countType(child, type);
            return count;
        }
        if (!element.isJsonObject()) return 0;
        var node = element.getAsJsonObject();
        int count = node.has("type") && node.get("type").isJsonPrimitive()
                && type.equals(node.get("type").getAsString()) ? 1 : 0;
        for (var entry : node.entrySet()) count += countType(entry.getValue(), type);
        return count;
    }
}
