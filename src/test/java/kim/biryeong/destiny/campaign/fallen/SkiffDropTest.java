package kim.biryeong.destiny.campaign.fallen;

import kim.biryeong.destiny.campaign.RisingEncounters.Slot;
import kim.biryeong.destiny.campaign.RisingServices.FallenKind;
import kim.biryeong.destiny.campaign.RisingServices.Zone;
import kim.biryeong.destiny.campaign.fallen.SkiffDrop.Choice;
import kim.biryeong.destiny.campaign.fallen.SkiffDrop.Sky;
import kim.biryeong.destiny.campaign.fallen.SkiffDrop.Timing;
import net.minecraft.world.phys.Vec3;
import org.junit.jupiter.api.Test;

import java.util.*;
import java.util.function.Predicate;

import static org.junit.jupiter.api.Assertions.*;

class SkiffDropTest {
    static Slot s(FallenKind kind, double x, double z) {
        return new Slot("enemy.w." + kind + x + z, "w", kind, new Vec3(x, 64, z), 0, 1);
    }

    @Test void arriveFitsTheWaveLead() {
        assertEquals(Timing.MAX_SPEED, Timing.arriveSpeed(0), 1e-6, "no lead: fastest swoop");
        // WAVE_DELAY lead (30 t): 80/30 = 2.67x, the arrive clip ends by the spawn
        assertEquals(80f / 30f, Timing.arriveSpeed(30), 1e-4);
        assertTrue(Timing.arriveTicks(30) <= 30, "arrive must finish before the wave spawns");
        assertEquals(Timing.ARRIVE_CLIP, Timing.arriveTicks(80));
        assertEquals(1f, Timing.arriveSpeed(200), 1e-6, "never slower than authored");
        assertEquals(Timing.ARRIVE_CLIP, Timing.arriveTicks(200));
        assertEquals(Timing.MAX_SPEED, Timing.arriveSpeed(5), 1e-6, "capped");
        assertEquals((int) Math.ceil(80 / 3f), Timing.arriveTicks(5));
        assertTrue(Timing.DEPART_DELAY >= Timing.DROP_CLIP - 10, "riders land before the Skiff turns away");
        assertEquals(Timing.DEPART_DELAY + Timing.DEPART_CLIP, Timing.afterDrop());
        assertTrue(Timing.HOVER_TIMEOUT > Timing.arriveTicks(0) + 30, "a missing drop cue still despawns the Skiff");
        assertTrue(Timing.LIFT_HEIGHT < Timing.HOVER_HEIGHT);
    }

    @Test void onlyGroundReinforcementWavesRideSkiffs() {
        var two = List.of(s(FallenKind.DREG, 0, 0), s(FallenKind.VANDAL, 3, 1));
        assertTrue(Choice.skiffWave(Zone.DIVIDE, 1, two));
        assertTrue(Choice.skiffWave(Zone.DOCK13, 2, two));
        assertFalse(Choice.skiffWave(Zone.DIVIDE, 0, two), "opening wave has no lead time");
        assertFalse(Choice.skiffWave(Zone.GATEWAY, 1, two));
        assertFalse(Choice.skiffWave(null, 1, two));
        assertFalse(Choice.skiffWave(Zone.DIVIDE, 1, null));
        assertFalse(Choice.skiffWave(Zone.DIVIDE, 1, List.of(s(FallenKind.DREG, 0, 0))), "a single dreg is not worth a ship");
        assertFalse(Choice.skiffWave(Zone.DIVIDE, 1, List.of(s(FallenKind.SHANK, 0, 0), s(FallenKind.SHANK, 1, 0))),
                "shanks fly in by themselves");
        assertFalse(Choice.skiffWave(Zone.DIVIDE, 1, List.of(s(FallenKind.DREG, 0, 0), s(FallenKind.DREG, 1, 0),
                s(FallenKind.WALKER, 5, 5))), "walker waves land on their own");
    }

