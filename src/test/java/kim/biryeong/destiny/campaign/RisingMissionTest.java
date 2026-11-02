package kim.biryeong.destiny.campaign;

import kim.biryeong.destiny.campaign.GuardianRisesProgress.Stage;
import kim.biryeong.destiny.campaign.RisingServices.Handle;
import kim.biryeong.destiny.campaign.RisingServices.Marker;
import kim.biryeong.destiny.campaign.RisingServices.Zone;
import net.minecraft.world.phys.Vec3;
import org.junit.jupiter.api.Test;

import java.util.*;

import static kim.biryeong.destiny.campaign.GuardianRisesProgress.Stage.*;
import static org.junit.jupiter.api.Assertions.*;

class RisingMissionTest {
    static class FakeHandle implements Handle {
        final Runnable done;
        boolean closed, fired;
        FakeHandle(Runnable done) { this.done = done; }
        void finish() { if (!fired) { fired = true; done.run(); } }
        @Override public boolean finished() { return fired; }
        @Override public void close() { closed = true; finish(); }
    }

    static final class FakePickup extends FakeHandle implements RisingServices.PickupHandle {
        final String kind;
        boolean collected;
        FakePickup(String kind) { super(() -> { }); this.kind = kind; }
        @Override public void collect() { collected = true; close(); }
    }

    static final class FakeHost implements RisingMission.Host {
        final EnumMap<Zone, List<Marker>> markers = new EnumMap<>(Zone.class);
        final EnumSet<Zone> ready = EnumSet.allOf(Zone.class);
        final List<String> voices = new ArrayList<>();
        final List<String> placed = new ArrayList<>();
        final List<String> problems = new ArrayList<>();
        final RisingEncountersTest.FakeSpawner spawner = new RisingEncountersTest.FakeSpawner();
        boolean presentation = true;
        Vec3 pos = Vec3.ZERO;
        Zone zone;
        FakeHandle opening, scan, departure;
        final List<FakeHandle> ships = new ArrayList<>();
        int rifles, shotguns, finishCalls, saves;
        boolean holding, finishOk = true, music;
        int musicCalls;

        FakeHost() {
            add(Zone.GATEWAY, "spawn.player", 0, 0);
            add(Zone.GATEWAY, "trigger.wall", 40, 0);
            add(Zone.GATEWAY, "exit.breach", 50, 0);
            add(Zone.BREACH, "spawn.player", 0, 0);
            add(Zone.BREACH, "trigger.breach_dark", 10, 0);
            add(Zone.BREACH, "enemy.breach_dark.1", 15, 5);
            add(Zone.BREACH, "trigger.rifle", 20, 0);
            add(Zone.BREACH, "prop.rifle", 24, 0);
            add(Zone.BREACH, "checkpoint.arm_yourself", 21, 0);
            add(Zone.BREACH, "enemy.breach_catwalks.1", 40, 5);
            add(Zone.BREACH, "enemy.breach_catwalks.2", 42, 5);
            add(Zone.BREACH, "prop.shotgun_cache", 60, 0);
            add(Zone.BREACH, "exit.divide", 80, 0);
            add(Zone.DIVIDE, "checkpoint.divide_walker", 0, 0);
            add(Zone.DIVIDE, "trigger.walker_arena", 30, 0);
            add(Zone.DIVIDE, "enemy.divide_fallen.1", 40, 0, "kind", "vandal");
            add(Zone.DIVIDE, "enemy.divide_walker.1", 50, 0, "kind", "walker");
            add(Zone.DIVIDE, "exit.dock13", 90, 0);
            add(Zone.DOCK13, "checkpoint.dock_13", 0, 0);
            add(Zone.DOCK13, "trigger.ship", 30, 0);
            add(Zone.DOCK13, "prop.ship", 34, 0);
            add(Zone.DOCK13, "enemy.dock_a.1", 40, 0);
            add(Zone.DOCK13, "enemy.dock_b.1", 45, 0);
        }
        void add(Zone z, String id, double x, double zz, String... tags) {
            var map = new HashMap<String, String>();
            for (int i = 0; i + 1 < tags.length; i += 2) map.put(tags[i], tags[i + 1]);
            markers.computeIfAbsent(z, k -> new ArrayList<>()).add(new Marker(id, new Vec3(x + z.ordinal() * 1000, 64, zz), 0, map));
        }
        void moveTo(Zone z, String id) { pos = marker(z, id).orElseThrow().pos(); }

