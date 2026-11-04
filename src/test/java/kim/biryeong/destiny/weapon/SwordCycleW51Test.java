package kim.biryeong.destiny.weapon;

import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;

/** Pure checks for authored Minecraft sword tuning, not exact Destiny stat assertions. */
class SwordCycleW51Test {
    @Test void bindingClampsCorruptEnergyAndDelayWithoutGrantingEnergy() {
        var c = new SwordCycle();
        c.bind(Integer.MIN_VALUE, Integer.MIN_VALUE, 50);
        assertEquals(0, c.energy());
        assertEquals(0, c.rechargeRemaining(50));
        c.bind(Integer.MAX_VALUE, Integer.MAX_VALUE, 80);
        assertEquals(SwordCycle.CAPACITY, c.energy());
        assertEquals(SwordCycle.RECHARGE_DELAY, c.rechargeRemaining(80));
        assertEquals(SwordCycle.RECHARGE_DELAY, c.rechargeRemaining(Long.MIN_VALUE));
        c.bind(42_123, 7, 100);
        assertEquals(42_123, c.energy());
        assertEquals(7, c.rechargeRemaining(100));
        assertEquals(1, c.rechargeRemaining(106));
        assertEquals(0, c.rechargeRemaining(107));
        assertEquals(0, c.rechargeRemaining(Long.MAX_VALUE));
        assertEquals(42_123, c.energy());
    }

    @Test void defaultStateIsEmptyAndGettersNeverChargeIt() {
        var c = new SwordCycle();
        for (int i = 0; i < 10; i++) {
            assertEquals(0, c.energy());
            assertFalse(c.guarding());
            assertEquals(0, c.combo());
            assertEquals(0, c.rechargeRemaining(Long.MAX_VALUE));
        }
    }

    @Test void duplicateAndBackwardTicksNeitherDrainNorRefreshDelayOrChangeActions() {
        var c = new SwordCycle();
        c.bind(20_000, 100);
        c.tick(100, true, true, true);
        c.tick(99, true, true, true);
        assertEquals(20_000, c.energy());
        assertFalse(c.guarding());
        c.tick(101, true, true, true);
        assertEquals(19_500, c.energy());
        assertTrue(c.guarding());
        c.tick(101, false, false, false);
        c.tick(Long.MIN_VALUE, false, false, false);
        assertEquals(19_500, c.energy());
        assertTrue(c.guarding());
        assertEquals(19, c.rechargeRemaining(102));
        c.light(101);
        c.tick(101, true, true, true);
        c.tick(100, true, true, true);
        assertFalse(c.guarding());
        assertEquals(1, c.combo());
        c.tick(102, true, true, true);
        assertEquals(19_000, c.energy());
        assertEquals(20, c.rechargeRemaining(102));
        c.tick(121, false, true, true);
        c.tick(121, true, true, true);
        c.tick(120, true, true, true);
        assertEquals(19_000, c.energy());
        assertEquals(1, c.rechargeRemaining(121));
        assertFalse(c.guarding());
        c.tick(122, false, true, true);
        c.tick(122, false, true, true);
        assertEquals(20_250, c.energy());
    }

    @Test void authoredFourSecondRechargeSaturatesWithoutOverflow() {
        var c = new SwordCycle();
        c.bind(0, 0);
        for (int tick = 1; tick < 80; tick++) c.tick(tick, false, false, false);
        assertEquals(98_750, c.energy());
        c.tick(80, false, false, false);
        assertEquals(SwordCycle.CAPACITY, c.energy());
        c.tick(81, false, false, false);
        assertEquals(SwordCycle.CAPACITY, c.energy());
        c.bind(SwordCycle.CAPACITY - 1, 100);
        c.tick(101, false, false, false);
        assertEquals(SwordCycle.CAPACITY, c.energy());
    }

