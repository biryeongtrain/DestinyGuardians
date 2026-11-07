package kim.biryeong.destiny.test;

import kim.biryeong.destiny.campaign.GuardianRisesInstances;
import kim.biryeong.destiny.campaign.RisingServices;
import kim.biryeong.destiny.campaign.map.RisingZones;
import kim.biryeong.destiny.campaign.map.ZoneTemplate;
import kim.biryeong.destiny.world.template.NbtTemplateChunkGenerator;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.commands.arguments.blocks.BlockStateParser;
import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.levelgen.Heightmap;
import java.util.UUID;
import java.util.concurrent.TimeUnit;

/** Real asynchronous Fantasy generation, admission, cancellation, and per-instance isolation. */
public final class RisingNbtW339GameTests {
    private static void check(GameTestHelper h, boolean condition, String why) {
        h.assertTrue(condition, Component.literal(why));
    }

    @GameTest(structure="destiny-test:floor", environment="destiny-test:w90_isolated", maxTicks=4000)
    public void generatesFourNbtZonesAndOwnsWarmupThroughAdoption(GameTestHelper h) {
        var server = h.getLevel().getServer();
        var instances = new GuardianRisesInstances(server, 2);
        var zones = RisingServices.zones().orElseThrow();
        var owner = UUID.randomUUID(); var nextOwner = UUID.randomUUID();
        var spareOwner = UUID.randomUUID();
        var first = new GuardianRisesInstances.Instance[1];
        var second = new GuardianRisesInstances.Instance[1];
        var warmup = new RisingServices.ZoneBuild[1];
        int[] index = {0};
        long deadline = System.nanoTime() + TimeUnit.SECONDS.toNanos(180);
        long[] lastPoll = {System.nanoTime()}, worldStart = {0};
        TestCleanup.register(h, () -> {
            if (warmup[0] != null) warmup[0].cancel();
            for (var instance : instances.instances()) check(h, instances.close(instance), "Fixture owns empty worlds");
        });
        h.onEachTick(() -> {
            // Headless GameTest ticks do not wait 50ms; pace only this async fixture, never production worldgen.
            long delay = lastPoll[0] + TimeUnit.MILLISECONDS.toNanos(50) - System.nanoTime();
            if (delay > 0) java.util.concurrent.locks.LockSupport.parkNanos(delay);
            lastPoll[0] = System.nanoTime();
            check(h, System.nanoTime() < deadline, "NBT warmup exceeded 180 seconds, zone=" + index[0]);
            if (first[0] == null) {
                var made = instances.prepare(spareOwner);
                if (made.isEmpty()) return;
                first[0] = made.orElseThrow();
                worldStart[0] = first[0].level().getGameTime();
            }
            if (index[0] < RisingServices.Zone.values().length) {
                var zone = RisingServices.Zone.values()[index[0]];
                if (warmup[0] == null) {
                    warmup[0] = geometryWarmup(instances, first[0], zone);
                    var owned = warmup[0]; instances.own(first[0], owned::cancel);
                    check(h, !owned.step(0), "Zero budget cannot request chunks");
                }
                if (!warmup[0].step(2_000_000)) return;
                check(h, warmup[0].progress() == 1, "Ready only after all requested chunks are full");
                verify(h, first[0], zone);
                if (index[0] == 0) {
                    check(h, first[0].level().getGameTime() > worldStart[0], "Empty Fantasy level ticks during preparation");
                    check(h, instances.adopt(first[0], spareOwner, owner), "Completed spare transfers to real owner");
                    instances.ready(first[0]); instances.running(first[0]);
                }
                warmup[0] = null; index[0]++;
                return;
            }
            // A new player's copy generates from the original template, never the first player's mutable chunks.
            if (second[0] == null) {
                second[0] = instances.prepare(nextOwner).orElseThrow();
                check(h, second[0].level() != first[0].level(), "Personal instances have separate mutable worlds");
                warmup[0] = geometryWarmup(instances, second[0], RisingServices.Zone.GATEWAY);
                var owned = warmup[0]; instances.own(second[0], owned::cancel);
                // Cancellation after requests must remain safe and permit the owner to retry in a new instance.
                owned.step(2_000_000); owned.cancel(); owned.cancel();
                check(h, !owned.step(2_000_000), "Cancelled warmup never resumes or declares readiness");
                check(h, instances.close(second[0]), "Cancelled owner can close while chunk futures are pending");
                check(h, instances.close(second[0]), "Close is idempotent");
                warmup[0] = null;
                second[0] = instances.prepare(nextOwner).orElseThrow();
                warmup[0] = geometryWarmup(instances, second[0], RisingServices.Zone.GATEWAY);
                var retry = warmup[0]; instances.own(second[0], retry::cancel);
            }
            if (!warmup[0].step(2_000_000)) return;
            var generator = (NbtTemplateChunkGenerator) second[0].level().getChunkSource().getGenerator();
            var source = generator.templates().getFirst();
            var at = RisingServices.zones().orElseThrow().markers(RisingServices.Zone.GATEWAY,
                    GuardianRisesInstances.origin(RisingServices.Zone.GATEWAY)).all().stream()
                    .filter(m -> m.id().equals("spawn.player")).findFirst().orElseThrow().pos();
            var floor = BlockPos.containing(at).below();
            var expected = source.getBlockState(floor);
            check(h, second[0].level().getBlockState(floor).equals(expected), "Second world matches original spawn floor");
            first[0].level().setBlock(floor, Blocks.GOLD_BLOCK.defaultBlockState(), 2);
            check(h, second[0].level().getBlockState(floor).equals(expected)
                    && source.getBlockState(floor).equals(expected), "Changing one instance never changes source or another copy");
            instances.ready(second[0]);
            check(h, instances.close(first[0]) && instances.close(second[0]), "Both worlds cleanly release owned warmups");
            check(h, instances.instances().isEmpty(), "No retained instance owners");
            h.succeed();
        });
    }

