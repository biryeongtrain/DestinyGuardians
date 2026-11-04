package kim.biryeong.destiny.campaign;

import kim.biryeong.destiny.campaign.RisingServices.FallenKind;
import kim.biryeong.destiny.campaign.RisingServices.Marker;
import net.minecraft.world.phys.Vec3;
import org.junit.jupiter.api.Test;

import java.util.*;

import static kim.biryeong.destiny.campaign.GuardianRisesProgress.Stage.*;
import static org.junit.jupiter.api.Assertions.*;

class RisingEncountersTest {
    static Marker m(String id, String... tags) {
        var map = new HashMap<String, String>();
        for (int i = 0; i + 1 < tags.length; i += 2) map.put(tags[i], tags[i + 1]);
        return new Marker(id, new Vec3(id.hashCode() % 50, 64, 0), 0, map);
    }

    /** Spawns succeed unless listed; records events so tests can kill or lose enemies. */
    static final class FakeSpawner implements RisingEncounters.Spawner {
        final Map<UUID, RisingEncounters.Events> live = new LinkedHashMap<>();
        final Map<UUID, RisingEncounters.Slot> slots = new HashMap<>();
        final Set<UUID> frozen = new HashSet<>();
        final List<UUID> discarded = new ArrayList<>();
        int failNext;
        @Override public UUID spawn(RisingEncounters.Slot slot, boolean active, RisingEncounters.Events events) {
            if (failNext > 0) { failNext--; return null; }
            UUID id = UUID.randomUUID();
            live.put(id, events);
            slots.put(id, slot);
            if (!active) frozen.add(id);
            return id;
        }
        @Override public void setActive(UUID id, boolean active) { if (active) frozen.remove(id); else frozen.add(id); }
        @Override public void discard(UUID id) {
            var events = live.remove(id);
            discarded.add(id);
            if (events != null) events.lost(id); // the Fallen service reports discards as lost
        }
        @Override public Optional<Vec3> position(UUID id) { return live.containsKey(id) ? Optional.of(slots.get(id).pos()) : Optional.empty(); }
        void kill(UUID id) { var e = live.remove(id); if (e != null) e.defeated(id); }
        void lose(UUID id) { var e = live.remove(id); if (e != null) e.lost(id); }
        void killAll() { for (UUID id : List.copyOf(live.keySet())) if (!frozen.contains(id)) kill(id); }
    }

    static GuardianRisesProgress at(GuardianRisesProgress.Stage stage) {
        var p = new GuardianRisesProgress(UUID.randomUUID());
        p.forceStage(stage);
        return p;
    }

    @Test void mapOrderTagSequencesEncountersInsteadOfNames() {
        var plan = RisingEncounters.plan(List.of(
                m("enemy.breach_chest.0", "kind", "dreg", "order", "3"),
                m("enemy.breach_first.0", "kind", "dreg", "order", "1"),
                m("enemy.breach_far.0", "kind", "dreg", "order", "2")));
        assertEquals(List.of("enemy.breach_first.0", "enemy.breach_far.0", "enemy.breach_chest.0"),
                plan.waves().stream().map(w -> w.get(0).markerId()).toList());
    }

    @Test void planGroupsEncountersInMarkerOrderAndWalkerLast() {
        var plan = RisingEncounters.plan(List.of(
                m("enemy.divide_walker.1", "kind", "walker"),
                m("enemy.divide_a.10", "kind", "vandal"), m("enemy.divide_a.2"), m("enemy.divide_a.1", "kind", "captain"),
                m("enemy.divide_b.1", "kind", "shank"),
                m("enemy.breach_dark.1"), m("trigger.walker_arena"), m("enemy.bad")));
        assertEquals(3, plan.waves().size());
        assertEquals(List.of("enemy.divide_a.1", "enemy.divide_a.2", "enemy.divide_a.10"),
                plan.waves().get(0).stream().map(RisingEncounters.Slot::markerId).toList());
        assertEquals(FallenKind.CAPTAIN, plan.waves().get(0).get(0).kind());
        assertEquals(FallenKind.DREG, plan.waves().get(0).get(1).kind(), "missing kind defaults to dreg");
        assertEquals(FallenKind.SHANK, plan.waves().get(1).get(0).kind());
        assertEquals(FallenKind.WALKER, plan.waves().get(2).get(0).kind());
        assertTrue(plan.hasWalker());
        assertEquals(1, RisingEncounters.decorations(List.of(m("enemy.breach_dark.1"), m("enemy.breach.1"))).size());
    }

