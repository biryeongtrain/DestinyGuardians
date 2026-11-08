package kim.biryeong.destiny.campaign.map;

import kim.biryeong.destiny.campaign.RisingServices;
import net.minecraft.commands.arguments.blocks.BlockStateParser;
import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.TicketType;
import net.minecraft.world.level.ChunkPos;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;

import java.io.*;
import java.nio.charset.StandardCharsets;
import java.util.*;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ConcurrentHashMap;
import java.util.zip.GZIPInputStream;

/**
 * Immutable block template of one Guardian Rises zone, decoded from a bundled {@code .zone} file
 * (written by scripts/campaign/rising_maps.py; format in docs/design/guardian-rises/map-pipeline.md).
 *
 * <p>Storage is sparse: only 16x16x16 zone-local sections that contain blocks are kept, one byte per
 * cell. Templates are cached per zone and shared read-only by every mission instance; placement state
 * lives in {@link Build}.
 */
public final class ZoneTemplate {
    public static final byte[] MAGIC = "DGZONE01".getBytes(StandardCharsets.US_ASCII);
    public static final int MAX_EDGE = 2048, MAX_HEIGHT = 384, MAX_PALETTE = 256;
    public static final String RESOURCE_DIR = "/data/destiny/guardian_rises/zones/";
    private static final Map<String, ZoneTemplate> CACHE = new ConcurrentHashMap<>();

    private final String id;
    private final int sizeX, sizeY, sizeZ;
    private final List<String> palette;
    private final Section[] sections;
    private final long blockCount;
    private volatile BlockState[] states;

    /** Non-empty 16^3 section at zone-local section coordinates; cells indexed (y << 8) | (z << 4) | x. */
    record Section(int sx, int sy, int sz, byte[] cells, int nonAir) {}

    private ZoneTemplate(String id, int sizeX, int sizeY, int sizeZ, List<String> palette, Section[] sections, long blockCount) {
        this.id = id; this.sizeX = sizeX; this.sizeY = sizeY; this.sizeZ = sizeZ;
        this.palette = List.copyOf(palette); this.sections = sections; this.blockCount = blockCount;
    }

    public String id() { return id; }
    public int sizeX() { return sizeX; }
    public int sizeY() { return sizeY; }
    public int sizeZ() { return sizeZ; }
    public List<String> palette() { return palette; }
    /** Number of non-air blocks placed by a full build. */
    public long blockCount() { return blockCount; }
    int sectionCount() { return sections.length; }

    public static String resourceName(RisingServices.Zone zone) {
        return zone.name().toLowerCase(Locale.ROOT);
    }

    /** Cached bundled template; the first call decodes (~0.1-1 s), later calls are free. */
    public static ZoneTemplate get(RisingServices.Zone zone) {
        return CACHE.computeIfAbsent(resourceName(zone), name -> {
            String path = RESOURCE_DIR + name + ".zone";
            try (InputStream in = ZoneTemplate.class.getResourceAsStream(path)) {
                if (in == null) throw new UncheckedIOException(new FileNotFoundException(path));
                return decode(name, in);
            } catch (IOException e) {
                throw new UncheckedIOException("Invalid zone template " + path, e);
            }
        });
    }

    /** Warms the cache off-thread so the first mission start does not decode on the server thread. */
    public static CompletableFuture<Void> preloadAsync() {
        return CompletableFuture.runAsync(() -> {
            for (RisingServices.Zone z : RisingServices.Zone.values()) get(z);
        });
    }

    /** Palette index (0 = air) at zone-local coordinates; out-of-bounds reads are air. */
    public int paletteIndexAt(int x, int y, int z) {
        if (x < 0 || y < 0 || z < 0 || x >= sizeX || y >= sizeY || z >= sizeZ) return 0;
        Section s = find(x >> 4, y >> 4, z >> 4);
        return s == null ? 0 : s.cells[((y & 15) << 8) | ((z & 15) << 4) | (x & 15)] & 0xFF;
    }

    private Section find(int sx, int sy, int sz) {
        int lo = 0, hi = sections.length - 1;
        long key = order(sx, sy, sz);
        while (lo <= hi) {
            int mid = (lo + hi) >>> 1;
            Section s = sections[mid];
            long k = order(s.sx, s.sy, s.sz);
            if (k == key) return s;
            if (k < key) lo = mid + 1; else hi = mid - 1;
        }
        return null;
    }

