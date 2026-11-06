package kim.biryeong.destiny.activity.presentation;

import com.google.gson.*;
import org.junit.jupiter.api.Test;
import java.nio.charset.StandardCharsets;
import java.util.*;
import static org.junit.jupiter.api.Assertions.*;

class ActivityFailureAtlasTest {
    @Test void allTwelveCustomGuiSpritesAreExplicitlyCollectedByTheItemAtlas() throws Exception {
        // Files existing in a ZIP is insufficient:26.3 defaults only scan textures/item and textures/block.
        JsonObject atlas = read("/assets/minecraft/atlases/items.json");
        Set<String> collected = new HashSet<>();
        for (var value : atlas.getAsJsonArray("sources")) {
            var source = value.getAsJsonObject();
            if (source.has("type") && source.get("type").getAsString().equals("minecraft:single"))
                collected.add(source.has("sprite") ? source.get("sprite").getAsString() : source.get("resource").getAsString());
        }
        List<String> names = new ArrayList<>(List.of("restricted", "wipe", "backdrop"));
        for (int n = 0; n < 9; n++) names.add("black_" + n);
        for (String name : names) {
            var model = read("/assets/destiny_activity_failure/models/gui/" + name + ".json");
            String texture = model.getAsJsonObject("textures").get("layer0").getAsString();
            assertTrue(collected.contains(texture), "Sprite absent from actual item atlas sources: " + texture);
            try (var input = getClass().getResourceAsStream("/assets/" + texture.replace(":", "/textures/") + ".png")) {
                assertNotNull(input, texture);
            }
        }
    }
    private JsonObject read(String path) throws Exception {
        try (var input = getClass().getResourceAsStream(path)) {
            assertNotNull(input, path);
            return JsonParser.parseString(new String(input.readAllBytes(), StandardCharsets.UTF_8)).getAsJsonObject();
        }
    }
}
