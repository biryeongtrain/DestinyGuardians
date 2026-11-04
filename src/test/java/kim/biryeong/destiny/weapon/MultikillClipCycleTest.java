package kim.biryeong.destiny.weapon;

import java.util.Random;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class MultikillClipCycleTest {
    private static MultikillClipCycle buff(int count, long killTick, long reloadTick) {
        var cycle = new MultikillClipCycle();
        for (int i = 0; i < count; i++) assertTrue(cycle.killed(killTick));
        assertTrue(cycle.reloaded(reloadTick));
        return cycle;
    }

    @Test void startsInertAndKillsAloneNeverGrantDamage() {
        var c = new MultikillClipCycle();
        for (long tick : new long[]{-1, 0, 100, Long.MAX_VALUE}) {
            assertEquals(0, c.stacks(tick)); assertEquals(0, c.remaining(tick));
            assertEquals(1f, c.capture(tick).multiplier());
        }
        assertFalse(c.reloaded(0));
        for (int n = 0; n < 5; n++) assertTrue(c.killed(0));
        assertEquals(0, c.stacks(0)); assertEquals(1f, c.capture(0).multiplier());
        assertTrue(c.reloaded(0)); assertEquals(3, c.stacks(0));
    }

    @Test void exactOneTwoThreeBonusesAndCap() {
        float[] multipliers = {1f, 1.17f, 1.33f, 1.5f};
        for (int n = 1; n <= 8; n++) {
            var c = buff(n, 12, 15);
            assertEquals(Math.min(n, 3), c.stacks(15));
            assertEquals(multipliers[Math.min(n, 3)], c.capture(15).multiplier());
            assertEquals(100, c.remaining(15));
        }
    }

    @Test void eachKillGapIsInclusiveSeventyTicksNotTotalChainDuration() {
        var c = new MultikillClipCycle();
        c.killed(0); c.update(70); c.killed(70); c.killed(140);
        assertTrue(c.reloaded(212));
        assertEquals(3, c.stacks(212));
        var reset = new MultikillClipCycle();
        reset.killed(0); reset.killed(71); reset.reloaded(71);
        assertEquals(1, reset.stacks(71));
    }

    @Test void reloadBoundaryIsInclusiveSeventyTwoAndDoesNotUseKillGap() {
        for (int delta : new int[]{70, 71, 72}) {
            var c = new MultikillClipCycle();
            c.killed(10); c.killed(10); c.update(10 + delta);
            assertTrue(c.reloaded(10 + delta));
            assertEquals(2, c.stacks(10 + delta));
        }
        var late = new MultikillClipCycle();
        late.killed(10); assertFalse(late.reloaded(83));
        assertEquals(0, late.stacks(83));
    }

    @Test void fourthKillAtCapRefreshesLastKillForReload() {
        var c = new MultikillClipCycle();
        for (int tick : new int[]{0, 70, 140, 210}) c.killed(tick);
        assertTrue(c.reloaded(282)); assertEquals(3, c.stacks(282));
    }

    @Test void qualifyingReloadConsumesChainAndRepeatedInsertDoesNotExtendDeadline() {
        var c = buff(3, 0, 1);
        assertFalse(c.reloaded(2)); assertFalse(c.reloaded(72));
        assertEquals(3, c.stacks(100)); assertEquals(1, c.remaining(100));
        assertFalse(c.reloaded(101)); assertEquals(0, c.stacks(101));
    }

    @Test void weakerQualifyingReloadOverwritesStrongerBuffAndGetsNewDeadline() {
        var c = buff(3, 0, 1);
        c.killed(20);
        assertEquals(3, c.stacks(20)); // kills do not change existing paid damage
        assertTrue(c.reloaded(21));
        assertEquals(1, c.stacks(21)); assertEquals(1.17f, c.capture(21).multiplier());
        assertEquals(100, c.remaining(21));
        assertEquals(1, c.stacks(120)); assertEquals(0, c.stacks(121));
    }

    @Test void strongerAndSameStrengthRetriggersAreAlsoOverwrites() {
        var c = buff(1, 0, 0);
        for (int tick : new int[]{1, 2, 3}) c.killed(tick);
        assertTrue(c.reloaded(4)); assertEquals(3, c.stacks(4));
        for (int i = 0; i < 3; i++) c.killed(5);
        assertTrue(c.reloaded(6)); assertEquals(3, c.stacks(6));
        assertEquals(100, c.remaining(6));
    }

    @Test void expiredKillChainReloadPreservesExistingBuffAndDoesNotRefresh() {
        var c = buff(3, 0, 0);
        c.killed(1); c.update(74);
        assertFalse(c.reloaded(74));
        assertEquals(3, c.stacks(74)); assertEquals(26, c.remaining(74));
        assertFalse(c.reloaded(99)); assertEquals(1, c.remaining(99));
        assertEquals(0, c.stacks(100));
    }

    @Test void buffDeadlineIsExclusiveAndPendingKillsCanOutliveBuff() {
        var c = buff(2, 0, 1);
        c.killed(100);
        assertEquals(2, c.stacks(100)); assertEquals(1, c.remaining(100));
        c.update(101);
        assertEquals(0, c.stacks(101)); assertEquals(1f, c.capture(101).multiplier());
        assertTrue(c.reloaded(101)); assertEquals(1, c.stacks(101));
    }

    @Test void stowClearsLiveBuffAndPendingKillsRetainingClockGuard() {
        var c = buff(3, 10, 12); c.killed(13); c.clear();
        assertEquals(0, c.stacks(13)); assertEquals(0, c.remaining(13));
        assertFalse(c.reloaded(13)); assertFalse(c.killed(12));
        assertTrue(c.killed(14)); assertTrue(c.reloaded(14));
        assertEquals(1, c.stacks(14));
        c.clear(); c.clear(); assertFalse(c.reloaded(15));
    }

    @Test void snapshotsStayFrozenAcrossKillReloadDowngradeExpiryAndStow() {
        var c = new MultikillClipCycle();
        var initial = c.capture(0);
        c.killed(0); c.killed(0); c.killed(0);
        var killingShot = c.capture(0);
        c.reloaded(1); var three = c.capture(1);
        c.killed(2); c.reloaded(2); var one = c.capture(2);
        c.update(102); c.clear();
        assertEquals(1f, initial.multiplier()); assertEquals(1f, killingShot.multiplier());
        assertEquals(1.5f, three.multiplier()); assertEquals(1.17f, one.multiplier());
        assertEquals(1f, c.capture(102).multiplier());
    }

    @Test void readsCannotCreateConsumeExpireOrMoveDeadlines() {
        var c = buff(2, 10, 12);
        assertEquals(100, c.remaining(12));
        c.killed(20);
        assertEquals(0, c.stacks(1000)); assertEquals(0, c.remaining(-1));
        assertEquals(92, c.remaining(20));
        assertEquals(2, c.stacks(20));
        assertTrue(c.reloaded(20)); assertEquals(1, c.stacks(20));
    }

    @Test void negativeBackwardEventsAndReadsFailClosedWithoutMutatingValidState() {
        var c = buff(2, 100, 100); c.killed(110); c.update(120);
        for (long tick : new long[]{Long.MIN_VALUE, -1, 0, 100, 119}) {
            assertFalse(c.killed(tick)); assertFalse(c.reloaded(tick)); c.update(tick);
            assertEquals(0, c.stacks(tick)); assertEquals(0, c.remaining(tick));
            assertEquals(1f, c.capture(tick).multiplier());
        }
        assertEquals(2, c.stacks(120)); assertEquals(80, c.remaining(120));
        assertTrue(c.reloaded(120)); assertEquals(1, c.stacks(120));
    }

    @Test void overflowReloadFailsClosedAndLastSafeDeadlineExpiresExactly() {
        long lastSafe = Long.MAX_VALUE - 100;
        var c = buff(3, lastSafe, lastSafe);
        assertEquals(100, c.remaining(lastSafe));
        assertEquals(3, c.stacks(Long.MAX_VALUE - 1)); assertEquals(1, c.remaining(Long.MAX_VALUE - 1));
        assertEquals(0, c.stacks(Long.MAX_VALUE));
        c.killed(lastSafe + 1);
        assertFalse(c.reloaded(lastSafe + 1));
        assertEquals(99, c.remaining(lastSafe + 1));
        var extreme = new MultikillClipCycle();
        assertTrue(extreme.killed(Long.MAX_VALUE));
        assertFalse(extreme.reloaded(Long.MAX_VALUE));
        extreme.update(Long.MAX_VALUE);
        assertEquals(0, extreme.stacks(Long.MAX_VALUE));
    }

    @Test void deterministicSchedulesMatchIndependentKillListAndBuffModel() {
        var c = new MultikillClipCycle(); var random = new Random(165);
        var chain = new java.util.ArrayList<Long>();
        long tick = 0, deadline = -1; int count = 0;
        for (int n = 0; n < 20000; n++) {
            tick += random.nextInt(80);
            if (tick >= deadline) count = 0;
            switch (random.nextInt(5)) {
                case 0, 1 -> {
                    if (!chain.isEmpty() && tick - chain.getLast() > 70) chain.clear();
                    chain.add(tick); assertTrue(c.killed(tick));
                }
                case 2 -> {
                    boolean qualifies = !chain.isEmpty() && tick - chain.getLast() <= 72;
                    assertEquals(qualifies, c.reloaded(tick));
                    if (qualifies) { count = Math.min(3, chain.size()); deadline = tick + 100; }
                    chain.clear();
                }
                case 3 -> { c.clear(); chain.clear(); count = 0; deadline = -1; }
                default -> c.update(tick);
            }
            assertEquals(count, c.stacks(tick));
            assertEquals(count == 0 ? 0 : deadline - tick, c.remaining(tick));
        }
    }
}
