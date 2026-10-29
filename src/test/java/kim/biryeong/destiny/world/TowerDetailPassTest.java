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

import java.util.*;
import java.util.function.Function;

import static org.junit.jupiter.api.Assertions.*;

class TowerDetailPassTest {
    @BeforeAll static void bootstrap() {
        SharedConstants.tryDetectVersion();
        Bootstrap.bootStrap();
    }
    private static BlockState parse(String value) {
        try { return BlockStateParser.parseForBlock(BuiltInRegistries.BLOCK, value, false).blockState(); }
        catch (com.mojang.brigadier.exceptions.CommandSyntaxException e) { throw new IllegalArgumentException(value, e); }
    }

    @Test void measuredPlanKeepsSourceGeometrySpawnAndFiveDistinctSpaces() throws Exception {
        TowerVoxelMap map = TowerVoxelMap.loadBundled();
        var plan = TowerDetailPass.plan(map);
        Map<BlockPos, String> initial = new HashMap<>();
        TowerDetailPass.initialPlan(map).forEach(p -> p.edits().forEach(e -> initial.put(e.pos(), e.replacement())));
        Map<String, Integer> counts = new TreeMap<>();
        Set<BlockPos> touched = new HashSet<>();
        var spawn = map.manifest().spawn();
        assertEquals(1_151_116, map.blockCount());
        for (var piece : plan) {
            counts.merge(piece.id().split("/")[0], piece.edits().size(), Integer::sum);
            for (var support : piece.supports()) {
                int index = map.paletteIndexAt(support.pos().getX(), support.pos().getY(), support.pos().getZ());
                if (index >= 0) assertEquals(map.palette().get(index), support.expected());
                else {
                    assertTrue(piece.id().contains("crown-"), "Only appended crowns may read an old trunk");
                    assertEquals(initial.get(support.pos()), support.expected());
                }
            }
            for (var e : piece.edits()) {
                assertTrue(touched.add(e.pos()), "Overlapping props: " + e.pos());
                assertTrue(map.manifest().bounds().contains(e.pos().getX(), e.pos().getY(), e.pos().getZ()));
                int index = map.paletteIndexAt(e.pos().getX(), e.pos().getY(), e.pos().getZ());
                assertEquals(index < 0 ? "minecraft:air" : map.palette().get(index), e.expected());
                assertTrue(e.expected().equals("minecraft:air") || e.expected().equals("minecraft:smooth_stone"));
                if (!e.expected().equals("minecraft:air")) {
                    assertEquals(-1, map.paletteIndexAt(e.pos().getX(), e.pos().getY() + 1, e.pos().getZ()));
                    assertEquals(-1, map.paletteIndexAt(e.pos().getX(), e.pos().getY() + 2, e.pos().getZ()));
                }
                assertTrue(Math.abs(e.pos().getX() - Math.floor(spawn.x())) > 8
                        || Math.abs(e.pos().getZ() - Math.floor(spawn.z())) > 8, "Spawn/rescue neighborhood");
                assertFalse(parse(e.replacement()).isAir());
            }
        }
        System.out.println("TOWER_DETAIL_COUNTS=" + counts + " pieces=" + plan.size() + " cells=" + touched.size());
        System.out.println("TOWER_DETAIL_OBJECTS=" + plan.stream().map(TowerDetailPass.Piece::id)
                .filter(s -> !s.contains("inlay/") && !s.contains("apron-")).toList());
        assertEquals(Set.of("arrival", "market", "garden", "overlook", "service"), counts.keySet());
        for (var e : counts.entrySet()) assertTrue(e.getValue() >= 35, e.getKey() + " needs substantial furnishing");
        assertTrue(counts.values().stream().mapToInt(Integer::intValue).sum() < 4_000);
        assertTrue(TowerDetailPass.OPERATIONS_PER_TICK <= 48);
    }

