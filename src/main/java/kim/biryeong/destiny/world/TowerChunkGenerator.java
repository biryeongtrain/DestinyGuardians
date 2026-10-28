package kim.biryeong.destiny.world;

import com.mojang.serialization.MapCodec;
import com.mojang.serialization.codecs.RecordCodecBuilder;
import net.minecraft.commands.arguments.blocks.BlockStateParser;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Holder;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.server.level.WorldGenRegion;
import net.minecraft.world.level.LevelHeightAccessor;
import net.minecraft.world.level.NoiseColumn;
import net.minecraft.world.level.StructureManager;
import net.minecraft.world.level.biome.Biome;
import net.minecraft.world.level.biome.BiomeManager;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.chunk.ChunkAccess;
import net.minecraft.world.level.chunk.ChunkGenerator;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.level.levelgen.RandomState;
import net.minecraft.world.level.levelgen.blending.Blender;
import xyz.nucleoid.fantasy.util.VoidChunkGenerator;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.util.Arrays;
import java.util.EnumSet;
import java.util.Set;
import java.util.concurrent.CompletableFuture;

/** Finite sparse map over Fantasy's structure/feature/mob-free void generator. */
public final class TowerChunkGenerator extends VoidChunkGenerator {
    public static final MapCodec<TowerChunkGenerator> CODEC = RecordCodecBuilder.mapCodec(instance -> instance.group(
            Biome.CODEC.fieldOf("biome").forGetter(TowerChunkGenerator::getBiome)
    ).apply(instance, biome -> new TowerChunkGenerator(biome, bundledMap())));
    private final TowerVoxelMap map;
    private final BlockState[] palette;

    public TowerChunkGenerator(Holder<Biome> biome, TowerVoxelMap map) {
        super(biome);
        this.map = map;
        this.palette = new BlockState[map.palette().size()];
        for (int i = 0; i < palette.length; i++) {
            try {
                palette[i] = BlockStateParser.parseForBlock(BuiltInRegistries.BLOCK, map.palette().get(i), false).blockState();
            } catch (com.mojang.brigadier.exceptions.CommandSyntaxException e) {
                throw new IllegalArgumentException("Invalid tower block state: " + map.palette().get(i), e);
            }
        }
    }

    public static TowerVoxelMap bundledMap() { return Bundled.MAP; }
    private static final class Bundled {
        static final TowerVoxelMap MAP = load();
        private static TowerVoxelMap load() {
            try { return TowerVoxelMap.loadBundled(); }
            catch (IOException e) { throw new UncheckedIOException("타워 맵을 읽을 수 없습니다.", e); }
        }
    }
    public TowerVoxelMap map() { return map; }
    public BlockState blockAt(int x, int y, int z) {
        int index = map.paletteIndexAt(x, y, z);
        return index < 0 ? Blocks.AIR.defaultBlockState() : palette[index];
    }
    @Override protected MapCodec<? extends ChunkGenerator> codec() { return CODEC; }
    @Override public int getMinY() { return TowerVoxelMap.MIN_Y; }
    @Override public int getGenDepth() { return TowerVoxelMap.HEIGHT; }
    @Override public int getSeaLevel() { return TowerVoxelMap.MIN_Y; }

    @Override
    public CompletableFuture<ChunkAccess> buildTerrain(ChunkAccess chunk, Blender blender, RandomState randomState,
            StructureManager structures, BiomeManager biomes, WorldGenRegion carverRegion, Set<Holder<Biome>> possibleBiomes) {
        BlockPos.MutableBlockPos pos = new BlockPos.MutableBlockPos();
        map.forChunk(chunk.getPos().x(), chunk.getPos().z(), (x, y, z, index) ->
                chunk.setBlockState(pos.set(x, y, z), palette[index]));
        // No neighbor updates, shell filling, terrain noise, or source GLB loading.
        Heightmap.primeHeightmaps(chunk, EnumSet.allOf(Heightmap.Types.class));
        return CompletableFuture.completedFuture(chunk);
    }

    @Override
    public int getBaseHeight(int x, int z, Heightmap.Types type, LevelHeightAccessor level, RandomState randomState) {
        int top = Math.min(map.manifest().bounds().maxY(), level.getMinY() + level.getHeight() - 1);
        int bottom = Math.max(map.manifest().bounds().minY(), level.getMinY());
        for (int y = top; y >= bottom; y--) if (type.isOpaque().test(blockAt(x, y, z))) return y + 1;
        return level.getMinY();
    }

    @Override
    public NoiseColumn getBaseColumn(int x, int z, LevelHeightAccessor level, RandomState randomState) {
        BlockState[] states = new BlockState[level.getHeight()];
        Arrays.fill(states, Blocks.AIR.defaultBlockState());
        for (int i = 0; i < states.length; i++) states[i] = blockAt(x, level.getMinY() + i, z);
        return new NoiseColumn(level.getMinY(), states);
    }
}
