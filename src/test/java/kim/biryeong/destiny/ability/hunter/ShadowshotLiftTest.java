package kim.biryeong.destiny.ability.hunter;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class ShadowshotLiftTest {
    @Test void releaseDropMatchesTheVersionedFullDrawRootChange() throws Exception {
        double[] roots = new double[2];
        int index = 0;
        for (String version : new String[]{"h20", "h21"}) {
            try (var stream = getClass().getResourceAsStream("/destiny/animation/hunter_" + version + ".animation.json")) {
                assertNotNull(stream);
                var pack = com.google.gson.JsonParser.parseReader(new java.io.InputStreamReader(stream,
                        java.nio.charset.StandardCharsets.UTF_8)).getAsJsonObject();
                boolean found = false;
                for (var entry : pack.getAsJsonArray("animations")) {
                    var clip = entry.getAsJsonObject();
                    if (!clip.get("name").getAsString().equals("h15_super_void_attack")) continue;
                    for (var value : clip.getAsJsonObject("animators").asMap().values()) {
                        var bone = value.getAsJsonObject();
                        if (!bone.get("name").getAsString().equals("player_root")) continue;
                        for (var keyValue : bone.getAsJsonArray("keyframes")) {
                            var key = keyValue.getAsJsonObject();
                            if (key.get("channel").getAsString().equals("position")
                                    && Math.abs(key.get("time").getAsDouble() - .30) < 1e-8) {
                                roots[index] = key.getAsJsonArray("data_points").get(0).getAsJsonObject().get("y").getAsDouble();
                                found = true;
                            }
                        }
                    }
                }
                assertTrue(found);
            }
            index++;
        }
        assertEquals((roots[0] - roots[1]) / 16, ShadowshotLift.RELEASE_DROP, 1e-9);
    }

    @Test void verticalAssistIsSmallAndConvergesWithoutOvershooting() {
        double y = 0;
        for (int i = 0; i < 5; i++) {
            double velocity = ShadowshotLift.verticalSpeed(.6 - y);
            assertTrue(velocity <= .22 && velocity >= -.06);
            y += velocity;
            assertTrue(y <= .6 + 1e-9);
        }
        assertEquals(.6, y, 1e-9);
        assertEquals(0, ShadowshotLift.verticalSpeed(0));
        assertEquals(-.06, ShadowshotLift.verticalSpeed(-2));
        assertEquals(.22, ShadowshotLift.verticalSpeed(2));
    }
}
