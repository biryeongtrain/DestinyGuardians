package kim.biryeong.destiny.world.template;

import kim.biryeong.destiny.campaign.RisingServices;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.TicketType;
import net.minecraft.world.level.ChunkPos;
import xyz.nucleoid.map_templates.BlockBounds;
import java.util.*;
import java.util.concurrent.CompletableFuture;

/** Bounded asynchronous generation requests. Retains only its own tickets until session cleanup. */
public class TemplateChunkWarmup implements RisingServices.ZoneBuild {
    private final TicketType ticket = new TicketType(0, TicketType.FLAG_LOADING | TicketType.FLAG_KEEP_DIMENSION_ACTIVE);
    private final ServerLevel level;
    private final List<ChunkPos> chunks = new ArrayList<>();
    private final Map<ChunkPos, CompletableFuture<?>> pending = new LinkedHashMap<>();
    private int requested, completed;
    private boolean cancelled;
    public TemplateChunkWarmup(ServerLevel level, BlockBounds bounds) { this(level, bounds, 0); }
    /** {@code margin} chunk columns around the template are prepared too: an arriving fireteam's view
     * distance otherwise creates every empty column beyond the template on the server thread at once. */
    public TemplateChunkWarmup(ServerLevel level, BlockBounds bounds, int margin) {
        this.level = level;
        if (!level.getServer().isSameThread()) throw new IllegalStateException("Chunk warmup requires server thread");
        if (margin < 0) throw new IllegalArgumentException("Negative warmup margin");
        for(int x=(bounds.min().getX()>>4)-margin;x<=(bounds.max().getX()>>4)+margin;x++)
            for(int z=(bounds.min().getZ()>>4)-margin;z<=(bounds.max().getZ()>>4)+margin;z++) chunks.add(new ChunkPos(x,z));
    }
    public int columns() { return chunks.size(); }
    @Override public boolean step(long budget) {
        if (cancelled) return false;
        if (!level.getServer().isSameThread()) throw new IllegalStateException("Chunk warmup requires server thread");
        if (budget <= 0) return completed == chunks.size();
        long deadline=System.nanoTime()+budget;
        for(var e:pending.entrySet()) {
            if(e.getValue().isCancelled() || e.getValue().isCompletedExceptionally())
                throw new IllegalStateException("Template chunk generation failed: "+e.getKey());
        }
        // At most eight new column requests per tick; generation has its own worker scheduling.
        int count=0;
        while(requested<chunks.size() && count++<8 && System.nanoTime()<deadline) {
            var at=chunks.get(requested++);
            pending.put(at,level.getChunkSource().addTicketAndLoadWithRadius(ticket,at,0));
        }
        completed=0;
        for(var e:pending.entrySet()) if(e.getValue().isDone()
                && level.getChunkSource().getChunkNow(e.getKey().x(),e.getKey().z())!=null) completed++;
        return completed==chunks.size();
    }
    @Override public double progress() { return completed/(double)chunks.size(); }
    @Override public void cancel() {
        if(cancelled)return;
        cancelled=true;
        for(var at:pending.keySet()) level.getChunkSource().removeTicketWithRadius(ticket,at,0);
        pending.clear();
    }
}
