package kim.biryeong.destiny.test;

import kim.biryeong.destiny.strike.devils.*;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.commands.arguments.blocks.BlockStateParser;
import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.levelgen.Heightmap;
import java.util.List;
import java.util.UUID;

public final class DevilsNbtGameTests {
    private static void check(GameTestHelper h, boolean condition, String text) {
        h.assertTrue(condition, Component.literal(text));
    }
    @GameTest(structure="destiny-test:floor", maxTicks=3000, environment="destiny-test:w90_isolated")
    public void nbtGeneratesAllFourMapsWithOriginalBlocksAndWorldOffsets(GameTestHelper h) {
        var server=h.getLevel().getServer();
        var preload=DevilsMaps.preloadAsync(server);
        var instances=new DevilsInstances(server,1);
        var instance=new DevilsInstances.Instance[1];
        var build=new DevilsWorldBuild[1];
        var stations=new DevilsSupplyStations[1];
        int[] zoneIndex={0};
        var admissionFailures = new java.util.ArrayList<String>();
        // GameTestServer.waitUntilNextTick only runs queued tasks: 1800 test ticks are NOT 90 seconds.
        // Pace this async integration fixture, without sleeping/patching the production builder or ticking worlds manually.
        long deadline=System.nanoTime()+java.util.concurrent.TimeUnit.SECONDS.toNanos(120);
        long[] nextPoll={System.nanoTime()};
        long[] preparedGameTime={Long.MIN_VALUE};
        TestCleanup.register(h,()->{
            if(stations[0]!=null)stations[0].close();
            if(build[0]!=null)build[0].close();
            if(instance[0]!=null)instances.close(instance[0]);
        });
        h.onEachTick(()->{
            if (zoneIndex[0]>=DevilsPlan.Zone.values().length) return;
            if (!preload.isDone() || build[0]==null || build[0].state()==DevilsWorldBuild.State.BUILDING) {
                long remaining=nextPoll[0]-System.nanoTime();
                while (remaining>0) {
                    java.util.concurrent.locks.LockSupport.parkNanos(remaining);
                    check(h,!Thread.currentThread().isInterrupted(),"Async NBT fixture interrupted");
                    remaining=nextPoll[0]-System.nanoTime();
                }
                nextPoll[0]=System.nanoTime()+java.util.concurrent.TimeUnit.MILLISECONDS.toNanos(50);
            }
            check(h,System.nanoTime()<deadline,"Async NBT fixture exceeded 120 seconds; preload="+preload.isDone()
                    +", build="+(build[0]==null?"not created":build[0].state()+" progress="+build[0].progress())
                    +", worldTicks="+(instance[0]==null?"not created":instance[0].level().getGameTime()-preparedGameTime[0]));
            if(!preload.isDone())return;
            preload.join();
            if(instance[0]==null) {
                instance[0]=instances.prepare(List.of(UUID.randomUUID())).orElseThrow();
                build[0]=new DevilsWorldBuild(instance[0].level());
                preparedGameTime[0]=instance[0].level().getGameTime();
            }
            build[0].tick(2_000_000);
            check(h,build[0].state()!=DevilsWorldBuild.State.FAILED,"Chunk generation must not fail: "+build[0].failure());
            if(build[0].state()!=DevilsWorldBuild.State.READY)return;
            // This must progress through the real Fantasy/server lifecycle. Never manually force chunk loads to hide a deadlock.
            check(h,instance[0].level().getGameTime()>preparedGameTime[0],"Fantasy world must actually tick during warmup");
            if(stations[0]==null){
                stations[0]=new DevilsSupplyStations(instance[0].level());
                check(h,stations[0].prepare(),"All four zones have safe supply station pads");
                check(h,stations[0].prepare(),"Supply preparation is idempotent");
                var displays=instance[0].level().getEntitiesOfClass(net.minecraft.world.entity.Display.BlockDisplay.class,
                        new net.minecraft.world.phys.AABB(0,-64,0,2500,320,1000));
                check(h,displays.size()==12,"Exactly three case parts per zone, no duplicate entities");
            }
            if(zoneIndex[0]>=DevilsPlan.Zone.values().length)return;
            var zone=DevilsPlan.Zone.values()[zoneIndex[0]++];
            var grid=DevilsMaps.template(zone);
            var nbt=DevilsMaps.nbt(zone);
            var level=instance[0].level();
            kim.biryeong.destiny.strike.devils.DevilsSkiffSurvey.inspect(h,level,zone);
            admissionFailures.addAll(verifyZonePackAdmission(h, level, zone, false));
            if (zone == DevilsPlan.Zone.RF) admissionFailures.addAll(verifyZonePackAdmission(h, level, zone, true));
            if (zone == DevilsPlan.Zone.BL) {
                var cohort = new java.util.ArrayList<DevilsPlan.Slot>(List.of(DevilsPlan.walker(), DevilsPlan.brig(1), DevilsPlan.brig(2)));
                DevilsPlan.packs(zone, "entry").forEach(pack -> cohort.addAll(pack.slots()));
                admissionFailures.addAll(verifyAdmission(h, level, zone, List.of(cohort), "BL-boss-entry "));
            }
            if (zone == DevilsPlan.Zone.SP) {
                verifyTransientShieldBlocking(h, level);
                verifySepiksWarpPads(h, level);
                var cohorts = new java.util.ArrayList<List<DevilsPlan.Slot>>();
                var guards = new java.util.ArrayList<DevilsPlan.Slot>(List.of(DevilsPlan.sepiks()));
                DevilsPlan.packs(zone, "guard").forEach(pack -> guards.addAll(pack.slots()));
                cohorts.add(guards);
                for (int shield = 1; shield <= 2; shield++) {
                    var cohort = new java.util.ArrayList<DevilsPlan.Slot>(List.of(DevilsPlan.sepiks()));
                    for (int i = 1; i <= 3; i++) cohort.add(DevilsPlan.servitor(shield, i));
                    cohort.addAll(DevilsPlan.pack("SP-shield-" + shield).slots());
                    cohorts.add(cohort);
                }
                for (String anchor : List.of("SP.IN.0", "SP.IN.1", "SP.IN.2"))
                    admissionFailures.addAll(verifyAdmission(h, level, zone, cohorts, "SP-boss-cohort " + anchor + " ", anchor));
                admissionFailures.addAll(verifyAdmission(h, level, zone, cohorts.subList(1, 3),
                        "SP-shield-central ", "SP.C.ground"));
            }
            check(h,level.getChunkSource().getGenerator() instanceof DevilsTemplateGenerator,"Instance uses NBT chunk generator");
            var palette=new BlockState[grid.palette().size()];
            try {
                for(int i=0;i<palette.length;i++)palette[i]=BlockStateParser.parseForBlock(BuiltInRegistries.BLOCK,grid.palette().get(i),false).blockState();
            }catch(Exception e){throw new IllegalStateException(e);}
            var origin=DevilsWorldBuild.origin(zone);var pos=new BlockPos.MutableBlockPos();
            long count=0;
            for(int y=0;y<grid.sizeY();y++)for(int z=0;z<grid.sizeZ();z++)for(int x=0;x<grid.sizeX();x++) {
                pos.set(origin.getX()+x,origin.getY()+y,origin.getZ()+z);
                var expected=palette[grid.paletteIndexAt(x,y,z)];
                if(nbt.getBlockState(pos)!=expected)check(h,false,"NBT differs at "+zone+" "+pos);
                if(level.getBlockState(pos)!=expected)check(h,false,"Generated world differs at "+zone+" "+pos);
                if(!expected.isAir())count++;
            }
            check(h,count==grid.blockCount(),"Non-air block count matches authoring grid");
            for(int z=0;z<grid.sizeZ();z+=7)for(int x=0;x<grid.sizeX();x+=7) {
                int wx=origin.getX()+x,wz=origin.getZ()+z;
                int expected=level.getMinY();
                for(int y=grid.sizeY()-1;y>=0;y--) if(!palette[grid.paletteIndexAt(x,y,z)].isAir()) {expected=origin.getY()+y+1;break;}
                int actual=level.getChunkSource().getGenerator().getBaseHeight(wx,wz,Heightmap.Types.WORLD_SURFACE_WG,level,level.getChunkSource().randomState());
                check(h,actual==expected,"World-coordinate base height matches template");
            }
            if(zoneIndex[0]==DevilsPlan.Zone.values().length) {
                check(h, admissionFailures.isEmpty(), "All-zone admission failures: " + admissionFailures);
                h.succeed();
            }
        });
    }