    /** Placement order: section column by column (x, then z), bottom to top inside a column. */
    private static long order(int sx, int sy, int sz) {
        return ((long) sx << 40) | ((long) sz << 20) | sy;
    }

    public static ZoneTemplate decode(String id, InputStream compressed) throws IOException {
        try (var in = new DataInputStream(new BufferedInputStream(new GZIPInputStream(compressed), 1 << 16))) {
            if (!Arrays.equals(in.readNBytes(MAGIC.length), MAGIC)) throw new IOException("Invalid zone magic");
            int sx = in.readInt(), sy = in.readInt(), sz = in.readInt();
            if (sx < 1 || sz < 1 || sy < 1 || sx > MAX_EDGE || sz > MAX_EDGE || sy > MAX_HEIGHT)
                throw new IOException("Invalid zone size " + sx + "x" + sy + "x" + sz);
            int n = in.readUnsignedShort();
            if (n < 1 || n > MAX_PALETTE) throw new IOException("Invalid palette size " + n);
            List<String> palette = new ArrayList<>(n);
            for (int i = 0; i < n; i++) {
                int len = in.readUnsignedShort();
                if (len < 1 || len > 512) throw new IOException("Invalid palette entry length");
                byte[] b = in.readNBytes(len);
                if (b.length != len) throw new EOFException("Truncated palette");
                String state = new String(b, StandardCharsets.UTF_8);
                if (i == 0 ? !state.equals("minecraft:air") : !ZonePalette.allowed(state))
                    throw new IOException("Palette entry not allowed: " + state);
                palette.add(state);
            }
            long total = (long) sx * sy * sz;
            int runs = in.readInt();
            if (runs < 1 || runs > total) throw new IOException("Invalid run count");
            Map<Long, byte[]> cells = new HashMap<>();
            Map<Long, int[]> counts = new HashMap<>();
            long index = 0, blocks = 0;
            for (int r = 0; r < runs; r++) {
                int value = readVarInt(in);
                long length = readVarInt(in);
                if (value >= n || length < 1 || index + length > total) throw new IOException("Run outside zone/palette");
                if (value != 0) {
                    for (long i = index, end = index + length; i < end; i++) {
                        int x = (int) (i % sx);
                        long t = i / sx;
                        int z = (int) (t % sz), y = (int) (t / sz);
                        long key = order(x >> 4, y >> 4, z >> 4);
                        byte[] c = cells.computeIfAbsent(key, k -> new byte[4096]);
                        c[((y & 15) << 8) | ((z & 15) << 4) | (x & 15)] = (byte) value;
                        counts.computeIfAbsent(key, k -> new int[1])[0]++;
                    }
                    blocks += length;
                }
                index += length;
            }
            if (index != total) throw new IOException("Zone runs do not cover the volume");
            if (in.read() != -1) throw new IOException("Trailing zone data");
            Section[] sections = cells.entrySet().stream().sorted(Map.Entry.comparingByKey()).map(e -> {
                long k = e.getKey();
                return new Section((int) (k >>> 40), (int) (k & 0xFFFFF), (int) ((k >>> 20) & 0xFFFFF), e.getValue(), counts.get(k)[0]);
            }).toArray(Section[]::new);
            return new ZoneTemplate(id, sx, sy, sz, palette, sections, blocks);
        }
    }

    private static int readVarInt(DataInput in) throws IOException {
        int value = 0, shift = 0;
        while (true) {
            int b = in.readUnsignedByte();
            value |= (b & 0x7F) << shift;
            if ((b & 0x80) == 0) return value;
            shift += 7;
            if (shift > 28) throw new IOException("VarInt too long");
        }
    }

    /** Parsed block states (server registries required); resolved once per template. */
    BlockState[] states() {
        BlockState[] s = states;
        if (s == null) {
            s = new BlockState[palette.size()];
            for (int i = 0; i < s.length; i++) {
                try { s[i] = BlockStateParser.parseForBlock(BuiltInRegistries.BLOCK, palette.get(i), false).blockState(); }
                catch (com.mojang.brigadier.exceptions.CommandSyntaxException e) { throw new IllegalStateException(palette.get(i), e); }
            }
            states = s;
        }
        return s;
    }

