package kim.biryeong.destiny.strike.devils;

import org.junit.jupiter.api.Test;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.function.Predicate;

import static kim.biryeong.destiny.strike.devils.DevilsDirector.*;
import static kim.biryeong.destiny.strike.devils.DevilsPlan.*;
import static org.junit.jupiter.api.Assertions.*;

class DevilsDirectorTest {
    static final class Fixture implements Host {
        final DevilsDirector director = new DevilsDirector(this);
        final Map<String, Spawn> live = new LinkedHashMap<>();
        final List<Spawn> spawns = new ArrayList<>();
        final Map<Cue, Long> cues = new LinkedHashMap<>();
        final Map<Long, Integer> spawnCallsPerTick = new HashMap<>();
        final Map<String, Long> packArrivals = new LinkedHashMap<>();
        final List<ActorRef> retired = new ArrayList<>();
        final List<String> resets = new ArrayList<>();
        final List<String> problems = new ArrayList<>();
        Predicate<Spawn> reject = s -> false;
        boolean deferred, managedTelegraphs;
        @Override public boolean managesSpawnTelegraphs() { return managedTelegraphs; }
        int retryTicks = 1;
        @Override public int spawnRetryTicks(ActorRef actor) { return retryTicks; }
        @Override public boolean spawnDeferred(ActorRef actor) { return deferred; }
        boolean finishCues = true, available = true, finishIntro = true;
        int completionCount, incomingCount;
        @Override public boolean spawn(Spawn spawn) {
            spawnCallsPerTick.merge(director.snapshot().tick(), 1, Integer::sum);
            if (reject.test(spawn)) return false;
            assertNull(live.put(spawn.slot().id(), spawn), "duplicate live slot");
            spawns.add(spawn);
            if (spawn.slot().ordinary()) packArrivals.putIfAbsent(spawn.slot().packId(), director.snapshot().tick());
            return true;
        }
        @Override public void retire(ActorRef ref, Retirement reason) {
            Spawn current = live.get(ref.slotId());
            if (current != null && current.ref().equals(ref)) live.remove(ref.slotId());
            retired.add(ref);
            // Actual entity discard emits lost synchronously: generation/state must already invalidate it.
            director.lost(ref, 1);
        }
        @Override public CuePlayback cue(Cue cue) {
            cues.put(cue, director.snapshot().tick() + 10);
            return available ? CuePlayback.playing(10) : CuePlayback.unavailable();
        }
        @Override public void cancelGeneration(long generation) { cues.keySet().removeIf(c -> c.generation() == generation); }
        @Override public void incoming(long generation, List<Slot> slots, int ticks) { incomingCount++; }
        @Override public void checkpointReset(Zone zone, long generation, String reason) { resets.add(reason); }
        @Override public void completed(long generation) { completionCount++; }
        @Override public void problem(String problem) { problems.add(problem); }
        void tick() {
            director.tick();
            if (finishCues && available && !director.snapshot().paused()) {
                for (var e : List.copyOf(cues.entrySet())) if (director.snapshot().tick() >= e.getValue()) {
                    cues.remove(e.getKey()); director.cueFinished(e.getKey());
                }
            }
            if (finishIntro && director.phase() == Phase.SP_INTRO && director.snapshot().phaseTicks() >= 80)
                director.introFinished(director.generation());
            Snapshot s = director.snapshot();
            if (s.phase() != Phase.CLOSED) {
                assertTrue(s.occupied() <= s.zone().actorCap(), s.toString());
                assertTrue(s.activePacks() <= s.zone().packCap(), s.toString());
            }
        }
        void ticks(int count) { for (int i = 0; i < count; i++) tick(); }
        void kill(String id) {
            Spawn spawn = live.remove(id);
            if (spawn != null) director.defeated(spawn.ref());
        }
        void killWhere(Predicate<Spawn> filter) {
            for (Spawn spawn : List.copyOf(live.values())) if (filter.test(spawn)) kill(spawn.slot().id());
        }
        void ordinary() { killWhere(s -> s.slot().ordinary()); }
        void until(Phase phase, int bound, boolean killOrdinary) {
            for (int i = 0; i < bound && director.phase() != phase; i++) {
                tick();
                if (killOrdinary) ordinary();
            }
            assertEquals(phase, director.phase());
        }
        void refinery() {
            assertTrue(director.begin(3)); until(Phase.RY_CLEAR, 2000, true);
            assertTrue(director.arrive(Zone.RF));
        }
        void blast() {
            refinery(); until(Phase.RF_DEVICE, 1000, true);
            for (int i = 0; i < 100 && !director.snapshot().deviceReady(); i++) tick();
            assertTrue(director.interact());
            until(Phase.RF_CLEAR, 5000, true);
            assertTrue(director.arrive(Zone.BL));
        }
        void lair() {
            blast(); ticks(160); ordinary();
            kill("BL-walker"); kill("BL-brig-1"); kill("BL-brig-2");
            assertEquals(Phase.BL_CLEAR, director.phase());
            assertTrue(director.arrive(Zone.SP));
            until(Phase.SP_DAMAGE1, 1500, true);
        }
        Spawn sepiks() { return live.get("SP-sepiks"); }
        void shield(int index) {
            Spawn boss = sepiks();
            double hp = director.snapshot().sepiksHealth();
            double applied = director.allowedDamage(boss.ref(), hp, 99999);
            director.healthChanged(boss.ref(), hp - applied);
            assertEquals(index == 1 ? Phase.SP_SHIELD1 : Phase.SP_SHIELD2, director.phase());
        }
        void servitors() { killWhere(s -> s.slot().kind() == Kind.SERVITOR); }
    }