    private static java.util.List<String> verifyZonePackAdmission(GameTestHelper h, net.minecraft.server.level.ServerLevel level, DevilsPlan.Zone zone, boolean entryCohort) {
        var packs = DevilsPlan.packs().stream().filter(p -> p.zone() == zone && (!entryCohort || p.phase().equals("entry"))).toList();
        List<List<DevilsPlan.Slot>> cohorts = entryCohort
                ? List.of(packs.stream().flatMap(p -> p.slots().stream()).toList())
                : packs.stream().map(DevilsPlan.Pack::slots).toList();
        return verifyAdmission(h, level, zone, cohorts, entryCohort ? "entry-cohort " : "");
    }

    /** Each cohort shares reservations; separate encounter phases release their previous footprint. */
    private static java.util.List<String> verifyAdmission(GameTestHelper h, net.minecraft.server.level.ServerLevel level,
            DevilsPlan.Zone zone, List<List<DevilsPlan.Slot>> cohorts, String label) {
        return verifyAdmission(h, level, zone, cohorts, label, zone.name() + ".IN.0");
    }

    private static java.util.List<String> verifyAdmission(GameTestHelper h, net.minecraft.server.level.ServerLevel level,
            DevilsPlan.Zone zone, List<List<DevilsPlan.Slot>> cohorts, String label, String playerAnchor) {
        var player = TestPlayers.create(h, new net.minecraft.world.phys.Vec3(2, 1, 2), 0, 0);
        var entry = DevilsMaps.anchor(zone, playerAnchor, DevilsWorldBuild.origin(zone)).pos();
        try {
            player.teleportTo(level, entry.x, entry.y, entry.z, java.util.Set.of(), 0, 0, true);
            player.setGameMode(net.minecraft.world.level.GameType.SURVIVAL);
            var rejected = new java.util.ArrayList<String>();
            var reservations = new java.util.ArrayList<net.minecraft.world.phys.AABB>();
            for (var cohort : cohorts) {
            reservations.clear();
            for (var slot : cohort) {
                // The boss already exists before a Guardian enters the central damage lane.
                // Admit it from arrival, retain its footprint, then move the test Guardian for the shield adds.
                if (slot.kind() == DevilsPlan.Kind.SEPIKS && playerAnchor.equals("SP.C.ground")) {
                    var arrival = DevilsMaps.anchor(zone, "SP.IN.0", DevilsWorldBuild.origin(zone)).pos();
                    player.teleportTo(level, arrival.x, arrival.y, arrival.z, java.util.Set.of(), 0, 0, true);
                }
                var type = BuiltInRegistries.ENTITY_TYPE.getValue(net.minecraft.resources.Identifier.fromNamespaceAndPath(
                        "destiny", "devils_" + slot.kind().name().toLowerCase(java.util.Locale.ROOT)));
                var probe = (net.minecraft.world.entity.Mob) type.create(level, net.minecraft.world.entity.EntitySpawnReason.COMMAND);
                check(h, probe != null, "Registered mob creates admission probe");
                var failures = new java.util.ArrayList<String>();
                int candidates = DevilsMaps.candidates(zone, slot.anchor(), DevilsWorldBuild.origin(zone)).size();
                java.util.Optional<DevilsSpatial.Point> at = java.util.Optional.empty();
                // Mirror production's three completed search failures. Budget yields are not failures.
                var search = new DevilsSpatial.Search();
                for (int attempt = 0; attempt < 3 && at.isEmpty(); attempt++) {
                    var stableSlot = new DevilsPlan.Slot(slot.id(), zone, slot.packId(), slot.kind(), slot.anchor(),
                            Math.floorMod(slot.index() + attempt - (int) (level.getGameTime() / 40), Math.max(1, candidates)));
                    int slices = 0;
                    do {
                        check(h, ++slices <= 250, "Bounded spatial search must finish: " + slot.id());
                        at = DevilsSpatial.spawn(level, stableSlot, DevilsWorldBuild.origin(zone), probe,
                                List.of(player), reservations, search, failures::add);
                    } while (at.isEmpty() && search.pending());
                }
                if (at.isEmpty()) {
                    rejected.add(label + slot.id() + " " + slot.kind() + ": " + failures);
                }
                else reservations.add(DevilsSpatial.bodyAt(probe, at.orElseThrow().pos()));
                probe.discard();
                if (slot.kind() == DevilsPlan.Kind.SEPIKS && playerAnchor.equals("SP.C.ground"))
                    player.teleportTo(level, entry.x, entry.y, entry.z, java.util.Set.of(), 0, 0, true);
            }
            }
            return rejected;
        } finally {
            player.teleportTo(h.getLevel(), h.absolutePos(new BlockPos(2,1,2)).getX(), h.absolutePos(new BlockPos(2,1,2)).getY(),
                    h.absolutePos(new BlockPos(2,1,2)).getZ(), java.util.Set.of(), 0, 0, true);
            TestPlayers.remove(player);
        }
    }
    private static void verifyTransientShieldBlocking(GameTestHelper h, net.minecraft.server.level.ServerLevel level) {
        var zone = DevilsPlan.Zone.SP; var origin = DevilsWorldBuild.origin(zone);
        var slot = DevilsPlan.servitor(1, 1);
        var player = TestPlayers.create(h, new net.minecraft.world.phys.Vec3(2,1,2),0,0);
        var type = BuiltInRegistries.ENTITY_TYPE.getValue(net.minecraft.resources.Identifier.fromNamespaceAndPath("destiny", "devils_servitor"));
        var probe = (net.minecraft.world.entity.Mob) type.create(level, net.minecraft.world.entity.EntitySpawnReason.COMMAND);
        var oldBlocks = new java.util.LinkedHashMap<BlockPos, BlockState>();
        try {
            var entry = DevilsMaps.anchor(zone, "SP.IN.0", origin).pos();
            player.teleportTo(level, entry.x, entry.y, entry.z, java.util.Set.of(),0,0,true);
            player.setGameMode(net.minecraft.world.level.GameType.SURVIVAL);
            var candidates = DevilsMaps.candidates(zone,slot.anchor(),origin);
            var occupied = candidates.stream().map(m -> DevilsSpatial.bodyAt(probe,m.pos())).toList();
            var search = new DevilsSpatial.Search(); var failures = new java.util.ArrayList<String>();
            for (int retry=0;retry<5;retry++) {
                check(h, DevilsSpatial.spawn(level,slot,origin,probe,List.of(player),occupied,search,failures::add).isEmpty(), "Occupied shield pads cannot spawn");
                check(h, search.waiting() && !search.pending() && failures.isEmpty(), "Temporary occupancy is a delayed retry, not failed geometry or budget continuation");
            }
            check(h, DevilsSpatial.spawn(level,slot,origin,probe,List.of(player),List.of(),search,failures::add).isPresent(), "Released reservations admit shield actor");
            check(h, !search.waiting() && !search.pending(), "Successful search clears retry state");
            var warned = DevilsSpatial.spawn(level,slot,origin,probe,List.of(player),List.of(),search,failures::add).orElseThrow().pos();
            check(h, DevilsSpatial.recheck(level,slot,origin,probe,warned,List.of(player),List.of()), "Selected warning pad revalidates when unchanged");
            check(h, !DevilsSpatial.recheck(level,slot,origin,probe,warned,List.of(player),occupied), "Later reservation prevents activation at warned pad");
            var near = candidates.getFirst().pos();
            player.teleportTo(level,near.x,near.y,near.z,java.util.Set.of(),0,0,true);
            check(h, DevilsSpatial.spawn(level,slot,origin,probe,List.of(player),List.of(),search,failures::add).isEmpty() && search.waiting(), "Nearby Guardian delays all shield alternatives");
            check(h, !DevilsSpatial.recheck(level,slot,origin,probe,warned,List.of(player),List.of()), "Guardian approaching during warning prevents activation");
            player.teleportTo(level,entry.x,entry.y,entry.z,java.util.Set.of(),0,0,true);
            check(h, DevilsSpatial.spawn(level,slot,origin,probe,List.of(player),List.of(),search,failures::add).isPresent(), "Moving away admits shield actor without a reset");
            // Hide every eligible target behind cover without changing any authored spawn pad.
            // A stationary flyer has no firing line now, but the pad can become usable as the player moves.
            var cover = new java.util.LinkedHashMap<BlockPos, BlockState>();
            var center = player.blockPosition();
            try {
                for (int x=-2;x<=2;x++) for (int y=-1;y<=3;y++) for (int z=-2;z<=2;z++) {
                    if (Math.abs(x)!=2 && Math.abs(z)!=2 && y!=-1 && y!=3) continue;
                    var at = center.offset(x,y,z); var state = level.getBlockState(at);
                    cover.put(at,state); oldBlocks.putIfAbsent(at,state);
                    level.setBlockAndUpdate(at,net.minecraft.world.level.block.Blocks.STONE.defaultBlockState());
                }
                for (int retry=0;retry<5;retry++) {
                    check(h, DevilsSpatial.spawn(level,slot,origin,probe,List.of(player),List.of(),search,failures::add).isEmpty(), "Covered Guardian cannot admit a stationary flyer without a firing line");
                    check(h, search.waiting() && !search.pending() && failures.isEmpty(), "Temporary loss of firing line waits without resetting the encounter");
                }
                check(h, !DevilsSpatial.recheck(level,slot,origin,probe,warned,List.of(player),List.of()), "Taking cover during warning prevents stationary flyer activation");
            } finally { cover.forEach(level::setBlockAndUpdate); }
            check(h, DevilsSpatial.spawn(level,slot,origin,probe,List.of(player),List.of(),search,failures::add).isPresent(), "Restored firing line admits shield actor with the same search");
            check(h, !search.waiting() && failures.isEmpty(), "Restored firing line clears waiting without placement failure");
            // Unlike transient actors, genuinely invalid geometry must still report a completed failure.
            for (var marker : candidates) {
                var at = BlockPos.containing(marker.pos()); oldBlocks.putIfAbsent(at, level.getBlockState(at));
                level.setBlockAndUpdate(at, net.minecraft.world.level.block.Blocks.STONE.defaultBlockState());
            }
            check(h, DevilsSpatial.spawn(level,slot,origin,probe,List.of(player),List.of(),search,failures::add).isEmpty(), "Blocked geometry refuses shield actor");
            check(h, !search.waiting() && !search.pending() && failures.size()==1, "Static invalid pads remain a completed placement failure");
        } finally {
            oldBlocks.forEach(level::setBlockAndUpdate); probe.discard();
            var home=h.absolutePos(new BlockPos(2,1,2));
            player.teleportTo(h.getLevel(),home.getX(),home.getY(),home.getZ(),java.util.Set.of(),0,0,true);
            TestPlayers.remove(player);
        }
    }