    @Test void explicitWaveTagsAndActiveCap() {
        var markers = new ArrayList<Marker>();
        for (int i = 0; i < 40; i++) markers.add(m("enemy.dock_swarm." + i));
        markers.add(m("enemy.dock_late.1", "wave", "0"));
        var plan = RisingEncounters.plan(markers);
        assertEquals(List.of("enemy.dock_late.1"), plan.waves().get(0).stream().map(RisingEncounters.Slot::markerId).toList());
        assertEquals(RisingEncounters.MAX_ACTIVE, plan.waves().get(1).size());
    }

    @Test void wavesArriveOnlyWhenThinAndSealAfterFinalWave() {
        var progress = at(BREACH_FIGHT);
        var spawner = new FakeSpawner();
        var waves = new ArrayList<Integer>();
        var plan = RisingEncounters.plan(List.of(m("enemy.a.1"), m("enemy.a.2"), m("enemy.b.1"), m("enemy.b.2")));
        var run = new RisingEncounters.Run(progress, plan, spawner, new RisingEncounters.Cues() {
            @Override public void wave(int i, int total, boolean walker) { waves.add(i); }
        }, 0);
        run.tick(0);
        assertEquals(List.of(0), waves);
        assertEquals(2, run.alive());
        assertFalse(progress.sealed(), "not sealed before the final wave");
        for (int t = 1; t < 200; t++) run.tick(t);
        assertEquals(List.of(0), waves, "no timer-driven wave while the first wave is alive");
        var first = new ArrayList<>(spawner.live.keySet());
        spawner.kill(first.get(0));
        run.tick(200);
        assertEquals(List.of(0), waves, "small waves wait for the last enemy");
        spawner.kill(first.get(1));
        assertFalse(progress.encounterCleared(), "empty between waves is not cleared");
        run.tick(201);
        run.tick(201 + RisingEncounters.WAVE_DELAY);
        assertEquals(List.of(0, 1), waves);
        assertTrue(progress.sealed());
        assertFalse(run.cleared());
        spawner.killAll();
        assertTrue(run.cleared());
        assertEquals(4, run.defeated());
        assertTrue(progress.advance(progress.token()));
    }

    @Test void spawnFailureRetriesAndNeverClears() {
        var progress = at(SHIP_DEFENSE);
        var spawner = new FakeSpawner();
        spawner.failNext = 1;
        var failures = new ArrayList<Integer>();
        var run = new RisingEncounters.Run(progress, RisingEncounters.plan(List.of(m("enemy.dock.1"))), spawner,
                new RisingEncounters.Cues() { @Override public void spawnFailure(RisingEncounters.Slot s, int n) { failures.add(n); } }, 0);
        run.tick(0);
        assertEquals(List.of(1), failures);
        assertFalse(progress.sealed(), "a failed mandatory spawn must not seal");
        assertFalse(run.cleared());
        run.tick(RisingEncounters.RETRY_DELAY);
        assertEquals(1, run.alive());
        assertTrue(progress.sealed());
        spawner.killAll();
        assertTrue(run.cleared());
    }