    // ------------------------------------------------------------------------------------------
    // Budgeted placement
    // ------------------------------------------------------------------------------------------

    /** Placement destination. Implemented over a ServerLevel at runtime and in memory by tests. */
    interface Target {
        /** Requests the chunks covering the block range; true once all are loaded and writable. */
        boolean ensureLoaded(int minX, int minZ, int maxX, int maxZ);
        void set(int x, int y, int z, int paletteIndex);
        /** The column of sections [minX..maxX, minZ..maxZ] is finished (ticket window bookkeeping). */
        default void columnDone(int minX, int minZ, int maxX, int maxZ) {}
        /** Starts loading the chunks of an upcoming column early (no wait). Released with the build. */
        default void prefetch(int minX, int minZ, int maxX, int maxZ) {}
        default void close() {}
    }

    /** Starts a placement at the zone-local origin (0,0,0) = {@code origin}. Expects an empty (void) region. */
    public Build begin(ServerLevel level, BlockPos origin) {
        if (!level.getServer().isSameThread()) throw new IllegalStateException("Zone placement requires the server thread");
        if (origin.getY() < level.getMinY() || origin.getY() + sizeY - 1 > level.getMaxY())
            throw new IllegalArgumentException("Zone " + id + " (height " + sizeY + ") does not fit at y=" + origin.getY());
        return new Build(this, new LevelTarget(level, origin, states()));
    }

    Build begin(Target target) { return new Build(this, target); }

    /** One budgeted placement run. Not thread-safe; drive it from the server tick. */
    public static final class Build implements RisingServices.ZoneBuild {
        private static final int CHECK_EVERY = 128;
        /**
         * Columns whose chunks are requested ahead of placement. Without it every new column waits for its own
         * ticket round trip (~2 ticks), which made the 706-column Gateway take ~78 s of black screen.
         */
        static final int PREFETCH_COLUMNS = 192;
        private int prefetched = -1;
        private final ZoneTemplate template;
        private final Target target;
        private int section, cell;
        private long placed;
        private boolean done, cancelled;

        private Build(ZoneTemplate template, Target target) { this.template = template; this.target = target; }

        @Override public boolean step(long nanoBudget) {
            if (done || cancelled) return true;
            long deadline = System.nanoTime() + Math.max(0, nanoBudget);
            Section[] sections = template.sections;
            int sinceCheck = 0;
            while (section < sections.length) {
                Section s = sections[section];
                int x0 = s.sx << 4, z0 = s.sz << 4, y0 = s.sy << 4;
                if (cell == 0) {
                    prefetch();
                    if (!target.ensureLoaded(x0, z0, x0 + 15, z0 + 15)) return false;
                }
                byte[] c = s.cells;
                while (cell < 4096) {
                    int v = c[cell] & 0xFF;
                    int i = cell++;
                    if (v != 0) {
                        target.set(x0 + (i & 15), y0 + (i >>> 8), z0 + ((i >>> 4) & 15), v);
                        placed++;
                        if (++sinceCheck >= CHECK_EVERY) {
                            sinceCheck = 0;
                            if (System.nanoTime() >= deadline && cell < 4096) return false;
                        }
                    }
                }
                cell = 0;
                section++;
                if (section == sections.length || sections[section].sx != s.sx || sections[section].sz != s.sz)
                    target.columnDone(x0, z0, x0 + 15, z0 + 15);
                if (System.nanoTime() >= deadline && section < sections.length) return false;
            }
            done = true;
            target.close();
            return true;
        }

        /** Requests the chunks of the next PREFETCH_COLUMNS distinct columns after the current section. */
        private void prefetch() {
            Section[] sections = template.sections;
            int columns = 0, i = Math.max(section, prefetched + 1);
            // Count columns already requested ahead of the current one so the window stays bounded.
            for (int j = section + 1; j < i && j < sections.length; j++)
                if (sections[j].sx != sections[j - 1].sx || sections[j].sz != sections[j - 1].sz) columns++;
            for (; i < sections.length && columns < PREFETCH_COLUMNS; i++) {
                Section s = sections[i];
                if (i == 0 || s.sx != sections[i - 1].sx || s.sz != sections[i - 1].sz) {
                    columns++;
                    target.prefetch(s.sx << 4, s.sz << 4, (s.sx << 4) + 15, (s.sz << 4) + 15);
                }
                prefetched = i;
            }
        }

