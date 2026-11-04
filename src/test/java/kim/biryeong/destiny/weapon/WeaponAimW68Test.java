package kim.biryeong.destiny.weapon;

import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

/** Pure state tests; timing examples are generic, not assertions about catalog weapons. */
class WeaponAimW68Test {
    private static final float EPSILON = 0.000001f;

    @Test
    void halfProgressIsAnExactEarlyThresholdInBothDirections() {
        var state = new WeaponAimState();
        state.tick(0, true, 4, 8, 0f);
        assertEquals(0.25f, state.progress());
        assertFalse(state.progress() >= 0.5f);

        state.tick(1, true, 4, 8, 0f);
        assertEquals(0.5f, state.progress());
        assertTrue(state.progress() >= 0.5f);
        assertTrue(state.progress() < 1f, "Early threshold precedes full completion");

        state.tick(2, false, 4, 8, 0f);
        assertEquals(0.375f, state.progress());
        assertFalse(state.progress() >= 0.5f);
        state.tick(3, true, 4, 8, 0f);
        assertEquals(0.625f, state.progress());
        state.tick(4, false, 4, 8, 0f);
        assertEquals(0.5f, state.progress());
        assertTrue(state.progress() >= 0.5f);
    }

    @Test
    void genericPrimaryExampleEntersInTwoRatherThanFourTicksWithTheSameExit() {
        var faster = new WeaponAimState();
        var baseline = new WeaponAimState();
        float[] fasterEntry = {0.5f, 1f, 1f, 1f};
        float[] baselineEntry = {0.25f, 0.5f, 0.75f, 1f};
        for (int tick = 0; tick < 4; tick++) {
            faster.tick(tick, true, 2, 4, 0f);
            baseline.tick(tick, true, 4, 4, 0f);
            assertEquals(fasterEntry[tick], faster.progress());
            assertEquals(baselineEntry[tick], baseline.progress());
        }

        float[] exit = {0.75f, 0.5f, 0.25f, 0f};
        for (int step = 0; step < exit.length; step++) {
            faster.tick(4 + step, false, 2, 4, 0f);
            baseline.tick(4 + step, false, 4, 4, 0f);
            assertEquals(exit[step], faster.progress());
            assertEquals(exit[step], baseline.progress());
        }
    }

    @Test
    void genericSpecialExampleCompletesInSixRatherThanSevenTicksWithinFloatTolerance() {
        var faster = new WeaponAimState();
        var baseline = new WeaponAimState();
        float[] fasterEntry = {1f / 6, 2f / 6, 0.5f, 4f / 6, 5f / 6, 1f, 1f};
        float[] baselineEntry = {1f / 7, 2f / 7, 3f / 7, 4f / 7, 5f / 7, 6f / 7, 1f};
        for (int tick = 0; tick < 7; tick++) {
            faster.tick(tick, true, 6, 7, 0f);
            baseline.tick(tick, true, 7, 7, 0f);
            assertEquals(fasterEntry[tick], faster.progress(), EPSILON);
            assertEquals(baselineEntry[tick], baseline.progress(), EPSILON);
            if (tick == 5) {
                assertEquals(1f, faster.progress(), EPSILON);
                assertTrue(baseline.progress() < 1f);
            }
        }

        for (int step = 1; step <= 7; step++) {
            faster.tick(6 + step, false, 6, 7, 0f);
            baseline.tick(6 + step, false, 7, 7, 0f);
            float expected = (7 - step) / 7f;
            assertEquals(expected, faster.progress(), EPSILON);
            assertEquals(expected, baseline.progress(), EPSILON);
        }
    }

    @Test
    void repeatedReversalsContinueFromCurrentProgressWithoutRestarting() {
        var state = new WeaponAimState();
        boolean[] aiming = {true, true, false, true, false, false, true, false};
        float[] expected = {0.25f, 0.5f, 0.375f, 0.625f, 0.5f, 0.375f, 0.625f, 0.5f};
        for (int tick = 0; tick < aiming.length; tick++) {
            state.tick(tick, aiming[tick], 4, 8, 0f);
            assertEquals(expected[tick], state.progress(), "Reversal at tick " + tick);
        }
    }

