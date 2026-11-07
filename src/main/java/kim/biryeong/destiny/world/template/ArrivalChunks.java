package kim.biryeong.destiny.world.template;

import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.level.ChunkPos;
import xyz.nucleoid.map_templates.BlockBounds;
import java.util.function.Consumer;

/** One actual teleport destination, never a map rectangle or a view-distance prefetch. */
public final class ArrivalChunks implements AutoCloseable {
    private final ServerLevel level;
    private final Consumer<Boolean> tickWhileEmpty;
    private ChunkPos destination;
    private TemplateChunkWarmup request;
    private boolean closed;
    public ArrivalChunks(ServerLevel level, Consumer<Boolean> tickWhileEmpty) {
        this.level = level; this.tickWhileEmpty = tickWhileEmpty;
    }
    public boolean ready(BlockPos position) {
        if (!level.getServer().isSameThread()) throw new IllegalStateException("Arrival requires server thread");
        if (closed) return false;
        var target = new ChunkPos(position.getX() >> 4, position.getZ() >> 4);
        if (!target.equals(destination)) {
            release(); destination = target;
        }
        if (level.getChunkSource().getChunkNow(target.x(), target.z()) != null) return true;
        if (request == null) {
            // The normal chunk pipeline handles only this column's generation dependencies.
            var at = position.immutable();
            request = new TemplateChunkWarmup(level, new BlockBounds(at, at), 0);
            tickWhileEmpty.accept(true);
        }
        return request.step(2_000_000L);
    }
    public int requestedColumns() { return request == null ? 0 : request.columns(); }
    private void release() {
        if (request != null) { request.cancel(); request = null; tickWhileEmpty.accept(false); }
    }
    @Override public void close() {
        if (closed) return;
        closed = true; release();
    }
}
