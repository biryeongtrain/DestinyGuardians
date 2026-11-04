package kim.biryeong.destiny.fx;

import com.google.gson.JsonParser;
import com.mojang.serialization.JsonOps;
import net.minecraft.client.color.item.ItemTintSources;
import net.minecraft.client.renderer.item.ItemModels;
import net.minecraft.client.resources.model.cuboid.CuboidModel;
import org.junit.jupiter.api.Test;

import javax.imageio.ImageIO;
import java.io.StringReader;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.HashSet;
import java.util.HexFormat;

import static org.junit.jupiter.api.Assertions.*;

class WeaponReticleAssetsW44Test {
    private static final Path ROOT = Path.of("src/main/resources/assets/destiny");

    @Test
    void everyOriginalTextureAndVanillaQuadDecodesAndMatchesManifest() throws Exception {
        ItemModels.bootstrap();
        ItemTintSources.bootstrap();
        var manifest = JsonParser.parseString(Files.readString(Path.of("art/hud/w44-reticle/manifest.json"))).getAsJsonObject();
        assertTrue(manifest.get("originalArtwork").getAsBoolean());
        assertEquals(2, manifest.get("maxHudNodes").getAsInt());
        assertEquals(18, manifest.getAsJsonArray("shapes").size());
        assertEquals(55, manifest.getAsJsonObject("sha256").size());
        for (var entry : manifest.getAsJsonObject("sha256").entrySet()) {
            byte[] content = Files.readAllBytes(Path.of(entry.getKey()));
            assertEquals(entry.getValue().getAsString(), HexFormat.of().formatHex(
                    MessageDigest.getInstance("SHA-256").digest(content)), entry.getKey());
        }
        var distinctTextures = new HashSet<String>();
        for (var value : manifest.getAsJsonArray("shapes")) {
            String name = "reticle_w44_" + value.getAsString();
            var item = JsonParser.parseString(Files.readString(ROOT.resolve("items/gui/hud/" + name + ".json"))).getAsJsonObject();
            var itemModel = item.getAsJsonObject("model");
            assertTrue(ItemModels.CODEC.parse(JsonOps.INSTANCE, itemModel).isSuccess(), name);
            assertEquals("destiny:gui/hud/" + name, itemModel.get("model").getAsString());
            assertEquals("minecraft:custom_model_data", itemModel.getAsJsonArray("tints")
                    .get(0).getAsJsonObject().get("type").getAsString());
            String source = Files.readString(ROOT.resolve("models/gui/hud/" + name + ".json"));
            assertNotNull(CuboidModel.fromStream(new StringReader(source)), name);
            var quad = JsonParser.parseString(source).getAsJsonObject();
            assertFalse(quad.has("parent"), "No vanilla icon/extruded-item parent");
            assertEquals("destiny:item/hud/" + name, quad.getAsJsonObject("textures").get("0").getAsString());
            assertEquals(1, quad.getAsJsonArray("elements").size());
            var element = quad.getAsJsonArray("elements").get(0).getAsJsonObject();
            assertEquals(8, element.getAsJsonArray("from").get(2).getAsInt());
            assertEquals(8, element.getAsJsonArray("to").get(2).getAsInt());
            assertEquals(2, element.getAsJsonObject("faces").size());
            for (String face : new String[]{"north", "south"})
                assertEquals(0, element.getAsJsonObject("faces").getAsJsonObject(face).get("tintindex").getAsInt());
            var texture = ROOT.resolve("textures/item/hud/" + name + ".png");
            distinctTextures.add(HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(texture))));
            var image = ImageIO.read(texture.toFile());
            assertNotNull(image);
            assertEquals(128, image.getWidth());
            assertEquals(128, image.getHeight());
            assertTrue(image.getColorModel().hasAlpha());
            assertEquals(0, image.getRGB(0, 0) >>> 24, "Transparent corners");
            assertEquals(value.getAsString().equals("dot") ? 255 : 0, image.getRGB(64, 64) >>> 24,
                    "Outer frame leaves centre open; fixed dot alone marks the aim point");
            int occupied = 0;
            for (int y = 0; y < 128; y++)
                for (int x = 0; x < 128; x++)
                    if ((image.getRGB(x, y) >>> 24) > 32) occupied++;
            assertTrue(occupied > 100 && occupied < 128 * 128 / 2, "Sparse legible geometry: " + name);
        }
        assertEquals(18, distinctTextures.size(), "Every family/frame variant has its own artwork");
        assertFalse(Files.exists(ROOT.resolve("textures/item/hud/reticle_w44_sword.png")));
        assertFalse(Files.exists(ROOT.resolve("textures/item/hud/reticle_w44_glaive.png")));
    }
}