    @Test void smallerFireteamsKeepTheSameOpeningEncounter() {
        for (int count = 1; count <= 3; count++) {
            var f = new Fixture();
            assertTrue(f.director.begin(count));
            f.ticks(600);
            assertEquals(24, f.live.size());
            assertEquals(Phase.RY_APPROACH, f.director.phase());
        }
    }

    @Test void admissionAllowsOneToThreeAndAudioMustComplete() {
        var f = new Fixture(); f.finishCues = false;
        for (int count : new int[]{-1, 0, 4}) assertFalse(f.director.begin(count));
        assertTrue(f.director.begin(3)); assertFalse(f.director.begin(3));
        f.ticks(100);
        assertEquals(Phase.BRIEFING, f.director.phase());
        assertTrue(f.spawns.isEmpty());
        f.director.cueFinished(f.cues.keySet().iterator().next());
        assertEquals(Phase.RY_APPROACH, f.director.phase());
    }

    @Test void fullPackReservationTelegraphsAndNeverExceedsTwoSpawnsPerTick() {
        var f = new Fixture(); f.director.begin(3);
        f.until(Phase.RY_APPROACH, 100, false);
        f.tick();
        assertEquals(8, f.director.snapshot().reserved());
        assertEquals(0, f.director.snapshot().live());
        f.ticks(39); assertTrue(f.spawns.isEmpty());
        f.tick(); assertEquals(2, f.spawns.size());
        f.ticks(400); assertEquals(24, f.live.size());
        assertEquals(0, f.director.snapshot().defeated());
        assertTrue(f.spawnCallsPerTick.values().stream().allMatch(n -> n <= 2));
        f.ordinary(); assertEquals(Phase.RY_CLEAR, f.director.phase());
    }

    @Test void lostReusesSlotHealthAndIgnoresOldIncarnationDeath() {
        var f = new Fixture(); f.director.begin(3); f.ticks(60);
        Spawn original = f.live.values().iterator().next();
        f.live.remove(original.slot().id());
        f.director.lost(original.ref(), 7, 0);
        assertEquals(0, f.director.snapshot().defeated());
        f.director.defeated(original.ref());
        f.ticks(41);
        Spawn replacement = f.live.get(original.slot().id());
        assertNotNull(replacement); assertEquals(7, replacement.health());
        assertNotEquals(original.ref(), replacement.ref());
        f.director.defeated(original.ref());
        assertEquals(0, f.director.snapshot().defeated());
        f.kill(original.slot().id()); assertEquals(1, f.director.snapshot().defeated());
    }

