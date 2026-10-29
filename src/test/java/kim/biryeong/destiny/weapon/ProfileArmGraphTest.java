package kim.biryeong.destiny.weapon;

import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import net.minecraft.world.item.component.CustomModelData;
import org.junit.jupiter.api.Test;

import java.lang.reflect.Method;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashSet;
import java.util.List;

import static org.junit.jupiter.api.Assertions.*;

/** Pure JUnit: no Bootstrap, codec registry, server, client, pack generation or fixture writes. */
class ProfileArmGraphTest {
    private static final String PREFIX = "destiny:skin_arm_w204/poses/";
    private static final Path ITEMS = Path.of("src/main/resources/assets/destiny/items/weapon_hands_w201");

    @Test void projectionRemovesWeaponTintsAndEmptyCompositesWithoutAliasing() {
        var arm = pose("right_classic");
        arm.add("tints", JsonParser.parseString("[{\"type\":\"minecraft:custom_model_data\",\"index\":64}]"));
        arm.add("transformation", JsonParser.parseString("{\"translation\":[1,2,3]}"));
        var source = composite(empty(), model("destiny:weapon/test"), composite(empty(), arm));
        var before = source.deepCopy();
        var projected = ProfileArmGraph.armsOnly(source);
        assertEquals("minecraft:model", projected.get("type").getAsString());
        assertFalse(projected.has("tints"));
        assertEquals(arm.get("transformation"), projected.get("transformation"));
        projected.getAsJsonObject("transformation").addProperty("changed", true);
        assertEquals(before, source);
        assertEquals(empty(), ProfileArmGraph.armsOnly(composite(empty(), model("minecraft:stick"))));
        assertEquals(empty(), ProfileArmGraph.armsOnly(model("destiny:skin_arm_w204/right_classic")));
        assertEquals(empty(), ProfileArmGraph.armsOnly(model("other:skin_arm_w204/poses/right_classic")));
    }

    @Test void compositeRetainsOrderDuplicatesAndReadOnlyInputsAndResult() {
        var source = composite(pose("left"), composite(empty(), pose("right")), pose("left"));
        var before = source.deepCopy();
        var data = data(List.of(7f), List.of(true), List.of("hip"));
        var graph = ProfileArmGraph.armsOnly(source);
        var graphBefore = graph.deepCopy();
        var selected = ProfileArmGraph.select(graph, data, false, false);
        assertEquals(ids("left", "right", "left"), selected);
        assertThrows(UnsupportedOperationException.class, () -> selected.add("bad"));
        assertEquals(before, source);
        assertEquals(graphBefore, graph);
        assertEquals(List.of(7f), data.floats());
        assertEquals(List.of(true), data.flags());
        assertEquals(List.of("hip"), data.strings());
    }

    @Test void conditionDefaultsAndVirtualFlagsAreIndependentOfPhysicalCmd() {
        var graph = ProfileArmGraph.armsOnly(condition(8,
                condition(9, condition(1, pose("slim_true"), pose("slim_false")),
                        condition(0, pose("classic_true"), pose("classic_false"))), pose("hidden")));
        assertEquals(ids("classic_false"), ProfileArmGraph.select(graph, null, false, false));
        assertEquals(ids("slim_false"), ProfileArmGraph.select(graph, CustomModelData.EMPTY, true, false));
        assertEquals(ids("slim_true"), ProfileArmGraph.select(graph,
                data(List.of(), List.of(false, true), List.of()), true, false));
        var flags = new ArrayList<>(Collections.nCopies(10, false));
        flags.set(0, true); flags.set(9, true); // physical 8=false,9=true must both be overridden
        var physical = data(List.of(), List.copyOf(flags), List.of());
        assertEquals(ids("classic_true"), ProfileArmGraph.select(graph, physical, false, false));
        assertEquals(flags, physical.flags());
        assertEquals(pose("same"), ProfileArmGraph.armsOnly(condition(0, pose("same"), pose("same"))));
        var implicitIndex = condition(0, pose("yes"), pose("no")); implicitIndex.remove("index");
        assertEquals(ids("yes"), ProfileArmGraph.select(ProfileArmGraph.armsOnly(implicitIndex),
                data(List.of(), List.of(true), List.of()), false, false));
    }

