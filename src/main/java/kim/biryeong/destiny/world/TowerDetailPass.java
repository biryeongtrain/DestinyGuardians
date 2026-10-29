package kim.biryeong.destiny.world;

import com.mojang.serialization.Codec;
import kim.biryeong.destiny.DestinyGuardians;
import net.minecraft.commands.arguments.blocks.BlockStateParser;
import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.TicketType;
import net.minecraft.world.level.ChunkPos;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.saveddata.SavedData;
import net.minecraft.world.level.saveddata.SavedDataType;

import java.util.*;
import java.util.concurrent.CompletableFuture;

/** Small, source-checked Courtyard finishing pass, also applied to previously saved Tower chunks.
 * References and review cameras: docs/qa/2026-10-29/w243/tower-worker.md.
 * No source voxel, generator, stairs, spawn, or existing world is regenerated.
 */
public final class TowerDetailPass implements AutoCloseable {
    static final int OPERATIONS_PER_TICK = 48;
    private static final long TICK_BUDGET_NANOS = 2_000_000;
    // A private, nonpersistent loading ticket: never reuses/removes a player's or QA's ticket.
    private static final TicketType LOAD_TICKET = new TicketType(0, TicketType.FLAG_LOADING | TicketType.FLAG_KEEP_DIMENSION_ACTIVE);
    private static final SavedDataType<Ledger> LEDGER = new SavedDataType<>(
            Identifier.fromNamespaceAndPath("destiny", "tower_courtyard_details_v1"),
            Ledger::new, Ledger.CODEC, null);
    private final ServerLevel level;
    private final List<Piece> pieces;
    private final Ledger ledger;
    private final int operationsPerTick;
    private final boolean wholePieceGuard;
    private final String label;
    private final Map<String, BlockState> states = new HashMap<>();
    private final Map<ChunkPos, CompletableFuture<?>> tickets = new LinkedHashMap<>();
    private int pieceIndex, editIndex, changed, skipped;
    private boolean checked, closed;

    private TowerDetailPass(ServerLevel level, TowerVoxelMap map) {
        this(level, plan(map), LEDGER, OPERATIONS_PER_TICK, true, "디테일");
    }

    /** Shared bounded driver; materials use per-cell guards and their own persistent ledger. */
    TowerDetailPass(ServerLevel level, List<Piece> pieces, SavedDataType<Ledger> ledgerType,
            int operationsPerTick, boolean wholePieceGuard, String label) {
        if (!level.getServer().isSameThread()) throw new IllegalStateException("Tower overlay requires server thread");
        this.level = level;
        this.pieces = List.copyOf(pieces);
        this.ledger = level.getDataStorage().computeIfAbsent(ledgerType);
        this.operationsPerTick = operationsPerTick;
        this.wholePieceGuard = wholePieceGuard;
        this.label = label;
        DestinyGuardians.LOGGER.info("타워 {} 적용 준비: {} 조각 / {} 후보 좌표", label, pieces.size(),
                pieces.stream().mapToInt(p -> p.edits().size()).sum());
    }

    static TowerDetailPass start(ServerLevel level, TowerVoxelMap map) {
        if (!level.getServer().isSameThread()) throw new IllegalStateException("Tower details require server thread");
        return new TowerDetailPass(level, map);
    }