    private static void verifySepiksWarpPads(GameTestHelper h, net.minecraft.server.level.ServerLevel level) {
        var zone = DevilsPlan.Zone.SP; var origin = DevilsWorldBuild.origin(zone);
        var player = TestPlayers.create(h,new net.minecraft.world.phys.Vec3(2,1,2),0,0);
        var type = BuiltInRegistries.ENTITY_TYPE.getValue(net.minecraft.resources.Identifier.fromNamespaceAndPath("destiny","devils_sepiks"));
        var probe = (net.minecraft.world.entity.Mob)type.create(level,net.minecraft.world.entity.EntitySpawnReason.COMMAND);
        try {
            var entry=DevilsMaps.anchor(zone,"SP.IN.0",origin).pos();
            player.teleportTo(level,entry.x,entry.y,entry.z,java.util.Set.of(),0,0,true);
            player.setGameMode(net.minecraft.world.level.GameType.SURVIVAL);
            probe.setPos(entry);
            var pads=new java.util.ArrayList<net.minecraft.world.phys.Vec3>();
            for(int i=1;i<=4;i++) {
                var pad=DevilsMaps.anchor(zone,"SP.WARP."+i,origin).pos(); pads.add(pad);
                check(h,DevilsSpatial.recheckWarp(level,origin,probe,pad,List.of(player),List.of()),"Sepiks authored warp body/route valid: "+i);
            }
            var chosen=DevilsSpatial.warp(level,origin,probe,List.of(player),List.of()).orElseThrow();
            check(h,!DevilsSpatial.recheckWarp(level,origin,probe,chosen.pos().add(.1,0,0),List.of(player),List.of()),"Only exact authored warp anchors accepted");
            var occupied=pads.stream().map(p -> DevilsSpatial.bodyAt(probe,p)).toList();
            check(h,DevilsSpatial.warp(level,origin,probe,List.of(player),occupied).isEmpty(),"Reserved warp pads cannot be selected");
            check(h,!DevilsSpatial.recheckWarp(level,origin,probe,chosen.pos(),List.of(player),occupied),"Late spawn reservation cancels warp commit");
            player.teleportTo(level,chosen.pos().x,chosen.pos().y,chosen.pos().z,java.util.Set.of(),0,0,true);
            check(h,!DevilsSpatial.recheckWarp(level,origin,probe,chosen.pos(),List.of(player),List.of()),"Approaching Guardian cancels warp commit");
            player.teleportTo(level,entry.x,entry.y,entry.z,java.util.Set.of(),0,0,true);
            for(var pad:pads) {
                probe.setPos(pad);
                var next=DevilsSpatial.warp(level,origin,probe,List.of(player),List.of()).orElseThrow();
                check(h,next.pos().distanceToSqr(pad)>=4,"Warp never selects current anchor");
            }
        } finally {
            probe.discard();var home=h.absolutePos(new BlockPos(2,1,2));
            player.teleportTo(h.getLevel(),home.getX(),home.getY(),home.getZ(),java.util.Set.of(),0,0,true);
            TestPlayers.remove(player);
        }
    }

}