    @Test void lostEnemyRespawnsAndKeepsEncounterOpen() {
        var progress = at(DIVIDE_WALKER);
        var spawner = new FakeSpawner();
        var run = new RisingEncounters.Run(progress, RisingEncounters.plan(List.of(m("enemy.walker.1", "kind", "walker"))), spawner, null, 0);
        run.tick(0);
        UUID walker = spawner.live.keySet().iterator().next();
        spawner.lose(walker);
        assertEquals(1, progress.enemiesRemaining(), "lost enemy is still owed");
        assertFalse(run.cleared());
        run.tick(10);
        assertEquals(0, run.alive());
        run.tick(10 + RisingEncounters.RESPAWN_DELAY);
        assertEquals(1, run.alive());
        UUID replacement = spawner.live.keySet().iterator().next();
        assertNotEquals(walker, replacement);
        assertEquals(FallenKind.WALKER, spawner.slots.get(replacement).kind());
        spawner.kill(replacement);
        assertTrue(run.cleared());
    }

    @Test void restartMakesOldCallbacksStale() {
        var progress = at(BREACH_FIGHT);
        var spawner = new FakeSpawner();
        var run = new RisingEncounters.Run(progress, RisingEncounters.plan(List.of(m("enemy.a.1"), m("enemy.a.2"))), spawner, null, 0);
        run.tick(0);
        var old = new ArrayList<>(spawner.live.entrySet());
        progress.restartCheckpoint();
        assertEquals(ARM_YOURSELF, progress.stage());
        run.discard();
        assertEquals(2, spawner.discarded.size());
        // A late kill from the previous generation must not touch the new encounter.
        assertTrue(progress.advance(progress.token()));
        var fresh = new RisingEncounters.Run(progress, RisingEncounters.plan(List.of(m("enemy.a.1"), m("enemy.a.2"))), spawner, null, 1);
        fresh.tick(1);
        old.get(0).getValue().defeated(old.get(0).getKey());
        old.get(1).getValue().lost(old.get(1).getKey());
        assertEquals(2, progress.enemiesRemaining());
        assertEquals(0, fresh.defeated());
        assertFalse(run.current());
    }

    @Test void decorationsAreFrozenAndUntracked() {
        var progress = at(BREACH_DARK);
        var spawner = new FakeSpawner();
        var decor = new RisingEncounters.Decor(spawner, RisingEncounters.decorations(List.of(m("enemy.breach_dark.1"), m("enemy.breach_dark.2"))));
        assertEquals(2, decor.size());
        assertEquals(2, spawner.frozen.size());
        assertEquals(0, progress.enemiesRemaining());
        decor.discard();
        decor.discard();
        assertEquals(2, spawner.discarded.size());
    }

    @Test void skiffCuesLeadEachReinforcementWaveAndNeverBlockSpawns() {
        var progress = at(BREACH_FIGHT);
        var spawner = new FakeSpawner();
        var log = new ArrayList<String>();
        var plan = RisingEncounters.plan(List.of(m("enemy.a.1"), m("enemy.b.1"), m("enemy.b.2"), m("enemy.c.1")));
        var run = new RisingEncounters.Run(progress, plan, spawner, new RisingEncounters.Cues() {
            @Override public void incoming(int i, int total, List<RisingEncounters.Slot> wave, int ticks) {
                log.add("in" + i + "/" + ticks); throw new IllegalStateException("presentation bug");
            }
            @Override public void spawned(int i, int total, List<RisingEncounters.Slot> wave) {
                log.add("sp" + i + "/" + wave.size()); throw new IllegalStateException("presentation bug");
            }
        }, 0);
        run.tick(0);
        assertEquals(List.of("sp0/1"), log, "the opening wave has no incoming lead");
        assertEquals(1, run.alive(), "a throwing cue does not undo the spawn");
        spawner.killAll();
        run.tick(10);
        assertEquals(List.of("sp0/1", "in1/" + RisingEncounters.WAVE_DELAY), log);
        run.tick(11);
        assertEquals(2, log.size(), "incoming fires once per thin period");
        run.tick(10 + RisingEncounters.WAVE_DELAY);
        assertEquals("sp1/2", log.get(2));
        assertEquals(2, run.alive());
        assertEquals(2, run.wavesSpawned());
    }
}
