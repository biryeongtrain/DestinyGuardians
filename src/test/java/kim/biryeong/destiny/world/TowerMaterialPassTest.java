package kim.biryeong.destiny.world;

import com.mojang.serialization.JsonOps;
import net.minecraft.SharedConstants;
import net.minecraft.commands.arguments.blocks.BlockStateParser;
import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.server.Bootstrap;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;

import java.io.*;
import java.nio.charset.StandardCharsets;
import java.util.*;
import java.util.zip.GZIPOutputStream;

import static org.junit.jupiter.api.Assertions.*;

class TowerMaterialPassTest {
    @BeforeAll static void bootstrap() {
        SharedConstants.tryDetectVersion();
        Bootstrap.bootStrap();
    }
    private static BlockState parse(String name) {
        try { return BlockStateParser.parseForBlock(BuiltInRegistries.BLOCK, name, false).blockState(); }
        catch (com.mojang.brigadier.exceptions.CommandSyntaxException e) { throw new IllegalArgumentException(name, e); }
    }
    private static byte[] compressed(String palette, String cells, String sha) throws IOException {
        String json = "{\"schema\":1,\"sourceVoxelSHA256\":\"" + sha
                + "\",\"palette\":[" + palette + "],\"cells\":[" + cells + "]}";
        var bytes = new ByteArrayOutputStream();
        try (var gzip = new GZIPOutputStream(bytes)) { gzip.write(json.getBytes(StandardCharsets.UTF_8)); }
        return bytes.toByteArray();
    }
    private static List<TowerDetailPass.Piece> decode(TowerVoxelMap map, String palette, String cells) throws IOException {
        return TowerMaterialPass.decode(new ByteArrayInputStream(compressed(palette, cells, TowerMaterialPass.SOURCE_SHA256)),
                map, TowerMaterialPass.SOURCE_SHA256);
    }

    @Test void rejectsInvalidSourcePaletteGeometryDuplicatesAndOversizeBeforeAnyWrite() throws Exception {
        var map = TowerVoxelMap.loadBundled();
        String white = "\"minecraft:white_concrete\"", cell = "[70,74,-20,0]";
        assertEquals(1, decode(map, white, cell).getFirst().edits().size());
        assertThrows(IOException.class, () -> TowerMaterialPass.decode(new ByteArrayInputStream(
                compressed(white, cell, "bad")), map, TowerMaterialPass.SOURCE_SHA256));
        assertThrows(IOException.class, () -> TowerMaterialPass.decode(new ByteArrayInputStream(
                compressed(white, cell, TowerMaterialPass.SOURCE_SHA256)), map, "bad"));
        assertThrows(IOException.class, () -> decode(map, "\"minecraft:stone_slab\"", cell));
        assertThrows(IOException.class, () -> decode(map, "\"minecraft:chest\"", cell));
        assertThrows(IOException.class, () -> decode(map, white, "[70,75,-20,0]")); // original air
        assertThrows(IOException.class, () -> decode(map, white, "[70,74,-20,1]"));
        assertThrows(IOException.class, () -> decode(map, white, "[70.5,74,-20,0]"));
        assertThrows(IOException.class, () -> decode(map, white, cell + "," + cell));
        assertThrows(IOException.class, () -> decode(map, white, String.join(",", Collections.nCopies(100_001, cell))));
        BlockPos[] interior = {null};
        for (int cx = 3; cx <= 5 && interior[0] == null; cx++) for (int cz = -4; cz <= -1 && interior[0] == null; cz++) {
            map.forChunk(cx, cz, (x, y, z, index) -> {
                if (interior[0] != null || !map.palette().get(index).equals("minecraft:smooth_stone")) return;
                BlockPos pos = new BlockPos(x, y, z);
                if (Arrays.stream(net.minecraft.core.Direction.values()).allMatch(d -> {
                    var a = pos.relative(d); return map.paletteIndexAt(a.getX(), a.getY(), a.getZ()) >= 0;
                })) interior[0] = pos;
            });
        }
        assertNotNull(interior[0], "Bundled map has a buried smooth-stone sample");
        BlockPos buried = interior[0];
        assertThrows(IOException.class, () -> decode(map, white, "[" + buried.getX() + "," + buried.getY() + "," + buried.getZ() + ",0]"));
        // Validate the exact master-owned shipped gzip as well as the small rejection fixtures.
        try (var shipped = TowerMaterialPassTest.class.getResourceAsStream(TowerMaterialPass.RESOURCE);
             var source = TowerMaterialPassTest.class.getResourceAsStream(TowerVoxelMap.VOXEL_RESOURCE)) {
            assertNotNull(shipped);
            assertNotNull(source);
            String sha = HexFormat.of().formatHex(java.security.MessageDigest.getInstance("SHA-256").digest(source.readAllBytes()));
            var actual = TowerMaterialPass.decode(shipped, map, sha);
            int count = actual.stream().mapToInt(p -> p.edits().size()).sum();
            assertTrue(count > 0 && count <= TowerMaterialPass.MAX_CELLS);
            System.out.println("TOWER_MATERIAL_SHIPPED_CELLS=" + count + " chunks=" + actual.size());
        }
    }

