package kim.biryeong.destiny.weapon;

import java.util.Random;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class AdrenalineJunkieCycleW173Test {
    @Test void startsInertAndQueriesDoNotGrantOrRefresh() {
        var c = new AdrenalineJunkieCycle();
        for (long tick : new long[]{-1, 0, 1, 90, Long.MAX_VALUE}) {
            assertEquals(0, c.stacks(tick)); assertEquals(0, c.remaining(tick));
            assertEquals(1f, c.capture(tick).multiplier());
        }
        assertTrue(c.killed(0));
        assertEquals(90, c.remaining(0));
        assertEquals(1, c.remaining(89));
        assertEquals(90, c.remaining(0)); // reads cannot advance the clock or deadline
    }

    @Test void weaponKillsAddOneUpToFiveWithExactMultipliers() {
        var c = new AdrenalineJunkieCycle();
        float[] values = {1f, 1.067f, 1.133f, 1.2f, 1.266f, 1.333f};
        assertEquals(values[0], c.multiplier(0));
        for (int n = 1; n <= 8; n++) {
            assertTrue(c.killed(n));
            assertEquals(Math.min(n, 5), c.stacks(n));
            assertEquals(values[Math.min(n, 5)], c.multiplier(n));
            assertEquals(90, c.remaining(n));
        }
    }

    @Test void everyWeaponKillRefreshesAllStacksIncludingAtCap() {
        var c = new AdrenalineJunkieCycle();
        for (int n = 0; n < 5; n++) assertTrue(c.killed(n));
        assertEquals(1, c.remaining(93));
        assertTrue(c.killed(93));
        assertEquals(5, c.stacks(182));
        assertEquals(1, c.remaining(182));
        assertEquals(0, c.stacks(183));
        assertEquals(1f, c.multiplier(183));
    }

    @Test void exactExpiryStartsAtOneAndNeverDecaysOneStackAtATime() {
        var c = new AdrenalineJunkieCycle();
        assertTrue(c.grenadeKilled(10));
        assertEquals(5, c.stacks(99));
        assertEquals(0, c.stacks(100));
        assertEquals(0, c.remaining(100));
        assertTrue(c.killed(100));
        assertEquals(1, c.stacks(100));
        assertEquals(90, c.remaining(100));
        c.update(190);
        assertEquals(0, c.stacks(190));
        assertEquals(0, c.stacks(191));
    }

    @Test void grenadeSetsFiveImmediatelyAndRefreshesExistingFive() {
        var c = new AdrenalineJunkieCycle();
        assertTrue(c.grenadeKilled(0));
        assertEquals(5, c.stacks(0));
        assertEquals(1.333f, c.multiplier(0));
        assertTrue(c.grenadeKilled(89));
        assertEquals(90, c.remaining(89));
        assertEquals(5, c.stacks(178));
        assertEquals(0, c.stacks(179));
        assertTrue(c.killed(179));
        assertTrue(c.grenadeKilled(180));
        assertEquals(5, c.stacks(180));
    }

    @Test void sameTickDistinctFinalBlowsCanReachCapAndKeepOneDeadline() {
        var c = new AdrenalineJunkieCycle();
        for (int n = 0; n < 6; n++) assertTrue(c.killed(12));
        assertEquals(5, c.stacks(12));
        assertEquals(90, c.remaining(12));
        assertEquals(0, c.remaining(102));
    }

    @Test void emissionSnapshotsDoNotChangeAfterKillRefreshExpiryOrStow() {
        var c = new AdrenalineJunkieCycle();
        var unbuffed = c.capture(0);
        c.killed(0);
        var one = c.capture(0);
        c.grenadeKilled(1);
        var five = c.capture(1);
        c.update(91); c.clear(); c.killed(92);
        assertEquals(1f, unbuffed.multiplier());
        assertEquals(1.067f, one.multiplier());
        assertEquals(1.333f, five.multiplier());
        assertEquals(1.067f, c.multiplier(92));
    }

    @Test void negativeAndBackwardEventsFailClosedWithoutMovingDeadline() {
        var c = new AdrenalineJunkieCycle();
        assertFalse(c.killed(-1)); assertFalse(c.grenadeKilled(Long.MIN_VALUE));
        c.killed(100); c.update(120);
        assertEquals(0, c.stacks(119)); assertEquals(0, c.remaining(-1));
        assertEquals(1f, c.multiplier(119));
        assertFalse(c.killed(119)); assertFalse(c.grenadeKilled(100));
        c.update(119); c.update(-1);
        assertEquals(1, c.stacks(120)); assertEquals(70, c.remaining(120));
        assertTrue(c.killed(120)); assertEquals(2, c.stacks(120));
    }

    @Test void overflowIsRejectedAndLastSafeDeadlineExpiresExactly() {
        var c = new AdrenalineJunkieCycle();
        long lastSafe = Long.MAX_VALUE - 90;
        assertTrue(c.killed(lastSafe));
        assertEquals(90, c.remaining(lastSafe));
        assertFalse(c.killed(lastSafe + 1)); assertFalse(c.grenadeKilled(Long.MAX_VALUE));
        assertEquals(1, c.stacks(Long.MAX_VALUE - 1));
        assertEquals(1, c.remaining(Long.MAX_VALUE - 1));
        assertEquals(0, c.stacks(Long.MAX_VALUE));
        assertEquals(1f, c.multiplier(Long.MAX_VALUE));
    }

    @Test void revocationClearsImmediatelyIncludingSameTickAndRetainsClockGuard() {
        var c = new AdrenalineJunkieCycle();
        c.grenadeKilled(12); c.clear();
        assertEquals(0, c.stacks(12)); assertEquals(0, c.remaining(12));
        assertEquals(1f, c.multiplier(12));
        assertFalse(c.killed(11));
        assertTrue(c.killed(12)); assertEquals(1, c.stacks(12));
        c.update(102); c.clear();
        assertFalse(c.grenadeKilled(101));
        assertTrue(c.grenadeKilled(102)); assertEquals(5, c.stacks(102));
    }

    @Test void deterministicMixedEventScheduleMatchesSingleDeadlineModel() {
        var c = new AdrenalineJunkieCycle();
        var random = new Random(110);
        long tick = 0, deadline = -1;
        int count = 0;
        for (int n = 0; n < 10000; n++) {
            tick += random.nextInt(100);
            if (tick >= deadline) count = 0;
            switch (random.nextInt(4)) {
                case 0 -> { assertTrue(c.killed(tick)); count = Math.min(5, count + 1); deadline = tick + 90; }
                case 1 -> { assertTrue(c.grenadeKilled(tick)); count = 5; deadline = tick + 90; }
                case 2 -> { c.clear(); count = 0; deadline = -1; }
                default -> c.update(tick);
            }
            assertEquals(count, c.stacks(tick));
            assertEquals(count == 0 ? 0 : deadline - tick, c.remaining(tick));
        }
    }
}
