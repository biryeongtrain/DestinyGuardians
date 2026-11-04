package kim.biryeong.destiny.weapon;

import com.google.gson.JsonParser;
import org.junit.jupiter.api.Test;
import java.nio.charset.StandardCharsets;
import java.util.*;
import static org.junit.jupiter.api.Assertions.*;

class PerkBatchAW320Test {
    @Test void killingWindStartsFiveSecondsExtendsFiveAndCapsAtEightRemaining() {
        var c = new KillingWindCycle();
        c.killed(0, 100, 100, 160);
        assertEquals(100, c.remaining(0));
        c.killed(50, 100, 100, 160);
        assertEquals(150, c.remaining(50));
        c.killed(60, 100, 100, 160);
        assertEquals(160, c.remaining(60));
        c.stowed();
        assertFalse(c.active(61));
        c.killed(300, 100, 100, 160);
        assertEquals(100, c.remaining(300));
    }

    @Test void airAssaultStacksRefreshAndAirborneKillsGrantTwo() {
        var c = new AirAssaultCycle();
        c.killed(0, false, 2, 2, 100);
        assertEquals(1, c.stacks(99));
        assertEquals(0, c.stacks(100));
        c.killed(200, false, 2, 2, 100);
        c.killed(250, false, 2, 2, 100);
        assertEquals(2, c.stacks(349));
        c.killed(400, false, 2, 2, 100); // expired at 350 -> fresh single stack
        assertEquals(1, c.stacks(400));
        c.killed(500, true, 2, 2, 100);
        assertEquals(2, c.stacks(500));
        c.stowed();
        assertEquals(0, c.stacks(501));
    }

    @Test void shotSwapBanksTwoPerKillCapsAtSixAndConsumesOnePerStow() {
        var c = new ShotSwapCycle();
        assertFalse(c.stowed());
        for (int i = 0; i < 4; i++) c.killed(2, 6);
        assertEquals(6, c.stacks());
        assertTrue(c.stowed());
        assertEquals(5, c.stacks());
    }

    @Test void slideNeedsRecentSprintGroundCrouchEdgeAndSpeed() {
        var d = new SlideDetector();
        long t = 0;
        for (; t < 40; t++) assertFalse(d.sample(t, true, true, false, .28));
        assertTrue(d.sample(t, true, false, true, .25));
        assertEquals(40, d.sprintTicksAtSlide());
        assertFalse(d.sample(++t, true, false, true, .2)); // held crouch is not a new slide
        // plain crouch without sprint
        var e = new SlideDetector();
        assertFalse(e.sample(0, true, false, false, .1));
        assertFalse(e.sample(1, true, false, true, .3));
        // airborne or too slow or sprint too long ago
        for (boolean ground : new boolean[]{false, true}) {
            var f = new SlideDetector();
            f.sample(0, true, true, false, .28);
            f.sample(1, true, true, false, .28);
            assertFalse(f.sample(2, ground, false, true, ground ? .05 : .3));
        }
        var g = new SlideDetector();
        g.sample(0, true, true, false, .28);
        for (int i = 1; i <= 3; i++) g.sample(i, true, false, false, .28);
        assertFalse(g.sample(4, true, false, true, .3));
        // non-contiguous sampling never starts a slide
        var h = new SlideDetector();
        h.sample(0, true, true, false, .28);
        assertFalse(h.sample(5, true, false, true, .3));
    }

    @Test void slideBuffCooldownFirstShotStowAndRefillRounding() {
        var c = new SlideBuffCycle();
        assertTrue(c.slide(0, 50, 6));
        assertFalse(c.slide(5, 50, 6));
        assertTrue(c.slide(6, 50, 6));
        assertEquals(50, c.remaining(6));
        c.shot();
        assertFalse(c.active(7));
        assertTrue(c.slide(20, 60, 10));
        c.stowed();
        assertFalse(c.active(20));
        assertEquals(3, SlideBuffCycle.refillRounds(20, .15));
        assertEquals(1, SlideBuffCycle.refillRounds(4, .15));
        assertEquals(5, SlideBuffCycle.refillRounds(33, .15));
        assertEquals(0, SlideBuffCycle.refillRounds(0, .15));
    }