    @Test void selectMatchesScalarAndArrayStringsMissingIsNotEmptyStringAndLeftOnlyChoosesContext() {
        var strings = json("""
                {"type":"minecraft:select","property":"minecraft:custom_model_data","cases":[
                  {"when":["hip","ads"],"model":{"type":"minecraft:model","model":"destiny:skin_arm_w204/poses/aim"}},
                  {"when":"","model":{"type":"minecraft:model","model":"destiny:skin_arm_w204/poses/blank"}}
                ],"fallback":{"type":"minecraft:model","model":"destiny:skin_arm_w204/poses/default"}}
                """);
        var graph = ProfileArmGraph.armsOnly(strings);
        assertEquals(ids("default"), ProfileArmGraph.select(graph, null, false, false));
        assertEquals(ids("default"), ProfileArmGraph.select(graph, CustomModelData.EMPTY, false, false));
        assertEquals(ids("blank"), ProfileArmGraph.select(graph, data(List.of(), List.of(), List.of("")), false, false));
        for (String key : List.of("hip", "ads"))
            assertEquals(ids("aim"), ProfileArmGraph.select(graph, data(List.of(), List.of(), List.of(key)), false, false));
        var context = select("minecraft:display_context", "firstperson_lefthand", pose("left"), pose("right"));
        assertEquals(ids("left"), ProfileArmGraph.select(ProfileArmGraph.armsOnly(context), null, false, true));
        assertEquals(ids("right"), ProfileArmGraph.select(ProfileArmGraph.armsOnly(context), null, false, false));
        context.getAsJsonArray("cases").get(0).getAsJsonObject().add("model", strings);
        assertEquals(ids("aim"), ProfileArmGraph.select(ProfileArmGraph.armsOnly(context),
                data(List.of(), List.of(), List.of("ads")), false, true));
    }

    @Test void selectMinimizesSameBranchesAndValidatesDeadCasesBeforeCollapsing() {
        var source = select("minecraft:custom_model_data", "hip", pose("same"), pose("same"));
        assertEquals(pose("same"), ProfileArmGraph.armsOnly(source));
        var extra = new JsonObject(); extra.addProperty("when", "ads"); extra.add("model", pose("other"));
        source.getAsJsonArray("cases").add(extra);
        extra = extra.deepCopy(); extra.addProperty("when", "inspect"); source.getAsJsonArray("cases").add(extra);
        var graph = ProfileArmGraph.armsOnly(source);
        assertEquals(1, graph.getAsJsonArray("cases").size());
        assertEquals(JsonParser.parseString("[\"ads\",\"inspect\"]"),
                graph.getAsJsonArray("cases").get(0).getAsJsonObject().get("when"));
        source.getAsJsonArray("cases").get(0).getAsJsonObject().addProperty("when", "ads");
        assertThrows(IllegalArgumentException.class, () -> ProfileArmGraph.armsOnly(source));
    }

    @Test void rangeUsesNativeFloorScaleMissingDefaultAndNanFallbackAcrossAllSupportedLanes() {
        for (int index = 1; index <= 6; index++) {
            var source = range(index, new float[]{0f, .25f, .5f, 1f}, pose("fallback"));
            var graph = ProfileArmGraph.armsOnly(source);
            assertEquals(ids("frame0"), ProfileArmGraph.select(graph, null, false, false));
            assertEquals(ids("frame0"), ProfileArmGraph.select(graph, CustomModelData.EMPTY, false, false));
            for (float value : new float[]{Float.NEGATIVE_INFINITY, -.1f, -0f, 0f, Math.nextDown(.25f), .25f,
                    Math.nextUp(.25f), .75f, Float.POSITIVE_INFINITY, Float.NaN}) {
                String expected = Float.isNaN(value) || value < 0 ? "fallback"
                        : value < .25f ? "frame0" : value < .5f ? "frame1" : value < 1f ? "frame2" : "frame3";
                assertEquals(ids(expected), ProfileArmGraph.select(graph, lane(index, value), false, false));
            }
            source.addProperty("scale", 2f);
            assertEquals(ids("frame2"), ProfileArmGraph.select(ProfileArmGraph.armsOnly(source), lane(index, .25f), false, false));
            source.addProperty("scale", -2f);
            assertEquals(ids("frame2"), ProfileArmGraph.select(ProfileArmGraph.armsOnly(source), lane(index, -.25f), false, false));
            source.addProperty("scale", 0f);
            assertEquals(ids("fallback"), ProfileArmGraph.select(ProfileArmGraph.armsOnly(source), lane(index, Float.POSITIVE_INFINITY), false, false));
            source.addProperty("scale", Float.NaN);
            assertEquals(ids("fallback"), ProfileArmGraph.select(ProfileArmGraph.armsOnly(source), lane(index, .5f), false, false));
            source.addProperty("scale", Float.POSITIVE_INFINITY);
            assertEquals(ids("frame3"), ProfileArmGraph.select(ProfileArmGraph.armsOnly(source), lane(index, .5f), false, false));
            assertEquals(ids("fallback"), ProfileArmGraph.select(ProfileArmGraph.armsOnly(source), null, false, false));
        }
    }

