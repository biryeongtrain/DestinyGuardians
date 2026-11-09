package kim.biryeong.destiny.weapon;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class PerkExpansionStatsCycleTest {
    private static void sample(PerkExpansionStatsCycle c, long tick, boolean sprint) {
        c.sample(tick, true, sprint, false, false, false);
    }
    @Test void confirmedHitsExpireRefreshAndSaturateWithoutGetterMutation() {
        var c = new PerkExpansionStatsCycle();
        c.hit(0, 3); assertEquals(3, c.enlightenedStacks(0)); assertEquals(12, c.enlightenedBonus(0));
        c.hit(39, 3); assertEquals(6, c.enlightenedStacks(39));
        for (int i = 0; i < 10; i++) c.enlightenedStacks(60);
        assertEquals(19, c.enlightenedRemaining(60));
        c.hit(78, 10); assertEquals(12, c.enlightenedStacks(78)); assertEquals(50, c.enlightenedBonus(78));
        assertEquals(0, c.enlightenedStacks(118));
        c.hit(118, 1); assertEquals(1, c.enlightenedStacks(118));
        c.hit(119, 0); assertEquals(39, c.enlightenedRemaining(119));
    }
    @Test void sprintRequiresContinuousHeldTimeThenLingersAndRestarts() {
        var c = new PerkExpansionStatsCycle();
        sample(c, 0, true); sample(c, 29, true); assertEquals(0, c.eddyRemaining(29));
        sample(c, 30, true); assertEquals(60, c.eddyRemaining(30));
        sample(c, 31, false); assertEquals(59, c.eddyRemaining(31));
        sample(c, 70, true); assertEquals(60, c.eddyRemaining(70));
        sample(c, 71, false); assertEquals(59, c.eddyRemaining(71));
        sample(c, 130, false); assertEquals(0, c.eddyRemaining(130));
        sample(c, 131, true); sample(c, 160, true); assertEquals(0, c.eddyRemaining(160));
        sample(c, 161, true); assertEquals(60, c.eddyRemaining(161));
    }
    @Test void interruptedSprintAndStowDoNotBorrowProgress() {
        var c = new PerkExpansionStatsCycle();
        sample(c, 0, true); sample(c, 29, false); sample(c, 30, true);
        sample(c, 59, true); assertEquals(0, c.eddyRemaining(59));
        sample(c, 60, true); assertEquals(20, c.eddyReload(60));
        c.stowed(61); assertEquals(0, c.eddyRemaining(61));
        sample(c, 62, true); sample(c, 91, true); assertEquals(0, c.eddyRemaining(91));
    }
    @Test void amplifiedIsHeldOnlyAndDoesNotFabricateSprintTimer() {
        var c = new PerkExpansionStatsCycle();
        c.sample(0, true, false, true, false, false); assertEquals(60, c.eddyReload(0));
        c.sample(1, true, false, false, false, false); assertEquals(0, c.eddyRemaining(1));
        c.sample(2, false, false, true, false, false); assertEquals(0, c.eddyReload(2));
    }
    @Test void perfectFloatAcceptsThreeSecondSpacingButNotLongerGaps() {
        var c = new PerkExpansionStatsCycle();
        c.damage(0); c.damage(60); sample(c, 119, false); assertEquals(0, c.floatRemaining(119));
        c.damage(120); assertEquals(200, c.floatRemaining(120));
        sample(c, 180, false); assertEquals(140, c.floatRemaining(180));
        c.damage(200); assertEquals(200, c.floatRemaining(200));
        sample(c, 400, false); assertEquals(0, c.floatRemaining(400));
        c = new PerkExpansionStatsCycle(); c.damage(0); c.damage(61); c.damage(121);
        sample(c, 180, false); assertEquals(0, c.floatRemaining(180));
        c.damage(181); assertEquals(200, c.floatRemaining(181));
    }
    @Test void stowRevokesOffhandButPreservesEarnedCombatAndHitEffects() {
        var c = new PerkExpansionStatsCycle();
        c.damage(0); c.damage(60); c.damage(120); c.hit(120, 3); c.kill(120);
        c.stowed(121);
        assertEquals(0, c.offhandRemaining(121)); assertEquals(199, c.floatRemaining(121));
        assertEquals(3, c.enlightenedStacks(121));
        c.kill(122); assertEquals(140, c.offhandRemaining(122));
        assertEquals(0, c.offhandRemaining(262));
    }
    @Test void twoWeaponsHaveIndependentTimersAndResetRevokesEverything() {
        var one = new PerkExpansionStatsCycle(); var two = new PerkExpansionStatsCycle();
        one.kill(0); one.hit(0, 3); sample(one, 0, true); sample(one, 30, true);
        sample(two, 30, false);
        assertEquals(0, two.offhandRemaining(30)); assertEquals(0, two.enlightenedStacks(30));
        assertEquals(0, two.eddyRemaining(30));
        one.reset(); assertEquals(0, one.offhandRemaining(30)); assertEquals(0, one.enlightenedStacks(30));
        assertEquals(0, one.eddyRemaining(30)); assertFalse(one.keepAway(30));
    }
    @Test void backwardsClockAndOverflowRemainBounded() {
        var c = new PerkExpansionStatsCycle();
        c.kill(200); c.hit(200, 3); sample(c, 10, false);
        assertEquals(0, c.offhandRemaining(10)); assertEquals(0, c.enlightenedStacks(10));
        assertThrows(IllegalArgumentException.class, () -> sample(c, -1, false));
        c.kill(Long.MAX_VALUE - 2); assertEquals(2, c.offhandRemaining(Long.MAX_VALUE - 2));
        assertEquals(0, c.offhandRemaining(Long.MAX_VALUE)); assertEquals(0, c.offhandRemaining(-1));
    }
}
