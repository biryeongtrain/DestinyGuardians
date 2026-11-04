package kim.biryeong.destiny.activity.presentation;

import com.google.gson.JsonParser;
import org.junit.jupiter.api.Test;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.HashSet;
import static org.junit.jupiter.api.Assertions.*;

class BriefingFormationTest {
    @Test void centreLeadsAndSidesStandOnCameraLeftAndRight() {
        // Team faces +Z (yaw 0); the camera stands at +Z looking back, so its screen-right is world +X.
        var centre = BriefingFormation.slot(0, 0); var left = BriefingFormation.slot(1, 0); var right = BriefingFormation.slot(2, 0);
        assertEquals(0, centre.x, 1e-9); assertTrue(centre.z > 0, "centre steps toward the camera");
        assertEquals(-BriefingFormation.LANE, left.x, 1e-9); assertTrue(left.z < 0);
        assertEquals(BriefingFormation.LANE, right.x, 1e-9); assertTrue(right.z < 0);
        var turned = BriefingFormation.slot(2, 90); // facing -X: screen-right becomes world +Z
        assertEquals(BriefingFormation.LANE, turned.z, 1e-9);
    }
    @Test void everyBriefingClipShipsAndHoldsBeyondTheVoice() throws Exception {
        try (var in = getClass().getResourceAsStream("/destiny/animation/briefing_crota_landing.animation.json")) {
            assertNotNull(in);
            var names = new HashSet<String>();
            for (var e : JsonParser.parseReader(new InputStreamReader(in, StandardCharsets.UTF_8)).getAsJsonObject().getAsJsonArray("animations")) {
                var clip = e.getAsJsonObject(); names.add(clip.get("name").getAsString());
                // Zavala's briefing line is 22.142 s; the final pose must still be held when it ends.
                assertTrue(clip.get("length").getAsDouble() >= 23, clip.get("name").getAsString());
            }
            assertEquals(new HashSet<>(BriefingFormation.CLIPS), names);
        }
        assertEquals(177, BriefingFormation.MOTION_TICKS, "265 source frames at 30 fps");
    }
}
