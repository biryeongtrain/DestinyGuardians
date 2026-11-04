package kim.biryeong.destiny.strike.devils;

import kim.biryeong.destiny.combat.Combat;
import kim.biryeong.destiny.guardian.Element;
import kim.biryeong.destiny.test.TestCleanup;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.phys.Vec3;
import java.util.*;
import static kim.biryeong.destiny.strike.devils.DevilsDirector.*;
import static kim.biryeong.destiny.strike.devils.DevilsPlan.*;

/** Real actor/model/Combat integration; ordinary encounter actors are recorded by the host. */
public final class DevilsFactionFixture {
    private static void check(GameTestHelper h, boolean ok, String message) {
        h.assertTrue(ok, Component.literal(message));
    }
    private static final class HostFixture implements Host {
        final DevilsDirector director = new DevilsDirector(this);
        final Map<String, Spawn> live = new LinkedHashMap<>();
        final List<Cue> cues = new ArrayList<>();
        public boolean spawn(Spawn spawn) { live.put(spawn.slot().id(), spawn); return true; }
        public void retire(ActorRef ref, Retirement why) { live.remove(ref.slotId()); }
        public CuePlayback cue(Cue cue) { cues.add(cue); return CuePlayback.playing(1); }
        void tick(boolean killOrdinary) {
            director.tick();
            for (var cue : List.copyOf(cues)) { cues.remove(cue); director.cueFinished(cue); }
            if (killOrdinary) for (var spawn : List.copyOf(live.values())) if (spawn.slot().ordinary()) {
                live.remove(spawn.slot().id()); director.defeated(spawn.ref());
            }
        }
        void until(GameTestHelper h, Phase phase, int limit) {
            for (int i=0; i<limit && director.phase()!=phase; i++) tick(true);
            check(h,director.phase()==phase,"Director reaches "+phase);
        }
    }
    /** A real encounter-owned actor of {@code kind} at a fixed position; the player is the sole participant. */
    public static DevilsMob liveActor(GameTestHelper h, ServerPlayer player, Kind kind, Vec3 relativeFeet) {
        var f=new HostFixture();
        check(h,f.director.begin(1),"Solo admission");
        for(int i=0;i<2000&&f.live.values().stream().noneMatch(v->v.slot().kind()==kind);i++)f.tick(false);
        var spawn=f.live.values().stream().filter(v->v.slot().kind()==kind).findFirst().orElse(null);
        check(h,spawn!=null,"Director schedules a live "+kind);
        var at=h.absoluteVec(relativeFeet);
        var runtime=new DevilsActors(h.getLevel(),()->f.director,new DevilsActors.Environment(){
            public List<ServerPlayer> participants(){return List.of(player);}
            public Optional<Vec3> spawnPoint(Slot slot,DevilsMob mob){return Optional.of(at);}
            public boolean contains(Zone zone,Vec3 feet){return true;}
            public Optional<Vec3> sepiksWarp(DevilsMob mob){return Optional.empty();}
        });
        TestCleanup.register(h,runtime::close);
        check(h,runtime.spawn(spawn),"Actor spawn "+kind);
        var mob=runtime.active.get(spawn.ref());
        check(h,mob!=null&&mob.getHealth()==(float)kind.health(),"Planned health "+kind);
        mob.setNoAi(true); mob.setPos(at.x,at.y,at.z);
        return mob;
    }
    public static void verifyModelCatalog(GameTestHelper h) {
        var f=new HostFixture();
        var runtime=new DevilsActors(h.getLevel(),()->f.director,new DevilsActors.Environment(){
            public List<ServerPlayer> participants(){return List.of();}
            public Optional<Vec3> spawnPoint(Slot slot,DevilsMob mob){return Optional.of(h.absoluteVec(new Vec3(5,20,5)));}
            public boolean contains(Zone zone,Vec3 feet){return true;}
            public Optional<Vec3> sepiksWarp(DevilsMob mob){return Optional.empty();}
        });
        TestCleanup.register(h,runtime::close);
        for(var kind:Kind.values()) {
            String id="catalog-"+kind.name();
            var slot=new Slot(id,Zone.RY,"catalog",kind,"fixture",0);
            var ref=new ActorRef(1,id,0);
            check(h,runtime.spawn(new Spawn(slot,ref,kind.health(),kind.shield())),"Actual model attachment: "+kind);
            check(h,runtime.actors().size()==1&&runtime.actors().getFirst().kind()==kind,"Correct registered actor: "+kind);
            runtime.retire(ref,Retirement.CLOSED);
            check(h,runtime.actors().isEmpty(),"Catalog fixture releases actor: "+kind);
        }
        check(h,DevilsActors.model(Kind.WALKER).equals("rg_walker"),"Retained Walker routing");
    }
    public static void verifyRetargetWarning(GameTestHelper h) {
        var f = new HostFixture();
        check(h, f.director.begin(1), "Retarget encounter starts");
        f.until(h, Phase.RY_CLEAR, 2000);
        check(h, f.director.arrive(Zone.RF), "Retarget refinery setup");
        for(int i=0;i<400;i++) f.tick(false);
        var at = h.absoluteVec(new Vec3(3, 2, 3));
        int[] charges = {0};
        var runtime = new DevilsActors(h.getLevel(), () -> f.director, new DevilsActors.Environment() {
            public List<ServerPlayer> participants() { return List.of(); }
            public Optional<Vec3> spawnPoint(Slot slot, DevilsMob mob) { return Optional.of(at); }
            public boolean contains(Zone zone, Vec3 feet) { return true; }
            public Optional<Vec3> sepiksWarp(DevilsMob mob) { return Optional.empty(); }
            public void sound(DevilsMob mob, String event) {
                if (mob.kind() == Kind.THRALL && event.equals("charge")) charges[0]++;
            }
        });
        TestCleanup.register(h, runtime::close);
        var spawns = new ArrayList<Spawn>();
        spawns.add(f.live.values().stream().filter(v -> v.slot().kind()==Kind.THRALL).findFirst().orElseThrow());
        spawns.addAll(f.live.values().stream().filter(v -> v.slot().kind()==Kind.DREG).limit(2).toList());
        DevilsMob[] mobs = new DevilsMob[3];
        for (int i=0;i<3;i++) {
            var spawn = spawns.get(i);
            check(h, runtime.spawn(spawn), "Retarget actor attaches with director-owned slot");
            mobs[i] = runtime.active.get(spawn.ref());
        }
        var attacker=mobs[0]; var original=mobs[1]; var replacement=mobs[2];
        original.setPos(at.add(1.5,0,0)); replacement.setPos(at.add(-2,0,0));
        // Isolate the attack state machine: real entities/damage/models, manually stepped AI without movement.
        for(int i=0;i<41;i++) { runtime.tick(false); attacker.customServerAiStep(h.getLevel()); }
        check(h, charges[0]==1 && original.getHealth()==original.getMaxHealth(), "Original melee warning is one step from impact");
        runtime.retire(original.reference(), Retirement.CLOSED);
        float before=replacement.getHealth();
        runtime.tick(false); attacker.customServerAiStep(h.getLevel());
        check(h, replacement.getHealth()==before, "New target cannot inherit the previous target's near-complete melee warning");
        check(h, charges[0]==2, "Replacement gets a fresh warning");
        for(int i=0;i<11;i++) { runtime.tick(false); attacker.customServerAiStep(h.getLevel()); }
        check(h, replacement.getHealth()==before, "Fresh warning lasts all twelve steps");
        runtime.tick(false); attacker.customServerAiStep(h.getLevel());
        check(h, replacement.getHealth()==before-3, "Melee lands only after its new warning");
    }