    @Test
    void duplicateTickCannotAdvanceProgressOrRecoverBloomTwiceEvenWithDifferentArguments() {
        var state = new WeaponAimState();
        state.tick(0, false, 4, 8, 0.125f);
        state.shot(0.75f);
        for (int tick = 1; tick <= 4; tick++) {
            state.tick(tick, true, 4, 8, 0.125f);
        }
        assertEquals(1f, state.progress());
        assertEquals(0.625f, state.bloom());

        state.tick(4, false, 1, 1, 1f);
        assertEquals(1f, state.progress());
        assertEquals(0.625f, state.bloom());
        assertEquals(1, state.shots());

        state.tick(5, false, 4, 8, 0.125f);
        assertEquals(0.875f, state.progress());
        assertEquals(0.5f, state.bloom());
    }

    @Test
    void resetClearsStateButPreservesTheSameTickGuard() {
        var state = new WeaponAimState();
        state.tick(10, true, 4, 8, 0f);
        state.shot(0.75f);
        assertEquals(0.25f, state.progress());
        assertEquals(1, state.shots());

        state.reset();
        assertEquals(0f, state.progress());
        assertEquals(0f, state.bloom());
        assertEquals(0, state.shots());
        state.tick(10, true, 1, 1, 1f);
        assertEquals(0f, state.progress());
        assertEquals(0f, state.bloom());
        assertEquals(0, state.shots());

        state.tick(11, true, 4, 8, 0.125f);
        assertEquals(0.25f, state.progress());
        assertEquals(0f, state.bloom());
    }

    @Test
    void progressClampsAtFullAndZeroAndNonpositiveDurationsTakeOneTick() {
        var state = new WeaponAimState();
        for (int tick = 0; tick < 20; tick++) {
            state.tick(tick, true, 3, 7, 0f);
            assertTrue(state.progress() >= 0f && state.progress() <= 1f);
        }
        assertEquals(1f, state.progress());
        for (int tick = 20; tick < 40; tick++) {
            state.tick(tick, false, 3, 7, 0f);
            assertTrue(state.progress() >= 0f && state.progress() <= 1f);
        }
        assertEquals(0f, state.progress());

        for (int enter : new int[]{1, 0, -3}) {
            for (int exit : new int[]{1, 0, -7}) {
                var immediate = new WeaponAimState();
                immediate.tick(0, true, enter, exit, 0f);
                assertEquals(1f, immediate.progress());
                immediate.tick(1, true, enter, exit, 0f);
                assertEquals(1f, immediate.progress());
                immediate.tick(2, false, enter, exit, 0f);
                assertEquals(0f, immediate.progress());
                immediate.tick(3, false, enter, exit, 0f);
                assertEquals(0f, immediate.progress());
            }
        }
    }

    @Test
    void legacyOverloadMatchesEqualDurationsAcrossEveryEightTickInputSequence() {
        for (int duration : new int[]{1, 2, 4, 7}) {
            for (float recovery : new float[]{0f, 0.125f, 1f}) {
                for (int sequence = 0; sequence < 256; sequence++) {
                    var legacy = new WeaponAimState();
                    var explicit = new WeaponAimState();
                    int units = 0;
                    int shots = 0;
                    for (int tick = 0; tick < 8; tick++) {
                        if (tick == 4 && (sequence & 1) == 0) {
                            legacy.reset();
                            explicit.reset();
                            units = 0;
                            shots = 0;
                        }
                        boolean aiming = (sequence & (1 << tick)) != 0;
                        legacy.tick(tick, aiming, duration, recovery);
                        explicit.tick(tick, aiming, duration, duration, recovery);
                        // Integer fractions provide an oracle independent of either overload.
                        units = Math.max(0, Math.min(duration, units + (aiming ? 1 : -1)));
                        String context = "duration=" + duration + ", sequence=" + sequence + ", tick=" + tick;
                        assertEquals(units / (float) duration, legacy.progress(), EPSILON, context);
                        assertEquals(units / (float) duration, explicit.progress(), EPSILON, context);
                        assertSameState(legacy, explicit, context);

                        legacy.tick(tick, !aiming, duration, 1f);
                        explicit.tick(tick, !aiming, duration, duration, 1f);
                        assertEquals(units / (float) duration, legacy.progress(), EPSILON, context);
                        assertEquals(units / (float) duration, explicit.progress(), EPSILON, context);
                        assertSameState(legacy, explicit, context);
                        if (tick == 0 || tick == 6) {
                            legacy.shot(0.25f);
                            explicit.shot(0.25f);
                            shots++;
                            assertSameState(legacy, explicit, context);
                        }
                        assertEquals(shots, legacy.shots(), context);
                        assertEquals(shots, explicit.shots(), context);
                    }
                }
            }
        }
    }

