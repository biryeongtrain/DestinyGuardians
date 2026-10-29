package kim.biryeong.destiny.world;

import com.google.gson.*;
import kim.biryeong.destiny.DestinyGuardians;
import net.minecraft.commands.arguments.blocks.BlockStateParser;
import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.level.ChunkPos;
import net.minecraft.world.level.EmptyBlockGetter;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.saveddata.SavedDataType;

import java.io.*;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.*;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.CompletionException;
import java.util.zip.GZIPInputStream;

/** Versioned, source-pinned recoloring of exposed full smooth-stone blocks only.
 * Parsing/geometry checks run off-thread; the shared bounded driver writes on the server thread.
 * Master owns the JSON data and source artwork review. Existing props and user edits always win.
 */
public final class TowerMaterialPass implements AutoCloseable {
    static final String RESOURCE = "/data/destiny/tower/courtyard-materials-w243.json.gz";
    static final String SOURCE_SHA256 = "55425ec1d14bc970ba05e90338e10a34468498d8a655d49ebc014d633996098d";
    static final int MAX_CELLS = 100_000, OPERATIONS_PER_TICK = 128;
    private static final int MAX_JSON_BYTES = 16 * 1024 * 1024;
    private static final String EXPECTED = "minecraft:smooth_stone";
    private static final SavedDataType<TowerDetailPass.Ledger> LEDGER = new SavedDataType<>(
            Identifier.fromNamespaceAndPath("destiny", "tower_courtyard_materials_v1"),
            TowerDetailPass.Ledger::new, TowerDetailPass.Ledger.CODEC, null);
    private final ServerLevel level;
    private final CompletableFuture<List<TowerDetailPass.Piece>> prepared;
    private TowerDetailPass driver;
    private boolean closed;

