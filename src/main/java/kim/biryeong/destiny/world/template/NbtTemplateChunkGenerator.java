package kim.biryeong.destiny.world.template;

import net.minecraft.core.BlockPos;
import net.minecraft.core.SectionPos;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.WorldGenRegion;
import net.minecraft.world.level.*;
import net.minecraft.world.level.biome.*;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.chunk.ChunkAccess;
import net.minecraft.world.level.levelgen.*;
import net.minecraft.world.level.levelgen.blending.Blender;
import xyz.nucleoid.fantasy.util.TransientChunkGenerator;
import xyz.nucleoid.map_templates.MapTemplate;
import java.util.List;
import java.util.concurrent.CompletableFuture;

/** Nucleoid section-NBT generation, following steve-td's TemplateChunkGenerator pattern.
 * Templates already contain world coordinates and are shared read-only after publication.
 * No terrain placement, structures, features or naturally spawned entities run after generation.
 */
public class NbtTemplateChunkGenerator extends TransientChunkGenerator {
    private final List<MapTemplate> templates;
    public NbtTemplateChunkGenerator(MinecraftServer server, List<MapTemplate> templates) {
        this(server, templates, Biomes.THE_VOID);
    }
    /** Activity-owned atmosphere; the default remains the featureless void biome. */
    public NbtTemplateChunkGenerator(MinecraftServer server, List<MapTemplate> templates,
            net.minecraft.resources.ResourceKey<Biome> biome) {
        super(new FixedBiomeSource(server.registryAccess().getOrThrow(biome)));
        this.templates = List.copyOf(templates);
    }
    public List<MapTemplate> templates() { return templates; }

    @Override public CompletableFuture<ChunkAccess> buildTerrain(ChunkAccess chunk, Blender blender, RandomState random,
            StructureManager structures, BiomeManager biomes, WorldGenRegion region, java.util.Set<net.minecraft.core.Holder<Biome>> possibleBiomes) {
        // World generation already owns this chunk; avoid another unbounded common-pool queue.
        int cx = chunk.getPos().x(), cz = chunk.getPos().z();
        for (var template : templates) {
            var bounds = template.getBounds();
            if (cx < bounds.min().getX() >> 4 || cx > bounds.max().getX() >> 4
                    || cz < bounds.min().getZ() >> 4 || cz > bounds.max().getZ() >> 4) continue;
            int min = Math.max(chunk.getMinSectionY(), bounds.min().getY() >> 4);
            int max = Math.min(chunk.getMaxSectionY(), bounds.max().getY() >> 4);
            var pos = new BlockPos.MutableBlockPos();
            var surface = chunk.getOrCreateHeightmapUnprimed(Heightmap.Types.WORLD_SURFACE_WG);
            var floor = chunk.getOrCreateHeightmapUnprimed(Heightmap.Types.OCEAN_FLOOR_WG);
            for (int sy = min; sy <= max; sy++) {
                var source = template.getChunk(SectionPos.asLong(cx, sy, cz));
                if (source == null) continue;
                var section = chunk.getSection(chunk.getSectionIndexFromSectionY(sy));
                section.acquire();
                try {
                    for (int y=0; y<16; y++) for (int z=0; z<16; z++) for (int x=0; x<16; x++) {
                        BlockState state = source.get(x,y,z);
                        if (state.isAir()) continue;
                        int wy=(sy<<4)+y;
                        pos.set((cx<<4)+x,wy,(cz<<4)+z);
                        if (!bounds.contains(pos)) continue;
                        section.setBlockState(x,y,z,state,false);
                        surface.update(x,wy,z,state); floor.update(x,wy,z,state);
                        var blockEntity = template.getBlockEntityNbt(pos);
                        if (blockEntity != null) chunk.setBlockEntityNbt(blockEntity.copy());
                    }
                } finally { section.release(); }
            }
        }
        return CompletableFuture.completedFuture(chunk);
    }
    @Override public int getBaseHeight(int x,int z,Heightmap.Types kind,LevelHeightAccessor world,RandomState random) {
        var column = getBaseColumn(x,z,world,random);
        for(int y=world.getMaxY();y>=world.getMinY();y--)
            if(kind.isOpaque().test(column.getBlock(y))) return y+1;
        return world.getMinY();
    }
    @Override public NoiseColumn getBaseColumn(int x,int z,LevelHeightAccessor world,RandomState random) {
        BlockState[] states = new BlockState[world.getHeight()];
        java.util.Arrays.fill(states, Blocks.AIR.defaultBlockState());
        var pos = new BlockPos.MutableBlockPos(x,0,z);
        for(var template:templates) if(template.getBounds().contains(x,z)) {
            int min=Math.max(world.getMinY(),template.getBounds().min().getY());
            int max=Math.min(world.getMaxY(),template.getBounds().max().getY());
            for(int y=min;y<=max;y++) states[y-world.getMinY()]=template.getBlockState(pos.setY(y));
        }
        return new NoiseColumn(world.getMinY(),states);
    }
    @Override public void applyBiomeDecoration(WorldGenLevel level,ChunkAccess chunk,StructureManager structures) { }
    @Override public void createStructures(net.minecraft.core.RegistryAccess registries,
            net.minecraft.world.level.chunk.ChunkGeneratorStructureState placement, StructureManager structures,
            ChunkAccess chunk, net.minecraft.world.level.levelgen.structure.templatesystem.StructureTemplateManager manager,
            net.minecraft.resources.ResourceKey<Level> dimension) { }
    @Override public void createReferences(WorldGenLevel level,StructureManager structures,ChunkAccess chunk) { }
    @Override public void spawnOriginalMobs(WorldGenRegion region) { }
    @Override public int getGenDepth() { return 384; }
    @Override public int getMinY() { return -64; }
    @Override public int getSeaLevel() { return -64; }
    @Override public void addDebugScreenInfo(List<String> text,RandomState random,BlockPos pos, net.minecraft.world.level.levelgen.densityfunction.SamplerContext context) { }
}