    /** TEST ONLY: exhaustive geometry sampling intentionally warms each map; production begin() never does. */
    private static RisingServices.ZoneBuild geometryWarmup(GuardianRisesInstances instances,
            GuardianRisesInstances.Instance instance, RisingServices.Zone zone) {
        instances.tickForArrival(instance, true);
        return new kim.biryeong.destiny.world.template.TemplateChunkWarmup(instance.level(), RisingZones.bounds(zone), 0);
    }

    private static void verify(GameTestHelper h, GuardianRisesInstances.Instance instance, RisingServices.Zone zone) {
        var level = instance.level();
        check(h, level.getChunkSource().getGenerator() instanceof NbtTemplateChunkGenerator, "Production NBT generator installed");
        var generator = (NbtTemplateChunkGenerator) level.getChunkSource().getGenerator();
        var template = generator.templates().get(zone.ordinal());
        var grid = ZoneTemplate.get(zone);
        var origin = GuardianRisesInstances.origin(zone);
        check(h, template.getBounds().min().equals(origin), "NBT world offset preserved");
        var palette = new BlockState[grid.palette().size()];
        try {
            for (int i=0;i<palette.length;i++) palette[i] = BlockStateParser.parseForBlock(
                    BuiltInRegistries.BLOCK, grid.palette().get(i), false).blockState();
        } catch (Exception e) { throw new IllegalStateException(e); }
        // Sample vertical columns across the map, including source air/solid transitions and chunk boundaries.
        var pos = new BlockPos.MutableBlockPos();
        int samples=0;
        for (int z=0;z<grid.sizeZ();z+=15) for (int x=0;x<grid.sizeX();x+=15) {
            for (int y=0;y<grid.sizeY();y++) {
                pos.set(origin.getX()+x, origin.getY()+y, origin.getZ()+z);
                var expected=palette[grid.paletteIndexAt(x,y,z)];
                check(h, template.getBlockState(pos).equals(expected), "NBT matches authoring voxel at " + pos);
                check(h, level.getBlockState(pos).equals(expected), "Generated chunk matches authoring voxel at " + pos);
                samples++;
            }
            int top=origin.getY()-1;
            for(int y=grid.sizeY()-1;y>=0;y--)
                if(!palette[grid.paletteIndexAt(x,y,z)].isAir()){top=origin.getY()+y;break;}
            check(h,level.getHeight(Heightmap.Types.WORLD_SURFACE,origin.getX()+x,origin.getZ()+z)==top+1
                    || top<origin.getY(),"Generated heightmap matches template column");
        }
        kim.biryeong.destiny.DestinyGuardians.LOGGER.info("[RisingNBT QA] {} checked {} vertical voxel samples",zone,samples);
    }
}