    @Test void rangeEmptyMissingFallbackAndRedundantEntriesKeepFallbackSemantics() {
        var source = range(1, new float[]{0f, .5f, 1f}, pose("fallback"));
        source.remove("fallback");
        assertEquals(List.of(), ProfileArmGraph.select(ProfileArmGraph.armsOnly(source), lane(1, Float.NaN), false, false));
        assertEquals(List.of(), ProfileArmGraph.select(ProfileArmGraph.armsOnly(source), lane(1, -.1f), false, false));
        source.add("entries", new JsonArray());
        assertEquals(empty(), ProfileArmGraph.armsOnly(source));
        source.add("fallback", pose("fallback"));
        assertEquals(pose("fallback"), ProfileArmGraph.armsOnly(source));
        source = range(1, new float[]{0f, .25f, .5f, 1f}, pose("fallback"));
        var entries = source.getAsJsonArray("entries");
        entries.get(0).getAsJsonObject().add("model", pose("fallback"));
        entries.get(2).getAsJsonObject().add("model", pose("frame1"));
        var graph = ProfileArmGraph.armsOnly(source);
        assertEquals(2, graph.getAsJsonArray("entries").size());
        assertEquals(ids("fallback"), ProfileArmGraph.select(graph, lane(1, Float.NaN), false, false));
        assertEquals(ids("frame1"), ProfileArmGraph.select(graph, lane(1, .75f), false, false));
        var noFallback = select("minecraft:custom_model_data", "hip", pose("aim"), empty());
        noFallback.remove("fallback");
        assertEquals(List.of(), ProfileArmGraph.select(ProfileArmGraph.armsOnly(noFallback), null, false, false));
    }

    @Test void signedZeroMatchesNativeSmallAndBinarySearchAndSurvivesMinimization() throws Exception {
        for (int count : List.of(2, 15, 16, 61)) {
            float[] thresholds = new float[count];
            for (int i = 1; i < count; i++) thresholds[i] = i;
            var source = range(1, thresholds, pose("fallback"));
            var graph = ProfileArmGraph.armsOnly(source);
            for (float value : new float[]{-0f, 0f, Math.nextDown(0f), Math.nextUp(0f), Float.NEGATIVE_INFINITY, Float.POSITIVE_INFINITY}) {
                int nativeIndex = nativeFloor(thresholds, value);
                assertEquals(ids(nativeIndex < 0 ? "fallback" : "frame" + nativeIndex),
                        ProfileArmGraph.select(graph, lane(1, value), false, false), "count=" + count + " value=" + value);
            }
            for (var e : source.getAsJsonArray("entries")) e.getAsJsonObject().add("model", pose("same"));
            graph = ProfileArmGraph.armsOnly(source);
            assertEquals(ids(count < 16 ? "same" : "fallback"), ProfileArmGraph.select(graph, lane(1, -0f), false, false));
        }
        var source = range(1, new float[]{-0f, +0f}, pose("fallback"));
        assertEquals(ids("frame1"), ProfileArmGraph.select(ProfileArmGraph.armsOnly(source), lane(1, -0f), false, false));
    }

