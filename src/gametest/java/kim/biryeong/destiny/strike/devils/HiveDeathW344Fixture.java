package kim.biryeong.destiny.strike.devils;

import kim.biryeong.destiny.test.TestCleanup;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.phys.Vec3;
import java.util.*;
import static kim.biryeong.destiny.strike.devils.DevilsDirector.*;
import static kim.biryeong.destiny.strike.devils.DevilsPlan.*;

/** Script prior encounter progression; the selected Hive actor, damage and sound callback remain real. */
public final class HiveDeathW344Fixture {
    private static final class Setup implements Host {
        final DevilsDirector director=new DevilsDirector(this);
        final Map<String,Spawn> live=new LinkedHashMap<>();
        final List<Cue> cues=new ArrayList<>();
        public boolean spawn(Spawn s){live.put(s.slot().id(),s);return true;}
        public void retire(ActorRef r,Retirement why){live.remove(r.slotId());}
        public CuePlayback cue(Cue c){cues.add(c);return CuePlayback.playing(1);}
        void tick(){director.tick();for(var c:List.copyOf(cues)){cues.remove(c);director.cueFinished(c);}}
        void clearOrdinary(){for(var s:List.copyOf(live.values()))if(s.slot().ordinary()){live.remove(s.slot().id());director.defeated(s.ref());}}
        void until(GameTestHelper h,Phase target,int bound){for(int i=0;i<bound&&director.phase()!=target;i++){tick();clearOrdinary();}h.assertTrue(director.phase()==target,"Setup reaches "+target);}
    }
    public static DevilsMob spawn(GameTestHelper h,ServerPlayer player,Kind kind) {
        var f=new Setup();TestCleanup.register(h,f.director::close);
        h.assertTrue(f.director.begin(1),"Solo setup");f.until(h,Phase.RY_CLEAR,2000);
        h.assertTrue(f.director.arrive(Zone.RF),"Refinery setup");
        if(kind==Kind.WIZARD) {
            f.until(h,Phase.RF_DEVICE,2000);
            for(int i=0;i<100&&!f.director.snapshot().deviceReady();i++)f.tick();
            h.assertTrue(f.director.interact(),"Start defense waves");
        }
        Spawn selected=null;
        for(int i=0;i<6000&&selected==null;i++) {
            f.tick();selected=f.live.values().stream().filter(s->s.slot().kind()==kind).findFirst().orElse(null);
            if(selected==null)f.clearOrdinary();
        }
        h.assertTrue(selected!=null,"Director reserves "+kind);
        var at=h.absoluteVec(new Vec3(4,20,4));
        var runtime=new DevilsActors(h.getLevel(),()->f.director,new DevilsActors.Environment(){
            public List<ServerPlayer> participants(){return List.of(player);}
            public Optional<Vec3> spawnPoint(Slot slot,DevilsMob mob){return Optional.of(at);}
            public boolean contains(Zone z,Vec3 point){return true;}
            public Optional<Vec3> sepiksWarp(DevilsMob mob){return Optional.empty();}
            public void sound(DevilsMob mob,String event){DevilsCombatSounds.play(h.getLevel(),List.of(player),mob.kind(),event,mob.position());}
        });
        TestCleanup.register(h,runtime::close);h.assertTrue(runtime.spawn(selected),"Actual Hive model/entity inserted");
        var mob=runtime.actors().getFirst();mob.setNoAi(true);mob.setNoGravity(true);return mob;
    }
}
