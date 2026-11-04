package kim.biryeong.destiny.fx;

import com.google.gson.JsonParser;
import org.junit.jupiter.api.Test;

import javax.imageio.ImageIO;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.HexFormat;
import java.util.List;

import static org.junit.jupiter.api.Assertions.*;

class WeaponScopeHudAssetsW45Test {
    private static final Path ROOT = Path.of("src/main/resources/assets/destiny");
    private static final List<String> IDS = List.of("bite_of_the_fox", "beloved", "apostate",
            "line_in_the_sand", "stormchaser");

    @Test void everyGeneratedAssetIsPinnedAndEveryQuadHasActualTextureAndTint() throws Exception {
        var manifest = JsonParser.parseString(Files.readString(Path.of("art/hud/w45-scope/manifest.json"))).getAsJsonObject();
        int pack = 0;
        for (var entry : manifest.getAsJsonObject("sha256").entrySet()) {
            Path file = Path.of(entry.getKey());
            assertEquals(entry.getValue().getAsString(), HexFormat.of().formatHex(
                    MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(file))), entry.getKey());
            if (file.startsWith(ROOT)) pack++;
        }
        assertEquals(24, pack, "Three sniper frames + five reticles, each PNG/model/item");
        for (String id : IDS) for (String part : List.of("frame", "reticle")) {
            String name = "scope_w45_" + id + "_" + part;
            if (part.equals("frame") && IDS.indexOf(id) >= 3) {
                assertFalse(Files.exists(ROOT.resolve("items/gui/hud/" + name + ".json")), "LFR must keep real 3D optics");
                continue;
            }
            var item = JsonParser.parseString(Files.readString(ROOT.resolve("items/gui/hud/" + name + ".json"))).getAsJsonObject();
            assertEquals("destiny:gui/hud/" + name, item.getAsJsonObject("model").get("model").getAsString());
            assertEquals(0, item.getAsJsonObject("model").getAsJsonArray("tints").get(0).getAsJsonObject().get("index").getAsInt());
            var model = JsonParser.parseString(Files.readString(ROOT.resolve("models/gui/hud/" + name + ".json"))).getAsJsonObject();
            assertEquals(1, model.getAsJsonArray("elements").size());
            assertEquals("destiny:item/hud/" + name, model.getAsJsonObject("textures").get("0").getAsString());
            assertNotNull(ImageIO.read(ROOT.resolve("textures/item/hud/" + name + ".png").toFile()));
        }
    }

    @Test void sniperMasksHaveClearAimWindowsOpaquePeripheryAndDifferentActualShapes() throws Exception {
        for (String id : IDS.subList(0, 3)) {
            var image = ImageIO.read(ROOT.resolve("textures/item/hud/scope_w45_" + id + "_frame.png").toFile());
            assertEquals(1024, image.getWidth());
            assertEquals(1024, image.getHeight());
            assertEquals(255, image.getRGB(0, 0) >>> 24);
            for (int y = 482; y < 542; y++) for (int x = 482; x < 542; x++)
                assertEquals(0, image.getRGB(x, y) >>> 24, "Aim ray stays clear: " + id);
            // At 3840 virtual square, wide masks cover a 32:9 viewport without stretching the lens.
            assertEquals(255, image.getRGB(12, 512) >>> 24);
        }
        var circle = ImageIO.read(ROOT.resolve("textures/item/hud/scope_w45_beloved_frame.png").toFile());
        var hive = ImageIO.read(ROOT.resolve("textures/item/hud/scope_w45_apostate_frame.png").toFile());
        var fox = ImageIO.read(ROOT.resolve("textures/item/hud/scope_w45_bite_of_the_fox_frame.png").toFile());
        assertEquals(0, circle.getRGB(512, 340) >>> 24);
        assertEquals(255, hive.getRGB(512, 340) >>> 24);
        assertEquals(255, fox.getRGB(512, 340) >>> 24);
        assertEquals(0, fox.getRGB(310, 410) >>> 24);
        assertNotEquals(0, hive.getRGB(290, 405) >>> 24);
    }

    @Test void hollowSightCentersStayOpenAndChevronTipNotItsBoxIsAtAimPoint() throws Exception {
        for (String id : List.of("beloved", "apostate", "line_in_the_sand")) {
            var image = ImageIO.read(ROOT.resolve("textures/item/hud/scope_w45_" + id + "_reticle.png").toFile());
            assertEquals(128, image.getWidth());
            assertEquals(0, image.getRGB(64, 64) >>> 24, "Hollow sight central ray: " + id);
        }
        var fox = ImageIO.read(ROOT.resolve("textures/item/hud/scope_w45_bite_of_the_fox_reticle.png").toFile());
        assertTrue((fox.getRGB(64, 65) >>> 24) > 100, "Chevron apex at aim point");
        assertEquals(0, fox.getRGB(64, 44) >>> 24, "Not vertically centred using the chevron's box");
        var storm = ImageIO.read(ROOT.resolve("textures/item/hud/scope_w45_stormchaser_reticle.png").toFile());
        assertTrue((storm.getRGB(64, 64) >>> 24) > 100);
    }

    @Test void onlyVanillaSpriteCrossAndAttackIndicatorAreTransparentWithNativeDimensions() throws Exception {
        var dimensions = java.util.Map.of("crosshair", new int[]{15, 15},
                "crosshair_attack_indicator_background", new int[]{16, 4},
                "crosshair_attack_indicator_full", new int[]{16, 16},
                "crosshair_attack_indicator_progress", new int[]{16, 4});
        for (var entry : dimensions.entrySet()) {
            var image = ImageIO.read(Path.of("src/main/resources/assets/minecraft/textures/gui/sprites/hud/"
                    + entry.getKey() + ".png").toFile());
            assertEquals(entry.getValue()[0], image.getWidth());
            assertEquals(entry.getValue()[1], image.getHeight());
            for (int y = 0; y < image.getHeight(); y++) for (int x = 0; x < image.getWidth(); x++)
                assertEquals(0, image.getRGB(x, y) >>> 24);
        }
    }
}
