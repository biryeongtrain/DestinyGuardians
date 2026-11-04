package kim.biryeong.destiny.fx;

import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import net.minecraft.client.resources.model.cuboid.CuboidModel;
import org.junit.jupiter.api.Test;

import java.io.InputStreamReader;
import java.io.StringReader;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;

import static org.junit.jupiter.api.Assertions.*;

/** Saved resource/native parser gates; actual equipped stacks and pixels have separate gates. */
class ShadowshotH22Test {
    private static final String READY = "h15_super_void", ATTACK = READY + "_attack";
    private static final Set<String> LEGS = Set.of("prl_right_leg", "prfl_right_foreleg", "pll_left_leg", "plfl_left_foreleg");

    private static JsonObject resource(String path) throws Exception {
        try (var stream = ShadowshotH22Test.class.getResourceAsStream(path)) {
            assertNotNull(stream, path);
            return JsonParser.parseReader(new InputStreamReader(stream, StandardCharsets.UTF_8)).getAsJsonObject();
        }
    }

    private static Map<String, JsonObject> clips(String version) throws Exception {
        var result = new HashMap<String, JsonObject>();
        for (var a : resource("/destiny/animation/hunter_" + version + ".animation.json").getAsJsonArray("animations")) {
            var clip = a.getAsJsonObject();
            assertNull(result.put(clip.get("name").getAsString(), clip));
        }
        return result;
    }

    private static Map<String, JsonObject> bones(JsonObject clip) {
        var result = new HashMap<String, JsonObject>();
        for (var a : clip.getAsJsonObject("animators").asMap().values()) {
            var bone = a.getAsJsonObject();
            result.put(bone.get("name").getAsString(), bone);
        }
        return result;
    }

    private static JsonObject at(JsonObject bone, String channel, double time) {
        for (var a : bone.getAsJsonArray("keyframes")) {
            var key = a.getAsJsonObject();
            if (key.get("channel").getAsString().equals(channel) && Math.abs(key.get("time").getAsDouble() - time) < 1e-8)
                return key.getAsJsonArray("data_points").get(0).getAsJsonObject();
        }
        throw new AssertionError("Missing key " + bone.get("name") + " " + channel + " " + time);
    }

    @Test void preservesH21RigOtherSeventeenClipsAndAllCrouchedLegCurves() throws Exception {
        var before = clips("h21"); var after = clips("h22");
        assertEquals(19, after.size()); assertEquals(before.keySet(), after.keySet());
        for (String name : after.keySet()) {
            if (!List.of(READY, ATTACK).contains(name)) assertEquals(before.get(name), after.get(name));
            else {
                assertEquals(before.get(name).get("length"), after.get(name).get("length"));
                assertEquals(before.get(name).get("loop"), after.get(name).get("loop"));
                for (String leg : LEGS) assertEquals(bones(before.get(name)).get(leg), bones(after.get(name)).get(leg));
            }
        }
        var oldArt = JsonParser.parseString(Files.readString(Path.of("art/blockbench/animations/guardian_hunter_h21.bbmodel"))).getAsJsonObject();
        var newArt = JsonParser.parseString(Files.readString(Path.of("art/blockbench/animations/guardian_hunter_h22.bbmodel"))).getAsJsonObject();
        for (var field : oldArt.entrySet()) if (!Set.of("name", "model_identifier", "animations").contains(field.getKey()))
            assertEquals(field.getValue(), newArt.get(field.getKey()), field.getKey());
        assertEquals("guardian_hunter_h22", newArt.get("name").getAsString());
    }

