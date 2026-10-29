package kim.biryeong.destiny.fx;

import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import org.junit.jupiter.api.Test;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.HashMap;
import java.util.Map;
import java.util.Set;
import static org.junit.jupiter.api.Assertions.*;

/** The installed source-Void revision keeps the accepted Arc motion and rig. */
class HunterSourceW199Test {
    private JsonObject read(String name) throws Exception {
        return JsonParser.parseString(Files.readString(Path.of(name))).getAsJsonObject();
    }
    private Map<String, JsonObject> clips(JsonObject document) {
        var clips = new HashMap<String, JsonObject>();
        for (var entry : document.getAsJsonArray("animations")) {
            var clip = entry.getAsJsonObject();
            assertNull(clips.put(clip.get("name").getAsString(), clip));
        }
        return clips;
    }
    @Test void installedVersionUsesSourceVoidWithoutChangingOtherClipsOrGeometry() throws Exception {
        assertEquals("guardian_hunter_w259_r1", HunterModelAssets.MODEL_NAME);
        assertEquals("/destiny/animation/hunter_w199.animation.json", HunterModelAssets.ANIMATION_RESOURCE);
        var root = "src/main/resources/destiny/animation/";
        var before = read(root + "hunter_w197.animation.json");
        var after = read(root + "hunter_w199.animation.json");
        // W255 retains the W199 baseline and W252 throw while appending source class casts.
        assertEquals("guardian_hunter_w199_r1", after.get("model").getAsString());
        var overlay=clips(read(root+"grenade_w252.animation.json"));
        assertEquals(Set.of("h15_grenade"),overlay.keySet());
        assertNotEquals(clips(after).get("h15_grenade"),overlay.get("h15_grenade"));
        var oldClips = clips(before);
        var newClips = clips(after);
        assertEquals(oldClips.keySet(), newClips.keySet());
        assertEquals(20, newClips.size());
        boolean changed = false;
        for (var name : oldClips.keySet()) {
            if (name.startsWith("h15_super_void"))
                changed |= !oldClips.get(name).equals(newClips.get(name));
            else assertEquals(oldClips.get(name), newClips.get(name), name);
        }
        assertTrue(changed, "Source Void pose must reach the installed resource");
        var oldRig = read("art/blockbench/animations/guardian_hunter_w197_r1.bbmodel");
        var newRig = read("art/blockbench/animations/guardian_hunter_w199_r1.bbmodel");
        for (var field : oldRig.entrySet())
            if (!Set.of("name", "model_identifier", "animations").contains(field.getKey()))
                assertEquals(field.getValue(), newRig.get(field.getKey()), field.getKey());
        assertEquals(4, ShadowshotTiming.DRAW_TICKS);
        assertEquals(7, ShadowshotTiming.RELEASE_TICKS);
    }
}
