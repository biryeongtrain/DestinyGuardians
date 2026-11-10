package kim.biryeong.destiny.world;

import net.minecraft.resources.ResourceKey;
import net.minecraft.server.MinecraftServer;
import net.minecraft.util.ProgressListener;
import net.minecraft.world.level.Level;
import xyz.nucleoid.fantasy.RuntimeLevel;
import xyz.nucleoid.fantasy.RuntimeLevelConfig;

/**
 * Disposable activity terrain needs unload persistence during a run, but no periodic bulk save.
 * Keep {@code noSave} false: native ChunkMap uses that flag to suppress chunk unloading as well.
 * Individual dirty chunks still follow native unload serialization, preserving pasted geometry
 * and encounter edits when players leave a chunk and return within the same activity instance.
 * Player data and checkpoint attachments are saved separately by PlayerList.
 */
public class TemporaryActivityLevel extends RuntimeLevel {
    public TemporaryActivityLevel(MinecraftServer server, ResourceKey<Level> key,
                                  RuntimeLevelConfig config, Style style) {
        super(server, key, config, requireTemporary(style));
    }

    private static Style requireTemporary(Style style) {
        if (style != Style.TEMPORARY)
            throw new IllegalArgumentException("Temporary activity save policy requires a temporary Fantasy level");
        return style;
    }

    @Override public final void save(ProgressListener progress, boolean flush, boolean skipSave) {
        // Fantasy already excludes temporary levels from flushed saves. Also exclude periodic
        // level-wide saves; native per-chunk unload saves do not enter ServerLevel.save().
    }
}
