package kim.biryeong.destiny.campaign.fallen;

import kim.biryeong.destiny.campaign.fallen.WalkerBoss.Machine;
import kim.biryeong.destiny.campaign.fallen.WalkerBoss.Outcome;
import kim.biryeong.destiny.campaign.fallen.WalkerBoss.Phase;
import kim.biryeong.destiny.campaign.fallen.WalkerBoss.Region;
import kim.biryeong.destiny.campaign.fallen.WalkerBoss.Tuning;
import org.junit.jupiter.api.Test;

import java.util.Random;

import static org.junit.jupiter.api.Assertions.*;

/** Walker phase machine (W300): leg break, weakpoint gating, shot de-duplication, primary-only completion. */
class WalkerBossTest {
    private static final Tuning T = Tuning.BASE;

    @Test void startsArmoredWithOnlyLegsVulnerable() {
        var m = new Machine(T);
        assertEquals(Phase.ARMORED, m.phase());
        for (Region r : Region.values()) assertEquals(r.leg(), m.vulnerable(r), r.name());
        assertEquals(Outcome.DEFLECTED, m.hit(Region.HULL, 50, key(1)).outcome());
        assertEquals(Outcome.DEFLECTED, m.hit(Region.WEAKPOINT, 50, key(2)).outcome());
        assertEquals(T.core(), m.core(), 1e-9);
    }

    @Test void legBreakStaggerExposedRecoverCycle() {
        var m = new Machine(T);
        var h = m.hit(Region.LEG_FL, T.legArmor() - 1, key(1));
        assertEquals(Outcome.LEG_DAMAGE, h.outcome());
        assertEquals(Outcome.LEG_BROKEN, m.hit(Region.LEG_FL, 5, key(2)).outcome());
        assertFalse(m.hit(Region.LEG_FL, 5, key(3)).accepted(), "broken leg takes nothing");
        assertEquals(Phase.LEG_BREAK, m.phase());
        assertEquals(Region.LEG_FL, m.brokenLeg());
        // Weakpoint still closed during the break and stagger animations.
        assertFalse(m.hit(Region.WEAKPOINT, 10, key(4)).accepted());
        assertEquals(Phase.STAGGER, advance(m, T.legBreakTicks()));
        assertFalse(m.hit(Region.WEAKPOINT, 10, key(5)).accepted());
        assertEquals(Phase.EXPOSED, advance(m, T.staggerTicks()));
        assertTrue(m.vulnerable(Region.WEAKPOINT));
        assertFalse(m.vulnerable(Region.LEG_FR), "legs are not targets while exposed");
        var core = m.hit(Region.WEAKPOINT, 10, key(6));
        assertEquals(Outcome.CORE_DAMAGE, core.outcome());
        assertEquals(10 * T.weakpointMultiplier(), core.applied(), 1e-9);
        assertEquals(Phase.RECOVER, advance(m, T.exposedTicks()));
        assertFalse(m.hit(Region.WEAKPOINT, 10, key(7)).accepted());
        assertEquals(Phase.ARMORED, advance(m, T.recoverTicks()));
        assertEquals(1, m.cycles());
        assertEquals(T.legArmor() * T.legRestore(), m.leg(Region.LEG_FL), 1e-9);
        assertEquals(T.legArmor(), m.leg(Region.LEG_FR), 1e-9);
        assertNull(m.brokenLeg());
    }

    @Test void sameShotIsCreditedOnceButDeflectionDoesNotConsumeIt() {
        var m = new Machine(T);
        Object shot = key(42);
        // Splash touching the hull first must still be able to reach a leg.
        assertEquals(Outcome.DEFLECTED, m.hit(Region.HULL, 30, shot).outcome());
        assertEquals(Outcome.LEG_DAMAGE, m.hit(Region.LEG_BR, 30, shot).outcome());
        assertEquals(Outcome.DUPLICATE, m.hit(Region.LEG_BL, 30, shot).outcome());
        assertEquals(Outcome.DUPLICATE, m.hit(Region.LEG_BR, 30, shot).outcome());
        assertEquals(T.legArmor() - 30, m.leg(Region.LEG_BR), 1e-9);
        assertEquals(T.legArmor(), m.leg(Region.LEG_BL), 1e-9);
        // Keys expire after a couple of ticks (memory bound); a new tick is a new shot anyway.
        m.tick(); m.tick(); m.tick();
        assertEquals(Outcome.LEG_DAMAGE, m.hit(Region.LEG_BL, 1, shot).outcome());
        // Null key (unknown source) is never de-duplicated.
        assertTrue(m.hit(Region.LEG_BL, 1, null).accepted());
        assertTrue(m.hit(Region.LEG_BL, 1, null).accepted());
    }