        @Override public Optional<Marker> marker(Zone z, String id) {
            return markers.getOrDefault(z, List.of()).stream().filter(m -> m.id().equals(id)).findFirst();
        }
        @Override public List<Marker> markers(Zone z, String prefix) {
            return markers.getOrDefault(z, List.of()).stream().filter(m -> m.id().startsWith(prefix)).toList();
        }
        @Override public Vec3 position() { return pos; }
        @Override public boolean zoneReady(Zone z) { return ready.contains(z); }
        @Override public void prepareZone(Zone z) { }
        @Override public void place(Zone z, Marker anchor) { zone = z; pos = anchor.pos(); placed.add(z + ":" + anchor.id()); }
        @Override public int voice(String id) { voices.add(id); return 20; }
        @Override public Handle openingScan(Runnable done) { return presentation ? opening = new FakeHandle(done) : null; }
        @Override public Handle ghostScan(Vec3 target, int ticks, Runnable done) { return presentation ? scan = new FakeHandle(done) : null; }
        @Override public Handle departure(Vec3 p, float yaw, Runnable done) { return presentation ? departure = new FakeHandle(done) : null; }
        @Override public Handle shipProp(Vec3 p, float yaw) {
            if (!presentation) return null;
            var h = new FakeHandle(() -> { });
            ships.add(h);
            return h;
        }
        final List<FakePickup> pickups = new ArrayList<>();
        @Override public RisingServices.PickupHandle pickup(Vec3 p, float yaw, String kind) {
            if (!presentation) return null;
            var h = new FakePickup(kind);
            pickups.add(h);
            return h;
        }
        List<String> openPickups() { return pickups.stream().filter(h -> !h.closed).map(h -> h.kind).toList(); }
        long openShips() { return ships.stream().filter(h -> !h.closed).count(); }
        @Override public void grantRifle() { rifles++; holding = true; }
        @Override public void grantShotgun() { shotguns++; }
        @Override public boolean ownsRifle() { return rifles > 0; }
        @Override public boolean holdingRifle() { return holding; }
        @Override public RisingEncounters.Spawner spawner(Zone z) { return spawner; }
        @Override public boolean finish() { finishCalls++; return finishOk; }
        @Override public void startMusic() { music = true; musicCalls++; }
        @Override public void notice(String text) { }
        @Override public void problem(String text) { problems.add(text); }
        @Override public void saved() { saves++; }
    }

    int now;
    void run(RisingMission m, int ticks) { for (int i = 0; i < ticks; i++) m.tick(++now); }
    void until(RisingMission m, Stage stage, int max) {
        for (int i = 0; i < max && m.stage() != stage; i++) m.tick(++now);
        assertEquals(stage, m.stage());
    }
    static RisingMission fresh(FakeHost host) {
        return new RisingMission(UUID.randomUUID(), new RisingMission.Saved(
                new GuardianRisesProgress.Snapshot(GHOST_SCAN, false, false), false, false), host);
    }
    void fightAll(RisingMission m, FakeHost host, int max) {
        for (int i = 0; i < max && m.stage().ordinal() < DEPARTURE.ordinal() && host.spawner.live.size() + m.progress().enemiesRemaining() >= 0; i++) {
            Stage before = m.stage();
            host.spawner.killAll();
            m.tick(++now);
            if (m.stage() != before) return;
        }
    }