    private TowerMaterialPass(ServerLevel level, TowerVoxelMap map) {
        this.level = level;
        prepared = CompletableFuture.supplyAsync(() -> {
            try (InputStream data = TowerMaterialPass.class.getResourceAsStream(RESOURCE);
                 InputStream source = TowerMaterialPass.class.getResourceAsStream(TowerVoxelMap.VOXEL_RESOURCE)) {
                if (data == null) throw new IOException("타워 재질 데이터가 없습니다: " + RESOURCE);
                if (source == null) throw new IOException("타워 원본 복셀이 없습니다");
                String actualSha = HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(source.readAllBytes()));
                return decode(data, map, actualSha);
            } catch (IOException | NoSuchAlgorithmException e) { throw new CompletionException(e); }
        });
    }

    static TowerMaterialPass start(ServerLevel level, TowerVoxelMap map) {
        return new TowerMaterialPass(level, map);
    }

    /** Only called once the detail/branch pass has successfully finished. Never waits on IO. */
    void tick() {
        if (closed) return;
        if (driver == null) {
            if (!prepared.isDone()) return;
            try {
                driver = new TowerDetailPass(level, prepared.join(), LEDGER, OPERATIONS_PER_TICK, false, "재질");
            } catch (CompletionException e) {
                DestinyGuardians.LOGGER.error("타워 재질 적용 생략: 검증 실패. 기존 월드와 이력은 보존합니다", e.getCause());
                closed = true;
                return;
            }
        }
        driver.tick();
        if (driver.isFinished()) close();
    }

    boolean isFinished() { return driver != null && driver.isFinished(); }

    @Override public void close() {
        if (driver != null) driver.close();
        prepared.cancel(false);
        closed = true;
    }

    /** Reject the entire data set before a single write if provenance or geometry is invalid. */
    static List<TowerDetailPass.Piece> decode(InputStream compressed, TowerVoxelMap map, String actualSourceSha) throws IOException {
        try (var gzip = new GZIPInputStream(compressed)) {
            byte[] bytes = gzip.readNBytes(MAX_JSON_BYTES + 1);
            if (bytes.length > MAX_JSON_BYTES) throw new IOException("타워 재질 JSON 크기 초과");
            JsonObject root = JsonParser.parseString(new String(bytes, StandardCharsets.UTF_8)).getAsJsonObject();
            if (integer(root.get("schema")) != 1 || !SOURCE_SHA256.equals(root.get("sourceVoxelSHA256").getAsString())
                    || !SOURCE_SHA256.equals(actualSourceSha)) throw new IOException("타워 재질 원본 SHA/schema 불일치");
            JsonArray paletteJson = root.getAsJsonArray("palette");
            if (paletteJson.isEmpty() || paletteJson.size() > 4096) throw new IOException("타워 재질 팔레트 크기 오류");
            List<String> palette = new ArrayList<>();
            for (var value : paletteJson) {
                String name = value.getAsString();
                if (!name.matches("minecraft:[a-z0-9_]+(\\[[a-z0-9_=,]+\\])?"))
                    throw new IOException("바닐라 재질 상태만 허용합니다: " + name);
                BlockState state = BlockStateParser.parseForBlock(BuiltInRegistries.BLOCK, name, false).blockState();
                if (state.isAir() || !state.getFluidState().isEmpty() || state.hasBlockEntity()
                        || !Block.isShapeFullBlock(state.getCollisionShape(EmptyBlockGetter.INSTANCE, BlockPos.ZERO)))
                    throw new IOException("충돌을 유지하는 온전한 블록만 허용합니다: " + name);
                palette.add(name);
            }
            JsonArray cells = root.getAsJsonArray("cells");
            if (cells.size() > MAX_CELLS) throw new IOException("타워 재질 100000좌표 상한 초과");
            Map<ChunkPos, List<TowerDetailPass.Edit>> chunks = new LinkedHashMap<>();
            Set<Long> seen = new HashSet<>();
            for (var cell : cells) {
                JsonArray row = cell.getAsJsonArray();
                if (row.size() != 4) throw new IOException("타워 재질 좌표는 x/y/z/paletteIndex 4개여야 합니다");
                int x = integer(row.get(0)), y = integer(row.get(1)), z = integer(row.get(2)), index = integer(row.get(3));
                if (index < 0 || index >= palette.size() || !map.manifest().bounds().contains(x, y, z))
                    throw new IOException("타워 재질 좌표/팔레트 범위 오류");
                BlockPos pos = new BlockPos(x, y, z);
                int source = map.paletteIndexAt(x, y, z);
                if (source < 0 || !EXPECTED.equals(map.palette().get(source)) || !exposed(map, pos))
                    throw new IOException("원본의 노출 smooth_stone만 재질 변경할 수 있습니다: " + pos);
                if (!seen.add(pos.asLong())) throw new IOException("중복 타워 재질 좌표: " + pos);
                chunks.computeIfAbsent(new ChunkPos(x >> 4, z >> 4), ignored -> new ArrayList<>())
                        .add(new TowerDetailPass.Edit(pos, EXPECTED, palette.get(index)));
            }
            List<TowerDetailPass.Piece> pieces = new ArrayList<>();
            chunks.forEach((chunk, edits) -> pieces.add(new TowerDetailPass.Piece("materials/" + chunk.x() + "/" + chunk.z(),
                    List.copyOf(edits), List.of(), Set.of(chunk))));
            return List.copyOf(pieces);
        } catch (RuntimeException | com.mojang.brigadier.exceptions.CommandSyntaxException e) {
            throw new IOException("타워 재질 데이터 해석 실패", e);
        }
    }

    private static int integer(JsonElement value) { return value.getAsBigDecimal().intValueExact(); }
    private static boolean exposed(TowerVoxelMap map, BlockPos pos) {
        for (var direction : net.minecraft.core.Direction.values()) {
            BlockPos adjacent = pos.relative(direction);
            if (map.paletteIndexAt(adjacent.getX(), adjacent.getY(), adjacent.getZ()) < 0) return true;
        }
        return false;
    }
}
