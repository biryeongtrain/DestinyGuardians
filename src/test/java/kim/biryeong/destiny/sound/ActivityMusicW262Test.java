package kim.biryeong.destiny.sound;

import com.google.gson.JsonParser;
import kim.biryeong.destiny.crucible.ControlMatch;
import kim.biryeong.minigamelib.music.OggVorbis;
import org.junit.jupiter.api.Test;
import java.nio.file.Files;
import java.nio.file.Path;
import static kim.biryeong.destiny.sound.MusicSequence.Scene.*;
import static org.junit.jupiter.api.Assertions.*;

class ActivityMusicW262Test {
    @Test void tutorialHasItsOwnSceneRegardlessOfStageOrTowerTransition() {
        assertEquals(TUTORIAL, ActivityMusic.scene(false, false, ControlMatch.Phase.WAITING, true));
        assertEquals(TUTORIAL, ActivityMusic.scene(true, false, ControlMatch.Phase.WAITING, true));
        assertEquals(TOWER, ActivityMusic.scene(true, false, ControlMatch.Phase.WAITING, false));
    }
    @Test void matchOwnershipOverridesTowerUntilLeaveAndCombatIsSilent() {
        assertEquals(TOWER, ActivityMusic.scene(true, false, ControlMatch.Phase.WAITING));
        assertEquals(NONE, ActivityMusic.scene(false, false, ControlMatch.Phase.INTRO));
        assertEquals(NONE, ActivityMusic.scene(true, true, ControlMatch.Phase.WAITING));
        assertEquals(NONE, ActivityMusic.scene(false, true, ControlMatch.Phase.PLAYING));
        assertEquals(INTRO, ActivityMusic.scene(false, true, ControlMatch.Phase.INTRO));
        assertEquals(RESULTS, ActivityMusic.scene(false, true, ControlMatch.Phase.RESULTS));
    }
    @Test void allScheduledSoundsStreamAndDurationsMatchEncodedAudio() throws Exception {
        var root=Path.of("src/main/resources");
        var catalog=JsonParser.parseString(Files.readString(root.resolve("data/destiny/activity_music.json"))).getAsJsonObject();
        var sounds=JsonParser.parseString(Files.readString(root.resolve("assets/destiny_music/sounds.json"))).getAsJsonObject();
        for(var scene:catalog.entrySet()) for(var element:scene.getValue().getAsJsonArray()) {
            var track=element.getAsJsonObject();
            var definition=sounds.getAsJsonObject(track.get("event").getAsString()).getAsJsonArray("sounds");
            assertEquals(1, definition.size(),"Server timeline must not randomly choose a different-length source");
            var sound=definition.get(0).getAsJsonObject();
            assertTrue(sound.get("stream").getAsBoolean());
            String resource=sound.get("name").getAsString();
            // Sound file IDs resolve under sounds/, independently of the event identifier.
            var parts=resource.split(":",2);
            var path=root.resolve("assets/"+parts[0]+"/sounds/"+parts[1]+".ogg");
            assertEquals(OggVorbis.duration(path),track.get("seconds").getAsDouble(),.02,resource);
        }
    }
}