    /** Called by the server lifecycle tick, even when Fantasy pauses an empty dimension. */
    void tick() {
        if (closed) return;
        if (pieceIndex >= pieces.size()) {
            DestinyGuardians.LOGGER.info("타워 {} 적용 완료: {} 변경, {} 건너뜀; 영구 이력 유지", label, changed, skipped);
            close();
            return;
        }
        Piece piece = pieces.get(pieceIndex);
        if (piece.edits().stream().allMatch(e -> ledger.considered.contains(e.pos().asLong()))) {
            nextPiece();
            return;
        }
        // One asynchronous FULL-chunk request per tick. getChunkFuture on the server thread
        // performs managedBlock in 26.3; deliberately use the nonblocking ticket API instead.
        for (ChunkPos chunk : piece.chunks()) {
            if (!tickets.containsKey(chunk)) {
                tickets.put(chunk, level.getChunkSource().addTicketAndLoadWithRadius(LOAD_TICKET, chunk, 0));
                return;
            }
        }
        if (tickets.values().stream().anyMatch(f -> !f.isDone())) return;
        if (tickets.values().stream().anyMatch(f -> f.isCompletedExceptionally() || f.isCancelled())) {
            DestinyGuardians.LOGGER.warn("Tower detail chunk load failed for {}; preserving existing blocks", piece.id());
            close();
            return;
        }
        if (piece.chunks().stream().anyMatch(c -> level.getChunkSource().getChunkNow(c.x(), c.z()) == null)) return;
        if (!checked && wholePieceGuard) {
            // A conflicting support or target cancels the whole object, rather than leaving
            // a tree/canopy floating above an administrator's edited foundation.
            boolean pristine = piece.supports().stream().allMatch(s -> current(s.pos()).equals(state(s.expected())))
                    && piece.edits().stream().allMatch(e -> ledger.considered.contains(e.pos().asLong())
                    || current(e.pos()).equals(state(e.expected())));
            if (!pristine) {
                piece.edits().forEach(e -> ledger.consider(e.pos()));
                skipped += piece.edits().size();
                nextPiece();
                return;
            }
            checked = true;
        }
        long deadline = System.nanoTime() + TICK_BUDGET_NANOS;
        int operations = 0;
        while (editIndex < piece.edits().size() && operations < operationsPerTick && System.nanoTime() < deadline) {
            Edit edit = piece.edits().get(editIndex++);
            if (ledger.considered.contains(edit.pos().asLong())) continue;
            operations++;
            // Recheck at write time: player edits between ticks always win. Consume skipped
            // cells too, so later restarts do not recreate a deliberately removed decoration.
            if (apply(edit, ledger, () -> piece.supports().stream().allMatch(s -> current(s.pos()).equals(state(s.expected()))),
                    this::current, this::state, (pos, block) -> level.setBlock(pos, block,
                            Block.UPDATE_CLIENTS | Block.UPDATE_KNOWN_SHAPE))) changed++;
            else skipped++;
        }
        if (editIndex == piece.edits().size()) nextPiece();
    }

    /** Same conditional write path used by live ticks and the small in-memory regression fixture. */
    static boolean apply(Edit edit, Ledger ledger, java.util.function.BooleanSupplier supported,
            java.util.function.Function<BlockPos, BlockState> read, java.util.function.Function<String, BlockState> parse,
            java.util.function.BiPredicate<BlockPos, BlockState> write) {
        if (ledger.contains(edit.pos())) return false;
        boolean changed = supported.getAsBoolean() && read.apply(edit.pos()).equals(parse.apply(edit.expected()))
                && write.test(edit.pos(), parse.apply(edit.replacement()));
        ledger.consider(edit.pos());
        return changed;
    }

    private BlockState current(BlockPos pos) {
        // Every accessed chunk has an owned ticket and was observed FULL before this read.
        return level.getBlockState(pos);
    }
    private BlockState state(String value) {
        return states.computeIfAbsent(value, key -> {
            try { return BlockStateParser.parseForBlock(BuiltInRegistries.BLOCK, key, false).blockState(); }
            catch (com.mojang.brigadier.exceptions.CommandSyntaxException e) { throw new IllegalArgumentException(key, e); }
        });
    }
    private void nextPiece() {
        releaseTickets();
        pieceIndex++;
        editIndex = 0;
        checked = false;
    }
    private void releaseTickets() {
        tickets.keySet().forEach(c -> level.getChunkSource().removeTicketWithRadius(LOAD_TICKET, c, 0));
        tickets.clear();
    }
    boolean isFinished() { return closed && pieceIndex >= pieces.size(); }

