package kim.biryeong.destiny.weapon;

import com.google.gson.JsonParser;
import eu.pb4.polymer.resourcepack.api.PackResource;
import net.minecraft.client.resources.model.cuboid.CuboidModel;
import net.minecraft.client.resources.model.cuboid.UnbakedCuboidGeometry;
import org.junit.jupiter.api.Test;

import java.io.StringReader;
import java.nio.file.Files;
import java.nio.file.Path;

import static org.junit.jupiter.api.Assertions.*;

/** Actual 26.3 resource deserializer, headless and without baking/GPU/download.
 * This catches format/rotation rejection; it does NOT certify a live client view.
 */
class WeaponSurfaceNativeParserTest {
    @Test void emittedModelsParseWithTheTargetGamesCuboidDeserializer() throws Exception {
        var rules = WeaponSurfaceW123Assets.rules();
        for (String path : rules.keySet()) {
            String original = Files.readString(Path.of("src/main/resources").resolve(path));
            String output = WeaponSurfaceW123Assets.convert(path, PackResource.fromString(original), rules).asString();
            var json = JsonParser.parseString(output).getAsJsonObject();
            var parsed = assertDoesNotThrow(() -> CuboidModel.fromStream(new StringReader(output)), path);
            var geometry = assertInstanceOf(UnbakedCuboidGeometry.class, parsed.geometry(), path);
            assertEquals(json.getAsJsonArray("elements").size(), geometry.elements().size(), path);
            for (int i = 0; i < geometry.elements().size(); i++) {
                var element = geometry.elements().get(i);
                var source = json.getAsJsonArray("elements").get(i).getAsJsonObject();
                assertEquals(source.getAsJsonObject("faces").size(), element.faces().size(), path + " #" + i);
                if (source.has("rotation")) {
                    assertNotNull(element.rotation(), path + " #" + i);
                    assertTrue(Float.isFinite(element.rotation().transform().m00()), path);
                } else assertNull(element.rotation(), path + " #" + i);
            }
        }
    }
}