    @Test
    void asymmetricTransitionsLeaveBloomAndShotCountUntouchedWhenRecoveryIsZero() {
        var state = new WeaponAimState();
        state.tick(0, false, 2, 8, 0f);
        state.shot(0.5f);
        state.shot(0.25f);
        boolean[] aiming = {true, true, false, false, true, false, true, false};
        float[] progress = {0.5f, 1f, 0.875f, 0.75f, 1f, 0.875f, 1f, 0.875f};
        for (int step = 0; step < aiming.length; step++) {
            state.tick(step + 1, aiming[step], 2, 8, 0f);
            assertEquals(progress[step], state.progress());
            assertEquals(0.75f, state.bloom());
            assertEquals(2, state.shots());
        }
    }

    @Test
    void bloomRecoveryIsIndependentOfEntryExitDurationsAndAimDirection() {
        var fastEntry = new WeaponAimState();
        var slowEntry = new WeaponAimState();
        fastEntry.tick(0, false, 2, 8, 0.125f);
        slowEntry.tick(0, false, 7, 3, 0.125f);
        fastEntry.shot(0.75f);
        slowEntry.shot(0.75f);
        float[] expectedBloom = {0.75f, 0.75f, 0.75f, 0.625f, 0.5f, 0.375f, 0.25f, 0.125f, 0f, 0f};
        for (int step = 0; step < expectedBloom.length; step++) {
            int tick = step + 1;
            boolean aiming = tick <= 4 || tick % 2 == 0;
            fastEntry.tick(tick, aiming, 2, 8, 0.125f);
            slowEntry.tick(tick, !aiming, 7, 3, 0.125f);
            assertEquals(expectedBloom[step], fastEntry.bloom());
            assertEquals(expectedBloom[step], slowEntry.bloom());
            assertEquals(1, fastEntry.shots());
            assertEquals(1, slowEntry.shots());
        }
    }

    @Test
    void anotherShotOnTheThirdTickRestartsTheThreeTickRecoveryDelay() {
        var state = new WeaponAimState();
        state.tick(0, true, 2, 8, 0.125f);
        state.shot(0.25f);
        for (int tick = 1; tick <= 3; tick++) {
            state.tick(tick, true, 2, 8, 0.125f);
            assertEquals(0.25f, state.bloom(), "No recovery through shot tick + 3");
        }
        state.shot(0.125f);
        assertEquals(0.375f, state.bloom());
        assertEquals(2, state.shots());
        for (int tick = 4; tick <= 6; tick++) {
            state.tick(tick, false, 2, 8, 0.125f);
            assertEquals(0.375f, state.bloom());
        }
        state.tick(7, false, 2, 8, 0.125f);
        assertEquals(0.25f, state.bloom(), "Recovery starts at latest shot tick + 4");
        state.tick(8, false, 2, 8, 0.125f);
        assertEquals(0.125f, state.bloom());
        state.tick(9, false, 2, 8, 0.125f);
        assertEquals(0f, state.bloom());
        state.tick(10, false, 2, 8, 0.125f);
        assertEquals(0f, state.bloom());
        assertEquals(2, state.shots());
    }

    @Test
    void shotAfterRecoverySurvivesADuplicateTickAndRestartsItsOwnDelay() {
        var state = new WeaponAimState();
        state.tick(0, false, 6, 7, 0.125f);
        state.shot(0.75f);
        for (int tick = 1; tick <= 4; tick++) {
            state.tick(tick, true, 6, 7, 0.125f);
        }
        assertEquals(0.625f, state.bloom());
        state.shot(0.25f);
        assertEquals(0.875f, state.bloom());
        state.tick(4, false, 1, 1, 1f);
        assertEquals(0.875f, state.bloom());
        assertEquals(2, state.shots());
        for (int tick = 5; tick <= 7; tick++) {
            state.tick(tick, false, 6, 7, 0.125f);
            assertEquals(0.875f, state.bloom());
        }
        state.tick(8, false, 6, 7, 0.125f);
        assertEquals(0.75f, state.bloom());
        assertEquals(2, state.shots());
    }

    private static void assertSameState(WeaponAimState expected, WeaponAimState actual, String context) {
        assertEquals(expected.progress(), actual.progress(), context);
        assertEquals(expected.bloom(), actual.bloom(), context);
        assertEquals(expected.shots(), actual.shots(), context);
    }
}