    @Override public void close() {
        releaseTickets();
        closed = true;
    }

    /** Position ledger survives normal world save/reopen, including user removals and skipped conflicts.
     * It is scoped to this Tower dimension, not the overworld. Never clear this data to reapply art.
     */
    static final class Ledger extends SavedData {
        static final Codec<Ledger> CODEC = Codec.LONG.listOf().fieldOf("considered").xmap(Ledger::new,
                l -> l.considered.stream().sorted().toList()).codec();
        private final Set<Long> considered;
        Ledger() { considered = new HashSet<>(); }
        private Ledger(List<Long> saved) { considered = new HashSet<>(saved); }
        boolean contains(BlockPos pos) { return considered.contains(pos.asLong()); }
        void consider(BlockPos pos) { if (considered.add(pos.asLong())) setDirty(); }
    }

    record Edit(BlockPos pos, String expected, String replacement) {}
    record Support(BlockPos pos, String expected) {}
    record Piece(String id, List<Edit> edits, List<Support> supports, Set<ChunkPos> chunks) {}

    static List<Piece> plan(TowerVoxelMap map) {
        var initial = initialPlan(map);
        Planner b = new Planner(map);
        b.pieces.addAll(initial);
        initial.forEach(p -> p.edits().forEach(e -> b.occupied.add(e.pos())));
        // Vision 1 revision: append new-air cells only. The original 907 edits and ledger
        // remain untouched, so a saved Tower receives these additions without replaying art.
        b.arrivalCrown("arrival/crown-west-r2", 64, 74, -38, -1);
        b.arrivalCrown("arrival/crown-east-r2", 78, 74, -32, 1);
        return List.copyOf(b.pieces);
    }

    static List<Piece> initialPlan(TowerVoxelMap map) {
        Planner b = new Planner(map);
        // 1. Arrival forecourt: low white planters, two small spreading trees, warm lights.
        b.planter("arrival/tree-west", 64, 74, -38, true);
        b.planter("arrival/tree-east", 78, 74, -32, true);
        b.bench("arrival/bench", 79, 74, -9);
        b.lamp("arrival/lamp-west", 63, 74, -31);
        b.lamp("arrival/lamp-east", 83, 74, -28);
        b.panel("arrival/inlay", 64, 74, -46, 11, 3);
        // 2. Courtyard vendor frontage: three red/orange fabric bays, counters and utility cases.
        for (int x : new int[]{28, 43, 58}) {
            b.stall("market/stall-" + x, x, 74, -96);
            b.panel("market/apron-" + x, x - 3, 74, -92, 7, 3);
            b.crates("market/cases-" + x, x + 5, 74, -96);
        }
        b.lamp("market/lamp-west", 21, 74, -91);
        b.lamp("market/lamp-east", 65, 74, -96);
        // 3. Lower garden walk. Keep the long axial route beside these edge furnishings open.
        b.planter("garden/tree-north", 17, 72, -38, true);
        b.planter("garden/flowers-south", 17, 72, -22, false);
        b.bench("garden/bench", 20, 72, -30);
        b.lamp("garden/lamp", 14, 72, -28);
        b.panel("garden/inlay", 20, 72, -42, 2, 6);
        // 4. South overlook lounge, in the existing terrace footprint.
        b.planter("overlook/tree", 85, 74, 3, true);
        b.bench("overlook/bench-west", 76, 74, 2);
        b.bench("overlook/bench-east", 95, 74, 5);
        b.rail("overlook/lounge-rail", 72, 74, 7, 9);
        b.lamp("overlook/lamp", 91, 74, 7);
        b.panel("overlook/inlay", 76, 74, -3, 7, 2);
        // 5. Lower eastern service bay: source dark decking stays intact; surface-level conduits/cases.
        b.crates("service/cases-north", 74, 70, -75);
        b.crates("service/cases-south", 75, 70, -64);
        b.conduit("service/conduit", 73, 70, -78, 9);
        b.workbench("service/workbench", 78, 70, -70);
        b.lamp("service/work-light-south", 72, 70, -62);
        b.lamp("service/work-light-north", 72, 70, -82);
        return List.copyOf(b.pieces);
    }

