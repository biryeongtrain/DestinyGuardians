package kim.biryeong.destiny.world;

import com.google.gson.*;
import kim.biryeong.destiny.DestinyGuardians;
import net.minecraft.commands.arguments.blocks.BlockStateParser;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
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
import java.security.DigestInputStream;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.*;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.CompletionException;
import java.util.zip.GZIPInputStream;

/** Source-pinned baked surface overlay, after details and W243. Existing edits and ledgers win. */
public final class TowerBakedMaterialPass implements AutoCloseable {
    static final String RESOURCE = "/data/destiny/tower/courtyard-baked-w245.json.gz";
    static final String PRIOR_SHA256 = "a0ecb154be54569b4bb183fdbc33dd03b750da6c97a4024f0fd7e79b5ad429f4";
    static final int MAX_CELLS = 200_000, OPERATIONS_PER_TICK = 128;
    private static final int MAX_JSON_BYTES = 32 * 1024 * 1024;
    private static final int MAX_PRIOR_BYTES = 16 * 1024 * 1024;
    private static final SavedDataType<TowerDetailPass.Ledger> LEDGER = new SavedDataType<>(
            Identifier.fromNamespaceAndPath("destiny", "tower_courtyard_baked_w245"),
            TowerDetailPass.Ledger::new, TowerDetailPass.Ledger.CODEC, null);
    private final ServerLevel level;
    private final CompletableFuture<List<TowerDetailPass.Piece>> prepared;
    private TowerDetailPass driver;
    private boolean closed;

    private TowerBakedMaterialPass(ServerLevel level, TowerVoxelMap map) {
        this.level = level;
        // All resource IO, gzip/JSON decoding, palette parsing and source geometry checks are off-thread.
        prepared = CompletableFuture.supplyAsync(() -> {
            try (InputStream data = resource(RESOURCE);
                 InputStream source = resource(TowerVoxelMap.VOXEL_RESOURCE);
                 InputStream prior = resource(TowerMaterialPass.RESOURCE)) {
                String sourceSha = sha256(source);
                byte[] priorBytes = prior.readNBytes(MAX_PRIOR_BYTES + 1);
                if (priorBytes.length > MAX_PRIOR_BYTES) throw new IOException("W243 압축 데이터 크기 초과");
                return decode(data, map, sourceSha, priorBytes);
            } catch (IOException e) { throw new CompletionException(e); }
        });
    }

    static TowerBakedMaterialPass start(ServerLevel level, TowerVoxelMap map) {
        return new TowerBakedMaterialPass(level, map);
    }

    /** Called only after W243 successfully finishes; never blocks on preparation. */
    void tick() {
        if (closed) return;
        if (driver == null) {
            if (!prepared.isDone()) return;
            try {
                driver = new TowerDetailPass(level, prepared.join(), LEDGER, OPERATIONS_PER_TICK, false, "baked W245");
            } catch (CompletionException e) {
                DestinyGuardians.LOGGER.error("타워 baked W245 생략: 검증 실패. 기존 월드와 이력을 보존합니다", e.getCause());
                close();
                return;
            }
        }
        driver.tick();
        if (driver.isFinished()) close();
    }

    @Override public void close() {
        if (driver != null) driver.close();
        prepared.cancel(false);
        closed = true;
    }

    private static InputStream resource(String name) throws IOException {
        InputStream input = TowerBakedMaterialPass.class.getResourceAsStream(name);
        if (input == null) throw new IOException("타워 리소스가 없습니다: " + name);
        return input;
    }

    private static String sha256(InputStream input) throws IOException {
        try {
            MessageDigest digest = MessageDigest.getInstance("SHA-256");
            new DigestInputStream(input, digest).transferTo(OutputStream.nullOutputStream());
            return HexFormat.of().formatHex(digest.digest());
        } catch (NoSuchAlgorithmException e) { throw new IOException("SHA-256 unavailable", e); }
    }