    @Test void fullMissionOpensInDarknessAndEndsAtTowerOnce() {
        var host = new FakeHost();
        var m = fresh(host);
        m.begin(now);
        run(m, 2);
        assertEquals(List.of("GATEWAY:spawn.player"), host.placed);
        assertNotNull(host.opening, "opening scan starts after placement");
        assertTrue(host.music);
        assertEquals(GHOST_SCAN, m.stage());
        host.opening.finish();
        run(m, 1);
        assertEquals(GATEWAY, m.stage());
        run(m, 140);
        assertEquals(List.of("80b75f64", "80b75f60"),
                host.voices.stream().filter(v -> List.of("80b75f64", "80b75f60").contains(v)).toList());

        host.moveTo(Zone.GATEWAY, "exit.breach");
        until(m, BREACH_DARK, 5);
        run(m, 2);
        assertEquals("BREACH:spawn.player", host.placed.getLast());
        assertEquals(1, host.spawner.frozen.size(), "silhouettes stay frozen");

        assertEquals(List.of("rifle"), host.openPickups(), "rifle marker visible in the dark corridor");
        host.moveTo(Zone.BREACH, "trigger.rifle");
        run(m, 2);
        assertNotNull(host.scan);
        host.scan.finish();
        until(m, ARM_YOURSELF, 3);
        assertEquals(0, host.rifles);
        assertEquals(0, host.spawner.live.size() - 1, "no hostile spawn before the rifle");
        host.moveTo(Zone.BREACH, "prop.rifle");
        until(m, BREACH_FIGHT, 120);
        assertEquals(1, host.rifles);
        assertEquals(1, host.pickups.size(), "one rifle marker from BREACH_DARK through ARM_YOURSELF");
        assertTrue(host.pickups.getFirst().collected, "taking the rifle plays the pickup effect");
        assertEquals(List.of(), host.openPickups());
        run(m, 1);
        assertTrue(host.spawner.discarded.size() >= 1, "silhouettes removed when the fight starts");
        assertEquals(2, m.progress().enemiesRemaining());
        fightAll(m, host, 10);
        assertEquals(SUPPLY_CACHE, m.stage());

        host.moveTo(Zone.BREACH, "exit.divide");
        run(m, 20);
        assertEquals(SUPPLY_CACHE, m.stage(), "cache is required before leaving");
        assertEquals(List.of("shotgun_cache"), host.openPickups());
        host.moveTo(Zone.BREACH, "prop.shotgun_cache");
        run(m, 2);
        assertEquals(1, host.shotguns);
        assertTrue(host.pickups.getLast().collected);
        assertEquals(List.of(), host.openPickups());
        host.moveTo(Zone.BREACH, "exit.divide");
        until(m, DIVIDE_WALKER, 3);
        run(m, 2);
        assertEquals("DIVIDE:checkpoint.divide_walker", host.placed.getLast());
        assertEquals(DIVIDE_WALKER, m.progress().snapshot().checkpoint());

        host.moveTo(Zone.DIVIDE, "trigger.walker_arena");
        run(m, 1);
        assertTrue(m.encounter().isPresent());
        for (int i = 0; i < 400 && m.stage() == DIVIDE_WALKER; i++) { if (i % 40 == 39) host.spawner.killAll(); m.tick(++now); }
        assertEquals(DOCK_13, m.stage());
        assertTrue(host.voices.contains("80b75f7f"), "walker call-out");

        host.moveTo(Zone.DIVIDE, "exit.dock13");
        run(m, 3);
        assertEquals("DOCK13:checkpoint.dock_13", host.placed.getLast());
        assertEquals(1, host.openShips(), "parked ship visible while searching Dock 13");
        host.moveTo(Zone.DOCK13, "trigger.ship");
        until(m, SHIP_DEFENSE, 3);
        run(m, 1);
        assertNotNull(host.scan);
        assertEquals(1, host.ships.size(), "same parked ship through the defense");
        for (int i = 0; i < 200 && m.stage() == SHIP_DEFENSE; i++) { host.spawner.killAll(); m.tick(++now); }
        assertEquals(DEPARTURE, m.stage());
        assertEquals(1, host.openShips(), "ship stays parked until the departure starts");

        run(m, 45);
        assertNotNull(host.departure);
        assertEquals(0, host.openShips(), "departure took the ship over: never two ships");
        assertEquals(1, host.ships.size());
        host.finishOk = false;
        host.departure.finish();
        run(m, 2);
        assertEquals(DEPARTURE, m.stage(), "failed Tower move keeps a safe retry state");
        assertEquals(1, host.finishCalls);
        host.finishOk = true;
        run(m, 45);
        assertTrue(m.complete());
        assertEquals(2, host.finishCalls);
        run(m, 200);
        m.onDeath();
        assertEquals(2, host.finishCalls, "completion is idempotent");
        assertTrue(m.snapshot().progress().completed());
        assertFalse(m.skip(GATEWAY));
    }