    @Test void farOutliersAndShanksSpawnNormally() {
        var dreg = s(FallenKind.DREG, 0, 0);
        var vandal = s(FallenKind.VANDAL, 4, 0);
        var captain = s(FallenKind.CAPTAIN, 2, 3);
        var shank = s(FallenKind.SHANK, 1, 1);
        var far = s(FallenKind.DREG, 60, 0);
        var riders = Choice.dropped(List.of(dreg, vandal, captain, shank, far));
        assertEquals(List.of(dreg, vandal, captain), riders);
        assertFalse(Choice.skiffWave(Zone.BREACH, 1, List.of(dreg, far)), "two dregs 60 m apart: one rider");
        Vec3 c = Choice.centroid(riders);
        assertEquals(2, c.x, 1e-9);
        assertEquals(1, c.z, 1e-9);
        assertEquals(64, c.y, 1e-9);
    }

    @Test void skiffApproachesFromBehindThePlayer() {
        Vec3 drop = new Vec3(0, 64, 0);
        float yaw = Choice.approachYaw(drop, new Vec3(0, 64, -20)); // player south... at -z: drop lies +z of the player
        double fx = -Math.sin(Math.toRadians(yaw)), fz = Math.cos(Math.toRadians(yaw));
        assertEquals(0, fx, 1e-6);
        assertEquals(1, fz, 1e-6, "forward points from the player toward the drop");
        float east = Choice.approachYaw(drop, new Vec3(-10, 64, 0));
        assertEquals(1, -Math.sin(Math.toRadians(east)), 1e-6);
        assertFalse(Float.isNaN(Choice.approachYaw(drop, drop)));
        assertFalse(Float.isNaN(Choice.approachYaw(drop, null)));
    }

    @Test void dockDefenceArrivesByShipButOtherOpeningWavesDoNot() {
        var two = List.of(s(FallenKind.DREG, 0, 0), s(FallenKind.VANDAL, 3, 1));
        assertFalse(Choice.skiffWave(Zone.DOCK13, 0, two), "Dock 13 opening wave is on site; waves 2-3 drop by Skiff");
        assertFalse(Choice.skiffWave(Zone.BREACH, 0, two));
        assertFalse(Choice.skiffWave(Zone.DIVIDE, 0, two));
        var units = Choice.ground(List.of(s(FallenKind.SHANK, 0, 0), two.get(0), s(FallenKind.DREG, 40, 0), two.get(1)), two);
        assertEquals(3, units.size(), "riders first, then the other ground units; shanks never");
        assertEquals(two, units.subList(0, 2));
    }

    /** Floor at y=63 everywhere; optional roof at y=ROOF over |x|,|z| <= 60 (wider than the search) with holes; walls. */
    static final class World implements Sky.Grid {
        static final int FLOOR = 63, ROOF = 72, TOP = 130;
        final boolean roof;
        final List<int[]> holes = new ArrayList<>(); // x0,z0,x1,z1 inclusive
        Predicate<int[]> walls = p -> false;
        int reads;
        World(boolean roof) { this.roof = roof; }
        World hole(int x0, int z0, int x1, int z1) { holes.add(new int[]{x0, z0, x1, z1}); return this; }
        boolean roofAt(int x, int z) {
            if (!roof || Math.abs(x) > 60 || Math.abs(z) > 60) return false;
            for (int[] h : holes) if (x >= h[0] && x <= h[2] && z >= h[1] && z <= h[3]) return false;
            return true;
        }
        @Override public boolean solid(int x, int y, int z) {
            reads++;
            return y <= FLOOR || (y == ROOF && roofAt(x, z)) || (y > FLOOR && y < TOP && walls.test(new int[]{x, y, z}));
        }
        @Override public boolean sky(int x, int y, int z) {
            if (y <= FLOOR) return false;
            if (y <= ROOF && roofAt(x, z)) return false;
            for (int yy = Math.max(y, FLOOR + 1); yy < TOP; yy++) if (walls.test(new int[]{x, yy, z})) return false;
            return true;
        }
    }

    static final Vec3 A = new Vec3(0.5, 64, 0.5), B = new Vec3(2.5, 64, 1.5);
    static Optional<Sky.Spot> find(World w, Vec3 hint) { return Sky.find(w, List.of(A, B), Choice.centroid(List.of(
            new Slot("a", "e", FallenKind.DREG, A, 0, 1), new Slot("b", "e", FallenKind.DREG, B, 0, 1))), hint); }

