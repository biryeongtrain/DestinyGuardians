package kim.biryeong.destiny.fx;

import com.google.gson.*;
import org.junit.jupiter.api.Test;
import java.nio.file.*;
import java.util.*;
import static org.junit.jupiter.api.Assertions.*;

class SwordPoseW146Test {
    private JsonArray clips() throws Exception {
        return JsonParser.parseString(Files.readString(Path.of("src/main/resources" + SwordPoseW146Assets.RESOURCE)))
                .getAsJsonObject().getAsJsonArray("animations");
    }
    @Test void versionedInstallPreservesTemplateAndHistoricalSwordModels() throws Exception {
        var template = JsonParser.parseString("{\"groups\":[],\"elements\":[{\"name\":\"artist_skin\"}],\"animations\":[{\"name\":\"artist_idle\"}]}").getAsJsonObject();
        var names = new HashSet<String>();
        for (var c : clips()) for (var a : c.getAsJsonObject().getAsJsonObject("animators").asMap().values()) {
            String name = a.getAsJsonObject().get("name").getAsString();
            if (names.add(name)) {
                var group = new JsonObject(); group.addProperty("name", name); group.addProperty("uuid", UUID.randomUUID().toString());
                template.getAsJsonArray("groups").add(group);
            }
        }
        var before = template.deepCopy(); var installed = SwordPoseW146Assets.buildModel(template, clips());
        assertEquals(before, template);
        assertEquals(before.get("groups"), installed.get("groups"));
        assertEquals(before.get("elements"), installed.get("elements"));
        assertEquals(13, installed.getAsJsonArray("animations").size());
        assertEquals("guardian_sword_w146", installed.get("name").getAsString());
        assertEquals("guardian_sword_w55", SwordStanceAssets.MODEL_NAME);
        assertThrows(IllegalArgumentException.class, () -> SwordPoseW146Assets.buildModel(template, new JsonArray()));
    }
    @Test void allAttackLengthsRemainCompatibleWithAuthoritativeContactTiming() throws Exception {
        var old = JsonParser.parseString(Files.readString(Path.of("src/main/resources/destiny/animation/sword_w53.animation.json")))
                .getAsJsonObject().getAsJsonArray("animations");
        var current = clips(); assertEquals(12, current.size());
        for (int i=0; i<8; i++) {
            assertEquals(old.get(i).getAsJsonObject().get("name"), current.get(i).getAsJsonObject().get("name"));
            assertEquals(old.get(i).getAsJsonObject().get("length"), current.get(i).getAsJsonObject().get("length"));
            assertEquals("once", current.get(i).getAsJsonObject().get("loop").getAsString());
        }
        for (int i=8; i<12; i++) assertEquals("loop", current.get(i).getAsJsonObject().get("loop").getAsString());
    }
    @Test void productionUsesNewVersionWithoutReplacingOldInstalledArtistFiles() throws Exception {
        var source = Files.readString(Path.of("src/main/java/kim/biryeong/destiny/fx/PlayerAnimations.java"));
        assertTrue(source.contains("BetterModel.limb(SwordPoseW146Assets.MODEL_NAME)"));
        assertTrue(Files.readString(Path.of("src/main/java/kim/biryeong/destiny/DestinyGuardians.java")).contains("SwordPoseW146Assets.prepare()"));
        var installer = Files.readString(Path.of("src/main/java/kim/biryeong/destiny/fx/SwordPoseW146Assets.java"));
        assertTrue(installer.contains("installIfAbsent(target, model)"));
        assertTrue(installer.contains("LinkOption.NOFOLLOW_LINKS"));
    }
}
