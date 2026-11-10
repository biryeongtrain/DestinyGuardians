package kim.biryeong.destiny.test;

import net.fabricmc.fabric.api.event.lifecycle.v1.ServerLifecycleEvents;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;

import java.util.ArrayDeque;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;

/** Opt-in timing observations for one explicitly owned scale fixture; never a save policy. */
public final class GameTestScaleSaveTrace {
    private static final boolean ENABLED = Boolean.getBoolean("destiny.gametest.scale.enabled");
    private static final int MAX_SAMPLES = 64;
    private static long nextGeneration;
    private static Session active;

    /** Scalar token cannot keep a world or server alive after stop. */
    public record Sample(long generation, int serverTick, long startedNanos) { }

    private static final class Session {
        final MinecraftServer server;
        final long generation = ++nextGeneration;
        final ArrayDeque<Map<String, Object>> samples = new ArrayDeque<>();
        long dropped;
        Session(MinecraftServer server) { this.server = server; }
    }

    static {
        if (ENABLED) ServerLifecycleEvents.SERVER_STOPPED.register(GameTestScaleSaveTrace::stop);
    }

    private GameTestScaleSaveTrace() { }

    public static synchronized void start(MinecraftServer server) {
        if (!ENABLED) return;
        Objects.requireNonNull(server, "Owned fixture server");
        if (active != null && active.server != server)
            throw new IllegalStateException("A different scale fixture already owns save tracing");
        active = new Session(server);
    }

    /** Returns detached scalar rows and clears the bounded pending queue. */
    public static synchronized List<Map<String, Object>> drain(MinecraftServer server) {
        if (active == null || active.server != server) return List.of();
        var rows = List.copyOf(active.samples);
        active.samples.clear();
        return rows;
    }

    public static synchronized void stop(MinecraftServer server) {
        if (active != null && active.server == server) active = null;
    }

    public static synchronized Sample begin(MinecraftServer server) {
        if (!ENABLED || active == null || active.server != server) return null;
        return new Sample(active.generation, server.getTickCount(), System.nanoTime());
    }

    public static void recordServer(MinecraftServer server, Sample sample, boolean silent, boolean flush,
                                    boolean force, boolean returned, boolean result) {
        if (sample == null) return;
        long elapsed = System.nanoTime() - sample.startedNanos();
        var row = row(server, sample, elapsed, "server.saveEverything", server.getClass().getName());
        row.put("silent", silent); row.put("flush", flush); row.put("force", force);
        row.put("outcome", returned ? "returned" : "threw");
        if (returned) row.put("result", result);
        append(server, sample, row);
    }

    /** Times ServerLevel's parent implementation. Overrides that do not call super produce no row. */
    public static void recordLevel(ServerLevel level, Sample sample, boolean flush, boolean noSave, boolean returned) {
        if (sample == null) return;
        long elapsed = System.nanoTime() - sample.startedNanos();
        var server = level.getServer();
        var row = row(server, sample, elapsed, "level.save.native_parent", level.getClass().getName());
        row.put("level", level.dimension().identifier().toString());
        row.put("flush", flush); row.put("no_save", noSave);
        row.put("outcome", returned ? "returned" : "threw");
        append(server, sample, row);
    }

    private static LinkedHashMap<String, Object> row(MinecraftServer server, Sample sample, long elapsed,
                                                     String style, String implementation) {
        var row = new LinkedHashMap<String, Object>();
        row.put("server_tick", sample.serverTick());
        row.put("server_tick_end", server.getTickCount());
        row.put("duration_ns", elapsed);
        row.put("style", style);
        row.put("class", implementation);
        return row;
    }

    private static synchronized void append(MinecraftServer server, Sample sample, Map<String, Object> row) {
        if (active == null || active.server != server || active.generation != sample.generation()) return;
        if (active.samples.size() == MAX_SAMPLES) {
            active.samples.removeFirst();
            active.dropped++;
        }
        row.put("dropped_before", active.dropped);
        active.samples.addLast(Map.copyOf(row));
    }
}
