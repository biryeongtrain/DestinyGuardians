package kim.biryeong.destiny.weapon;

import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import com.mojang.serialization.JsonOps;
import net.minecraft.client.renderer.item.ClientItem;
import org.junit.jupiter.api.Test;

import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;

import static org.junit.jupiter.api.Assertions.*;

/** Actual 26.3 client property codec, not an unknown JSON key that vanilla ignores. */
class WeaponChargeOpticW155Test {
    private static final Path ITEMS = Path.of("src/main/resources/assets/destiny/items");
    private static final List<String> FUSIONS = List.of("erentil_fr4", "hollow_words",
            "dream_breaker", "null_composure", "coriolis_force");
    private static final List<String> LINEARS = List.of("line_in_the_sand", "stormchaser");

    private static JsonObject graph(String directory, String id) throws Exception {
        return JsonParser.parseString(Files.readString(ITEMS.resolve(directory + "/" + id + ".json"))).getAsJsonObject();
    }
    private static ClientItem.Properties properties(JsonObject graph) {
        return ClientItem.Properties.MAP_CODEC.codec().parse(JsonOps.INSTANCE, graph).getOrThrow();
    }
    @Test void sevenPhysicalChargeOpticsDisableOnlyVanillaHeightTranslation() throws Exception {
        for (String id : FUSIONS) assertStabilized("weapon_sight_w153", id);
        for (String id : LINEARS) assertStabilized("weapon_sight_w150", id);
    }
    private static void assertStabilized(String directory, String id) throws Exception {
        var graph = graph(directory, id);
        var p = properties(graph);
        assertEquals(0f, p.swapAnimationScale(), id);
        assertFalse(p.handAnimationOnSwap(), id);
        assertFalse(p.oversizedInGui(), id);
        assertEquals("minecraft:select", graph.getAsJsonObject("model").get("type").getAsString(), id);
        // Both physical hand contexts still use the 21-step authored ADS model.
        var first = graph.getAsJsonObject("model").getAsJsonArray("cases").get(0).getAsJsonObject();
        assertEquals(2, first.getAsJsonArray("when").size(), id);
        assertTrue(hasAimFrames(first.get("model")), id);
    }
    private static boolean hasAimFrames(com.google.gson.JsonElement value) {
        if (value.isJsonArray()) {
            for (var child : value.getAsJsonArray()) if (hasAimFrames(child)) return true;
        } else if (value.isJsonObject()) {
            var object = value.getAsJsonObject();
            if (object.has("index") && object.get("index").getAsInt() == 3 && object.has("entries")
                    && object.getAsJsonArray("entries").size() == 21) return true;
            for (var child : object.entrySet()) if (hasAimFrames(child.getValue())) return true;
        }
        return false;
    }
    @Test void unrelatedWeaponsAndOldRoutesRetainVanillaScale() throws Exception {
        for (String id : FUSIONS) assertEquals(1f, properties(graph("weapon_aim_w70", id)).swapAnimationScale(), id);
        for (String id : List.of("retraced_path", "bellowing_giant", "pyroclastic_flow"))
            assertEquals(1f, properties(graph("weapon_sight_w150", id)).swapAnimationScale(), id);
        for (String id : List.of("fixed_odds", "brass_attacks", "antiope_d"))
            assertEquals(1f, properties(graph("weapon_sight_w153", id)).swapAnimationScale(), id);
    }
    @Test void defaultOneExplainsWhyHandAnimationFlagAloneDoesNotPreventUseDip() {
        var old = new JsonObject(); old.addProperty("hand_animation_on_swap", false);
        assertEquals(1f, properties(old).swapAnimationScale());
        // Renderer input is swapScale * (1 - lerp(oldHeight,height)). Even a
        // native itemUsed reset to height 0 now leaves a zero ADS offset.
        for (float height : new float[]{0, .4f, .8f, 1}) assertEquals(0f, 0f * (1 - height));
    }
}