    @Test void deathIsTerminal() {
        var m = new Machine(new Tuning(10, 20, 1.5, .6, 2, 2, 50, 2));
        m.hit(Region.LEG_FR, 10, key(1));
        advance(m, 2); advance(m, 2);
        assertEquals(Phase.EXPOSED, m.phase());
        var kill = m.hit(Region.WEAKPOINT, 100, key(2));
        assertEquals(Outcome.KILLED, kill.outcome());
        assertEquals(20, kill.applied(), 1e-9, "overkill is clamped to the remaining core");
        assertEquals(Phase.DEAD, m.phase());
        assertNull(m.tick());
        assertEquals(Outcome.DEFLECTED, m.hit(Region.WEAKPOINT, 1, key(3)).outcome());
        assertEquals(Outcome.DEFLECTED, m.hit(Region.LEG_BL, 1, key(4)).outcome());
    }

    @Test void ignoringTheWeakpointNeverSoftLocks() {
        var m = new Machine(T);
        for (int cycle = 0; cycle < 6; cycle++) {
            Region leg = Region.values()[cycle % 4];
            while (m.phase() == Phase.ARMORED) {
                if (m.leg(leg) <= 0) leg = Region.values()[(leg.ordinal() + 1) % 4];
                m.hit(leg, 50, null);
            }
            // Player does nothing during the whole window.
            int guard = 0;
            while (m.phase() != Phase.ARMORED && guard++ < 1000) m.tick();
            assertEquals(Phase.ARMORED, m.phase());
            boolean anyLeg = false;
            for (int i = 0; i < 4; i++) anyLeg |= m.vulnerable(Region.values()[i]);
            assertTrue(anyLeg, "a leg is always targetable after recover");
        }
        assertEquals(T.core(), m.core(), 1e-9);
    }

    @Test void primaryAutoRifleAloneCompletesTheFight() {
        // Auto rifle: 3 damage every 3 ticks; 65% of shots land on the intended region.
        int ticks = simulate(3, 3, .65, 7);
        assertTrue(ticks > 0, "never finished");
        assertTrue(ticks <= 20 * 150, "auto rifle took " + ticks / 20 + " s");
    }

    @Test void primaryHandCannonAloneCompletesTheFight() {
        int ticks = simulate(7, 10, .6, 11);
        assertTrue(ticks > 0 && ticks <= 20 * 180, "hand cannon took " + ticks / 20 + " s");
    }

    @Test void fightIsNotTrivialisedByAccurateFire() {
        // Perfect aim with a 3-damage/3-tick rifle and real reloads still needs two exposure windows.
        var perfect = engaged(3, 3, 33, 44, 1, 1, 3);
        assertTrue(perfect[1] >= 2, "windows " + perfect[1]);
        assertTrue(perfect[0] >= 20 * 20, "perfect fire took " + perfect[0] / 20 + " s");
    }

    @Test void difficultyScalesPoolsOnly() {
        var s = T.scaled(2);
        assertEquals(T.legArmor() * 2, s.legArmor(), 1e-9);
        assertEquals(T.core() * 2, s.core(), 1e-9);
        assertEquals(T.exposedTicks(), s.exposedTicks());
        assertEquals(T.core(), T.scaled(Double.NaN).core(), 1e-9);
    }

    // ---------------------------------------------------------------- r3: calibration against the real rifle

    /**
     * Engaged first-mission player with the real halfdan_d profile (WeaponProfile/WeaponBallistics, not invented):
     * 15-30 m, 55% of shots land on a leg while armoured, 45% on the weakpoint while exposed, full magazine/reload
     * cycle, nothing fired during break/stagger/recover. Must finish in 60-90 s over 2-3 exposure windows.
     */
    @Test void halfdanEngagedPlayerFinishesIn60to90SecondsOverTwoToThreeCycles() {
        var entry = kim.biryeong.destiny.weapon.WeaponCatalog.find(kim.biryeong.destiny.campaign.RisingLoadout.RIFLE).orElseThrow();
        var profile = kim.biryeong.destiny.weapon.WeaponProfile.forEntry(entry);
        var ballistics = kim.biryeong.destiny.weapon.WeaponBallistics.of(entry);
        var report = new StringBuilder(kim.biryeong.destiny.campaign.RisingLoadout.RIFLE + " damage=" + profile.damage() + " interval=" + profile.intervalTicks()
                + " mag=" + profile.magazine() + " reload=" + profile.reloadTicks() + " " + ballistics + "\n");
        for (double distance : new double[]{15, 22, 30}) {
            double hit = profile.damage() * ballistics.falloff(distance);
            double sum = 0; int maxCycles = 0, minCycles = 99;
            for (long seed = 1; seed <= 5; seed++) {
                var r = engaged(hit, profile.intervalTicks(), profile.magazine(), profile.reloadTicks(), .55, .45, seed);
                sum += r[0]; maxCycles = Math.max(maxCycles, (int) r[1]); minCycles = Math.min(minCycles, (int) r[1]);
                report.append(String.format("d=%.0f seed=%d %.1fs windows=%d%n", distance, seed, r[0] / 20.0, (int) r[1]));
            }
            double seconds = sum / 5 / 20;
            write(report.toString());
            if (distance <= 22) {
                assertTrue(seconds >= 55 && seconds <= 90, "d=" + distance + " took " + seconds + " s");
                assertTrue(minCycles >= 2 && maxCycles <= 3, "windows " + minCycles + ".." + maxCycles);
            } else assertTrue(seconds <= 120, "30 m must stay finishable: " + seconds);
        }
        // Perfect aim at 15 m still needs two windows.
        var perfect = engaged(profile.damage(), profile.intervalTicks(), profile.magazine(), profile.reloadTicks(), 1, 1, 1);
        assertTrue(perfect[1] >= 2, "perfect aim windows " + perfect[1]);
        report.append("perfect@15 ").append(perfect[0] / 20.0).append("s windows=").append((int) perfect[1]).append('\n');
        write(report.toString());
    }