    private static final class Planner {
        private final TowerVoxelMap map;
        private final List<Piece> pieces = new ArrayList<>();
        private final Set<BlockPos> occupied = new HashSet<>();
        Planner(TowerVoxelMap map) { this.map = map; }
        private String original(BlockPos p) {
            int i = map.paletteIndexAt(p.getX(), p.getY(), p.getZ());
            return i < 0 ? "minecraft:air" : map.palette().get(i);
        }
        private boolean protectedSpawn(BlockPos p) {
            var s = map.manifest().spawn();
            return Math.abs(p.getX() - Math.floor(s.x())) <= 8 && Math.abs(p.getZ() - Math.floor(s.z())) <= 8;
        }
        private final class ObjectBuilder {
            final String id;
            final int floor;
            final Map<BlockPos, String> targets = new LinkedHashMap<>();
            Support attachment;
            ObjectBuilder(String id, int floor) { this.id = id; this.floor = floor; }
            void put(int x, int y, int z, String state) { targets.put(new BlockPos(x, y, z), "minecraft:" + state); }
            void finish(boolean floorPanel) {
                List<Edit> edits = new ArrayList<>();
                Map<BlockPos, Support> supports = new LinkedHashMap<>();
                for (var entry : targets.entrySet()) {
                    BlockPos p = entry.getKey();
                    String source = original(p);
                    if (protectedSpawn(p) || occupied.contains(p)
                            || !map.manifest().bounds().contains(p.getX(), p.getY(), p.getZ())
                            || !(floorPanel ? source.equals("minecraft:smooth_stone")
                            && original(p.above()).equals("minecraft:air") && original(p.above(2)).equals("minecraft:air")
                            : source.equals("minecraft:air"))) {
                        // A whole prop is omitted if its measured footprint intersects source geometry.
                        return;
                    }
                    if (!floorPanel) {
                        BlockPos base = new BlockPos(p.getX(), floor, p.getZ());
                        String support = original(base);
                        if (!Set.of("minecraft:smooth_stone", "minecraft:black_concrete", "minecraft:iron_block").contains(support)) return;
                        supports.put(base, new Support(base, support));
                    }
                    edits.add(new Edit(p, source, entry.getValue()));
                }
                if (edits.isEmpty()) return;
                if (attachment != null) supports.put(attachment.pos(), attachment);
                Set<ChunkPos> chunks = new LinkedHashSet<>();
                edits.forEach(e -> chunks.add(new ChunkPos(e.pos().getX() >> 4, e.pos().getZ() >> 4)));
                supports.keySet().forEach(p -> chunks.add(new ChunkPos(p.getX() >> 4, p.getZ() >> 4)));
                pieces.add(new Piece(id, List.copyOf(edits), List.copyOf(supports.values()), Collections.unmodifiableSet(chunks)));
                occupied.addAll(targets.keySet());
            }
        }
        void planter(String id, int x, int y, int z, boolean tree) {
            var o = new ObjectBuilder(id, y);
            for (int dx = -2; dx <= 2; dx++) for (int dz = -2; dz <= 2; dz++) {
                boolean edge = Math.abs(dx) == 2 || Math.abs(dz) == 2;
                o.put(x + dx, y + 1, z + dz, edge ? "smooth_quartz_slab[type=bottom]" : "rooted_dirt");
                if (!edge) o.put(x + dx, y + 2, z + dz, tree ? "azalea_leaves[persistent=true]" :
                        ((dx + dz) % 2 == 0 ? "orange_tulip" : "oxeye_daisy"));
            }
            if (tree) {
                for (int h = 2; h <= 5; h++) o.put(x, y + h, z, "oak_log[axis=y]");
                for (int h = 5; h <= 7; h++) for (int dx = -2; dx <= 2; dx++) for (int dz = -2; dz <= 2; dz++) {
                    if (Math.abs(dx) + Math.abs(dz) > (h == 7 ? 2 : 3) || dx == 0 && dz == 0 && h == 5) continue;
                    o.put(x + dx, y + h, z + dz, "oak_leaves[persistent=true]");
                }
            }
            o.finish(false);
        }
        void arrivalCrown(String id, int x, int y, int z, int side) {
            var o = new ObjectBuilder(id, y);
            // The old trunk is a read-only anchor: removing/editing it cancels this addition.
            o.attachment = new Support(new BlockPos(x, y + 4, z), "minecraft:oak_log[axis=y]");
            for (int step = 1; step <= 2; step++) {
                fresh(o, x + step * side, y + 4, z, "oak_log[axis=x]");
                fresh(o, x, y + 4, z - step, "oak_log[axis=z]");
            }
            String leaves = "oak_leaves[persistent=true]";
            // Unequal lobes break the flat, centered silhouette seen in Vision 1.
            for (int dz = -1; dz <= 1; dz++) {
                for (int h = 5; h <= 6; h++) fresh(o, x + 3 * side, y + h, z + dz, leaves);
            }
            fresh(o, x + 3 * side, y + 7, z, leaves);
            for (int dz = 0; dz <= 1; dz++) fresh(o, x - 3 * side, y + 5, z + dz, leaves);
            for (int dx = -1; dx <= 1; dx++) fresh(o, x + dx, y + 5, z - 3, leaves);
            for (int dx : new int[]{0, side}) fresh(o, x + dx, y + 6, z - 3, leaves);
            for (int dz : new int[]{-1, 1}) fresh(o, x + 2 * side, y + 4, z + dz, leaves);
            fresh(o, x + 3 * side, y + 4, z, leaves);
            fresh(o, x + side, y + 4, z - 2, leaves);
            fresh(o, x + 2 * side, y + 7, z - 1, leaves);
            fresh(o, x + side, y + 7, z - 2, leaves);
            fresh(o, x + side, y + 8, z - 1, leaves);
            fresh(o, x + side, y + 8, z, leaves);
            fresh(o, x, y + 8, z - 1, leaves);
            o.finish(false);
        }
        private void fresh(ObjectBuilder o, int x, int y, int z, String state) {
            BlockPos p = new BlockPos(x, y, z);
            if (!occupied.contains(p) && !o.targets.containsKey(p)) o.put(x, y, z, state);
        }
        void bench(String id, int x, int y, int z) {
            var o = new ObjectBuilder(id, y);
            for (int dx = -2; dx <= 2; dx++) {
                o.put(x + dx, y + 1, z, "smooth_stone_slab[type=bottom]");
                o.put(x + dx, y + 1, z + 1, "polished_andesite_slab[type=top]");
                o.put(x + dx, y + 2, z + 1, "iron_bars[east=true,west=true]");
            }
            for (int dx : new int[]{-3, 3}) o.put(x + dx, y + 1, z, "polished_deepslate_wall");
            o.finish(false);
        }
        void lamp(String id, int x, int y, int z) {
            var o = new ObjectBuilder(id, y);
            o.put(x, y + 1, z, "polished_andesite");
            for (int h = 2; h <= 4; h++) o.put(x, y + h, z, "iron_bars");
            o.put(x, y + 5, z, "ochre_froglight");
            o.put(x, y + 6, z, "smooth_stone_slab[type=bottom]");
            o.finish(false);
        }
        void stall(String id, int x, int y, int z) {
            var o = new ObjectBuilder(id, y);
            for (int dx = -3; dx <= 3; dx++) for (int dz = -2; dz <= 1; dz++) {
                o.put(x + dx, y + 6, z + dz, (dz == 1 || dx == -3 || dx == 3) ? "orange_wool" : "red_wool");
                if (dz == 1 && dx % 2 == 0) o.put(x + dx, y + 5, z + dz, "red_wool");
            }
            for (int dx : new int[]{-3, 3}) for (int dz : new int[]{-2, 1})
                for (int h = 1; h <= 5; h++) o.put(x + dx, y + h, z + dz, "iron_bars");
            for (int dx = -2; dx <= 2; dx++) {
                o.put(x + dx, y + 1, z, "gray_concrete");
                o.put(x + dx, y + 2, z, "polished_andesite_slab[type=bottom]");
                o.put(x + dx, y + 1, z - 2, "red_concrete");
            }
            o.put(x - 1, y + 3, z, "gray_concrete");
            o.put(x - 1, y + 3, z + 1, "light_blue_stained_glass_pane[east=true,west=true]");
            o.put(x + 1, y + 3, z, "iron_block");
            o.put(x, y + 5, z - 1, "sea_lantern");
            o.finish(false);
        }
        void crates(String id, int x, int y, int z) {
            var o = new ObjectBuilder(id, y);
            for (int dx = 0; dx <= 2; dx++) {
                o.put(x + dx, y + 1, z, dx == 1 ? "yellow_terracotta" : "gray_concrete");
                o.put(x + dx, y + 2, z, "iron_trapdoor[half=bottom,open=false]");
            }
            o.put(x, y + 1, z + 1, "light_gray_concrete");
            o.put(x, y + 2, z + 1, "polished_andesite_slab[type=bottom]");
            o.finish(false);
        }
        void workbench(String id, int x, int y, int z) {
            var o = new ObjectBuilder(id, y);
            for (int dx = -2; dx <= 2; dx++) {
                o.put(x + dx, y + 1, z, dx % 2 == 0 ? "gray_concrete" : "yellow_terracotta");
                o.put(x + dx, y + 2, z, "smooth_quartz_slab[type=bottom]");
                o.put(x + dx, y + 1, z - 1, "iron_bars[east=true,west=true]");
                o.put(x + dx, y + 3, z - 1, "iron_bars[east=true,west=true]");
            }
            o.put(x - 1, y + 3, z, "light_blue_stained_glass_pane[east=true,west=true]");
            o.put(x + 1, y + 3, z, "iron_block");
            o.finish(false);
        }
        void rail(String id, int x, int y, int z, int length) {
            var o = new ObjectBuilder(id, y);
            for (int dx = 0; dx < length; dx++) {
                o.put(x + dx, y + 1, z, "iron_bars[east=true,west=true]");
                if (dx % 4 == 0) o.put(x + dx, y + 2, z, "smooth_stone_slab[type=bottom]");
            }
            o.finish(false);
        }
        void conduit(String id, int x, int y, int z, int length) {
            var o = new ObjectBuilder(id, y);
            for (int dz = 0; dz < length; dz++) o.put(x, y + 1, z + dz, "polished_blackstone_brick_slab[type=bottom]");
            o.put(x, y + 1, z, "yellow_terracotta");
            o.put(x, y + 1, z + length - 1, "yellow_terracotta");
            o.finish(false);
        }
        void panel(String id, int x, int y, int z, int width, int depth) {
            // Individual panels may straddle a missing/edited source floor. Each cell is its
            // own guarded piece; none fills air or extends the source surface.
            for (int dx = 0; dx < width; dx++) for (int dz = 0; dz < depth; dz++) {
                var o = new ObjectBuilder(id + "/" + dx + "-" + dz, y);
                o.put(x + dx, y, z + dz, dx == 0 || dx == width - 1 ? "polished_deepslate" :
                        (dz == 0 ? "light_gray_concrete" : "polished_andesite"));
                o.finish(true);
            }
        }
    }
}
