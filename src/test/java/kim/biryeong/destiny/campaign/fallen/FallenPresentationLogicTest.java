package kim.biryeong.destiny.campaign.fallen;

import kim.biryeong.destiny.campaign.RisingServices.FallenKind;
import kim.biryeong.destiny.campaign.fallen.FallenCallouts.Cue;
import kim.biryeong.destiny.campaign.fallen.WalkerBoss.Phase;
import org.junit.jupiter.api.Test;

import java.util.ArrayList;
import java.util.List;

import static org.junit.jupiter.api.Assertions.*;

/** W300 r4: pure health-bar visibility/trail logic and Walker callout dedupe/cooldown. */
class FallenPresentationLogicTest {

    // ------------------------------------------------------------------ health bar

    @Test void normalEnemyBarHiddenUntilDamagedThenFadesAfterFiveSeconds() {
        var m = new HealthBarModel();
        m.update(0, 1, 0);
        assertFalse(m.visible(1, false, false, true), "undamaged and not in sight: hidden");
        m.update(10, .7, 0);
        assertTrue(m.visible(10, false, false, true));
        assertTrue(m.visible(10 + HealthBarModel.FADE_TICKS - 1, false, false, true));
        assertFalse(m.visible(10 + HealthBarModel.FADE_TICKS, false, false, true), "fades 5 s after last damage");
        // A new hit refreshes the timer.
        m.update(50, .6, 0);
        assertTrue(m.visible(50 + HealthBarModel.FADE_TICKS - 1, false, false, true));
    }

    @Test void inSightShowsWithoutDamageAndDeadNeverShows() {
        var m = new HealthBarModel();
        m.update(0, 1, 0);
        assertTrue(m.visible(5, true, false, true));
        assertFalse(m.visible(5, true, false, false));
        assertFalse(m.visible(5, true, true, false), "dead boss hidden too");
    }

    @Test void bossAlwaysVisibleDuringTheFight() {
        var m = new HealthBarModel();
        m.update(0, 1, 0);
        assertTrue(m.visible(10_000, false, true, true));
    }

    @Test void whiteTrailHoldsThenShrinksToTheRealValue() {
        var m = new HealthBarModel();
        m.update(0, 1, 0);
        m.update(1, .6, 0);
        assertEquals(.6, m.health(), 1e-9);
        assertEquals(1, m.trail(), 1e-9);
        for (long t = 2; t <= 1 + HealthBarModel.TRAIL_DELAY; t++) m.update(t, .6, 0);
        assertEquals(1, m.trail(), 1e-9, "trail holds during the delay");
        var f = m.frame();
        assertEquals(60, f.fill());
        assertEquals(100, f.trail());
        long t = 2 + HealthBarModel.TRAIL_DELAY;
        m.update(t, .6, 0);
        assertTrue(m.trail() < 1 && m.trail() > .6);
        for (int i = 0; i < 40; i++) m.update(++t, .6, 0);
        assertEquals(.6, m.trail(), 1e-9, "trail never drops below health");
        assertEquals(m.frame().fill(), m.frame().trail());
    }

    @Test void healingOrShieldRegenNeverCountsAsDamage() {
        var m = new HealthBarModel();
        m.update(0, .5, 0);
        m.update(1, .8, 1);
        assertFalse(m.visible(2, false, false, true));
        m.update(3, .8, .4);
        assertTrue(m.visible(3, false, false, true), "shield loss counts as damage");
        assertEquals(40, m.frame().shield());
    }

    @Test void framesQuantizeSoTinyChangesSendNothing() {
        var m = new HealthBarModel();
        m.update(0, 1, 0);
        var a = m.frame();
        m.update(1, .9999, 0);
        assertEquals(a.fill(), m.frame().fill());
        m.update(2, Double.NaN, 0);
        assertEquals(0, m.frame().fill(), "non-finite health reads as empty, never crashes");
    }

