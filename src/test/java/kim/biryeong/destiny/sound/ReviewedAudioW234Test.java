package kim.biryeong.destiny.sound;

import com.google.gson.JsonParser;
import java.nio.file.Files;
import java.nio.file.Path;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class ReviewedAudioW234Test {
    @Test void currentIndexMatchesReviewedLayersAndKeepsExistingSubtitles() throws Exception {
        var current = JsonParser.parseString(Files.readString(Path.of("src/main/resources/assets/destiny/sounds.json"))).getAsJsonObject();
        var legacy = ReviewedAudioW234.legacyW102(current);
        assertEquals(178, legacy.size(), "Historical W102 index is preserved, not repinned");
        for (var entry : legacy.entrySet()) {
            var old = entry.getValue().getAsJsonObject();
            if (old.has("subtitle")) assertEquals(old.get("subtitle"), current.getAsJsonObject(entry.getKey()).get("subtitle"), entry.getKey());
        }
        assertEquals(87 + ReviewedAudioW234.pinnedAfterW270(), ReviewedAudioW234.verifiedLaterAudioPaths().size(), "W210 + W229 + W230 + W233 + W270 exact additions");
    }
    @Test void missingAddedEventAndAlteredClipOrSubtitleAreRejected() throws Exception {
        String event = "warlock.void.super.start";
        var missing = ReviewedAudioW234.expectedCurrent(); missing.remove(event);
        assertThrows(AssertionError.class, () -> ReviewedAudioW234.legacyW102(missing));
        var clip = ReviewedAudioW234.expectedCurrent();
        clip.getAsJsonObject(event).getAsJsonArray("sounds").get(0).getAsJsonObject().addProperty("name", "destiny:light_w233/unreviewed");
        assertThrows(AssertionError.class, () -> ReviewedAudioW234.legacyW102(clip));
        var subtitle = ReviewedAudioW234.expectedCurrent(); subtitle.getAsJsonObject("hunter.solar.melee.cast").remove("subtitle");
        assertThrows(AssertionError.class, () -> ReviewedAudioW234.legacyW102(subtitle));
    }
    @Test void unexpectedEventAndMutatedLegacyDefinitionAreRejected() throws Exception {
        var extra = ReviewedAudioW234.expectedCurrent(); extra.add("unreviewed.event", extra.get("ui.super_ready").deepCopy());
        assertThrows(AssertionError.class, () -> ReviewedAudioW234.legacyW102(extra));
        var legacy = ReviewedAudioW234.expectedCurrent();
        legacy.getAsJsonObject("weapon.hand_cannon.fire").getAsJsonArray("sounds").get(0).getAsJsonObject().addProperty("pitch", .5);
        assertThrows(AssertionError.class, () -> ReviewedAudioW234.legacyW102(legacy));
    }
}
