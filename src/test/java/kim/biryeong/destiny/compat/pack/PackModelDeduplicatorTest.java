package kim.biryeong.destiny.compat.pack;

import com.google.gson.JsonParser;
import eu.pb4.polymer.resourcepack.api.PackResource;
import org.junit.jupiter.api.Test;
import java.util.Map;
import java.util.Set;
import static org.junit.jupiter.api.Assertions.*;

class PackModelDeduplicatorTest {
    @Test void onlyIdenticalOwnedModelsShareADeterministicCanonicalId() {
        var same = PackResource.fromString("{\"parent\":\"destiny:item/base\",\"display\":{}}");
        var differentPose = PackResource.fromString("{\"parent\":\"destiny:item/base\",\"display\":{\"gui\":{}}}");
        var files = Map.of(
                "assets/destiny/models/weapon_reload/a.json", same,
                "assets/destiny/models/weapon_reload/b.json", same,
                "assets/destiny/models/weapon_reload/c.json", differentPose,
                "assets/destiny/models/weapon_reload/omitted.json", same,
                "assets/foreign/models/weapon_reload/a.json", same,
                "assets/destiny/models/item/base.json", same);
        assertEquals(Map.of("destiny:weapon_reload/b", "destiny:weapon_reload/a"),
                PackModelDeduplicator.aliases(files, Set.of("assets/destiny/models/weapon_reload/omitted.json")));
    }

    @Test void modelReferencesChangeButSelectorsTintsAndTransformsDoNot() {
        String source = """
            {"model":{"type":"minecraft:select","property":"minecraft:custom_model_data",
            "cases":[{"when":"destiny:weapon_reload/b","model":{"type":"minecraft:model",
            "model":"destiny:weapon_reload/b","transformation":[1,0,0,0],"tints":[{"value":42}]}}],
            "fallback":{"type":"minecraft:special","base":"destiny:weapon_reload/b",
            "model":{"type":"minecraft:player_head"}}}}
            """;
        var json = JsonParser.parseString(source);
        var aliases = Map.of("destiny:weapon_reload/b", "destiny:weapon_reload/a");
        assertTrue(PackModelDeduplicator.rewrite(json, aliases, false));
        var model = json.getAsJsonObject().getAsJsonObject("model");
        var entry = model.getAsJsonArray("cases").get(0).getAsJsonObject();
        assertEquals("destiny:weapon_reload/b", entry.get("when").getAsString());
        assertEquals("destiny:weapon_reload/a", entry.getAsJsonObject("model").get("model").getAsString());
        assertEquals(JsonParser.parseString("[1,0,0,0]"), entry.getAsJsonObject("model").get("transformation"));
        assertEquals("destiny:weapon_reload/a", model.getAsJsonObject("fallback").get("base").getAsString());
        var state = JsonParser.parseString("{\"variants\":{\"\":[{\"model\":\"destiny:weapon_reload/b\",\"y\":90}]}}");
        assertTrue(PackModelDeduplicator.rewrite(state, aliases, true));
        assertEquals(90, state.getAsJsonObject().getAsJsonObject("variants").getAsJsonArray("").get(0).getAsJsonObject().get("y").getAsInt());
        assertFalse(PackModelDeduplicator.rewrite(json, aliases, false));
    }
}
