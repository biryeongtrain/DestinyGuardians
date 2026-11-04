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
public final class DevilsWalkerFixture {
    private static void check(GameTestHelper h, boolean ok, String message) {
        h.assertTrue(ok, Component.literal(message));
    }
    private static final class HostFixture implements Host {
        final DevilsDirector director = new DevilsDirector(this);
        final Map<String, Spawn> live = new LinkedHashMap<>();
        final List<Cue> cues = new ArrayList<>();
        int completions;
        public void completed(long generation) { completions++; }
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

    private static HostFixture blast(GameTestHelper h) {
        var f = new HostFixture();
        check(h, f.director.begin(1), "Solo admission");
        f.until(h, Phase.RY_CLEAR, 2000);
        check(h, f.director.arrive(Zone.RF), "Refinery transition");
        f.until(h, Phase.RF_DEVICE, 1000);
        for (int i = 0; i < 100 && !f.director.snapshot().deviceReady(); i++) f.tick(true);
        check(h, f.director.interact(), "Refinery device activation");
        f.until(h, Phase.RF_CLEAR, 5000);
        check(h, f.director.arrive(Zone.BL), "Blast transition");
        for (int i = 0; i < 160; i++) f.tick(true);
        return f;
    }

    private static DevilsActors runtime(GameTestHelper h, ServerPlayer player, HostFixture f) {
        // Clear air avoids the small floor fixture ceiling; this does not test authored spawn pads.
        int[] placed = {0};
        var runtime = new DevilsActors(h.getLevel(), () -> f.director, new DevilsActors.Environment() {
            public List<ServerPlayer> participants() { return List.of(player); }
            public Optional<Vec3> spawnPoint(Slot slot, DevilsMob mob) {
                return Optional.of(h.absoluteVec(new Vec3(4, 20 + placed[0]++ * 10, 4)));
            }
            public boolean contains(Zone zone, Vec3 feet) { return true; }
            public Optional<Vec3> sepiksWarp(DevilsMob mob) { return Optional.empty(); }
        });
        TestCleanup.register(h, runtime::close);
        return runtime;
    }

    private static DevilsMob spawn(GameTestHelper h, DevilsActors runtime, Spawn spawn) {
        check(h, spawn != null && runtime.spawn(spawn), "Actual actor/model spawns");
        return runtime.actors().stream().filter(m -> m.reference().equals(spawn.ref())).findFirst().orElseThrow();
    }

    public static void verifyBrigs(GameTestHelper h, ServerPlayer player) {
        var f = blast(h); var runtime = runtime(h, player, f);
        for (int index = 1; index <= 2; index++) {
            var brig = spawn(h, runtime, f.live.get("BL-brig-" + index));
            check(h, brig.getMaxHealth() == 700 && !brig.armorOpen(), "Brig starts with closed armor and planned pool");
            Combat.damage(h.getLevel(), player, brig, 349, Element.ARC);
            check(h, brig.getHealth() == 351 && !brig.armorOpen(), "Armor stays closed above half health");
            Combat.damage(h.getLevel(), player, brig, 1, Element.ARC);
            check(h, brig.getHealth() == 350 && brig.armorOpen(), "Actual damage opens armor exactly at half health");
            int before = f.director.snapshot().defeated();
            check(h, Combat.damage(h.getLevel(), player, brig, 1000, Element.ARC), "Brig lethal hit reports kill");
            check(h, f.director.snapshot().defeated() == before + 1, "Brig death credited once");
            check(h, !Combat.damage(h.getLevel(), player, brig, 1000, Element.ARC), "Dead Brig cannot award another kill");
        }
        check(h, f.director.phase() == Phase.BL_BATTLE, "Two Brig kills cannot skip the living Walker");
    }