    @Test void rejectsUnsupportedSelectorTypesPropertiesLanesFieldsAndMalformedInputs() {
        for (var source : List.of(json("{\"type\":\"minecraft:special\"}"),
                select("minecraft:main_hand", "left", pose("x"), empty()),
                condition(2, empty(), empty()), range(0, new float[]{0}, empty()), range(7, new float[]{0}, empty()))) {
            assertThrows(IllegalArgumentException.class, () -> ProfileArmGraph.armsOnly(source));
            assertThrows(IllegalArgumentException.class, () -> ProfileArmGraph.select(source, null, false, false));
        }
        var stringIndex = select("minecraft:custom_model_data", "a", empty(), empty()); stringIndex.addProperty("index", 1);
        assertThrows(IllegalArgumentException.class, () -> ProfileArmGraph.armsOnly(stringIndex));
        var fractional = condition(0, empty(), empty()); fractional.addProperty("index", .5);
        assertThrows(IllegalArgumentException.class, () -> ProfileArmGraph.armsOnly(fractional));
        var badField = range(1, new float[]{0}, empty()); badField.addProperty("normalize", true);
        assertThrows(IllegalArgumentException.class, () -> ProfileArmGraph.armsOnly(badField));
        var dead = condition(8, pose("yes"), json("{\"type\":\"minecraft:bundle/selected_item\"}"));
        assertThrows(IllegalArgumentException.class, () -> ProfileArmGraph.armsOnly(dead));
        var numericWhen = select("minecraft:custom_model_data", "a", empty(), empty());
        numericWhen.getAsJsonArray("cases").get(0).getAsJsonObject().addProperty("when", 1);
        assertThrows(IllegalArgumentException.class, () -> ProfileArmGraph.armsOnly(numericWhen));
        assertThrows(IllegalArgumentException.class, () -> ProfileArmGraph.armsOnly(new JsonObject()));
    }

    @Test void rejectsUnsortedDuplicateNonFiniteAndFloatRoundedDuplicateThresholdsBeforeSimplifying() {
        for (float[] values : List.of(new float[]{1, 0}, new float[]{0, 0}, new float[]{Float.NaN}, new float[]{Float.POSITIVE_INFINITY})) {
            var source = range(1, values, empty());
            assertThrows(IllegalArgumentException.class, () -> ProfileArmGraph.armsOnly(source));
            assertThrows(IllegalArgumentException.class, () -> ProfileArmGraph.select(source, null, false, false));
        }
        var rounded = range(1, new float[]{1, 2}, empty());
        rounded.getAsJsonArray("entries").get(1).getAsJsonObject().addProperty("threshold", 1.00000000001);
        assertThrows(IllegalArgumentException.class, () -> ProfileArmGraph.armsOnly(rounded));
    }

    @Test void representativeRealRoutesMatchOriginalNativeSelectorsWithAtMostFourArms() throws Exception {
        for (String route : List.of("weapon/ace_of_spades", "weapon_reload_w221_pyroclastic_flow/pyroclastic_flow",
                "weapon_reload_w222_biting_winds/biting_winds", "weapon_insert_w221_ikelos_sg_v1_0_1/ikelos_sg_v1_0_1")) {
            var source = json(Files.readString(ITEMS.resolve(route + ".json"))).getAsJsonObject("model");
            var before = source.deepCopy();
            var graph = ProfileArmGraph.armsOnly(source);
            assertFalse(graph.toString().contains("\"tints\""), route);
            assertTrue(graph.toString().length() < source.toString().length() / 2, route);
            for (String mode : List.of("hip", "ads", "inspect", "scope", "unknown"))
                for (boolean slim : List.of(false, true))
                    for (boolean left : List.of(false, true)) {
                        var flags = new ArrayList<>(Collections.nCopies(10, false));
                        flags.set(0, true); flags.set(1, true); flags.set(8, true); flags.set(9, slim);
                        var cmd = data(List.of(0f, .5f, .5f, .5f, 2.5f, .5f, .5f), flags, List.of(mode));
                        var expected = original(source, cmd, left);
                        var actual = ProfileArmGraph.select(graph, cmd, slim, left);
                        assertEquals(expected, actual, route + "/" + mode + "/" + slim + "/" + left);
                        assertFalse(actual.isEmpty(), route);
                        assertTrue(actual.size() <= 4, route);
                    }
            assertEquals(before, source, route);
            System.out.println("W238 route " + route + ": " + source.toString().length() + " -> " + graph.toString().length() + " JSON chars");
        }
    }

