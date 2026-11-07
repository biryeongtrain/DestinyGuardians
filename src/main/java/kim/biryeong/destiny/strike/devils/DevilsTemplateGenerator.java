package kim.biryeong.destiny.strike.devils;

import kim.biryeong.destiny.world.template.NbtTemplateChunkGenerator;
import net.minecraft.server.MinecraftServer;
import xyz.nucleoid.map_templates.MapTemplate;
import java.util.List;

/** Strike adapter over the shared, read-only section-NBT generator. */
public final class DevilsTemplateGenerator extends NbtTemplateChunkGenerator {
    public DevilsTemplateGenerator(MinecraftServer server, List<MapTemplate> templates) {
        super(server, templates);
    }
}