    @Test void deathRestartsCheckpointAndOldEnemiesAreStale() {
        var host = new FakeHost();
        var m = fresh(host);
        m.begin(now);
        assertTrue(m.skip(BREACH_FIGHT));
        assertEquals(1, host.rifles, "skipping past the armoury grants the rifle");
        run(m, 3);
        assertEquals(2, m.progress().enemiesRemaining());
        var oldEvents = new ArrayList<>(host.spawner.live.entrySet());
        m.onDeath();
        assertEquals(ARM_YOURSELF, m.stage());
        assertEquals(0, host.spawner.live.size(), "encounter reset on death");
        run(m, 2);
        assertEquals("BREACH:checkpoint.arm_yourself", host.placed.getLast());
        until(m, BREACH_FIGHT, 120);
        assertEquals(1, host.rifles, "rifle not granted twice");
        run(m, 1);
        assertEquals(2, m.progress().enemiesRemaining());
        oldEvents.forEach(e -> e.getValue().defeated(e.getKey()));
        assertEquals(2, m.progress().enemiesRemaining(), "stale defeats ignored");
        fightAll(m, host, 10);
        assertEquals(SUPPLY_CACHE, m.stage());
    }

    @Test void restoredCheckpointEnablesMusicForNewConnection() {
        var host = new FakeHost();
        var m = new RisingMission(UUID.randomUUID(), new RisingMission.Saved(
                new GuardianRisesProgress.Snapshot(DOCK_13, true, false), true, true), host);
        m.begin(now);
        run(m, 2);
        assertEquals(List.of("DOCK13:checkpoint.dock_13"), host.placed);
        assertTrue(host.music);
        assertEquals(1, host.musicCalls);
        assertEquals(DOCK_13, m.stage());
    }

    @Test void missingPresentationFailsSafely() {
        var host = new FakeHost();
        host.presentation = false;
        var m = fresh(host);
        m.begin(now);
        until(m, GATEWAY, 60);
        assertFalse(host.problems.isEmpty());
    }

    @Test void missingCombatMarkersNeverClearByTimeout() {
        var host = new FakeHost();
        host.markers.get(Zone.BREACH).removeIf(mk -> mk.id().startsWith("enemy.breach_catwalks"));
        var m = fresh(host);
        m.begin(now);
        m.skip(BREACH_FIGHT);
        run(m, 2000);
        assertEquals(BREACH_FIGHT, m.stage());
        assertEquals(1, host.problems.stream().filter(p -> p.contains("전투 마커")).count());
    }

    @Test void waitsForZoneBuildBeforeTransition() {
        var host = new FakeHost();
        host.ready.remove(Zone.BREACH);
        var m = fresh(host);
        m.begin(now);
        m.skip(GATEWAY);
        run(m, 2);
        host.moveTo(Zone.GATEWAY, "exit.breach");
        run(m, 50);
        assertEquals(BREACH_DARK, m.stage());
        assertTrue(m.placing());
        assertEquals("GATEWAY:spawn.player", host.placed.getLast());
        host.ready.add(Zone.BREACH);
        run(m, 1);
        assertFalse(m.placing());
        assertEquals("BREACH:spawn.player", host.placed.getLast());
    }

    @Test void pauseFreezesEnemiesAndResumeReplaysInterruptedBeat() {
        var host = new FakeHost();
        var m = fresh(host);
        m.begin(now);
        run(m, 2);
        var first = host.opening;
        m.pause();
        assertTrue(first.closed);
        assertEquals(GHOST_SCAN, m.stage(), "closing the opening on disconnect does not advance");
        run(m, 50);
        m.resume(now, false);
        run(m, 2);
        assertNotSame(first, host.opening);
        assertEquals(2, host.musicCalls, "Reconnect enables music again; ordinary ticks do not repeat it");
    }

