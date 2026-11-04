package kim.biryeong.destiny.fx;

import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import net.minecraft.world.entity.player.Input;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.HashSet;
import java.util.UUID;

import static org.junit.jupiter.api.Assertions.*;

/** Pure clip/installation/completion contracts; no live server or BetterModel scheduler required. */
class HunterAnimationH15Test {
    @TempDir Path dir;

    private JsonArray clips() throws Exception {
        try (var stream = getClass().getResourceAsStream(HunterModelAssets.ANIMATION_RESOURCE)) {
            assertNotNull(stream);
            return JsonParser.parseReader(new InputStreamReader(stream, StandardCharsets.UTF_8))
                    .getAsJsonObject().getAsJsonArray("animations");
        }
    }

    @Test
    void remapsNewTemplateUuidsWithoutChangingSkinRigOrTemplate() throws Exception {
        JsonArray clips = clips();
        JsonObject template = JsonParser.parseString("""
                {"groups":[],"elements":[{"name":"skin","uv_offset":[16,24]}],
                 "outliner":[],"textures":[{"name":"skin_template"}],"animations":[{"name":"artist_idle"}]}
                """).getAsJsonObject();
        var seen = new HashSet<String>();
        for (var clip : clips) for (var value : clip.getAsJsonObject().getAsJsonObject("animators").asMap().values()) {
            String name = value.getAsJsonObject().get("name").getAsString();
            if (seen.add(name)) {
                JsonObject group = new JsonObject();
                group.addProperty("name", name);
                group.addProperty("uuid", UUID.randomUUID().toString());
                template.getAsJsonArray("groups").add(group);
            }
        }
        JsonObject before = template.deepCopy();
        JsonObject result = HunterModelAssets.buildModel(template, clips);
        assertEquals(before, template);
        for (String section : new String[]{"groups", "elements", "outliner", "textures"})
            assertEquals(template.get(section), result.get(section), section);
        assertEquals(clips.size() + 1, result.getAsJsonArray("animations").size());
        assertEquals("artist_idle", result.getAsJsonArray("animations").get(0).getAsJsonObject().get("name").getAsString());
        var uuids = new HashSet<String>();
        template.getAsJsonArray("groups").forEach(g -> uuids.add(g.getAsJsonObject().get("uuid").getAsString()));
        for (int i = 1; i <= clips.size(); i++)
            assertTrue(uuids.containsAll(result.getAsJsonArray("animations").get(i).getAsJsonObject()
                    .getAsJsonObject("animators").keySet()));
    }

    @Test
    void installedArtistModelsAreByteForBytePreserved() throws Exception {
        Path legacy = dir.resolve("guardian_hunter.bbmodel");
        Path target = dir.resolve(HunterModelAssets.MODEL_NAME + ".bbmodel");
        Files.writeString(legacy, "artist legacy contents");
        JsonObject initial = new JsonObject();
        initial.addProperty("name", "first installation");
        assertTrue(HunterModelAssets.installIfAbsent(target, initial));
        String installed = Files.readString(target);
        assertFalse(HunterModelAssets.installIfAbsent(target, new JsonObject()));
        assertEquals(installed, Files.readString(target));
        assertEquals("artist legacy contents", Files.readString(legacy));
    }

    @Test
    void incompatibleTemplateIsRejectedBeforeAnyInstall() throws Exception {
        JsonObject incomplete = JsonParser.parseString("{\"groups\":[],\"animations\":[]}").getAsJsonObject();
        assertThrows(IllegalArgumentException.class, () -> HunterModelAssets.buildModel(incomplete, clips()));
        assertFalse(Files.exists(dir.resolve(HunterModelAssets.MODEL_NAME + ".bbmodel")));
    }

    @Test
    void earlyDuplicateAndStaleBoneCallbacksCannotFinishANewerRun() {
        var old = new PlayerAnimations.Run("old_attack", 100, 8);
        var current = new PlayerAnimations.Run("new_release", 102, 12);
        old.completed.set(true);
        old.completed.set(true);
        assertTrue(old.finished(108));
        assertFalse(current.finished(108));
        current.completed.set(true);
        assertFalse(current.finished(113), "A short bone must not truncate the release");
        assertTrue(current.finished(114));
    }

    @Test
    void missingCompletionUsesBoundedGraceWithoutSyntheticTicks() {
        var release = new PlayerAnimations.Run("release", 200, 12);
        assertFalse(release.finished(217));
        assertTrue(release.finished(218));
        assertTrue(release.finished(250));
    }

    @Test
    void cardinalOpposedAndDiagonalInputsSelectDocumentedClips() {
        assertEquals("h15_roll_forward", PlayerAnimations.rollAnimation(Input.EMPTY));
        assertEquals("h15_roll_back", PlayerAnimations.rollAnimation(new Input(false, true, false, false, false, false, false)));
        assertEquals("h15_roll_left", PlayerAnimations.rollAnimation(new Input(false, false, true, false, false, false, false)));
        assertEquals("h15_roll_right", PlayerAnimations.rollAnimation(new Input(false, false, false, true, false, false, false)));
        assertEquals("h15_roll_forward", PlayerAnimations.rollAnimation(new Input(true, false, true, false, false, false, false)));
        assertEquals("h15_roll_forward", PlayerAnimations.rollAnimation(new Input(true, true, true, true, false, false, false)));
    }
}