    @Test void openSkyHoversStraightAboveTheRiders() {
        var spot = find(new World(false), null).orElseThrow();
        assertEquals(Sky.Kind.DIRECT, spot.kind());
        assertEquals(64 + Timing.HOVER_HEIGHT, spot.hover().y, 1e-9);
        assertEquals(0, spot.offset(), 1e-9);
        assertEquals(2, spot.seenBy());
    }

    @Test void roofedRidersUseTheNearestVisibleOpening() {
        // two roof holes big enough for the 16-block hull: one 12 m east, one 20 m north; the east one is nearer
        var w = new World(true).hole(12, -10, 32, 10).hole(-10, 20, 10, 40);
        var spot = find(w, null).orElseThrow();
        assertEquals(Sky.Kind.OFFSET, spot.kind());
        assertTrue(spot.hover().x > 10 && Math.abs(spot.hover().z) < 8, "east hole: " + spot.hover());
        assertTrue(w.sky((int) Math.floor(spot.hover().x), (int) spot.hover().y, (int) Math.floor(spot.hover().z)),
                "hovers under the hole's open sky: " + spot.hover());
        assertTrue(spot.seenBy() >= 1);
        assertTrue(spot.offset() <= Sky.RADIUS);
        assertTrue(Sky.sees(w, A, spot.hover()));
    }

    @Test void anOpeningHiddenBehindAWallIsNotUsed() {
        // hole 14 m east, but a full-height wall at x=8..9 between it and the riders; a farther hole north is visible
        var w = new World(true).hole(12, -10, 32, 10).hole(-10, 20, 10, 40);
        w.walls = p -> p[0] >= 8 && p[0] <= 9 && p[1] < World.ROOF;
        var spot = find(w, null).orElseThrow();
        assertTrue(Sky.lastReads() < 10_000, "cheap: hull fit uses the heightmap only");
        assertTrue(spot.hover().z > 20, "falls back to the visible northern hole: " + spot.hover());
        w.walls = p -> p[1] < World.ROOF && ((p[0] >= 8 && p[0] <= 9) || (p[2] >= 12 && p[2] <= 13));
        assertTrue(find(w, null).isEmpty(), "every opening hidden -> skip");
    }

    @Test void fullyRoofedHallsSkipAndStayWithinBudget() {
        var w = new World(true);
        assertTrue(find(w, null).isEmpty());
        assertTrue(Sky.lastReads() <= Sky.BUDGET);
        // a solid mountain everywhere above the floor: the read cap ends the search instead of scanning 40 m of rays
        var rock = new World(false);
        rock.walls = p -> true;
        assertTrue(find(rock, null).isEmpty());
        assertTrue(rock.reads <= Sky.BUDGET + 1);
    }

    @Test void markerHintWinsWhenUsableAndIsIgnoredWhenBlocked() {
        var w = new World(true).hole(12, -4, 22, 6).hole(-20, -20, -6, -6);
        var hint = new Vec3(-12, World.ROOF + 6, -12);
        var spot = find(w, hint).orElseThrow();
        assertEquals(Sky.Kind.HINT, spot.kind());
        assertEquals(-11.5, spot.hover().x, 1e-9);
        var blocked = find(w, new Vec3(0, World.ROOF - 4, 0)).orElseThrow(); // under the roof: rejected
        assertEquals(Sky.Kind.OFFSET, blocked.kind());
    }

    @Test void searchIsDeterministic() {
        var w = new World(true).hole(12, -4, 22, 6).hole(-22, -4, -12, 6);
        assertEquals(find(w, null).orElseThrow().hover(), find(w, null).orElseThrow().hover());
    }

    // ---- r9: hull fit, watching player, tracker culling ----

    static Optional<Sky.Spot> findFor(World w, Vec3 hint, float yaw, Vec3 viewer) {
        return Sky.find(w, List.of(A, B), Choice.centroid(List.of(
                new Slot("a", "e", FallenKind.DREG, A, 0, 1), new Slot("b", "e", FallenKind.DREG, B, 0, 1))), hint, yaw, viewer);
    }