    public static void verify(GameTestHelper h, ServerPlayer player) {
        player.setGameMode(net.minecraft.world.level.GameType.SPECTATOR);
        var f=new HostFixture();
        check(h,f.director.begin(1),"Solo admission");
        f.until(h,Phase.RY_CLEAR,2000);
        check(h,f.director.arrive(Zone.RF),"Refinery transition");
        for(int i=0;i<400;i++)f.tick(false);
        var at=h.absoluteVec(new Vec3(3,2,3));
        var env=new DevilsActors.Environment(){
            public List<ServerPlayer> participants(){return List.of(player);}
            public Optional<Vec3> spawnPoint(Slot slot,DevilsMob mob){return Optional.of(at);}
            public boolean contains(Zone zone,Vec3 feet){return true;}
            public Optional<Vec3> sepiksWarp(DevilsMob mob){return Optional.empty();}
        };
        var runtime=new DevilsActors(h.getLevel(),()->f.director,env);
        var foreign=new DevilsActors(h.getLevel(),()->f.director,env);
        TestCleanup.register(h,()->{runtime.close();foreign.close();});
        var fallen=f.live.values().stream().filter(s->s.slot().kind()==Kind.DREG).limit(2).toList();
        var hive=f.live.values().stream().filter(s->s.slot().kind()==Kind.THRALL).findFirst().orElseThrow();
        check(h,fallen.size()==2,"Mixed refinery packs are live");
        for(var s:fallen)check(h,runtime.spawn(s),"Fallen model spawn");
        check(h,runtime.spawn(hive),"Hive model spawn");
        var a=runtime.active.get(fallen.get(0).ref());
        var ally=runtime.active.get(fallen.get(1).ref());
        var b=runtime.active.get(hive.ref());
        b.setPos(at.x+2,at.y,at.z);ally.setPos(at.x+8,at.y,at.z);
        player.setPos(at.x+40,at.y,at.z);
        check(h,runtime.validTarget(a,b)&&runtime.validTarget(b,a),"Mutual hostility");
        check(h,!runtime.validTarget(a,ally)&&!runtime.validTarget(a,a),"No friendly targets");
        check(h,!a.hurtServer(h.getLevel(),ally.damageSources().mobAttack(ally),5),"Friendly damage rejected");
        check(h,foreign.spawn(hive),"Foreign actor fixture");
        var outsider=foreign.actors().getFirst();
        check(h,!runtime.validTarget(a,outsider),"Foreign session not targeted");
        check(h,!a.hurtServer(h.getLevel(),outsider.damageSources().mobAttack(outsider),5),"Foreign session damage rejected");
        float ah=a.getHealth(),bh=b.getHealth();
        for(int i=0;i<55;i++){runtime.tick(false);a.customServerAiStep(h.getLevel());b.customServerAiStep(h.getLevel());}
        check(h,a.getHealth()<ah&&b.getHealth()<bh,"Actual AI chooses nearby opposing faction and both melee attacks land");
        b.setHealth(b.getMaxHealth());b.setPos(at.x+6,at.y,at.z);
        float rangedBefore=b.getHealth();
        for(int i=0;i<55;i++){runtime.tick(false);a.customServerAiStep(h.getLevel());}
        check(h,b.isAlive()&&b.getHealth()<rangedBefore,"Actual ranged bolts collide with opposing faction");
        player.setGameMode(net.minecraft.world.level.GameType.SURVIVAL);
        player.setPos(at.x+10,at.y,at.z);
        a.getSensing().tick();b.getSensing().tick();
        check(h,a.selectTarget()==player&&b.selectTarget()==player,"Visible player outranks closer enemy faction for both sides");
        player.setGameMode(net.minecraft.world.level.GameType.SPECTATOR);
        check(h,a.selectTarget()==b,"Invalid player releases priority");
        player.setGameMode(net.minecraft.world.level.GameType.SURVIVAL);
        player.setPos(at.x,at.y,at.z+8);
        var wall=net.minecraft.core.BlockPos.containing(at.add(0,0,4));
        for(int x=-2;x<=2;x++)for(int y=0;y<4;y++)h.getLevel().setBlockAndUpdate(wall.offset(x,y,0),net.minecraft.world.level.block.Blocks.STONE.defaultBlockState());
        a.getSensing().tick();
        check(h,a.selectTarget()==b,"Unseen player does not preempt faction combat");
        a.damageCooldownTime=0;
        check(h,a.hurtServer(h.getLevel(),a.damageSources().playerAttack(player),1),"Player attack accepted behind cover");
        check(h,a.selectTarget()==player,"Attacking player gets immediate priority without line of sight");
        for(int i=0;i<101;i++){runtime.tick(false);a.customServerAiStep(h.getLevel());}
        check(h,a.selectTarget()!=player,"Lost player memory expires after five seconds");
        for(int x=-2;x<=2;x++)for(int y=0;y<4;y++)h.getLevel().setBlockAndUpdate(wall.offset(x,y,0),net.minecraft.world.level.block.Blocks.AIR.defaultBlockState());
        player.setPos(at.x+90,at.y,at.z);
        a.damageCooldownTime=0;
        check(h,a.hurtServer(h.getLevel(),a.damageSources().playerAttack(player),1),"Distant player attack accepted");
        check(h,a.selectTarget()==player,"Damage alerts mob beyond passive detection range");
        b.setLastHurtByPlayer(player,100);
        float energy=kim.biryeong.destiny.guardian.Guardians.data(player).superEnergy();
        int defeated=f.director.snapshot().defeated();
        b.damageCooldownTime=0;
        check(h,b.hurtServer(h.getLevel(),a.damageSources().mobAttack(a),1000),"Enemy lethal damage accepted");
        check(h,b.isDeadOrDying()&&f.director.snapshot().defeated()==defeated+1,"Enemy kill advances director once");
        check(h,kim.biryeong.destiny.guardian.Guardians.data(player).superEnergy()==energy,"Prior player tag does not receive faction kill energy");
        check(h,!runtime.combatTargets(a).contains(b),"Dead actor no longer targeted");
    }
}
