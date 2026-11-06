package kim.biryeong.destiny.fireteam;

import com.google.gson.JsonParser;
import org.junit.jupiter.api.Test;
import java.nio.file.*;
import java.security.MessageDigest;
import java.util.*;
import static org.junit.jupiter.api.Assertions.*;

class ActivityLaunchTimingW329Test {
    @Test void acceptedClickHasOneSecondLeadThenFiveFullNumberIntervalsAndNoZero() {
        assertEquals(120, ActivityLaunch.LAUNCH_AT);
        assertEquals(104, ActivityLaunch.FADE_START);
        for (int elapsed = -1; elapsed < 20; elapsed++) assertEquals(0, ActivityLaunch.numberAt(elapsed));
        for (int interval = 0; interval < 5; interval++) for (int tick = 0; tick < 20; tick++)
            assertEquals(5 - interval, ActivityLaunch.numberAt(20 + interval * 20 + tick));
        assertEquals(0, ActivityLaunch.numberAt(120));
        assertEquals(0, ActivityLaunch.numberAt(Integer.MAX_VALUE));
        assertTrue(FinderSounds.COUNTDOWN_AUDIO_TICKS > ActivityLaunch.LAUNCH_AT, "Success retains original audio tail");
    }
    @Test void exactSelectedOriginalAndEveryScopedSoundAliasRetainFullLengthAudio() throws Exception {
        var root = Path.of("art/audio/activity-launch-w329");
        var manifest = JsonParser.parseString(Files.readString(root.resolve("manifest.json"))).getAsJsonObject();
        byte[] original = Files.readAllBytes(root.resolve("source/Director - Mission Click and Countdown.mp3"));
        assertEquals("229a004fe54964c41ce25fddb1eb5c85e47a943b4d0cb9a555e43e66ca189222",
                HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(original)));
        assertEquals(159903, original.length);
        double duration = manifest.getAsJsonObject("output_info").getAsJsonObject("format").get("duration").getAsDouble();
        assertTrue(duration >= 6.343583 && duration < 6.363583, "Full source timeline retained with bounded codec padding");
        assertEquals((int)Math.ceil(duration * 20), FinderSounds.COUNTDOWN_AUDIO_TICKS);
        var assets = Path.of("src/main/resources/assets/destiny_activity_launch");
        var events = JsonParser.parseString(Files.readString(assets.resolve("sounds.json"))).getAsJsonObject();
        assertEquals(FinderSounds.COUNTDOWN_CHANNELS, events.size());
        for (int channel = 0; channel < FinderSounds.COUNTDOWN_CHANNELS; channel++) {
            var sound = events.getAsJsonObject("countdown_" + channel).getAsJsonArray("sounds").get(0).getAsJsonObject();
            assertEquals("destiny_activity_launch:director_mission_click_countdown", sound.get("name").getAsString());
        }
        byte[] encoded = Files.readAllBytes(assets.resolve("sounds/director_mission_click_countdown.ogg"));
        assertEquals("OggS", new String(encoded, 0, 4, java.nio.charset.StandardCharsets.US_ASCII));
        assertEquals(manifest.get("output_sha256").getAsString(), HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(encoded)));
    }
}