    @Test void authoredContinuousGuardDrainsWithoutHitsOrRegeneration() {
        var c = new SwordCycle();
        c.bind(SwordCycle.CAPACITY, 0);
        for (int tick = 1; tick <= 200; tick++) {
            c.tick(tick, true, true, true);
            assertEquals(100_000 - tick * 500, c.energy());
            assertEquals(tick < 200, c.guarding());
            assertEquals(20, c.rechargeRemaining(tick));
        }
        assertEquals(0, c.energy());
        assertFalse(c.guarding());
    }

    @Test void guardDrainIsBoundedAcrossTheEntireStoredEnergyRange() {
        var c = new SwordCycle();
        for (int stored = 0; stored <= SwordCycle.CAPACITY; stored++) {
            c.bind(stored, 20, 0);
            c.tick(1, true, true, true);
            assertEquals(Math.max(0, stored - 500), c.energy());
            assertEquals(stored > 500, c.guarding());
            assertEquals(stored > 0 ? 20 : 19, c.rechargeRemaining(1));
            c.tick(1, true, true, true);
            assertEquals(Math.max(0, stored - 500), c.energy());
        }
    }

    @Test void guardRequiresEveryGateButNonGuardRechargeDoesNot() {
        for (int mask = 0; mask < 8; mask++) {
            var c = new SwordCycle();
            c.bind(10_000, 0);
            c.tick(1, (mask & 1) != 0, (mask & 2) != 0, (mask & 4) != 0);
            assertEquals(mask == 7, c.guarding(), "guard gates " + mask);
            assertEquals(mask == 7 ? 9_500 : 11_250, c.energy());
            assertEquals(mask == 7 ? 20 : 0, c.rechargeRemaining(1));
        }
    }

    @Test void releasingOrLosingAmmoOrReadinessStopsDrainAndHonorsTheLastGuardDelay() {
        for (int mask = 0; mask < 7; mask++) {
            var c = new SwordCycle();
            c.bind(10_000, 0);
            c.tick(1, true, true, true);
            boolean wantsGuard = (mask & 1) != 0;
            boolean hasAmmo = (mask & 2) != 0;
            boolean attackReady = (mask & 4) != 0;
            for (int tick = 2; tick <= 20; tick++) {
                c.tick(tick, wantsGuard, hasAmmo, attackReady);
                assertFalse(c.guarding());
                assertEquals(9_500, c.energy());
            }
            assertEquals(1, c.rechargeRemaining(20));
            c.tick(21, wantsGuard, hasAmmo, attackReady);
            assertEquals(10_750, c.energy());
            assertFalse(c.guarding());
        }
    }

    @Test void emptyGuardNeedsARegenerationStepBeforeItCanStart() {
        var c = new SwordCycle();
        c.bind(0, SwordCycle.RECHARGE_DELAY, 100);
        c.tick(119, true, true, true);
        assertFalse(c.guarding());
        assertEquals(0, c.rechargeRemaining(120));
        assertEquals(0, c.energy());
        c.tick(120, true, true, true);
        assertEquals(1_250, c.energy());
        assertFalse(c.guarding());
        c.tick(120, true, true, true);
        assertFalse(c.guarding());
        c.tick(121, true, true, true);
        assertEquals(750, c.energy());
        assertTrue(c.guarding());
        assertEquals(20, c.rechargeRemaining(121));
    }

    @Test void exhaustionCannotRegenerateUntilTheFinalDrainDelayExpires() {
        var c = new SwordCycle();
        c.bind(500, 0);
        c.tick(1, true, true, true);
        assertEquals(0, c.energy());
        assertFalse(c.guarding());
        c.tick(20, true, true, true);
        assertEquals(0, c.energy());
        assertEquals(1, c.rechargeRemaining(20));
        c.tick(21, true, true, true);
        assertEquals(1_250, c.energy());
        assertFalse(c.guarding());
        c.tick(22, true, true, true);
        assertEquals(750, c.energy());
        assertTrue(c.guarding());
    }