    @Test void sightConeAndRange() {
        assertTrue(HealthBarModel.inSight(0, 0, 10, 0, 0, 1, 20, FallenHealthBars.SIGHT_COS));
        assertFalse(HealthBarModel.inSight(0, 0, 25, 0, 0, 1, 20, FallenHealthBars.SIGHT_COS), "beyond 20 m");
        assertFalse(HealthBarModel.inSight(5, 0, 10, 0, 0, 1, 20, FallenHealthBars.SIGHT_COS), "outside the cone");
        assertFalse(HealthBarModel.inSight(0, 0, 10, 0, 0, -1, 20, FallenHealthBars.SIGHT_COS), "looking away");
    }

    @Test void tiersAndColours() {
        assertEquals(FallenHealthBars.Tier.NORMAL, FallenHealthBars.tierOf(FallenKind.DREG));
        assertEquals(FallenHealthBars.Tier.NORMAL, FallenHealthBars.tierOf(FallenKind.VANDAL));
        assertEquals(FallenHealthBars.Tier.NORMAL, FallenHealthBars.tierOf(FallenKind.SHANK));
        assertEquals(FallenHealthBars.Tier.ELITE, FallenHealthBars.tierOf(FallenKind.CAPTAIN));
        assertEquals(FallenHealthBars.Tier.BOSS, FallenHealthBars.tierOf(FallenKind.WALKER));
        assertTrue(FallenHealthBars.Tier.BOSS.width > FallenHealthBars.Tier.NORMAL.width);
    }

    @Test void vanillaSpaceBackgroundMappingMatchesTheRenderer() {
        // DisplayRenderer: font px x in [-2,3], y in [-10,0] for " ", scaled by 0.025 -> 0.125 x 0.25 block at scale 1.
        assertEquals(.125, FallenHealthBars.BASE_W, 1e-12);
        assertEquals(.25, FallenHealthBars.BASE_H, 1e-12);
        var unit = new FallenHealthBars.Span(0, 1, 1);
        assertEquals(-.05, unit.renderedLeft(), 1e-9);
        assertEquals(.075, unit.renderedRight(), 1e-9);
    }

    @Test void barSegmentsTileSeamlesslyAtTheRequestedSize() {
        for (var tier : FallenHealthBars.Tier.values()) {
            double w = tier.width, h = tier.height;
            double[] cuts = {0, .37, .61, 1}; // fill | trail | empty
            double prevRight = Double.NaN, left = Double.NaN, right = Double.NaN;
            for (int i = 0; i < 3; i++) {
                var sp = FallenHealthBars.span(cuts[i] * w - w / 2, cuts[i + 1] * w - w / 2, h);
                if (i == 0) left = sp.renderedLeft(); else assertEquals(prevRight, sp.renderedLeft(), 1e-5, tier + " seam " + i);
                assertEquals((cuts[i + 1] - cuts[i]) * w, sp.renderedRight() - sp.renderedLeft(), 1e-5);
                assertEquals(h, FallenHealthBars.BASE_H * sp.scaleY(), 1e-6, "height via scale.y");
                prevRight = right = sp.renderedRight();
            }
            assertEquals(-w / 2, left, 1e-5, tier + " bar centred");
            assertEquals(w / 2, right, 1e-5);
        }
        assertEquals(.9, FallenHealthBars.Tier.NORMAL.width, 1e-12);
        assertEquals(.06, FallenHealthBars.Tier.NORMAL.height, 1e-12);
        assertEquals(3, FallenHealthBars.Tier.BOSS.width, 1e-12);
        assertEquals(.12, FallenHealthBars.Tier.BOSS.height, 1e-12);
        assertEquals(0, FallenHealthBars.span(.2, .2, .06).scaleX(), "empty segment collapses");
    }

    @Test void nameLineIsPointEighteenBlocksTall() {
        var t = FallenHealthBars.Tier.NORMAL;
        assertEquals(.18, t.nameScale * FallenHealthBars.LINE_PX * FallenHealthBars.PX, 1e-6);
        assertEquals(.8f, t.nameScale, 1e-6);
    }

    // ------------------------------------------------------------------ callouts

