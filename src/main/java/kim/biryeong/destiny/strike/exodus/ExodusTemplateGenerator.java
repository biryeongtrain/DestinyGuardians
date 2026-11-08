package kim.biryeong.destiny.strike.exodus;

import kim.biryeong.destiny.DestinyGuardians;
import kim.biryeong.destiny.world.template.NbtTemplateChunkGenerator;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.MinecraftServer;
import net.minecraft.world.level.biome.Biome;
import xyz.nucleoid.map_templates.MapTemplate;

import java.util.List;

/** Nessus sky, fog and red foliage without a client shader dependency. */
public final class ExodusTemplateGenerator extends NbtTemplateChunkGenerator {
    public static final ResourceKey<Biome> BIOME = ResourceKey.create(Registries.BIOME, DestinyGuardians.id("nessus"));

    public ExodusTemplateGenerator(MinecraftServer server, List<MapTemplate> templates) {
        super(server, templates, BIOME);
    }
}