    /** @return {ticks to kill, exposure windows used} */
    private static double[] engaged(double damage, int interval, int magazine, int reload, double legRate,
                                    double weakRate, long seed) {
        var m = new Machine(T);
        var rnd = new Random(seed);
        int ammo = magazine, reloading = 0, cooldown = 0, windows = 0;
        Phase last = m.phase();
        for (int t = 1; t <= 20 * 600; t++) {
            m.tick();
            if (m.phase() == Phase.EXPOSED && last != Phase.EXPOSED) windows++;
            last = m.phase();
            if (reloading > 0) { if (--reloading == 0) ammo = magazine; continue; }
            if (cooldown > 0) { cooldown--; continue; }
            Region target = null;
            for (Region r : Region.values()) if (m.vulnerable(r)) { target = r; break; }
            if (target == null) {
                // Players top off the magazine during the break/recover lulls.
                if (ammo < magazine / 2) reloading = reload;
                continue;
            }
            cooldown = interval - 1;
            if (--ammo <= 0) reloading = reload;
            double rate = target == Region.WEAKPOINT ? weakRate : legRate;
            if (rnd.nextDouble() < rate) m.hit(target, damage, key(t));
            if (m.phase() == Phase.DEAD) return new double[]{t, windows};
        }
        return new double[]{20 * 600, windows};
    }

    private static void write(String text) {
        try {
            var dir = java.nio.file.Path.of(System.getProperty("user.dir")).resolveSibling("w300-evidence/fallen/r3");
            if (java.nio.file.Files.isDirectory(dir)) java.nio.file.Files.writeString(dir.resolve("walker-ttk-halfdan.txt"), text);
        } catch (java.io.IOException ignored) { }
    }

    @Test void walkerHoldsItsArenaAndNeverRetreats() {
        var arena = new net.minecraft.world.phys.Vec3(287.5, 45, 244.5);
        var rnd = new Random(4);
        for (double dist : new double[]{8, 15, 22, 30, 45, 60}) {
            for (int i = 0; i < 50; i++) {
                double a = rnd.nextDouble() * Math.PI * 2;
                var player = arena.add(Math.cos(a) * dist, 0, Math.sin(a) * dist);
                var p = WalkerBoss.clampArena(arena, WalkerBoss.holdPoint(arena, player, rnd.nextDouble() * 2 - 1, rnd.nextDouble()));
                assertTrue(horizontal(p, arena) <= WalkerBoss.ARENA_RADIUS + 1e-9, "outside arena");
                assertTrue(horizontal(p, player) <= horizontal(arena, player) + 3.01, "retreated from the player");
                assertEquals(arena.y, p.y, 1e-9);
            }
        }
        assertEquals(arena, WalkerBoss.holdPoint(arena, null, 0, 0));
    }

    private static double horizontal(net.minecraft.world.phys.Vec3 a, net.minecraft.world.phys.Vec3 b) {
        return Math.hypot(a.x - b.x, a.z - b.z);
    }

    /** Returns ticks to kill, or -1 after 10 minutes. Player always shoots the currently vulnerable region. */
    private static int simulate(double damage, int interval, double hitRate, long seed) {
        var m = new Machine(T);
        var rnd = new Random(seed);
        for (int t = 1; t <= 20 * 600; t++) {
            m.tick();
            if (m.phase() == Phase.DEAD) return t;
            if (t % interval != 0 || rnd.nextDouble() > hitRate) continue;
            Region target = null;
            for (Region r : Region.values()) if (m.vulnerable(r)) { target = r; break; }
            if (target == null) continue;
            m.hit(target, damage, key(t));
            if (m.phase() == Phase.DEAD) return t;
        }
        return -1;
    }

    private static Phase advance(Machine m, int ticks) {
        Phase last = null;
        for (int i = 0; i < ticks; i++) { Phase p = m.tick(); if (p != null) last = p; }
        return last;
    }

    private static Object key(long n) { return new WalkerBoss.ShotKey(1, 1, n); }
}