    public static void verifySpawnPresentation(GameTestHelper h, ServerPlayer player) {
        var f = blast(h);
        var first = f.live.get("BL-brig-1");
        var second = f.live.get("BL-brig-2");
        var selected = h.absoluteVec(new Vec3(4, 20, 4));
        boolean[] padReady = {false};
        int[] notifications = {0};
        Spawn[] observed = {null};
        Vec3[] observedPosition = {null};
        boolean[] inserted = {false};
        DevilsActors[] owner = {null};
        owner[0] = new DevilsActors(h.getLevel(), () -> f.director, new DevilsActors.Environment() {
            public List<ServerPlayer> participants() { return List.of(player); }
            public Optional<Vec3> spawnPoint(Slot slot, DevilsMob mob) {
                return padReady[0] ? Optional.of(selected) : Optional.empty();
            }
            public boolean contains(Zone zone, Vec3 feet) { return true; }
            public Optional<Vec3> sepiksWarp(DevilsMob mob) { return Optional.empty(); }
            public void spawned(Spawn event, Vec3 at) {
                notifications[0]++;
                var mob = owner[0].actors().stream().filter(m -> m.reference().equals(event.ref())).findFirst().orElseThrow();
                observed[0] = event; observedPosition[0] = at;
                inserted[0] = at.equals(mob.position()) && h.getLevel().getEntity(mob.getUUID()) == mob;
                // Simulate a broken ship renderer after acceptance, not a spawn failure.
                throw new IllegalStateException("Expected fixture presentation failure");
            }
        });
        var runtime = owner[0];
        TestCleanup.register(h, runtime::close);
        check(h, !runtime.spawn(first) && notifications[0] == 0 && runtime.actors().isEmpty(),
                "Deferred pad selection sends no arrival notification");
        padReady[0] = true;
        check(h, runtime.spawn(first), "Presentation exception cannot reject an accepted combatant");
        check(h, notifications[0] == 1 && runtime.actors().size() == 1, "Exactly one accepted actor and notification");
        check(h, first.equals(observed[0]) && selected.equals(observedPosition[0]) && inserted[0],
                "Notification sees the actual inserted actor and selected position before throwing");
        check(h, !runtime.spawn(first) && notifications[0] == 1, "Duplicate request cannot replay presentation");
        var obstacle = net.minecraft.core.BlockPos.containing(selected);
        var original = h.getLevel().getBlockState(obstacle);
        TestCleanup.register(h, () -> h.getLevel().setBlockAndUpdate(obstacle, original));
        h.getLevel().setBlockAndUpdate(obstacle, net.minecraft.world.level.block.Blocks.STONE.defaultBlockState());
        check(h, !runtime.spawn(second) && notifications[0] == 1,
                "Block-obstructed selected pad cannot report a successful arrival");
        runtime.close();
        check(h, !runtime.spawn(second) && notifications[0] == 1 && runtime.actors().isEmpty(),
                "Closed runtime cannot emit stale arrival notifications");
    }

    /** Advances real server/entity ticks; arena geometry is covered separately by DevilsNbtGameTests. */
    public static void verifySepiksWarp(GameTestHelper h, ServerPlayer player, boolean obstructAfterWarning) {
        var f = blast(h);
        for (var s : List.copyOf(f.live.values())) if (s.slot().kind().boss()) f.director.defeated(s.ref());
        f.until(h, Phase.BL_CLEAR, 2000);
        check(h, f.director.arrive(Zone.SP), "Sepiks arena transition");
        f.until(h, Phase.SP_INTRO, 2000);
        check(h, f.director.introFinished(f.director.generation()), "Scripted intro setup");
        f.until(h, Phase.SP_DAMAGE1, 200);
        var start = h.absoluteVec(new Vec3(4, 20, 4));
        var destination = start.add(8, 0, 0);
        int[] began = {-1}, committed = {-1}, ended = {-1}, attempts = {0};
        boolean[] obstructed = {false};
        var runtime = new DevilsActors(h.getLevel(), () -> f.director, new DevilsActors.Environment() {
            public List<ServerPlayer> participants() { return List.of(player); }
            public Optional<Vec3> spawnPoint(Slot slot, DevilsMob mob) { return Optional.of(start); }
            public boolean contains(Zone zone, Vec3 feet) { return true; }
            public Optional<Vec3> sepiksWarp(DevilsMob mob) { return Optional.of(destination); }
            public boolean commitSepiksWarp(DevilsMob mob, Vec3 at) {
                attempts[0]++;
                committed[0] = h.getLevel().getServer().getTickCount();
                check(h, at.equals(destination), "Commit rechecks the originally warned destination");
                check(h, mob.position().distanceToSqr(start) < .0001, "No movement before commit validation");
                return !obstructed[0];
            }
            public void sound(DevilsMob mob, String event) {
                int now = h.getLevel().getServer().getTickCount();
                if (event.equals("teleport_begin")) {
                    check(h, began[0] == -1, "Exactly one warning");
                    began[0] = now;
                    // Simulates a reservation arriving after selection; NBT tests cover the spatial predicate.
                    obstructed[0] = obstructAfterWarning;
                } else if (event.equals("teleport_end")) {
                    ended[0] = now;
                    check(h, mob.position().distanceToSqr(destination) < .0001, "Arrival sound follows relocation");
                }
            }
        });
        TestCleanup.register(h, runtime::close);
        var boss = spawn(h, runtime, f.live.get("SP-sepiks"));
        h.onEachTick(() -> {
            if (began[0] < 0) return;
            int elapsed = h.getLevel().getServer().getTickCount() - began[0];
            if (elapsed < 15) check(h, boss.position().distanceToSqr(start) < .0001, "Warning retains source position");
            if (elapsed < 26) return;
            check(h, attempts[0] == 1 && committed[0] - began[0] == 15,
                    "Commit on the sixteenth entity step including the warning step");
            check(h, boss.position().distanceToSqr(obstructAfterWarning ? start : destination) < .0001,
                    "Late obstruction cancels relocation; clear destination relocates");
            check(h, obstructAfterWarning ? ended[0] == -1 : ended[0] == committed[0],
                    "Arrival sound only for successful relocation");
            h.succeed();
        });
    }