    @Test void readyAndEveryPreReleaseUpperKeyHoldTheSameFullDrawInsteadOfAnUndrawnRest() throws Exception {
        var full = bones(clips("h21").get(ATTACK));
        var after = clips("h22");
        for (String name : List.of(READY, ATTACK)) {
            for (var entry : bones(after.get(name)).entrySet()) {
                String bone = entry.getKey();
                if (LEGS.contains(bone) || bone.equals("cape_cape")) continue;
                var expected = at(full.get(bone), "rotation", .25);
                for (var value : entry.getValue().getAsJsonArray("keyframes")) {
                    var key = value.getAsJsonObject();
                    if (!key.get("channel").getAsString().equals("rotation")) continue;
                    if (name.equals(ATTACK) && key.get("time").getAsDouble() > .30) continue;
                    assertEquals(expected, key.getAsJsonArray("data_points").get(0), name + ":" + bone);
                }
            }
        }
        var attack = bones(after.get(ATTACK)); var ready = bones(after.get(READY));
        for (String bone : attack.keySet()) {
            assertEquals(at(ready.get(bone), "rotation", 0), at(attack.get(bone), "rotation", 0));
            assertEquals(at(ready.get(bone), "rotation", 0), at(attack.get(bone), "rotation", .90));
        }
    }

    @Test void fullDrawRootAndTPlusSevenOriginCorrectionRemainExactlyH21() throws Exception {
        var old = bones(clips("h21").get(ATTACK)); var now = bones(clips("h22").get(ATTACK));
        assertEquals(at(old.get("player_root"), "position", .30), at(now.get("player_root"), "position", .30));
        assertEquals(.90, clips("h22").get(ATTACK).get("length").getAsDouble(), 1e-9);
        for (var clip : clips("h22").values()) for (var v : bones(clip).get("player_root").getAsJsonArray("keyframes")) {
            var key = v.getAsJsonObject();
            if (!key.get("channel").getAsString().equals("position")) continue;
            var point = key.getAsJsonArray("data_points").get(0).getAsJsonObject();
            assertEquals(0, point.get("x").getAsDouble()); assertEquals(0, point.get("z").getAsDouble());
            assertTrue(Double.isFinite(point.get("y").getAsDouble()));
        }
    }

    @Test void paleThreeTimesThickerVStringParsesNativelyAndBothSegmentsMeetTheArrowNock() throws Exception {
        var before = resource("/assets/destiny/models/item/shadow_bow_h20_3.json");
        var after = resource("/assets/destiny/models/item/shadow_bow_h22_drawn.json");
        assertNotNull(CuboidModel.fromStream(new StringReader(after.toString())));
        assertEquals(before.get("display"), after.get("display"));
        assertEquals(before.get("textures"), after.get("textures"));
        var oldElements = before.getAsJsonArray("elements"); var elements = after.getAsJsonArray("elements");
        assertEquals(206, elements.size());
        for (int i = 0; i < elements.size(); i++) {
            if (i != 201 && i != 202) { assertEquals(oldElements.get(i), elements.get(i)); continue; }
            var cord = elements.get(i).getAsJsonObject(); var from = cord.getAsJsonArray("from"); var to = cord.getAsJsonArray("to");
            double length = to.get(1).getAsDouble() - from.get(1).getAsDouble();
            double angle = Math.toRadians(cord.getAsJsonObject("rotation").get("angle").getAsDouble());
            assertEquals(.24, to.get(0).getAsDouble() - from.get(0).getAsDouble(), 1e-9);
            assertEquals(.24, to.get(2).getAsDouble() - from.get(2).getAsDouble(), 1e-9);
            assertTrue(Math.abs(angle) > .38, "A taut V, not the old straight rest string");
            assertEquals(16.24, 11.27 + length * Math.sin(Math.abs(angle)), 1e-8);
            assertEquals(12, length * Math.cos(angle), 1e-8);
            for (var face : cord.getAsJsonObject("faces").asMap().values())
                assertEquals("[12.5,1,13,1.5]", face.getAsJsonObject().getAsJsonArray("uv").toString());
        }
        var definition = resource("/assets/destiny/items/shadow_bow_h22_drawn.json");
        assertEquals("destiny:item/shadow_bow_h22_drawn", definition.getAsJsonObject("model").get("model").getAsString());
    }
}
