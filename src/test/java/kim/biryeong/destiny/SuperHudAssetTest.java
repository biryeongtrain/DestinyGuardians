package kim.biryeong.destiny;

import com.google.gson.JsonParser;
import org.junit.jupiter.api.Test;
import javax.imageio.ImageIO;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import static org.junit.jupiter.api.Assertions.*;

class SuperHudAssetTest {
    @Test void allCueSpritesResolveTintedFlatModelsAndNonemptyTextures() throws Exception {
        var names = new ArrayList<String>();
        names.add("diamond_ready");
        for (int i = 0; i < 7; i++) names.add("ready_banner_" + i);
        for (int i = 0; i < 4; i++) names.add("ready_echo_" + i);
        for (int i = 0; i < 6; i++) names.add("cast_flash_" + i);
        for (String name : names) {
            try (var in = getClass().getResourceAsStream("/assets/destiny/items/gui/hud/" + name + ".json")) {
                assertNotNull(in, name);
                var item = JsonParser.parseString(new String(in.readAllBytes(), StandardCharsets.UTF_8))
                        .getAsJsonObject().getAsJsonObject("model");
                assertEquals("destiny:gui/hud/" + name, item.get("model").getAsString());
                assertEquals("minecraft:custom_model_data", item.getAsJsonArray("tints").get(0)
                        .getAsJsonObject().get("type").getAsString());
            }
            try (var in = getClass().getResourceAsStream("/assets/destiny/models/gui/hud/" + name + ".json")) {
                assertNotNull(in, name);
                var model = JsonParser.parseString(new String(in.readAllBytes(), StandardCharsets.UTF_8)).getAsJsonObject();
                assertEquals("destiny:item/hud/" + name, model.getAsJsonObject("textures").get("layer0").getAsString());
                assertEquals(1, model.getAsJsonArray("elements").size());
            }
            try (var in = getClass().getResourceAsStream("/assets/destiny/textures/item/hud/" + name + ".png")) {
                assertNotNull(in, name);
                var image = ImageIO.read(in);
                boolean visible = false;
                for (int y = 0; y < image.getHeight(); y++) for (int x = 0; x < image.getWidth(); x++)
                    visible |= image.getRGB(x, y) >>> 24 > 0;
                assertTrue(visible, name);
            }
        }
    }

    @Test void castNeverCoversCentralAimingAreaAndEnvelopeDecreases() throws Exception {
        long previous = Long.MAX_VALUE;
        for (int i = 0; i < 6; i++) {
            try (var in = getClass().getResourceAsStream("/assets/destiny/textures/item/hud/cast_flash_" + i + ".png")) {
                assertNotNull(in);
                var image = ImageIO.read(in);
                long alpha = 0;
                for (int y = 0; y < image.getHeight(); y++) for (int x = 0; x < image.getWidth(); x++) {
                    int a = image.getRGB(x, y) >>> 24;
                    alpha += a;
                    if (x > image.getWidth() * .15 && x < image.getWidth() * .85)
                        assertEquals(0, a, "Central 70% must stay clear");
                }
                assertTrue(alpha > 0 && alpha < previous);
                previous = alpha;
            }
        }
    }
}