    /** Entire plan is validated before creating a driver or touching saved data/world blocks. */
    static List<TowerDetailPass.Piece> decode(InputStream compressed, TowerVoxelMap map,
            String actualSourceSha, byte[] priorBytes) throws IOException {
        if (!TowerMaterialPass.SOURCE_SHA256.equals(actualSourceSha)
                || !PRIOR_SHA256.equals(sha256(new ByteArrayInputStream(priorBytes))))
            throw new IOException("타워 baked 원본/W243 실제 SHA 불일치");
        Map<Long, String> priorAt = new HashMap<>();
        for (var piece : TowerMaterialPass.decode(new ByteArrayInputStream(priorBytes), map, actualSourceSha))
            for (var edit : piece.edits()) priorAt.put(edit.pos().asLong(), edit.replacement());
        try (var gzip = new GZIPInputStream(compressed)) {
            byte[] bytes = gzip.readNBytes(MAX_JSON_BYTES + 1);
            if (bytes.length > MAX_JSON_BYTES) throw new IOException("타워 baked JSON 32MB 상한 초과");
            JsonObject root = JsonParser.parseString(new String(bytes, StandardCharsets.UTF_8)).getAsJsonObject();
            if (integer(root.get("schema")) != 1
                    || !TowerMaterialPass.SOURCE_SHA256.equals(string(root.get("sourceVoxelSHA256")))
                    || !PRIOR_SHA256.equals(string(root.get("priorMaterialSHA256"))))
                throw new IOException("타워 baked schema/원본/W243 선언 SHA 불일치");
            JsonArray paletteJson = root.getAsJsonArray("palette");
            if (paletteJson.isEmpty() || paletteJson.size() > 4096) throw new IOException("타워 baked 팔레트 크기 오류");
            List<String> palette = new ArrayList<>();
            for (var value : paletteJson) {
                String name = string(value);
                if (!name.matches("minecraft:[a-z0-9_]+(\\[[a-z0-9_=,]+\\])?"))
                    throw new IOException("바닐라 블록 상태만 허용합니다: " + name);
                BlockState block = BlockStateParser.parseForBlock(BuiltInRegistries.BLOCK, name, false).blockState();
                if (block.isAir() || !block.getFluidState().isEmpty() || block.hasBlockEntity()
                        || !Block.isShapeFullBlock(block.getCollisionShape(EmptyBlockGetter.INSTANCE, BlockPos.ZERO))
                        || !Block.isShapeFullBlock(block.getShape(EmptyBlockGetter.INSTANCE, BlockPos.ZERO)))
                    throw new IOException("온전한 full cube만 허용합니다: " + name);
                palette.add(name);
            }
            JsonArray cells = root.getAsJsonArray("cells");
            if (cells.size() > MAX_CELLS) throw new IOException("타워 baked 200000좌표 상한 초과");
            Set<Long> seen = new HashSet<>();
            Map<ChunkPos, List<TowerDetailPass.Edit>> chunks = new LinkedHashMap<>();
            for (var cell : cells) {
                JsonArray row = cell.getAsJsonArray();
                if (row.size() != 5) throw new IOException("타워 baked 좌표는 x/y/z/expected/replacement 5개여야 합니다");
                int x = integer(row.get(0)), y = integer(row.get(1)), z = integer(row.get(2));
                int expected = integer(row.get(3)), replacement = integer(row.get(4));
                if (expected < 0 || expected >= palette.size() || replacement < 0 || replacement >= palette.size()
                        || !map.manifest().bounds().contains(x, y, z))
                    throw new IOException("타워 baked 좌표/팔레트 범위 오류");
                BlockPos pos = new BlockPos(x, y, z);
                int sourceIndex = map.paletteIndexAt(x, y, z);
                if (sourceIndex < 0 || !exposed(map, pos)) throw new IOException("원본의 노출 복셀만 변경할 수 있습니다: " + pos);
                String expectedName = priorAt.getOrDefault(pos.asLong(), map.palette().get(sourceIndex));
                if (!expectedName.equals(palette.get(expected))) throw new IOException("타워 baked expected 불일치: " + pos);
                if (!seen.add(pos.asLong())) throw new IOException("중복 타워 baked 좌표: " + pos);
                chunks.computeIfAbsent(new ChunkPos(x >> 4, z >> 4), ignored -> new ArrayList<>())
                        .add(new TowerDetailPass.Edit(pos, expectedName, palette.get(replacement)));
            }
            List<TowerDetailPass.Piece> pieces = new ArrayList<>();
            chunks.forEach((chunk, edits) -> pieces.add(new TowerDetailPass.Piece("baked/w245/" + chunk.x() + "/" + chunk.z(),
                    List.copyOf(edits), List.of(), Set.of(chunk))));
            return List.copyOf(pieces);
        } catch (RuntimeException | com.mojang.brigadier.exceptions.CommandSyntaxException e) {
            throw new IOException("타워 baked 데이터 해석 실패", e);
        }
    }

    private static int integer(JsonElement value) {
        if (!value.isJsonPrimitive() || !value.getAsJsonPrimitive().isNumber()) throw new IllegalArgumentException("Expected integer");
        return value.getAsBigDecimal().intValueExact();
    }
    private static String string(JsonElement value) {
        if (!value.isJsonPrimitive() || !value.getAsJsonPrimitive().isString()) throw new IllegalArgumentException("Expected string");
        return value.getAsString();
    }
    private static boolean exposed(TowerVoxelMap map, BlockPos pos) {
        for (var direction : Direction.values()) {
            BlockPos adjacent = pos.relative(direction);
            if (map.paletteIndexAt(adjacent.getX(), adjacent.getY(), adjacent.getZ()) < 0) return true;
        }
        return false;
    }
}
