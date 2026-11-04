package kim.biryeong.destiny.fx;

import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import org.junit.jupiter.api.Test;

import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.HashMap;
import java.util.Map;
import java.util.Set;

import static org.junit.jupiter.api.Assertions.*;

/** Runtime-selected resource and the archived rig must agree before a model is installed. */
class HunterSourceW197Test {
    private JsonObject resource(String name) throws Exception {
        try (var stream = getClass().getResourceAsStream("/destiny/animation/" + name)) {
            assertNotNull(stream, name);
            return JsonParser.parseString(new String(stream.readAllBytes(), StandardCharsets.UTF_8)).getAsJsonObject();
        }
    }

    private Map<String, JsonObject> clips(JsonObject document) {
        var result = new HashMap<String, JsonObject>();
        for (var entry : document.getAsJsonArray("animations")) {
            var clip = entry.getAsJsonObject();
            assertNull(result.put(clip.get("name").getAsString(), clip));
        }
        return result;
    }

    @Test void archivedSourceArcRetainsItsVersionAndOtherClips() throws Exception {
        var current = resource("hunter_w197.animation.json");
        assertEquals("guardian_hunter_w197_r1", current.get("model").getAsString());
        var before = JsonParser.parseString(Files.readString(Path.of(
                "art/blockbench/animations/guardian_hunter_h26_r2.bbmodel"))).getAsJsonObject();
        var after = JsonParser.parseString(Files.readString(Path.of(
                "art/blockbench/animations/guardian_hunter_w197_r1.bbmodel"))).getAsJsonObject();
        for (var field : before.entrySet())
            if (!Set.of("name", "model_identifier", "animations").contains(field.getKey()))
                assertEquals(field.getValue(), after.get(field.getKey()), field.getKey());
        var archived = clips(resource("hunter_h26.animation.json"));
        var selected = clips(current);
        assertEquals(20, selected.size());
        assertEquals(archived.keySet(), selected.keySet());
        for (String name : selected.keySet()) {
            if (Set.of("h15_super_arc_start", "h15_super_arc_attack").contains(name))
                assertNotEquals(archived.get(name).get("animators"), selected.get(name).get("animators"), name);
            else assertEquals(archived.get(name), selected.get(name), name);
        }
    }

    @Test void sourceRetimingKeepsServerContactAndReleaseContract() throws Exception {
        var selected = clips(resource("hunter_w197.animation.json"));
        assertEquals(.50, selected.get("h15_super_arc_start").get("length").getAsDouble(), 1e-9);
        assertEquals(.35, selected.get("h15_super_arc_attack").get("length").getAsDouble(), 1e-9);
        assertEquals(11, SuperAttackTiming.ARC_DEPLOY);
        assertEquals(3, SuperAttackTiming.ARC_CONTACT);
        assertEquals(8, SuperAttackTiming.ARC_RECOVERY);
        assertEquals(4, SuperAttackTiming.ARC_DEPLOY_SWING);
        for (String name : Set.of("h15_super_arc_start", "h15_super_arc_attack")) {
            for (var entry : selected.get(name).getAsJsonObject("animators").entrySet()) {
                var animator = entry.getValue().getAsJsonObject();
                var keys = new java.util.HashSet<String>();
                for (var element : animator.getAsJsonArray("keyframes")) {
                    var key = element.getAsJsonObject();
                    double time = key.get("time").getAsDouble();
                    String channel = key.get("channel").getAsString();
                    assertTrue(keys.add(channel + ":" + time));
                    assertTrue(Double.isFinite(time) && time >= 0 && time <= selected.get(name).get("length").getAsDouble());
                    var point = key.getAsJsonArray("data_points").get(0).getAsJsonObject();
                    for (String axis : Set.of("x", "y", "z")) assertTrue(Double.isFinite(point.get(axis).getAsDouble()));
                    if (channel.equals("position") && animator.get("name").getAsString().equals("player_root")) {
                        assertEquals(0, point.get("x").getAsDouble());
                        assertEquals(0, point.get("z").getAsDouble());
                    }
                }
            }
        }
    }
}