    @Test void observingGuardForDamageHandlingDoesNotDrainEnergyOrRefreshDelay() {
        // Damage handling only reads guard state: there is no incoming-hit mutation API.
        var c = new SwordCycle();
        c.bind(10_000, 0);
        c.tick(1, true, true, true);
        for (int hit = 0; hit < 1_000; hit++) {
            assertTrue(c.guarding());
            assertEquals(9_500, c.energy());
            assertEquals(19, c.rechargeRemaining(2));
        }
        c.tick(2, true, true, true);
        assertEquals(9_000, c.energy());
        assertEquals(20, c.rechargeRemaining(2));
    }

    @Test void lightStopsGuardWithoutSpendingEnergyOrExtendingTheGuardRechargeDelay() {
        var c = new SwordCycle();
        c.bind(50_000, 0);
        c.tick(1, true, true, true);
        assertEquals(1, c.light(2));
        assertFalse(c.guarding());
        assertEquals(49_500, c.energy());
        assertEquals(19, c.rechargeRemaining(2));
        c.tick(20, false, true, true);
        assertEquals(49_500, c.energy());
        c.tick(21, false, true, true);
        assertEquals(50_750, c.energy());
        assertFalse(c.guarding());
    }

    @Test void heavySnapshotsPartialFullAndEmptyEnergyWithoutImplyingLinearDamage() {
        var c = new SwordCycle();
        c.bind(25_000, 0);
        assertEquals(0.25, c.heavy(1_000_000), 1e-12);
        assertEquals(0, c.energy());
        assertEquals(20, c.rechargeRemaining(1_000_000));
        assertEquals(0.0, c.heavy(1_000_010), 1e-12);
        assertEquals(20, c.rechargeRemaining(1_000_010));
        c.bind(SwordCycle.CAPACITY, 0);
        assertEquals(1.0, c.heavy(0), 1e-12);
        c.bind(1, 0);
        double nonzero = c.heavy(0);
        assertEquals(0.00001, nonzero, 1e-12);
        assertTrue(nonzero > 0, "Even one energy unit permits the caller's full-power heavy");
    }

    @Test void heavyClearsGuardAndComboAndBlocksRechargeUntilTheDeadline() {
        var c = new SwordCycle();
        c.bind(50_000, 0);
        c.light(0);
        c.tick(1, true, true, true);
        assertEquals(0.495, c.heavy(1), 1e-12);
        assertFalse(c.guarding());
        assertEquals(0, c.combo());
        c.tick(20, true, true, true);
        assertEquals(0, c.energy());
        assertFalse(c.guarding());
        c.tick(21, true, true, true);
        assertEquals(1_250, c.energy());
        assertFalse(c.guarding());
        assertEquals(1, c.light(21));
    }

    @Test void lightReturnsActualComboIndicesAndNeverSpendsOrPausesEnergy() {
        var c = new SwordCycle();
        c.bind(42_000, 0);
        assertEquals(1, c.light(1));
        assertEquals(2, c.light(2));
        assertEquals(3, c.light(3));
        assertEquals(3, c.combo());
        assertEquals(1, c.light(4));
        assertEquals(42_000, c.energy());
        assertEquals(0, c.rechargeRemaining(4));
        c.tick(5, false, true, true);
        assertEquals(43_250, c.energy());
        c.bind(0, 10);
        assertEquals(1, c.light(10));
        assertEquals(0, c.energy());
    }

    @Test void comboWindowIncludesItsBoundaryAndExpiresOnLightOrTick() {
        var c = new SwordCycle();
        c.bind(0, 0);
        assertEquals(1, c.light(0));
        assertEquals(2, c.light(30));
        assertEquals(3, c.light(60));
        assertEquals(1, c.light(91));
        c.tick(121, false, false, false);
        assertEquals(1, c.combo());
        c.tick(122, false, false, false);
        assertEquals(0, c.combo());
        assertEquals(1, c.light(122));
    }