    @Test void eachCueOncePerCycle() {
        var c = new FallenCallouts();
        assertTrue(c.request(Cue.LEGS, 0, 0).isPresent());
        assertTrue(c.request(Cue.LEGS, 0, 1000).isEmpty(), "no repeat in the same cycle");
        assertTrue(c.request(Cue.LEG_BROKEN, 0, 1000).isPresent());
        assertTrue(c.request(Cue.LEG_BROKEN, 0, 2000).isEmpty());
        assertTrue(c.request(Cue.LEG_BROKEN, 1, 3000).isPresent(), "new cycle may say it again");
    }

    @Test void cooldownSuppressesChatterButNotPriorityCues() {
        var c = new FallenCallouts();
        assertTrue(c.request(Cue.LEG_BROKEN, 0, 100).isPresent());
        // EXPOSED is priority: arrives 46 ticks after the break, must not be dropped.
        assertTrue(c.request(Cue.EXPOSED, 0, 146).isPresent());
        // A non-priority cue inside the cooldown is dropped (not queued).
        assertTrue(c.request(Cue.RECOVER, 0, 146 + FallenCallouts.COOLDOWN_TICKS - 1).isEmpty());
        assertTrue(c.request(Cue.RECOVER, 0, 146 + FallenCallouts.COOLDOWN_TICKS).isPresent(),
                "a dropped cue is not remembered as said; a later request after the cooldown goes through");
        assertTrue(c.request(Cue.DOWN, 0, 147).isPresent(), "death always gets its line");
    }

    @Test void fullSimulatedFightSaysAShortReadableScript() {
        var m = new WalkerBoss.Machine(WalkerBoss.Tuning.BASE);
        var c = new FallenCallouts();
        List<Cue> said = new ArrayList<>();
        c.request(Cue.LEGS, m.cycles(), 0).ifPresent(said::add);
        long t = 0;
        while (m.phase() != Phase.DEAD && t < 20 * 600) {
            t++;
            var entered = m.tick();
            if (entered != null) FallenCallouts.forPhase(entered).flatMap(cue -> c.request(cue, m.cycles(), m.now())).ifPresent(said::add);
            for (var r : WalkerBoss.Region.values()) if (m.vulnerable(r) && t % 3 == 0) {
                // Runtime.partHit routes LEG_BROKEN to the same phase callout as tick-driven phases.
                if (m.hit(r, 3.45 * .5, null).outcome() == WalkerBoss.Outcome.LEG_BROKEN)
                    FallenCallouts.forPhase(Phase.LEG_BREAK).flatMap(cue -> c.request(cue, m.cycles(), m.now())).ifPresent(said::add);
                break;
            }
            if (m.phase() == Phase.DEAD) c.request(Cue.DOWN, m.cycles(), m.now()).ifPresent(said::add);
        }
        assertEquals(Phase.DEAD, m.phase());
        assertEquals(Cue.LEGS, said.get(0));
        assertEquals(Cue.DOWN, said.get(said.size() - 1));
        assertTrue(said.contains(Cue.EXPOSED) && said.contains(Cue.LEG_BROKEN) && said.contains(Cue.RECOVER), said.toString());
        // Never two identical cues back to back.
        for (int i = 1; i < said.size(); i++) assertNotEquals(said.get(i - 1), said.get(i), said.toString());
        // Roughly one line per phase change, never a flood.
        assertTrue(said.size() <= 2 + 3 * (m.cycles() + 1), said.toString());
    }

    @Test void calloutLinesExistAsAuthoredSubtitleOnly() {
        for (Cue cue : Cue.values()) {
            var line = kim.biryeong.destiny.campaign.presentation.RisingSubtitles.line(cue.lineId).orElseThrow(() -> new AssertionError(cue.lineId));
            assertFalse(line.voice(), cue.lineId);
            assertTrue(line.authored(), cue.lineId);
            assertEquals("고스트", line.speaker());
            assertTrue(line.text().length() <= 30, "short: " + line.text());
        }
    }
}
