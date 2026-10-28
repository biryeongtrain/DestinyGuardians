package kim.biryeong.destiny.fx;

import com.google.gson.JsonParser;
import com.mojang.serialization.JsonOps;
import net.minecraft.client.color.item.ItemTintSources;
import net.minecraft.client.renderer.item.ItemModels;
import net.minecraft.client.resources.model.cuboid.CuboidModel;
import org.junit.jupiter.api.Test;
import java.io.StringReader;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import static org.junit.jupiter.api.Assertions.*;

class ExpandedAssetsW230Test {
    private static final List<String> PATHS = List.of("hunter/blade_barrage", "hunter/spectral_blades",
            "hunter/gathering_storm", "hunter/storms_edge", "titan/thundercrash", "titan/burning_maul",
            "titan/ward_of_dawn", "warlock/well_of_radiance", "warlock/chaos_reach", "warlock/nova_warp");

    @Test void everySelectableSuperHasItsOwnSourceStartAndHudDefinition() throws Exception {
        ItemModels.bootstrap(); ItemTintSources.bootstrap();
        Path root = Path.of("src/main/resources/assets/destiny");
        for (String path : PATHS) {
            String prefix = ClassSuperModelAssets.prefix(path);
            assertTrue(prefix.startsWith("w230_"), path);
            assertTrue(ClassSuperModelAssets.hasClip(prefix + "_start"), path);
            assertTrue(ClassSuperModelAssets.durationTicks(path, "start", 0) > 0, path);
            String icon = "w230_" + path.substring(path.indexOf('/') + 1);
            var item = JsonParser.parseString(Files.readString(root.resolve("items/gui/hud/" + icon + ".json"))).getAsJsonObject();
            assertTrue(ItemModels.CODEC.parse(JsonOps.INSTANCE, item.get("model")).isSuccess(), icon);
            assertNotNull(CuboidModel.fromStream(new StringReader(Files.readString(root.resolve("models/gui/hud/" + icon + ".json")))));
            assertNotNull(javax.imageio.ImageIO.read(root.resolve("textures/item/hud/" + icon + ".png").toFile()));
        }
        assertTrue(ClassSuperModelAssets.hasClip("w229_titan_arc_start"));
        assertTrue(ClassSuperModelAssets.hasClip("w229_titan_arc_start_air"));
        assertTrue(ClassSuperModelAssets.hasClip("w229_titan_arc_land"));
        assertFalse(ClassSuperModelAssets.isExpanded("hunter/arc_staff"));
    }
}