    @Test void boundedSearchDeferralsKeepReservationsAndDoNotResetCheckpoint() {
        var f = new Fixture(); f.reject = s -> true; f.deferred = true; f.director.begin(3);
        long generation = f.director.generation();
        f.ticks(160);
        assertEquals(generation, f.director.generation());
        assertTrue(f.resets.isEmpty());
        assertEquals(0, f.director.snapshot().defeated());
        assertEquals(8, f.director.snapshot().reserved());
        assertTrue(f.director.snapshot().slots().stream().allMatch(s -> s.failures() == 0));
        f.deferred = false; f.reject = s -> false; f.ticks(20);
        assertEquals(8, f.live.size());
        assertTrue(f.spawnCallsPerTick.values().stream().allMatch(n -> n <= 2));
    }

    @Test void threePlacementFailuresResetWithoutFakeKills() {
        var f = new Fixture(); f.reject = s -> true; f.director.begin(3);
        long generation = f.director.generation();
        f.ticks(160);
        assertTrue(f.director.generation() > generation);
        assertEquals(1, f.resets.size());
        assertEquals(0, f.director.snapshot().defeated());
        assertTrue(f.spawns.isEmpty());
    }

    @Test void refineryHas112FiniteActorsAndEightyEightRealDefenseKills() {
        var f = new Fixture(); f.refinery();
        f.until(Phase.RF_DEVICE, 1000, true);
        assertFalse(f.director.interact(), "barrier notice has not completed");
        f.ticks(10); assertTrue(f.director.interact()); assertFalse(f.director.interact());
        f.until(Phase.RF_CLEAR, 5000, true);
        assertEquals(112, f.spawns.stream().filter(s -> s.slot().zone() == Zone.RF).count());
        assertEquals(112, f.director.snapshot().defeated());
        assertEquals(88, f.director.snapshot().defenseDefeated());
        int old = f.spawns.size(); f.ticks(500); assertEquals(old, f.spawns.size());
        assertFalse(f.director.arrive(Zone.SP));
    }

    @Test void intermissionWaitsForBothVoiceAndEightSeconds() {
        var f = new Fixture(); f.refinery(); f.until(Phase.RF_DEVICE, 1000, true); f.ticks(10);
        assertTrue(f.director.interact()); f.until(Phase.RF_INTERMISSION1, 1500, true);
        f.finishCues = false; f.ticks(170);
        assertEquals(Phase.RF_INTERMISSION1, f.director.phase());
        Cue first = f.cues.keySet().stream().filter(c -> c.lineId().equals("80b59f25")).findFirst().orElseThrow();
        f.director.cueFinished(first);
        Cue second = f.cues.keySet().stream().filter(c -> c.lineId().equals("80b59f20")).findFirst().orElseThrow();
        f.director.cueFinished(second); f.tick();
        assertEquals(Phase.RF_DEFENSE2, f.director.phase());
    }

    @Test void unavailableVoiceHasExplicitFallbackButValidTimeoutResets() {
        var f = new Fixture(); f.available = false; f.director.begin(3); f.ticks(59);
        assertEquals(Phase.BRIEFING, f.director.phase()); f.tick();
        assertEquals(Phase.RY_APPROACH, f.director.phase());
        var stalled = new Fixture(); stalled.finishCues = false; stalled.director.begin(3);
        Cue old = stalled.cues.keySet().iterator().next(); stalled.ticks(210);
        assertEquals(1, stalled.resets.size()); assertEquals(Phase.BRIEFING, stalled.director.phase());
        stalled.director.cueFinished(old); assertEquals(Phase.BRIEFING, stalled.director.phase());
        assertTrue(stalled.spawns.isEmpty());
    }