    public static void verifySepiks(GameTestHelper h, ServerPlayer player) {
        var f = blast(h);
        // Prior encounters are scripted setup; Sepiks and every shield servitor below are real actors.
        for (var s : List.copyOf(f.live.values())) if (s.slot().kind().boss()) f.director.defeated(s.ref());
        f.until(h, Phase.BL_CLEAR, 2000);
        check(h, f.director.arrive(Zone.SP), "Sepiks arena transition");
        var runtime = runtime(h, player, f);
        for (int i = 0; i < 100 && !f.live.containsKey("SP-sepiks"); i++) f.tick(false);
        var boss = spawn(h, runtime, f.live.get("SP-sepiks"));
        check(h, boss.getHealth() == 2200 && boss.getMaxHealth() == 2200, "Real health exceeds vanilla 1024 limit");
        Combat.damage(h.getLevel(), player, boss, 10000, Element.ARC);
        check(h, boss.getHealth() == 2200, "Guard-phase Sepiks rejects damage");
        f.until(h, Phase.SP_INTRO, 2000);
        Combat.damage(h.getLevel(), player, boss, 10000, Element.ARC);
        check(h, boss.getHealth() == 2200, "Intro Sepiks rejects damage");
        check(h, f.director.introFinished(f.director.generation()), "Fixture acknowledges intro, not animation acceptance");
        f.until(h, Phase.SP_DAMAGE1, 200);
        for (int round = 1; round <= 2; round++) {
            float floor = round == 1 ? 1474 : 726;
            Combat.damage(h.getLevel(), player, boss, 10000, Element.ARC);
            check(h, boss.getHealth() == floor && !boss.isDeadOrDying(), "Oversized actual hit clamps at shield threshold");
            check(h, f.director.phase() == (round == 1 ? Phase.SP_SHIELD1 : Phase.SP_SHIELD2), "Actual health change enters shield phase");
            Combat.damage(h.getLevel(), player, boss, 10000, Element.ARC);
            check(h, boss.getHealth() == floor, "Shield blocks further damage");
            for (int i = 0; i < 80; i++) f.tick(true);
            for (int index = 1; index <= 3; index++) {
                var servant = spawn(h, runtime, f.live.get("SP-servitor-" + round + "-" + index));
                check(h, Combat.damage(h.getLevel(), player, servant, 1000, Element.ARC), "Actual shield servitor dies");
                if (index < 3) check(h, f.director.phase().shieldPhase(), "Shield stays until all three servitors die");
            }
            check(h, f.director.phase() == (round == 1 ? Phase.SP_RECOVER1 : Phase.SP_RECOVER2), "Last servitor starts recovery");
            Combat.damage(h.getLevel(), player, boss, 10000, Element.ARC);
            check(h, boss.getHealth() == floor, "Recovery still blocks damage");
            f.until(h, round == 1 ? Phase.SP_DAMAGE2 : Phase.SP_DAMAGE3, 100);
        }
        check(h, Combat.damage(h.getLevel(), player, boss, 10000, Element.ARC), "Final-phase Sepiks can die");
        check(h, f.director.phase() == Phase.COMPLETE && f.completions == 1, "Actual death completes strike once");
        check(h, !Combat.damage(h.getLevel(), player, boss, 10000, Element.ARC) && f.completions == 1, "Repeated lethal hit cannot repeat completion");
    }
    public static void verify(GameTestHelper h, ServerPlayer player) {
        var f=new HostFixture();
        check(h,f.director.begin(1),"Solo admission");
        f.until(h,Phase.RY_CLEAR,2000);
        check(h,f.director.arrive(Zone.RF),"Refinery transition");
        f.until(h,Phase.RF_DEVICE,1000);
        for(int i=0;i<100&&!f.director.snapshot().deviceReady();i++)f.tick(true);
        check(h,f.director.interact(),"Device activates");
        f.until(h,Phase.RF_CLEAR,5000);
        check(h,f.director.arrive(Zone.BL),"Blast transition");
        for(int i=0;i<160&&!f.live.containsKey("BL-walker");i++)f.tick(false);
        var spawn=f.live.get("BL-walker");
        check(h,spawn!=null,"Walker reserved and live in actual director");
        var at=h.absoluteVec(new Vec3(4,3,4));
        var runtime=new DevilsActors(h.getLevel(),()->f.director,new DevilsActors.Environment(){
            public List<ServerPlayer> participants(){return List.of(player);}
            public Optional<Vec3> spawnPoint(Slot slot,DevilsMob mob){return Optional.of(at);}
            public boolean contains(Zone zone,Vec3 feet){return true;}
            public Optional<Vec3> sepiksWarp(DevilsMob mob){return Optional.empty();}
        });
        TestCleanup.register(h,runtime::close);
        check(h,runtime.spawn(spawn),"Real Walker and retained BetterModel attach successfully");
        var root=runtime.actors().getFirst();
        var parts=h.getLevel().getEntitiesOfClass(DevilsMob.class,root.getBoundingBox().inflate(8),
                mob->mob.walkerPart()&&mob.damageOwner()==root);
        check(h,parts.size()==7,"Six leg proxies and one core");
        var leg=parts.stream().min(Comparator.comparingDouble(m->m.position().distanceToSqr(at.add(-3.1,.3,3)))).orElseThrow();
        var core=parts.stream().min(Comparator.comparingDouble(m->m.position().distanceToSqr(at.add(0,2.4,1.7)))).orElseThrow();
        check(h,Combat.damageOwner(leg)==root,"Perks resolve leg to root");
        float before=Combat.damagePool(leg);
        int sameTick=h.getLevel().getServer().getTickCount();
        try(var emission=Combat.emission(new Object())) {
            check(h,!Combat.damage(h.getLevel(),player,leg,40,Element.ARC),"Leg damage is not a kill");
            check(h,!Combat.damage(h.getLevel(),player,core,500,Element.ARC),"Same explosion cannot damage a second region");
        }
        check(h,Math.abs(Combat.damagePool(leg)-(before-40))<.001,"Combat measures actual leg loss");
        check(h,leg.getHealth()==leg.getMaxHealth(),"Proxy HP is not a second damage pool");
        try(var emission=Combat.emission(new Object())) {
            Combat.damage(h.getLevel(),player,leg,10,Element.ARC);
            try(var payload=Combat.emission(new Object())) {
                Combat.damage(h.getLevel(),player,leg,5,Element.ARC);
            }
            Combat.damage(h.getLevel(),player,leg,20,Element.ARC);
        }
        check(h,h.getLevel().getServer().getTickCount()==sameTick,"All emission checks execute in the same real server tick");
        check(h,Math.abs(Combat.damagePool(leg)-(before-55))<.001,
                "Distinct emissions and payload count independently; closing nested scope restores original dedup");
        root.walkerState().tick();
        check(h,!Combat.damage(h.getLevel(),player,leg,100,Element.ARC),"Leg break is not boss death");
        check(h,root.walkerState().phase()==DevilsWalkerState.Phase.STAGGER,"Leg break staggers");
        for(int i=0;i<DevilsWalkerState.STAGGER_TICKS;i++)root.walkerState().tick();
        check(h,core.precisionAt(core.position()),"Exposed core is precise");
        int defeated=f.director.snapshot().defeated();
        check(h,Combat.damage(h.getLevel(),player,core,2000,Element.ARC),"Core lethal hit reports root kill");
        check(h,root.isDeadOrDying(),"Root is dead");
        check(h,f.director.snapshot().defeated()==defeated+1,"Director credits exactly one boss death");
        check(h,parts.stream().allMatch(DevilsMob::isRemoved),"Death removes every proxy");
        check(h,!Combat.damage(h.getLevel(),player,core,2000,Element.ARC),"Stale proxy cannot award another kill");
        check(h,f.director.snapshot().defeated()==defeated+1,"Repeated hit cannot duplicate death");
    }
}
