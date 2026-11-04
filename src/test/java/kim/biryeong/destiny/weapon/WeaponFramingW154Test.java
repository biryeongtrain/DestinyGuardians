package kim.biryeong.destiny.weapon;

import com.google.gson.JsonParser;
import net.minecraft.client.resources.model.cuboid.CuboidModel;
import org.junit.jupiter.api.Test;
import java.io.StringReader;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import static org.junit.jupiter.api.Assertions.*;

class WeaponFramingW154Test {
    private static final Path MODELS = Path.of("src/main/resources/assets/destiny/models");

    @Test void targetParserAcceptsMachineGunAssembliesAndAllAceAimFrames() throws Exception {
        for (String id : List.of("hammerhead", "fixed_odds", "retrofit_escapade")) {
            var path = MODELS.resolve("weapon_surface_w123/" + id + ".json");
            var text = Files.readString(path);
            assertNotNull(CuboidModel.fromStream(new StringReader(text)));
            assertTrue(JsonParser.parseString(text).getAsJsonObject().getAsJsonArray("elements").size() <= 1000);
        }
        for (int frame = 0; frame <= 20; frame++) {
            for (String grip : List.of("native", "twohand")) {
                var path = MODELS.resolve("item/weapon_aim_w70/ace_of_spades_%02d_%s.json".formatted(frame, grip));
                assertNotNull(CuboidModel.fromStream(new StringReader(Files.readString(path))));
            }
        }
    }

    @Test void aceCloserAdsDoesNotModifyThirdPersonAndHipEndpoint() throws Exception {
        var base = JsonParser.parseString(Files.readString(MODELS.resolve("item/weapon/ace_of_spades.json"))).getAsJsonObject();
        var hip = JsonParser.parseString(Files.readString(MODELS.resolve("item/weapon_aim_w70/ace_of_spades_00_native.json"))).getAsJsonObject();
        var ads = JsonParser.parseString(Files.readString(MODELS.resolve("item/weapon_aim_w70/ace_of_spades_20_native.json"))).getAsJsonObject();
        assertEquals(87, base.getAsJsonArray("elements").size());
        assertEquals(base.get("display"), hip.get("display"));
        for (var entry : base.getAsJsonObject("display").entrySet()) {
            if (!entry.getKey().startsWith("firstperson_"))
                assertEquals(entry.getValue(), ads.getAsJsonObject("display").get(entry.getKey()));
        }
    }
}