    @Test void checkpointInvalidatesLateDeathsVoicesAndDiscardCallbacks() {
        var f = new Fixture(); f.refinery(); f.ticks(50);
        var old = List.copyOf(f.live.values());
        long generation = f.director.generation();
        f.director.resetCheckpoint("test wipe");
        assertEquals(generation + 1, f.director.generation());
        assertEquals(Phase.RF_ENTRY, f.director.phase());
        for (Spawn spawn : old) { f.director.defeated(spawn.ref()); f.director.lost(spawn.ref(), 1); }
        assertEquals(0, f.director.snapshot().defeated());
        assertTrue(f.live.isEmpty());
        assertEquals(1, f.resets.size());
        f.ticks(50); assertFalse(f.live.isEmpty());
    }

    @Test void blastThresholdsAreFiniteFifoAndBossDeathCancelsPendingPacks() {
        var f = new Fixture(); f.blast(); f.ticks(180);
        Spawn walker = f.live.get("BL-walker");
        for (int i = 0; i < 10; i++) f.director.healthChanged(walker.ref(), Kind.WALKER.health() * 3 / 16);
        f.kill("BL-brig-1"); f.kill("BL-brig-2");
        f.ticks(500); // backlog waits for whole-pack capacity
        assertTrue(f.director.snapshot().pendingPacks() > 0);
        assertTrue(f.director.snapshot().occupied() <= 32);
        f.kill("BL-walker");
        assertEquals(Phase.BL_CLEAR, f.director.phase());
        assertEquals(0, f.director.snapshot().pendingPacks());
        assertEquals(0, f.director.snapshot().occupied());
        int old = f.spawns.size(); f.ticks(1000); assertEquals(old, f.spawns.size());
        assertEquals(3, f.director.snapshot().defeated(), "neutral retreats cannot count as kills");
    }

    @Test void sepiksClampsBothThresholdsAndOnlyActualFinalDeathCompletes() {
        var f = new Fixture(); f.lair();
        assertEquals(181.5, f.director.allowedDamage(f.sepiks().ref(), 550, 10000), 1e-6);
        f.shield(1); assertEquals(368.5, f.director.snapshot().sepiksHealth(), 1e-6);
        assertEquals(0, f.director.allowedDamage(f.sepiks().ref(), 368.5, 500));
        f.ticks(30); assertEquals(3, f.director.snapshot().shieldServitors());
        f.servitors(); assertEquals(Phase.SP_RECOVER1, f.director.phase());
        f.ticks(39); assertEquals(Phase.SP_RECOVER1, f.director.phase()); f.tick();
        assertEquals(Phase.SP_DAMAGE2, f.director.phase());
        f.shield(2); assertEquals(181.5, f.director.snapshot().sepiksHealth(), 1e-6);
        f.ticks(30); f.servitors(); f.ticks(40);
        assertEquals(Phase.SP_DAMAGE3, f.director.phase());
        Spawn boss = f.sepiks(); f.director.healthChanged(boss.ref(), 0);
        assertEquals(0, f.completionCount);
        f.kill("SP-sepiks"); assertEquals(Phase.COMPLETE, f.director.phase());
        assertEquals(1, f.completionCount); f.director.defeated(boss.ref());
        assertEquals(1, f.completionCount); assertEquals(0, f.director.snapshot().occupied());
    }

    @Test void shieldSlotsRemainAvailableWithSurvivingNormalPacks() {
        var f = new Fixture(); f.lair(); f.ticks(180);
        f.shield(1); f.ticks(180);
        assertEquals(16, f.live.values().stream().filter(s -> s.slot().ordinary()).count());
        f.servitors(); f.ticks(40); f.shield(2); f.ticks(60);
        assertEquals(3, f.director.snapshot().shieldServitors());
        assertTrue(f.director.snapshot().occupied() <= 24);
        assertTrue(f.director.snapshot().pendingPacks() > 0);
        f.servitors(); f.ticks(40); assertEquals(Phase.SP_DAMAGE3, f.director.phase());
    }

