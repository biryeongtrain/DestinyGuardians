package kim.biryeong.destiny.strike.devils;

import kim.biryeong.destiny.world.template.TemplateChunkWarmup;
import net.minecraft.server.level.ServerLevel;
import xyz.nucleoid.map_templates.BlockBounds;

/** Strike compatibility adapter; requests and ticket ownership live in the shared builder. */
final class DevilsChunkWarmup extends TemplateChunkWarmup {
    DevilsChunkWarmup(ServerLevel level, BlockBounds bounds) { super(level, bounds); }
    DevilsChunkWarmup(ServerLevel level, BlockBounds bounds, int margin) { super(level, bounds, margin); }
}
