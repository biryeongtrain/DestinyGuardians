package kim.biryeong.destiny.fx;

import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import org.junit.jupiter.api.Test;

import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;

import static org.junit.jupiter.api.Assertions.*;

/** Resource contracts, not proof of the engine's handed transforms or rendered pose. */
class ShadowBowH19Test {
    private JsonObject resource(String path) throws Exception {
        try (var stream = getClass().getResourceAsStream("/assets/destiny/" + path)) {
            assertNotNull(stream, path);
            return JsonParser.parseReader(new InputStreamReader(stream, StandardCharsets.UTF_8)).getAsJsonObject();
        }
    }

    @Test void bothStatesResolveAndKeepTheSameLeftHandGrip() throws Exception {
        JsonObject rest = resource("models/item/shadow_bow_h19.json");
        JsonObject drawn = resource("models/item/shadow_bow_h19_drawn.json");
        assertEquals(rest.get("textures"), drawn.get("textures"));
        assertEquals(rest.get("display"), drawn.get("display"));
        assertEquals("[0,-90,0]", rest.getAsJsonObject("display").getAsJsonObject("thirdperson_lefthand")
                .get("rotation").toString());
        for (String name : new String[]{"shadow_bow_h19", "shadow_bow_h19_drawn"})
            assertEquals("destiny:item/" + name, resource("items/" + name + ".json")
                    .getAsJsonObject("model").get("model").getAsString());
    }

    @Test void drawAddsVStringAndNockedArrowWithoutChangingTheBowLimbs() throws Exception {
        var rest = resource("models/item/shadow_bow_h19.json").getAsJsonArray("elements");
        var drawn = resource("models/item/shadow_bow_h19_drawn.json").getAsJsonArray("elements");
        assertEquals(202, rest.size());
        assertEquals(206, drawn.size()); // Remove one straight string, add two strings and three arrow parts.
        int unchanged = 0;
        for (var element : rest) if (drawn.contains(element)) unchanged++;
        assertEquals(rest.size() - 1, unchanged);
        int angledStrings = 0;
        for (var value : drawn) {
            var element = value.getAsJsonObject();
            for (int axis = 0; axis < 3; axis++)
                assertTrue(element.getAsJsonArray("to").get(axis).getAsDouble()
                        > element.getAsJsonArray("from").get(axis).getAsDouble(), "Nonzero item cube");
            if (!rest.contains(value) && element.has("rotation")) {
                assertEquals(22.5, Math.abs(element.getAsJsonObject("rotation").get("angle").getAsDouble()));
                angledStrings++;
            }
        }
        assertEquals(2, angledStrings);
    }
}