    @Test void pauseFreezesTimersAndCloseIsIdempotent() {
        var f = new Fixture(); f.director.begin(3); f.ticks(60);
        long clock = f.director.snapshot().tick(); int spawns = f.spawns.size();
        f.director.pause(true); f.ticks(1000);
        assertEquals(clock, f.director.snapshot().tick()); assertEquals(spawns, f.spawns.size());
        f.director.pause(false); f.tick(); assertEquals(clock + 1, f.director.snapshot().tick());
        f.director.close(); int retired = f.retired.size(); f.director.close();
        assertEquals(retired, f.retired.size()); assertTrue(f.live.isEmpty());
        assertEquals(Phase.CLOSED, f.director.phase()); assertEquals(0, f.completionCount);
    }

    @Test void repeatedLossesResetAndNeverTurnIntoSuccess() {
        var f = new Fixture(); f.director.begin(3); f.ticks(60);
        String id = f.live.keySet().iterator().next(); long generation = f.director.generation();
        for (int n = 0; n < 3; n++) {
            Spawn s = f.live.remove(id); assertNotNull(s);
            f.director.lost(s.ref(), 5);
            if (n < 2) f.ticks(41);
        }
        assertEquals(generation + 1, f.director.generation());
        assertEquals(0, f.director.snapshot().defeated());
        assertEquals(Phase.BRIEFING, f.director.phase());
    }

    @Test void fullOptionalRouteSpawnsExactlyThe258PlannedSlotsOnce() {
        var f = new Fixture(); f.blast(); f.ticks(30);
        Spawn walker = f.live.get("BL-walker");
        f.director.healthChanged(walker.ref(), Kind.WALKER.health() * 3 / 16);
        f.kill("BL-brig-1"); f.kill("BL-brig-2");
        for (int i = 0; i < 1800; i++) { f.tick(); f.ordinary(); }
        assertEquals(59, f.spawns.stream().filter(s -> s.slot().zone() == Zone.BL).count());
        f.kill("BL-walker"); assertTrue(f.director.arrive(Zone.SP));
        f.until(Phase.SP_DAMAGE1, 1500, true);
        for (int shield = 1; shield <= 2; shield++) {
            for (int i = 0; i < 250; i++) { f.tick(); f.ordinary(); }
            f.shield(shield);
            for (int i = 0; i < 250; i++) { f.tick(); f.ordinary(); }
            f.servitors(); f.ticks(40);
        }
        for (int i = 0; i < 250; i++) { f.tick(); f.ordinary(); }
        f.kill("SP-sepiks");
        assertEquals(258, f.spawns.size());
        assertEquals(258, f.spawns.stream().map(s -> s.slot().id()).distinct().count());
        assertEquals(1, f.completionCount);
        assertEquals(0, f.resets.size());
        assertTrue(f.spawnCallsPerTick.values().stream().allMatch(n -> n <= 2));
    }

    @Test void cancelledRequiredCueAndIncompleteAwakeningNeverAdvance() {
        var f = new Fixture(); f.director.begin(3);
        Cue original = f.cues.keySet().iterator().next();
        f.director.cueCancelled(original);
        assertEquals(1, f.resets.size());
        f.director.cueFinished(original);
        assertEquals(Phase.BRIEFING, f.director.phase());
        var boss = new Fixture(); boss.blast(); boss.ticks(160);
        boss.kill("BL-walker"); boss.kill("BL-brig-1"); boss.kill("BL-brig-2");
        boss.director.arrive(Zone.SP); boss.finishIntro = false;
        boss.until(Phase.SP_INTRO, 1000, true);
        long generation = boss.director.generation();
        boss.ticks(280);
        assertEquals(generation + 1, boss.director.generation());
        assertEquals(Phase.SP_GUARD, boss.director.phase());
        assertFalse(boss.director.introFinished(generation));
        assertEquals(0, boss.completionCount);
    }