    @Test void stopIsLosslessForEnergyAndRechargeButClearsTransientState() {
        var c = new SwordCycle();
        c.bind(40_000, 0);
        c.light(0);
        c.tick(1, true, true, true);
        c.stop();
        c.stop();
        assertEquals(39_500, c.energy());
        assertEquals(1, c.rechargeRemaining(20));
        assertFalse(c.guarding());
        assertEquals(0, c.combo());
        c.tick(20, false, true, true);
        assertEquals(39_500, c.energy());
        c.tick(21, false, true, true);
        assertEquals(40_750, c.energy());
    }

    @Test void itemSnapshotRestoresDelayWithoutCrossItemLeakageOrOfflineCatchup() {
        var c = new SwordCycle();
        c.bind(30_000, 0);
        c.tick(1, true, true, true);
        c.light(2);
        int itemEnergy = c.energy();
        int itemDelay = c.rechargeRemaining(6);
        c.stop();
        c.bind(70_000, 100);
        assertEquals(70_000, c.energy());
        assertEquals(0, c.rechargeRemaining(100));
        assertFalse(c.guarding());
        assertEquals(0, c.combo());
        c.heavy(100);
        c.bind(itemEnergy, itemDelay, 1_000_000);
        assertEquals(29_500, c.energy());
        assertEquals(15, c.rechargeRemaining(1_000_000));
        c.tick(1_000_014, false, true, true);
        assertEquals(29_500, c.energy());
        c.tick(1_000_015, false, true, true);
        assertEquals(30_750, c.energy());
        c.bind(70_000, 100, 2_000_000);
        assertEquals(20, c.rechargeRemaining(2_000_000));
    }

    @Test void largeGapsApplyOnlyOneDrainOrRegenStepAndRebindingGrantsNone() {
        var c = new SwordCycle();
        c.bind(0, 0);
        c.tick(1_000_000, false, true, true);
        assertEquals(1_250, c.energy());
        c.tick(1_000_000, false, true, true);
        assertEquals(1_250, c.energy());
        c.bind(c.energy(), 2_000_000);
        assertEquals(1_250, c.energy());
        c.tick(2_000_000, true, true, true);
        assertFalse(c.guarding());
        c.tick(3_000_000, true, true, true);
        assertEquals(750, c.energy());
        assertTrue(c.guarding());
        assertEquals(20, c.rechargeRemaining(3_000_000));
        c.tick(4_000_000, true, true, true);
        assertEquals(250, c.energy());
        c.heavy(4_000_000);
        c.tick(Long.MAX_VALUE, false, true, true);
        assertEquals(1_250, c.energy());
    }

    @Test void rechargeAndComboArithmeticHandleLongTickExtremes() {
        var c = new SwordCycle();
        c.bind(10_000, 20, Long.MIN_VALUE);
        assertEquals(20, c.rechargeRemaining(Long.MIN_VALUE));
        assertEquals(1, c.rechargeRemaining(Long.MIN_VALUE + 19));
        c.tick(Long.MIN_VALUE + 20, false, true, true);
        assertEquals(11_250, c.energy());
        c.heavy(Long.MAX_VALUE - 10);
        assertEquals(20, c.rechargeRemaining(Long.MAX_VALUE - 10));
        assertEquals(10, c.rechargeRemaining(Long.MAX_VALUE));
        c.tick(Long.MAX_VALUE, true, true, true);
        assertEquals(0, c.energy());
        assertFalse(c.guarding());
        c.bind(0, 20, Long.MIN_VALUE);
        assertEquals(0, c.rechargeRemaining(Long.MAX_VALUE));
        c.light(Long.MIN_VALUE);
        assertEquals(1, c.light(Long.MAX_VALUE));
        assertEquals(1, c.light(Long.MIN_VALUE));
        c.tick(Long.MAX_VALUE, false, false, false);
        assertEquals(0, c.combo());
        assertEquals(1_250, c.energy());
        c.bind(10_000, Long.MAX_VALUE - 1);
        c.tick(Long.MAX_VALUE, true, true, true);
        assertEquals(9_500, c.energy());
        assertEquals(20, c.rechargeRemaining(Long.MAX_VALUE));
    }
}