    @Test void kickstartRequiresSprintStreak() {
        var c = new KickstartCycle();
        assertFalse(c.slide(0, 29, 30, 40));
        assertFalse(c.active(0));
        assertTrue(c.slide(10, 30, 30, 40));
        assertTrue(c.active(49));
        assertFalse(c.active(50));
    }

    @Test void tunnelVisionNeedsReloadWithinWindowOfKillAndSpendsTheKill() {
        var c = new TunnelVisionCycle();
        assertFalse(c.reloadFinished(10, 72, 100));
        c.killed(100);
        assertFalse(c.reloadFinished(173, 72, 100));
        c.killed(200);
        assertTrue(c.reloadFinished(272, 72, 100));
        assertEquals(100, c.remaining(272));
        assertFalse(c.reloadFinished(280, 72, 100)); // kill already spent
        c.killed(300);
        assertTrue(c.reloadFinished(310, 72, 100)); // refresh
        assertEquals(100, c.remaining(310));
    }

    @Test void eyeOfTheStormHysteresisAndLinearFraction() {
        var c = new ShieldTraitCycle();
        c.sample(0, 60, 40, 80, 20);
        assertEquals(0, c.eyeFraction(60, 80)); // not yet triggered
        c.sample(1, 40, 40, 80, 20);
        assertEquals(.5, c.eyeFraction(40, 80), 1e-9);
        c.sample(2, 60, 40, 80, 20);
        assertEquals(.25, c.eyeFraction(60, 80), 1e-9); // persists above trigger
        c.sample(3, 0, 40, 80, 20);
        assertEquals(1, c.eyeFraction(0, 80), 1e-9);
        c.sample(4, 80, 40, 80, 20);
        assertEquals(0, c.eyeFraction(80, 80));
    }

    @Test void fragileFocusOffAtZeroShieldBackOneSecondAfterFull() {
        var c = new ShieldTraitCycle();
        assertTrue(c.fragileActive());
        c.sample(0, 10, 40, 80, 20);
        assertTrue(c.fragileActive());
        c.sample(1, 0, 40, 80, 20);
        assertFalse(c.fragileActive());
        c.sample(2, 129, 40, 80, 20);
        c.sample(3, 130, 40, 80, 20);
        c.sample(22, 130, 40, 80, 20);
        assertFalse(c.fragileActive());
        c.sample(23, 130, 40, 80, 20);
        assertTrue(c.fragileActive());
        // a dip below full restarts the reactivation timer
        var d = new ShieldTraitCycle();
        d.sample(0, 0, 40, 80, 20);
        d.sample(1, 130, 40, 80, 20);
        d.sample(10, 120, 40, 80, 20);
        d.sample(25, 130, 40, 80, 20);
        d.sample(44, 130, 40, 80, 20);
        assertFalse(d.fragileActive());
        d.sample(45, 130, 40, 80, 20);
        assertTrue(d.fragileActive());
    }

    @Test void baitAndSwitchChainWindowNoRefreshAndRetrigger() {
        var a = new Object(); var b = new Object(); var c = new Object();
        var equipped = List.of(a, b, c);
        var cycle = new BaitAndSwitchCycle();
        assertFalse(cycle.damaged(0, a, equipped, 140, 200));
        assertFalse(cycle.damaged(100, b, equipped, 140, 200));
        assertFalse(cycle.damaged(300, c, equipped, 140, 200)); // gap 200 > 140 resets the chain
        assertFalse(cycle.damaged(400, a, equipped, 140, 200));
        assertTrue(cycle.damaged(500, b, equipped, 140, 200));
        assertEquals(200, cycle.remaining(500));
        assertFalse(cycle.damaged(600, a, equipped, 140, 200)); // timer disabled while active
        assertFalse(cycle.damaged(650, b, equipped, 140, 200));
        assertFalse(cycle.damaged(690, c, equipped, 140, 200));
        assertEquals(10, cycle.remaining(690));
        assertFalse(cycle.active(700));
        assertFalse(cycle.damaged(700, a, equipped, 140, 200)); // fresh chain after expiry
        assertFalse(cycle.damaged(710, b, equipped, 140, 200));
        assertTrue(cycle.damaged(720, c, equipped, 140, 200));
        // unequipped weapons never complete a chain
        var other = new BaitAndSwitchCycle();
        assertFalse(other.damaged(0, new Object(), List.of(a), 140, 200));
        assertTrue(other.damaged(1, a, List.of(a), 140, 200));
    }

