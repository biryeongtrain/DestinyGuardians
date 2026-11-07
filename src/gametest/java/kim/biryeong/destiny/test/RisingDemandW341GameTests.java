package kim.biryeong.destiny.test;

import kim.biryeong.destiny.campaign.*;
import kim.biryeong.destiny.world.template.ArrivalChunks;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.core.BlockPos;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.phys.Vec3;
import java.util.UUID;
import java.util.concurrent.TimeUnit;

/** World-generation-only fixture: no client resource pack, shaders, audio or framebuffer acceptance. */
public final class RisingDemandW341GameTests {
    private static void check(GameTestHelper h, boolean condition, String message) {
        h.assertTrue(condition, Component.literal(message));
    }
    @GameTest(structure="destiny-test:floor", environment="destiny-test:w90_isolated", maxTicks=10000)
    public void noIdleMapLoadsAndOnlyActualArrivalRequestsAColumn(GameTestHelper h) {
        var server=h.getLevel().getServer();
        var manager=new GuardianRisesInstances(server,2);
        var zones=RisingServices.zones().orElseThrow();
        var first=new GuardianRisesInstances.Instance[1];
        var player=new ServerPlayer[1];
        var arrival=new ArrivalChunks[1];
        int[] stage={0}, idleTicks={0};
        long deadline=System.nanoTime()+TimeUnit.SECONDS.toNanos(90);
        TestCleanup.register(h,()->{
            if(arrival[0]!=null)arrival[0].close();
            if(player[0]!=null) {
                var at=h.absoluteVec(new Vec3(2,1,2));
                player[0].teleportTo(h.getLevel(),at.x,at.y,at.z,java.util.Set.of(),0,0,true);
                h.getLevel().removePlayerImmediately(player[0],Entity.RemovalReason.DISCARDED);
                TestPlayers.remove(player[0]);
            }
            for(var instance:manager.instances())check(h,manager.close(instance),"All owned worlds close after pending arrivals are released");
        });
        h.onEachTick(()->{
            java.util.concurrent.locks.LockSupport.parkNanos(1_000_000);
            check(h,System.nanoTime()<deadline,"Demand-only world generation timed out, stage="+stage[0]);
            if(first[0]==null) {
                // Default campaign flag is enabled in this fixture: idle ticks must never create a spare.
                if(++idleTicks[0]<20)return;
                for(var level:server.getAllLevels())check(h,!level.dimension().identifier().getPath().startsWith("guardian_rises/"),"No automatic spare world");
                var created=manager.prepare(UUID.randomUUID());if(created.isEmpty())return;
                first[0]=created.orElseThrow();
                check(h,first[0].level().getChunkSource().getLoadedChunksCount()==0,"Assigning a generator does not load map chunks");
                for(var zone:RisingServices.Zone.values())
                    check(h,zones.begin(first[0].level(),zone,GuardianRisesInstances.origin(zone)).step(0),"Zone metadata is immediately available without terrain");
                check(h,first[0].level().getChunkSource().getLoadedChunksCount()==0,"Even checking all four zone metadata objects generates zero chunks");
                manager.ready(first[0]);manager.running(first[0]);idleTicks[0]=0;return;
            }
            var level=first[0].level();
            if(stage[0]==0&&idleTicks[0]++<20) {
                check(h,level.getChunkSource().getLoadedChunksCount()==0,"Idle instance remains empty before an actual arrival");return;
            }
            if(stage[0]<RisingServices.Zone.values().length) {
                var zone=RisingServices.Zone.values()[stage[0]];
                var spawn=zones.markers(zone,GuardianRisesInstances.origin(zone)).all().stream()
                        .filter(m->m.id().equals("spawn.player")).findFirst().orElseThrow();
                if(arrival[0]==null)arrival[0]=new ArrivalChunks(level,active->manager.tickForArrival(first[0],active));
                var at=BlockPos.containing(spawn.pos());
                boolean ready=arrival[0].ready(at);
                check(h,arrival[0].requestedColumns()<=1,"At most the one actual destination column is explicitly requested");
                if(!ready)return;
                check(h,level.getChunkSource().getChunkNow(at.getX()>>4,at.getZ()>>4)!=null,"Actual destination is full before teleport");
                if(stage[0]==0) {
                    // getLoadedChunksCount includes generation-dependency holders, not just FULL columns.
                    int full=0;
                    for(int x=(at.getX()>>4)-12;x<=(at.getX()>>4)+12;x++)
                        for(int z=(at.getZ()>>4)-12;z<=(at.getZ()>>4)+12;z++)
                            if(level.getChunkSource().getChunkNow(x,z)!=null)full++;
                    kim.biryeong.destiny.DestinyGuardians.LOGGER.info("[DemandChunks QA] First arrival: {} FULL columns, {} pipeline holders",full,level.getChunkSource().getLoadedChunksCount());
                    check(h,full<10,"First arrival did not warm a whole map or view-distance rectangle: FULL="+full);
                }
                if(player[0]==null)player[0]=TestPlayers.create(h,new Vec3(2,1,2),0,0,"DemandQA");
                check(h,player[0].teleportTo(level,spawn.pos().x,spawn.pos().y,spawn.pos().z,java.util.Set.of(),spawn.yaw(),0,true),"Teleport succeeds after destination readiness");
                arrival[0].close();arrival[0]=null;
                for(int i=stage[0]+1;i<RisingServices.Zone.values().length;i++) {
                    var future=RisingServices.Zone.values()[i];
                    var next=zones.markers(future,GuardianRisesInstances.origin(future)).all().stream()
                            .filter(m->m.id().equals("spawn.player")).findFirst().orElseThrow();
                    var pos=BlockPos.containing(next.pos());
                    check(h,level.getChunkSource().getChunkNow(pos.getX()>>4,pos.getZ()>>4)==null,"Future map is not prepared ahead of the player: "+future);
                }
                kim.biryeong.destiny.DestinyGuardians.LOGGER.info("[DemandChunks QA] {} reached, pipeline holders={}, future zones untouched",zone,level.getChunkSource().getLoadedChunksCount());
                stage[0]++;return;
            }
            var second=manager.prepare(UUID.randomUUID()).orElseThrow();
            var gate=new ArrivalChunks(second.level(),active->manager.tickForArrival(second,active));
            gate.ready(GuardianRisesInstances.origin(RisingServices.Zone.GATEWAY));
            check(h,gate.requestedColumns()==1,"Cancellation fixture has only one pending destination");
            gate.close();gate.close();
            check(h,!gate.ready(GuardianRisesInstances.origin(RisingServices.Zone.DOCK13)),"A closed arrival can never request another map");
            check(h,manager.close(second)&&manager.close(second),"Cancelled pending arrival world closes idempotently");
            h.succeed();
        });
    }
}