    @Test void actualUnique61FrameRangeBoundarySubsetMatchesNativeAndKeepsNanFallback() throws Exception {
        var source = json(Files.readString(ITEMS.resolve("weapon_reload_w221_pyroclastic_flow/pyroclastic_flow.json")))
                .getAsJsonObject("model");
        var graph = ProfileArmGraph.armsOnly(source);
        var range = find61(source);
        assertNotNull(range);
        var entries = range.getAsJsonArray("entries");
        var unique = new HashSet<Float>();
        for (var e : entries) unique.add(e.getAsJsonObject().get("threshold").getAsFloat());
        assertEquals(61, unique.size());
        for (int frame : new int[]{0, 1, 2, 15, 16, 29, 30, 59, 60}) {
            float threshold = entries.get(frame).getAsJsonObject().get("threshold").getAsFloat();
            for (float value : new float[]{Math.nextDown(threshold), threshold, Math.nextUp(threshold)}) {
                for (boolean slim : List.of(false, true)) {
                    var flags = new ArrayList<>(Collections.nCopies(10, false)); flags.set(8, true); flags.set(9, slim);
                    var cmd = data(List.of(0f, value), flags, List.of("hip"));
                    for (boolean left : List.of(false, true))
                        assertEquals(original(source, cmd, left), ProfileArmGraph.select(graph, cmd, slim, left),
                                "frame=" + frame + " value=" + value);
                }
            }
        }
        var nanFlags = new ArrayList<>(Collections.nCopies(10, false)); nanFlags.set(8, true);
        var nan = data(List.of(0f, Float.NaN), nanFlags, List.of("hip"));
        assertEquals(original(source, nan, false), ProfileArmGraph.select(graph, nan, false, false));
        assertFalse(ProfileArmGraph.select(graph, nan, false, false).isEmpty());
    }

    // Independent oracle: evaluate the unprojected source; use vanilla's actual floor method.
    // flags[8,9] are supplied physically here rather than applying the production virtual override.
    private static List<String> original(JsonObject node, CustomModelData cmd, boolean left) throws Exception {
        var out = new ArrayList<String>();
        switch (node.get("type").getAsString()) {
            case "minecraft:empty" -> { }
            case "minecraft:model" -> {
                String id = node.get("model").getAsString(); if (id.startsWith(PREFIX)) out.add(id);
            }
            case "minecraft:composite" -> {
                for (var child : node.getAsJsonArray("models")) out.addAll(original(child.getAsJsonObject(), cmd, left));
            }
            case "minecraft:condition" -> {
                int index = node.has("index") ? node.get("index").getAsInt() : 0;
                out.addAll(original(node.getAsJsonObject(Boolean.TRUE.equals(cmd.getBoolean(index)) ? "on_true" : "on_false"), cmd, left));
            }
            case "minecraft:select" -> {
                String key = node.get("property").getAsString().equals("minecraft:display_context")
                        ? (left ? "firstperson_lefthand" : "firstperson_righthand") : cmd.getString(0);
                JsonObject chosen = node.has("fallback") ? node.getAsJsonObject("fallback") : empty();
                for (var c : node.getAsJsonArray("cases")) {
                    var e = c.getAsJsonObject(); var when = e.get("when");
                    boolean match = when.isJsonArray() ? when.getAsJsonArray().asList().stream().anyMatch(v -> v.getAsString().equals(key))
                            : when.getAsString().equals(key);
                    if (match) chosen = e.getAsJsonObject("model");
                }
                out.addAll(original(chosen, cmd, left));
            }
            case "minecraft:range_dispatch" -> {
                var entries = node.getAsJsonArray("entries");
                float[] thresholds = new float[entries.size()];
                for (int i = 0; i < thresholds.length; i++) thresholds[i] = entries.get(i).getAsJsonObject().get("threshold").getAsFloat();
                Float stored = cmd.getFloat(node.get("index").getAsInt());
                float value = (stored == null ? 0f : stored) * (node.has("scale") ? node.get("scale").getAsFloat() : 1f);
                int index = Float.isNaN(value) ? -1 : nativeFloor(thresholds, value);
                var chosen = index < 0 ? (node.has("fallback") ? node.getAsJsonObject("fallback") : empty())
                        : entries.get(index).getAsJsonObject().getAsJsonObject("model");
                out.addAll(original(chosen, cmd, left));
            }
            default -> throw new AssertionError(node.get("type"));
        }
        return out;
    }