    @Test void statCurvesScaleByRatioAndStayNeutralWithoutBonus() {
        assertEquals(40, WeaponStatCurves.handlingTicks("dream_breaker", true, 40, 0, 1));
        assertEquals(40, WeaponStatCurves.handlingTicks("not_a_weapon", true, 40, 30, .8));
        int buffed = WeaponStatCurves.handlingTicks("dream_breaker", true, 40, 30, 1);
        assertTrue(buffed < 40 && buffed > 0);
        assertTrue(WeaponStatCurves.handlingTicks("dream_breaker", true, 40, 30, .7) < buffed);
        // Field Prep: +50 reload with x0.8 on duke (base reload 30)
        int reload = WeaponStatCurves.reloadTicks("duke_mk_44", 59, 50, .8);
        assertTrue(reload < 59 * .8);
        // stat cap: bonus beyond 100 behaves as 100
        assertEquals(WeaponStatCurves.handlingTicks("code_duello", false, 20, 31, 1),
            WeaponStatCurves.handlingTicks("code_duello", false, 20, 500, 1));
        assertTrue(WeaponStatCurves.adsTicks("dream_breaker", 6, 40, .8) >= 2);
    }

    @Test void pinnedPoolsLabelsAndFacadeRegistry() throws Exception {
        var expected = Map.ofEntries(Map.entry(FieldPrepProfile.ID, 13), Map.entry(SlidewaysProfile.ID, 9),
            Map.entry(SlideshotProfile.ID, 7), Map.entry(EyeOfTheStormProfile.ID, 7), Map.entry(KillingWindProfile.ID, 11),
            Map.entry(AirAssaultProfile.ID, 3), Map.entry(TunnelVisionProfile.ID, 3), Map.entry(FragileFocusProfile.ID, 1),
            Map.entry(KickstartProfile.ID, 1), Map.entry(ShotSwapProfile.ID, 1), Map.entry(BaitAndSwitchProfile.ID, 1));
        assertEquals(expected.keySet(), Set.copyOf(PerkBatchA.ids()));
        String labels;
        try (var in = PerkBatchAW320Test.class.getResourceAsStream("/destiny/weapons/w320-perks-ko-a.json")) {
            labels = new String(in.readAllBytes(), StandardCharsets.UTF_8);
        }
        var perks = JsonParser.parseString(labels).getAsJsonObject().getAsJsonObject("perks");
        for (var e : expected.entrySet()) {
            var rolls = PerkBatchA.rolls(e.getKey());
            assertEquals(e.getValue(), rolls.size(), e.getKey());
            long hash = rolls.getFirst().perkHash();
            assertTrue(rolls.stream().allMatch(r -> r.perkHash() == hash));
            assertTrue(WeaponStatCurves.supports(rolls.getFirst().id()));
            assertNotNull(PerkBatchA.name(e.getKey()));
            assertEquals(PerkBatchA.name(e.getKey()), perks.getAsJsonObject(e.getKey()).get("name").getAsString());
            assertEquals(hash, perks.getAsJsonObject(e.getKey()).get("hash").getAsLong());
        }
        assertTrue(perks.getAsJsonObject(KickstartProfile.ID).get("damage").getAsBoolean());
        assertTrue(perks.getAsJsonObject(BaitAndSwitchProfile.ID).get("damage").getAsBoolean());
        assertFalse(perks.getAsJsonObject(KillingWindProfile.ID).get("damage").getAsBoolean());
        assertEquals(List.of(), PerkBatchA.rolls("unknown"));
        assertEquals(new WeaponPerks.Roll("dimensional_hypotrochoid", ShotSwapProfile.rolls().getFirst().hash(), 3,
            ShotSwapProfile.HASH, ShotSwapProfile.rolls().getFirst().plugSetHash()), ShotSwapProfile.rolls().getFirst());
        assertEquals(1.05, KillingWindProfile.falloffScalar(), 1e-12);
        assertEquals(.2, WeaponKillingWind.speedMultiplier(), 1e-12);
    }
}