    @Test void theWholeSixteenBlockHullMustClearTheRoof() {
        // a 9x9 roof hole: the 7x7 hull core fits in it, the 16-long hull only above the roof line
        var w = new World(true).hole(-4, -4, 4, 4);
        var hint = new Vec3(0.5, World.ROOF - 1, 0.5); // inside the hole, like the Dock 13 markers
        assertFalse(Sky.hullFits(w, new Vec3(0.5, World.ROOF - 1, 0.5), 0), "hull ends cut into the roof at the hint height");
        var spot = findFor(w, hint, 0, null).orElseThrow();
        assertEquals(Sky.Kind.HINT, spot.kind(), "the hint column is kept");
        assertTrue(spot.hover().y - Sky.HULL_BELOW >= World.ROOF + 1, "raised until the hull clears the roof: " + spot.hover());
        assertTrue(Sky.hullFits(w, spot.hover(), spot.yaw()));
    }

    @Test void aLongSlotTurnsTheHull() {
        // a long north-south slot through the roof: east-west (yaw 90) does not fit, north-south does
        var w = new World(true).hole(-3, -40, 3, 40);
        var hint = new Vec3(0.5, World.ROOF - 1, 0.5);
        assertFalse(Sky.hullFits(w, new Vec3(0.5, World.ROOF - 1, 0.5), 90), "across the slot it hits the roof");
        assertTrue(Sky.hullFits(w, new Vec3(0.5, World.ROOF - 1, 0.5), 0));
        var spot = findFor(w, hint, 90, null).orElseThrow();
        assertEquals(World.ROOF - 1, spot.hover().y, 1e-9, "fits at the hint height once turned");
        double r = Math.toRadians(spot.yaw());
        assertTrue(Math.abs(Math.cos(r)) > .99, "heading north/south: " + spot.yaw());
    }

    @Test void prefersAHoleTheWatchingPlayerCanSee() {
        // riders see both holes; a pillar just east of the player hides the nearer east hole from them only
        var w = new World(true).hole(7, -10, 30, 10).hole(-10, 10, 10, 36);
        w.walls = p -> p[0] >= -2 && p[0] <= -1 && p[2] >= -4 && p[2] <= 4;
        Vec3 viewer = new Vec3(-6.5, 65.6, 0.5);
        var riderOnly = findFor(w, null, 0, null).orElseThrow();
        var forViewer = findFor(w, null, 0, viewer).orElseThrow();
        assertTrue(forViewer.viewerSees(), "picked a spot the player sees: " + forViewer.hover());
        assertTrue(Sky.viewerSees(w, viewer, forViewer.hover()));
        assertTrue(forViewer.seenBy() > 0, "riders still see it");
        assertNotEquals(riderOnly.hover(), forViewer.hover());
    }

    @Test void aPlayerWhoSeesNothingStillGetsTheRidersSkiff() {
        var w = new World(true).hole(12, -4, 22, 6);
        Vec3 viewer = new Vec3(-40.5, 65.6, 0.5);
        w.walls = p -> p[0] == -30; // full wall between the player and everything
        var spot = findFor(w, null, 0, viewer).orElseThrow();
        assertFalse(spot.viewerSees());
        assertEquals(findFor(w, null, 0, null).orElseThrow().hover(), spot.hover(), "falls back to the riders' first spot");
        assertTrue(Sky.lastReads() <= Sky.BUDGET);
    }

    @Test void approachPrefersAHeadingThatFliesInUnderOpenSky() {
        // open field except a tall wall north of the drop: the clip's last 26 m must not come through it
        var w = new World(false);
        w.walls = p -> p[2] >= 12 && p[2] <= 13 && p[1] < 120;
        var spot = findFor(w, null, 0, null).orElseThrow();
        assertTrue(Sky.approachClear(w, spot.hover(), spot.yaw()));
        assertFalse(Sky.approachClear(w, spot.hover(), 0), "yaw 0 approaches from the north, through the wall");
    }

    @Test void skiffTrackerIgnoresBetterModelSightTrace() {
        assertFalse(SkiffDrop.TRACKER.sightTrace(), "FOV culling would freeze the arrive flight ~90 blocks out");
    }

    @Test void skiffStaysLongEnoughToBeFound() {
        assertTrue(Timing.DEPART_DELAY >= 100, "holds station ~5 s after the drop");
        assertTrue(Timing.arriveTicks(30) + Timing.afterDrop() >= 200, "~10 s from the first cue to removal");
    }
}