    private static int nativeFloor(float[] thresholds, float value) throws Exception {
        Method method = Class.forName("net.minecraft.client.renderer.item.RangeSelectItemModel")
                .getDeclaredMethod("lastIndexLessOrEqual", float[].class, float.class);
        method.setAccessible(true);
        return (int) method.invoke(null, thresholds, value);
    }

    private static JsonObject find61(JsonObject node) {
        if (node.has("entries") && node.getAsJsonArray("entries").size() == 61) return node;
        for (String key : List.of("cases", "entries", "models")) if (node.has(key))
            for (var e : node.getAsJsonArray(key)) {
                var child = e.getAsJsonObject();
                var found = find61(key.equals("models") ? child : child.getAsJsonObject("model"));
                if (found != null) return found;
            }
        for (String key : List.of("on_true", "on_false", "fallback")) if (node.has(key)) {
            var found = find61(node.getAsJsonObject(key)); if (found != null) return found;
        }
        return null;
    }

    private static JsonObject json(String text) { return JsonParser.parseString(text).getAsJsonObject(); }
    private static JsonObject empty() { return json("{\"type\":\"minecraft:empty\"}"); }
    private static JsonObject model(String id) {
        var node = new JsonObject(); node.addProperty("type", "minecraft:model"); node.addProperty("model", id); return node;
    }
    private static JsonObject pose(String suffix) { return model(PREFIX + suffix); }
    private static List<String> ids(String... suffixes) { return List.of(suffixes).stream().map(s -> PREFIX + s).toList(); }
    private static CustomModelData data(List<Float> floats, List<Boolean> flags, List<String> strings) {
        return new CustomModelData(List.copyOf(floats), List.copyOf(flags), List.copyOf(strings), List.of(0x123456));
    }
    private static CustomModelData lane(int index, float value) {
        var floats = new ArrayList<>(Collections.nCopies(index + 1, 0f)); floats.set(index, value);
        return data(floats, List.of(), List.of());
    }
    private static JsonObject composite(JsonObject... models) {
        var node = json("{\"type\":\"minecraft:composite\"}"); var array = new JsonArray();
        for (var model : models) array.add(model); node.add("models", array); return node;
    }
    private static JsonObject condition(int index, JsonObject yes, JsonObject no) {
        var node = json("{\"type\":\"minecraft:condition\",\"property\":\"minecraft:custom_model_data\"}");
        node.addProperty("index", index); node.add("on_true", yes); node.add("on_false", no); return node;
    }
    private static JsonObject select(String property, String when, JsonObject model, JsonObject fallback) {
        var node = json("{\"type\":\"minecraft:select\"}"); node.addProperty("property", property);
        var entry = new JsonObject(); entry.addProperty("when", when); entry.add("model", model);
        var cases = new JsonArray(); cases.add(entry); node.add("cases", cases); node.add("fallback", fallback); return node;
    }
    private static JsonObject range(int index, float[] thresholds, JsonObject fallback) {
        var node = json("{\"type\":\"minecraft:range_dispatch\",\"property\":\"minecraft:custom_model_data\"}");
        node.addProperty("index", index); node.add("fallback", fallback); var entries = new JsonArray();
        for (int i = 0; i < thresholds.length; i++) {
            var entry = new JsonObject(); entry.addProperty("threshold", thresholds[i]); entry.add("model", pose("frame" + i)); entries.add(entry);
        }
        node.add("entries", entries); return node;
    }
}