    @Test void featureFlagAndEnrollment() {
        assertTrue(RisingMission.enabled(null));
        assertTrue(RisingMission.enabled("true"));
        assertFalse(RisingMission.enabled("false"));
        assertFalse(RisingMission.enabled(" FALSE "));
        assertTrue(RisingMission.required(0, false), "legacy tutorial completion is not a mission completion");
        assertFalse(RisingMission.required(0, true));
        assertFalse(RisingMission.required(RisingMission.REVISION, false), "never forced after completion");
    }

    @Test void parkedShipClosesOnDeathPauseAndRestart() {
        var host = new FakeHost();
        var m = fresh(host);
        m.begin(now);
        assertTrue(m.skip(DOCK_13));
        run(m, 3);
        assertEquals(1, host.openShips());
        m.pause();
        assertEquals(0, host.openShips(), "pause drops the parked ship");
        m.resume(++now, false);
        run(m, 2);
        assertEquals(1, host.openShips(), "resume brings it back");
        m.onDeath();
        run(m, 3);
        assertEquals(1, host.openShips(), "checkpoint restart: exactly one ship");
        assertTrue(m.skip(GATEWAY));
        run(m, 3);
        assertEquals(0, host.openShips(), "leaving Dock 13 closes it");
        m.close();
        assertEquals(0, host.openShips());
    }

    @Test void pickupMarkersCloseOnPauseRestartAndSkip() {
        var host = new FakeHost();
        var m = fresh(host);
        m.begin(now);
        assertTrue(m.skip(BREACH_DARK));
        run(m, 3);
        assertEquals(List.of("rifle"), host.openPickups());
        m.pause();
        assertEquals(List.of(), host.openPickups(), "pause drops the marker");
        m.resume(++now, false);
        run(m, 2);
        assertEquals(List.of("rifle"), host.openPickups(), "resume brings it back");
        m.onDeath();
        run(m, 3);
        assertTrue(host.openPickups().size() <= 1, "checkpoint restart never duplicates a marker");
        if (m.stage() != BREACH_DARK && m.stage() != ARM_YOURSELF)
            assertEquals(List.of(), host.openPickups(), "restart before the Breach closes it");
        assertTrue(m.skip(BREACH_DARK));
        run(m, 3);
        assertEquals(List.of("rifle"), host.openPickups());
        assertTrue(m.skip(DIVIDE_WALKER));
        run(m, 3);
        assertEquals(List.of(), host.openPickups(), "skip past the Breach closes it");
        assertTrue(host.pickups.stream().noneMatch(h -> h.collected), "closing without a pickup plays no effect");
        m.close();
        assertEquals(List.of(), host.openPickups());
    }

    @Test void storyLinesSurviveAQuickStageChange() {
        var host = new FakeHost();
        var m = fresh(host);
        m.begin(now);
        run(m, 2);
        host.opening.finish();
        run(m, 1);
        host.moveTo(Zone.GATEWAY, "exit.breach"); // straight to the wall: the Gateway lines are still queued
        until(m, BREACH_DARK, 5);
        run(m, 300);
        assertTrue(host.voices.containsAll(List.of("80b75f64", "80b75f60", "80b75f55")),
                "no story line is lost when the player outruns the Ghost: " + host.voices);
    }

    @Test void pickupReachIsThreeMetres() {
        var host = new FakeHost();
        // Keep the restore anchor away from the rifle so the reach is measured, not the placement.
        host.markers.get(Zone.BREACH).removeIf(mk -> mk.id().equals("checkpoint.arm_yourself"));
        host.add(Zone.BREACH, "checkpoint.arm_yourself", 10, 0);
        var m = fresh(host);
        m.begin(now);
        assertTrue(m.skip(ARM_YOURSELF));
        run(m, 3);
        assertEquals(List.of("rifle"), host.openPickups());
        Vec3 rifle = host.marker(Zone.BREACH, "prop.rifle").orElseThrow().pos();
        host.pos = rifle.add(3.05, 0, 0);
        run(m, 2);
        assertFalse(m.rifleGranted());
        host.pos = rifle.add(2.9, 0, 0);
        run(m, 2);
        assertTrue(m.rifleGranted(), "2.5..3.0 m now collects");
        assertTrue(host.pickups.getLast().collected);
    }
}