        @Override public double progress() {
            if (done) return 1.0;
            return template.blockCount == 0 ? 1.0 : Math.min(1.0, (double) placed / template.blockCount);
        }

        @Override public void cancel() {
            if (cancelled || done) return;
            cancelled = true;
            target.close();
        }

        public boolean done() { return done; }
        public long placed() { return placed; }
    }

    /** ServerLevel target: no neighbour/shape updates, no drops/on-place side effects; owned chunk tickets. */
    static final class LevelTarget implements Target {
        // Private non-persistent loading ticket (same pattern as TowerDetailPass); never touches others' tickets.
        private static final TicketType TICKET = new TicketType(0, TicketType.FLAG_LOADING | TicketType.FLAG_KEEP_DIMENSION_ACTIVE);
        private static final int FLAGS = Block.UPDATE_CLIENTS | Block.UPDATE_SKIP_ALL_SIDEEFFECTS;
        /** Finished section columns keep their tickets for a short window so pending light work settles. */
        private static final int WINDOW = 6;
        private final ServerLevel level;
        private final BlockPos origin;
        private final BlockState[] states;
        private final BlockPos.MutableBlockPos cursor = new BlockPos.MutableBlockPos();
        private final Map<ChunkPos, CompletableFuture<?>> tickets = new LinkedHashMap<>();
        private final ArrayDeque<List<ChunkPos>> finished = new ArrayDeque<>();
        private List<ChunkPos> active = List.of();
        private boolean closed;

        LevelTarget(ServerLevel level, BlockPos origin, BlockState[] states) {
            this.level = level; this.origin = origin.immutable(); this.states = states;
        }

        private List<ChunkPos> chunks(int minX, int minZ, int maxX, int maxZ) {
            List<ChunkPos> out = new ArrayList<>(4);
            for (int cx = (origin.getX() + minX) >> 4; cx <= (origin.getX() + maxX) >> 4; cx++)
                for (int cz = (origin.getZ() + minZ) >> 4; cz <= (origin.getZ() + maxZ) >> 4; cz++)
                    out.add(new ChunkPos(cx, cz));
            return out;
        }

        @Override public boolean ensureLoaded(int minX, int minZ, int maxX, int maxZ) {
            if (closed) return false;
            boolean ready = true;
            active = chunks(minX, minZ, maxX, maxZ);
            for (ChunkPos c : active) {
                CompletableFuture<?> f = tickets.get(c);
                if (f == null) {
                    tickets.put(c, level.getChunkSource().addTicketAndLoadWithRadius(TICKET, c, 0));
                    ready = false;
                } else if (!f.isDone() || level.getChunkSource().getChunkNow(c.x(), c.z()) == null) {
                    if (f.isCompletedExceptionally() || f.isCancelled())
                        throw new IllegalStateException("Zone chunk failed to load: " + c);
                    ready = false;
                }
            }
            return ready;
        }

        @Override public void prefetch(int minX, int minZ, int maxX, int maxZ) {
            if (closed) return;
            for (ChunkPos c : chunks(minX, minZ, maxX, maxZ))
                tickets.computeIfAbsent(c, k -> level.getChunkSource().addTicketAndLoadWithRadius(TICKET, k, 0));
        }

        @Override public void set(int x, int y, int z, int paletteIndex) {
            cursor.set(origin.getX() + x, origin.getY() + y, origin.getZ() + z);
            level.setBlock(cursor, states[paletteIndex], FLAGS);
        }

        @Override public void columnDone(int minX, int minZ, int maxX, int maxZ) {
            finished.addLast(chunks(minX, minZ, maxX, maxZ));
            while (finished.size() > WINDOW) release(finished.removeFirst());
        }

        private void release(List<ChunkPos> column) {
            for (ChunkPos c : column) {
                // A neighbouring column may still need this chunk; only drop it once nothing pending uses it.
                if (active.contains(c) || finished.stream().anyMatch(l -> l.contains(c))) continue;
                if (tickets.remove(c) != null) level.getChunkSource().removeTicketWithRadius(TICKET, c, 0);
            }
        }

        @Override public void close() {
            if (closed) return;
            closed = true;
            tickets.keySet().forEach(c -> level.getChunkSource().removeTicketWithRadius(TICKET, c, 0));
            tickets.clear();
            finished.clear();
        }
    }
}