    @Test void materialLedgerPreservesPropsEditsAndLaterRevertsWithoutChangingDetailsHistory() throws Exception {
        var map = TowerVoxelMap.loadBundled();
        var pieces = decode(map, "\"minecraft:white_concrete\"", "[70,74,-20,0],[71,74,-20,0],[72,74,-20,0]");
        var edits = pieces.stream().flatMap(p -> p.edits().stream()).toList();
        var detailsLedger = new TowerDetailPass.Ledger();
        TowerDetailPass.initialPlan(map).forEach(p -> p.edits().forEach(e -> detailsLedger.consider(e.pos())));
        String detailsBefore = TowerDetailPass.Ledger.CODEC.encodeStart(JsonOps.INSTANCE, detailsLedger).getOrThrow().toString();
        var materials = new TowerDetailPass.Ledger();
        Map<BlockPos, BlockState> world = new HashMap<>();
        world.put(edits.get(0).pos(), parse("minecraft:polished_andesite")); // existing floor inlay
        world.put(edits.get(1).pos(), Blocks.GOLD_BLOCK.defaultBlockState()); // administrator edit
        world.put(edits.get(2).pos(), parse("minecraft:smooth_stone"));
        int changes = 0;
        for (var e : edits) if (TowerDetailPass.apply(e, materials, () -> true, world::get,
                TowerMaterialPassTest::parse, (pos, state) -> { world.put(pos, state); return true; })) changes++;
        assertEquals(1, changes);
        assertEquals(parse("minecraft:polished_andesite"), world.get(edits.get(0).pos()));
        assertEquals(Blocks.GOLD_BLOCK.defaultBlockState(), world.get(edits.get(1).pos()));
        assertEquals(parse("minecraft:white_concrete"), world.get(edits.get(2).pos()));
        var reopened = TowerDetailPass.Ledger.CODEC.parse(JsonOps.INSTANCE,
                TowerDetailPass.Ledger.CODEC.encodeStart(JsonOps.INSTANCE, materials).getOrThrow()).getOrThrow();
        edits.forEach(e -> world.put(e.pos(), parse("minecraft:smooth_stone"))); // user deliberately reverts
        for (var e : edits) assertFalse(TowerDetailPass.apply(e, reopened, () -> true, world::get,
                TowerMaterialPassTest::parse, (pos, state) -> fail("A consumed material coordinate must not be reapplied")));
        assertEquals(detailsBefore, TowerDetailPass.Ledger.CODEC.encodeStart(JsonOps.INSTANCE, detailsLedger).getOrThrow().toString());
        assertEquals(128, TowerMaterialPass.OPERATIONS_PER_TICK);
        assertEquals(100_000, TowerMaterialPass.MAX_CELLS);
    }
}