    @Test void blockedFirstArrivalDoesNotCompressTheNextReinforcementGap() {
        var f = new Fixture(); f.refinery();
        f.until(Phase.RF_DEVICE, 1000, true); f.ticks(10); f.director.interact();
        f.until(Phase.RF_DEFENSE1, 100, false);
        long start = f.director.snapshot().tick();
        f.reject = s -> s.slot().id().startsWith("RF-defense1-1/") && f.director.snapshot().tick() < start + 80;
        for (int i = 0; i < 500; i++) { f.tick(); f.ordinary(); }
        long first = f.packArrivals.get("RF-defense1-1"), second = f.packArrivals.get("RF-defense1-2");
        assertTrue(second - first >= REINFORCEMENT_GAP, "actual arrivals: " + first + ", " + second);
        assertTrue(f.resets.isEmpty());
    }
    @Test void occupiedPadsWaitWithoutResetOrStarvingOtherReservedActors() {
        var f = new Fixture();
        f.reject = spawn -> spawn.slot().index() < 2;
        f.deferred = true; f.retryTicks = 10;
        f.director.begin(3); f.ticks(400);
        assertTrue(f.resets.isEmpty());
        assertTrue(f.spawns.size() >= 6, "Blocked first slots must let later reservations proceed");
        assertTrue(f.spawns.stream().noneMatch(spawn -> spawn.slot().index() < 2));
        assertTrue(f.spawnCallsPerTick.values().stream().allMatch(n -> n <= 2));
        f.reject = spawn -> false; f.deferred = false; f.ticks(40);
        assertTrue(f.spawns.stream().anyMatch(spawn -> spawn.slot().index() < 2));
        assertTrue(f.resets.isEmpty());
        assertEquals(f.spawns.size(), f.spawns.stream().map(spawn -> spawn.slot().id()).distinct().count());
    }

    @Test void oneTickSearchDeferralsCannotMonopolizeTheSpawnBudget() {
        var f = new Fixture();
        f.reject = spawn -> spawn.slot().index() < 2;
        f.deferred = true; f.retryTicks = 1; f.managedTelegraphs = true;
        f.director.begin(3); f.ticks(30);
        assertTrue(f.spawns.size() >= 6, "Resumable searches at the front must not starve clear later pads");
        assertTrue(f.spawns.stream().noneMatch(spawn -> spawn.slot().index() < 2));
        assertTrue(f.spawnCallsPerTick.values().stream().allMatch(n -> n <= SPAWNS_PER_TICK));
        assertTrue(f.resets.isEmpty());
        f.reject = spawn -> false; f.deferred = false; f.ticks(10);
        assertEquals(8, f.spawns.size());
        assertEquals(8, f.spawns.stream().map(spawn -> spawn.slot().id()).distinct().count());
        assertTrue(f.resets.isEmpty());
    }

    @Test void selectedPadHostStartsWarningWithoutDoubleReservationDelayAndPauseFreezesIt() {
        var f = new Fixture(); f.managedTelegraphs = true; f.deferred = true; f.retryTicks = 20;
        var readyAt = new HashMap<String, Long>();
        f.reject = spawn -> f.director.snapshot().tick() < readyAt.computeIfAbsent(spawn.slot().id(),
                ignored -> f.director.snapshot().tick() + TELEGRAPH_TICKS);
        f.director.begin(3); f.ticks(20);
        assertFalse(readyAt.isEmpty(), "Placement starts before the old reservation countdown finishes");
        assertTrue(f.spawns.isEmpty(), "No actor is live during its selected-pad warning");
        long clock = f.director.snapshot().tick();
        f.director.pause(true); f.ticks(100);
        assertEquals(clock, f.director.snapshot().tick()); assertTrue(f.spawns.isEmpty());
        f.director.pause(false);
        long first = readyAt.values().stream().mapToLong(Long::longValue).min().orElseThrow();
        f.ticks((int)(first-f.director.snapshot().tick()-1));
        assertTrue(f.spawns.isEmpty()); f.tick(); assertFalse(f.spawns.isEmpty());
        assertTrue(f.resets.isEmpty());
    }

}