    @Test void arrivalRevisionAppendsOnlyNewAirAfterSaved907WithoutTouchingOtherZones() throws Exception {
        var map = TowerVoxelMap.loadBundled();
        var initial = TowerDetailPass.initialPlan(map);
        var revised = TowerDetailPass.plan(map);
        assertEquals(initial, revised.subList(0, initial.size()), "Original pieces must remain byte-for-byte equivalent");
        var oldCells = initial.stream().flatMap(p -> p.edits().stream()).toList();
        assertEquals(907, oldCells.size());
        var ledger = new TowerDetailPass.Ledger();
        Map<BlockPos, BlockState> world = new HashMap<>();
        oldCells.forEach(e -> { ledger.consider(e.pos()); world.put(e.pos(), parse(e.replacement())); });
        var encoded = TowerDetailPass.Ledger.CODEC.encodeStart(JsonOps.INSTANCE, ledger).getOrThrow();
        var reopened = TowerDetailPass.Ledger.CODEC.parse(JsonOps.INSTANCE, encoded).getOrThrow();
        var additions = revised.subList(initial.size(), revised.size());
        assertEquals(2, additions.size(), "Both arrival trees need a measured extension");
        int changed = 0;
        for (var piece : additions) {
            assertTrue(piece.id().startsWith("arrival/crown-"));
            for (var edit : piece.edits()) {
                assertEquals("minecraft:air", edit.expected());
                assertTrue(edit.pos().getY() >= 78, "No new branches at player height");
                assertFalse(reopened.contains(edit.pos()));
                if (TowerDetailPass.apply(edit, reopened,
                        () -> piece.supports().stream().allMatch(s -> world.getOrDefault(s.pos(),
                                original(map, s.pos())).equals(parse(s.expected()))),
                        pos -> world.getOrDefault(pos, original(map, pos)), TowerDetailPassTest::parse,
                        (pos, block) -> { world.put(pos, block); return true; })) changed++;
            }
        }
        int expected = additions.stream().mapToInt(p -> p.edits().size()).sum();
        assertTrue(expected >= 40 && expected <= 100, "Keep the revision modest");
        assertEquals(expected, changed, "Saved v1 ledger must allow every new-air addition");
        for (var e : oldCells) assertEquals(parse(e.replacement()), world.get(e.pos()));
        System.out.println("TOWER_ARRIVAL_APPEND=" + changed + " original907=unchanged");
    }

    private static BlockState original(TowerVoxelMap map, BlockPos pos) {
        int index = map.paletteIndexAt(pos.getX(), pos.getY(), pos.getZ());
        return index < 0 ? Blocks.AIR.defaultBlockState() : parse(map.palette().get(index));
    }

    @Test void conditionalWritesPreserveEditsAndSaveRemovalHistory() {
        BlockPos p = new BlockPos(78, 75, -32);
        var edit = new TowerDetailPass.Edit(p, "minecraft:air", "minecraft:white_concrete");
        var ledger = new TowerDetailPass.Ledger();
        Map<BlockPos, BlockState> world = new HashMap<>();
        Function<BlockPos, BlockState> read = pos -> world.getOrDefault(pos, Blocks.AIR.defaultBlockState());
        java.util.function.BiPredicate<BlockPos, BlockState> write = (pos, state) -> { world.put(pos, state); return true; };
        assertTrue(TowerDetailPass.apply(edit, ledger, () -> true, read, TowerDetailPassTest::parse, write));
        assertEquals(parse("minecraft:white_concrete"), world.get(p));
        world.remove(p); // Administrator intentionally removes the newly placed block.
        var encoded = TowerDetailPass.Ledger.CODEC.encodeStart(JsonOps.INSTANCE, ledger).getOrThrow();
        var reopened = TowerDetailPass.Ledger.CODEC.parse(JsonOps.INSTANCE, encoded).getOrThrow();
        assertFalse(TowerDetailPass.apply(edit, reopened, () -> true, read, TowerDetailPassTest::parse, write));
        assertTrue(read.apply(p).isAir(), "Normal restart must not repair a player's removal");
        // An edited block and a removed support are consumed without writes as well.
        var fresh = new TowerDetailPass.Ledger();
        world.put(p, Blocks.GOLD_BLOCK.defaultBlockState());
        assertFalse(TowerDetailPass.apply(edit, fresh, () -> true, read, TowerDetailPassTest::parse, write));
        assertEquals(Blocks.GOLD_BLOCK.defaultBlockState(), world.get(p));
        world.remove(p);
        assertFalse(TowerDetailPass.apply(edit, new TowerDetailPass.Ledger(), () -> false, read, TowerDetailPassTest::parse, write));
        assertTrue(read.apply(p).isAir());
        assertFalse(TowerDetailPass.apply(edit, fresh, () -> true, read, TowerDetailPassTest::parse, write));
    }
}
