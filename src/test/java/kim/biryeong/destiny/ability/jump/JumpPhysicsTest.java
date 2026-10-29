package kim.biryeong.destiny.ability.jump;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;
import static kim.biryeong.destiny.ability.jump.JumpPhysics.*;

/** No Minecraft classes/bootstrap: exercise movement and resource invariants, not source strings. */
class JumpPhysicsTest {
    private static final double EPS = 1e-8;

    @Test void actualVanillaAscentWorksWhenServerDeltaIsZero() {
        Velocity sampled = new Velocity(.1, .42, .05), zero = new Velocity(0, 0, 0);
        assertEquals(sampled, observedVelocity(sampled, true, zero, zero));
        assertEquals(sampled, observedVelocity(zero, false, sampled, zero));
        assertTrue(glideTick(observedVelocity(sampled, true, zero, zero).y(), .12) > 0);
    }

    @Test void actualFallOverridesStaleAscentButZeroSampleAloneDoesNotProveAVerticalStop() {
        Velocity falling = new Velocity(.1, -.35, .05), stale = new Velocity(0, .5, 0);
        assertEquals(falling, observedVelocity(falling, true, stale, stale));
        assertTrue(glideTick(observedVelocity(falling, true, stale, stale).y(), .12) < 0);
        Velocity zero = new Velocity(0, 0, 0);
        assertEquals(stale, observedVelocity(zero, true, stale, stale));
    }

    @Test void horizontalPositionChangeWithUnchangedPositiveKnownYDoesNotEndGlideAscent() {
        MotionTracker tracker = new MotionTracker(new Displacement(0, 100, 0), 0);
        MotionEstimate start = tracker.observe(1, new Displacement(0, 100.42, 0), new Velocity(0, .164773282, 0), false);
        GlideCarry carry = new GlideCarry();
        carry.apply(1, start, .12, false);
        MotionEstimate horizontal = tracker.observe(2, new Displacement(0, 100.42, .075), new Velocity(0, .164773282, .075), false);
        assertFalse(horizontal.freshVertical());
        assertEquals(.164773282, horizontal.velocity().y(), EPS);
        assertTrue((carry.apply(2, horizontal, .12, false) - .08) * .98 > 0);
    }

    @Test void horizontalPositionChangeWithZeroKnownYIsMissingVerticalEvidenceEvenAtActivation() {
        MotionTracker tracker = new MotionTracker(new Displacement(0, 100, 0), 0);
        tracker.observe(1, new Displacement(0, 100.42, 0), new Velocity(0, .164773282, 0), false);
        MotionEstimate horizontal = tracker.observe(2, new Displacement(0, 100.42, .075), new Velocity(0, 0, .075), false);
        assertFalse(horizontal.freshVertical());
        assertTrue(horizontal.velocity().y() > 0);
        assertTrue((new GlideCarry().apply(2, horizontal, .12, false) - .08) * .98 > 0);
    }

    @Test void horizontalUpdatesDoNotRefreshOldVerticalEvidenceOrRefillFiniteCarry() {
        MotionTracker tracker = new MotionTracker(new Displacement(0, 100, 0), 0);
        MotionEstimate start = tracker.observe(1, new Displacement(0, 100.42, 0), new Velocity(0, .164773282, 0), false);
        GlideCarry carry = new GlideCarry();
        carry.apply(1, start, .12, false);
        double command = 0;
        for (int tick = 2; tick < 40; tick++) {
            MotionEstimate horizontal = tracker.observe(tick, new Displacement(0, 100.42, tick * .075), new Velocity(0, 0, .075), false);
            assertFalse(horizontal.freshVertical());
            if (tick >= 4) assertTrue(horizontal.velocity().y() <= 0);
            command = carry.apply(tick, horizontal, .12, false);
            if (tick < 6) assertTrue((command - .08) * .98 > 0);
        }
        assertTrue(command < 0);
    }

    @Test void verticalCoalescingUsesItsOwnClockWhileHorizontalPacketsKeepArriving() {
        MotionTracker tracker = new MotionTracker(new Displacement(0, 100, 0), 0);
        tracker.observe(1, new Displacement(0, 100.42, 0), new Velocity(0, .3332, 0), false);
        tracker.observe(2, new Displacement(0, 100.42, .1), new Velocity(0, 0, .1), false);
        tracker.observe(3, new Displacement(0, 100.42, .2), new Velocity(0, 0, .1), false);
        MotionEstimate arrived = tracker.observe(4, new Displacement(0, 101.02, .3), new Velocity(0, 0, .1), false);
        assertTrue(arrived.freshVertical());
        assertEquals(.2, arrived.velocity().y(), EPS);
        assertEquals(.1, arrived.velocity().z(), EPS);
        MotionEstimate falling = tracker.observe(5, new Displacement(0, 100.92, .4), new Velocity(0, .2, .1), false);
        assertTrue(falling.freshVertical());
        assertTrue(falling.velocity().y() < 0);
    }

    @Test void standingOnGroundDoesNotDiluteTheNextNativeJumpAcrossTheWholeIdlePeriod() {
        MotionTracker tracker = new MotionTracker(new Displacement(0, 100, 0), 0);
        for (int tick = 1; tick <= 100; tick++) {
            tracker.observe(tick, new Displacement(0, 100, 0), new Velocity(0, 0, 0), true);
        }
        MotionEstimate jump = tracker.observe(101, new Displacement(0, 100.42, 0), new Velocity(0, 0, 0), false);
        assertTrue(jump.freshVertical());
        assertEquals(.42, jump.velocity().y(), EPS);
    }

    @Test void missingPositionPacketsRetainMeasuredAscentInsteadOfReportingAStop() {
        MotionTracker tracker = new MotionTracker(new Displacement(0, 100, 0), 3380);
        Velocity zero = new Velocity(0, 0, 0);
        MotionEstimate rising = tracker.observe(3381, new Displacement(0, 100.42, 0), new Velocity(0, .3332, 0), false);
        assertTrue(rising.freshVertical());
        MotionEstimate gap = tracker.observe(3382, new Displacement(0, 100.42, 0), zero, false);
        assertFalse(gap.freshVertical());
        assertTrue(gap.velocity().y() > .3);
        MotionEstimate horizontalOnly = tracker.observe(3383, new Displacement(0, 100.42, 0), new Velocity(0, 0, .075), false);
        assertFalse(horizontalOnly.freshVertical());
        assertTrue(horizontalOnly.velocity().y() > 0);
        MotionEstimate arrived = tracker.observe(3384, new Displacement(0, 101.001335979, .02), new Velocity(0, .164773282, .02), false);
        assertEquals(.164773282, arrived.velocity().y(), EPS);
    }

    @Test void coalescedPositionUsesElapsedTimeSinceTheLastPositionChange() {
        MotionTracker tracker = new MotionTracker(new Displacement(0, 100, 0), 0);
        Velocity zero = new Velocity(0, 0, 0);
        tracker.observe(1, new Displacement(0, 100, 0), zero, false);
        tracker.observe(2, new Displacement(0, 100, 0), zero, false);
        MotionEstimate received = tracker.observe(3, new Displacement(0, 100.6, .9), zero, false);
        assertEquals(.3, received.velocity().z(), EPS);
        assertEquals(.2, received.velocity().y(), EPS);
        MotionEstimate duplicate = tracker.observe(3, new Displacement(0, 100.6, .9), zero, false);
        assertEquals(received, duplicate);
        MotionEstimate next = tracker.observe(4, new Displacement(0, 100.8, 1.2), zero, false);
        assertEquals(.3, next.velocity().z(), EPS);
    }

    @Test void latestKnownPacketRefinesAnAverageWithoutErasingAscentWithZeroY() {
        Velocity average = new Velocity(0, .30, .4);
        assertEquals(.164773282, observedVelocity(average, true, new Velocity(0, .164773282, .2), average).y(), EPS);
        assertEquals(.30, observedVelocity(average, true, new Velocity(0, 0, .075), average).y(), EPS);
        assertTrue(observedVelocity(average, true, new Velocity(0, -.08, .2), average).y() < 0);
    }

    @Test void measuredNativeAscentContinuesThroughMissingPacketsAndThenExpires() {
        GlideCarry carry = new GlideCarry();
        double command = carry.apply(3384, new MotionEstimate(new Velocity(0, .164773282, 0), true), .12, false);
        assertTrue((command - .08) * .98 > 0);
        double rise = 0;
        for (int tick = 3385; tick < 3420; tick++) {
            // No new position/known movement packet. Zero is an absence of evidence here.
            command = carry.apply(tick, new MotionEstimate(new Velocity(0, 0, 0), false), .12, false);
            double effective = (command - .08) * .98;
            rise += Math.max(0, effective);
            if (tick < 3405) assertTrue(effective > 0);
        }
        assertTrue(rise > 1.8);
        assertTrue(command < 0);
    }

    @Test void smallerOrLargerFreshPositivePacketsCannotDrainOrRefillActiveCarry() {
        GlideCarry baseline = new GlideCarry(), sampled = new GlideCarry();
        MotionEstimate launch = new MotionEstimate(new Velocity(0, .164773282, 0), true);
        baseline.apply(0, launch, .12, false);
        sampled.apply(0, launch, .12, false);
        for (int tick = 1; tick < 40; tick++) {
            MotionEstimate missing = new MotionEstimate(new Velocity(0, 0, 0), false);
            // Small positive packet deltas and coalesced larger deltas are both observations,
            // not new impulses. Keep sending them past exhaustion to detect an accidental refill.
            double packetY = tick % 2 == 0 ? .001 : .5;
            double actual = sampled.apply(tick, new MotionEstimate(new Velocity(0, packetY, 0), true), .12, false);
            assertEquals(baseline.apply(tick, missing, .12, false), actual, EPS);
            if (tick == 20) assertTrue((actual - .08) * .98 > 0);
            if (tick == 27) assertEquals(0, (actual - .08) * .98, EPS);
            if (tick >= 29) assertTrue(actual < 0);
        }
    }

    @Test void skippedServerTicksUseTheSameDecayAsRegularTicksWithoutDoubleApplying() {
        GlideCarry regular = new GlideCarry(), skipped = new GlideCarry();
        MotionEstimate launch = new MotionEstimate(new Velocity(0, .164773282, 0), true);
        MotionEstimate missing = new MotionEstimate(new Velocity(0, 0, 0), false);
        regular.apply(0, launch, .12, false);
        skipped.apply(0, launch, .12, false);
        double expected = 0;
        for (int tick = 1; tick <= 10; tick++) expected = regular.apply(tick, missing, .12, false);
        double command = skipped.apply(10, missing, .12, false);
        assertEquals(expected, command, EPS);
        assertEquals(.098773282, (command - .08) * .98, EPS);
        assertEquals(command, skipped.apply(10, launch, .12, false), EPS);
        for (int tick = 11; tick <= 26; tick++) expected = regular.apply(tick, missing, .12, false);
        assertEquals(expected, skipped.apply(26, missing, .12, false), EPS);
        for (int tick = 27; tick <= 30; tick++) {
            expected = regular.apply(tick, missing, .12, false);
            assertEquals(expected, skipped.apply(tick, missing, .12, false), EPS);
        }
        assertTrue(expected < 0);
        assertTrue(skipped.apply(31, launch, .12, false) < 0);
    }

    @Test void freshFallOverridesCarryAndDelayedPositivePacketsCannotRestartIt() {
        GlideCarry carry = new GlideCarry();
        carry.apply(0, new MotionEstimate(new Velocity(0, .3, 0), true), .12, false);
        assertTrue(carry.apply(1, new MotionEstimate(new Velocity(0, -.08, 0), true), .12, false) <= 0);
        for (int tick = 2; tick < 20; tick++) {
            assertTrue(carry.apply(tick, new MotionEstimate(new Velocity(0, .3, 0), true), .12, false) <= 0);
        }
        GlideCarry startedFalling = new GlideCarry();
        assertTrue(startedFalling.apply(0, new MotionEstimate(new Velocity(0, -.4, 0), true), .12, false) <= 0);
        assertTrue(startedFalling.apply(1, new MotionEstimate(new Velocity(0, .3, 0), false), .12, false) <= 0);
    }

    @Test void longPacketSilenceCannotKeepAStalePositiveLaunchAlive() {
        MotionTracker tracker = new MotionTracker(new Displacement(0, 100, 0), 0);
        tracker.observe(1, new Displacement(0, 100.42, 0), new Velocity(0, .3332, 0), false);
        MotionEstimate old = tracker.observe(8, new Displacement(0, 100.42, 0), new Velocity(0, 0, 0), false);
        assertFalse(old.freshVertical());
        assertTrue(old.velocity().y() <= 0);
        assertTrue(new GlideCarry().apply(8, old, .12, false) <= 0);
    }

    @Test void ceilingCollisionEndsCarryAndDuplicateTickCannotExtendIt() {
        GlideCarry carry = new GlideCarry();
        MotionEstimate rising = new MotionEstimate(new Velocity(0, .3, 0), true);
        double first = carry.apply(0, rising, .12, false);
        assertEquals(first, carry.apply(0, rising, .12, false), EPS);
        assertTrue(carry.apply(1, rising, .12, true) <= 0);
        assertTrue(carry.apply(2, rising, .12, false) <= 0);
    }

    @Test void continuousSteeringCannotPreserveAnInflatedCoalescedSpeedAsItsNewCap() {
        double acceptedCap = Mode.WARLOCK_BALANCED.horizontalSpeed;
        Velocity received = new Velocity(0, .1, 1.336995666);
        Velocity controlled = steer(capHorizontal(received, acceptedCap), 0, 1,
                Mode.WARLOCK_BALANCED.steering, acceptedCap);
        assertEquals(acceptedCap, controlled.horizontalSpeed(), EPS);
        assertEquals(.1, controlled.y(), EPS);
        double externalAtActivation = 1.2;
        assertEquals(1.2, capHorizontal(new Velocity(0, .1, 1.2), externalAtActivation).horizontalSpeed(), EPS);
    }

    @Test void hunterStrafeChangesDirectionMoreStronglyThanHighOrTriple() {
        Velocity falling = new Velocity(0, -.7, .2);
        Velocity high = hunter(Mode.HUNTER_HIGH, falling, -1, 0, Mode.HUNTER_HIGH.impulse);
        Velocity strafe = hunter(Mode.HUNTER_STRAFE, falling, -1, 0, Mode.HUNTER_STRAFE.impulse);
        Velocity triple = hunter(Mode.HUNTER_TRIPLE, falling, -1, 0, Mode.HUNTER_TRIPLE.impulse);
        assertTrue(strafe.x() < triple.x() && triple.x() < high.x());
        assertTrue(high.y() > strafe.y());
        assertTrue(strafe.y() > 0);
        assertEquals(0, hunter(Mode.HUNTER_HIGH, falling, 0, 0, .62).x(), EPS);
    }

    @Test void steeringCapsGeneratedSpeedWithoutErasingAnExternalImpulse() {
        Velocity speed = new Velocity(0, .2, 0);
        for (int i = 0; i < 100; i++) speed = steer(speed, 1, 1, .13, .52);
        assertEquals(.52, speed.horizontalSpeed(), EPS);
        assertEquals(.2, speed.y(), EPS);
        Velocity external = steer(new Velocity(1.2, -.4, 0), 1, 0, .1, .52);
        assertEquals(1.2, external.horizontalSpeed(), EPS);
        assertEquals(-.4, external.y(), EPS);
    }

    @Test void catapultArrestsAFallButHighAndStrafeNeedTimeToRecover() {
        assertTrue(liftStart(Mode.TITAN_CATAPULT, -.8) > 0);
        assertTrue(liftStart(Mode.TITAN_HIGH, -.8) < 0);
        assertTrue(liftStart(Mode.TITAN_STRAFE, -.8) < 0);
        assertTrue(liftStart(Mode.TITAN_HIGH, -.8) > liftStart(Mode.TITAN_STRAFE, -.8));
        assertEquals(1.1, liftTick(1.1, .1, .5), EPS);
    }

    @Test void liftProfilesHaveDifferentHeightAndLateralControl() {
        assertTrue(liftHeight(Mode.TITAN_HIGH) > liftHeight(Mode.TITAN_CATAPULT));
        assertTrue(liftHeight(Mode.TITAN_CATAPULT) > liftHeight(Mode.TITAN_STRAFE));
        assertTrue(Mode.TITAN_STRAFE.steering > Mode.TITAN_HIGH.steering);
        assertTrue(Mode.TITAN_STRAFE.horizontalSpeed > Mode.TITAN_CATAPULT.horizontalSpeed);
    }

    private static double liftHeight(Mode mode) {
        double vy = liftStart(mode, .3), height = 0, peak = 0;
        for (int tick = 0; tick < 80; tick++) {
            if (tick > 0 && tick < mode.duration) vy = liftTick(vy, mode.acceleration, mode.verticalLimit);
            height += vy; peak = Math.max(peak, height); vy = (vy - .08) * .98;
        }
        return peak;
    }

    @Test void glideCarriesButEventuallyExhaustsAnExistingAscent() {
        double vy = .164773282, previous = vy;
        int rising = 0;
        for (int tick = 0; tick < 60; tick++) {
            vy = (glideTick(vy, .12) - .08) * .98;
            assertTrue(vy <= previous + EPS);
            if (vy > 0) rising++;
            previous = vy;
        }
        assertTrue(rising > 25 && rising < 30);
        assertTrue(vy < 0);
        for (double fall : new double[]{0, -.001, -.4, -2}) assertTrue(glideTick(fall, .12) <= 0);
    }

    @Test void burstIsFastestAndStrafeTurnsMostWithBalancedBetween() {
        assertTrue(Mode.WARLOCK_BURST.horizontalSpeed > Mode.WARLOCK_BALANCED.horizontalSpeed);
        assertTrue(Mode.WARLOCK_BALANCED.horizontalSpeed > Mode.WARLOCK_STRAFE.horizontalSpeed);
        assertTrue(Mode.WARLOCK_STRAFE.steering > Mode.WARLOCK_BALANCED.steering);
        assertTrue(Mode.WARLOCK_BALANCED.steering > Mode.WARLOCK_BURST.steering);
        assertTrue(burstGlide(new Velocity(0, -.1, .2), 0, 1, .78).z() > .2);
    }

    @Test void commonAndLegacyTicksCannotDoubleSpendOrDoublePropel() {
        Budget budget = new Budget();
        assertTrue(budget.observe(10, false));
        assertEquals(Press.STARTED, budget.press(Mode.TITAN_STRAFE, 10, 16));
        assertFalse(budget.propel(10));
        assertTrue(budget.observe(11, false));
        assertTrue(budget.propel(11));
        double remaining = budget.remaining();
        assertFalse(budget.observe(11, false));
        assertFalse(budget.propel(11));
        assertEquals(remaining, budget.remaining(), EPS);
    }

    @Test void duplicateInputDoesNotCancelOrSpendTwice() {
        Budget budget = new Budget();
        assertEquals(Press.STARTED, budget.press(Mode.WARLOCK_BALANCED, 5, 60));
        assertEquals(Press.REJECTED, budget.press(Mode.WARLOCK_BALANCED, 5, 60));
        assertEquals(Mode.WARLOCK_BALANCED, budget.active());
        assertEquals(1, budget.starts());
    }

    @Test void cancellationPauseAndLoadoutSwapPreserveSharedFuel() {
        Budget budget = new Budget();
        assertEquals(Press.STARTED, budget.press(Mode.TITAN_STRAFE, 0, 16));
        for (int tick = 1; tick < 8; tick++) assertTrue(budget.propel(tick));
        assertEquals(.5, budget.remaining(), EPS);
        assertEquals(Press.STOPPED, budget.press(Mode.TITAN_STRAFE, 8, 16));
        for (int tick = 9; tick < 100; tick++) { budget.observe(tick, false); assertFalse(budget.propel(tick)); }
        assertEquals(.5, budget.remaining(), EPS);
        // Changing option and even class does not manufacture a fresh fuel pool.
        assertEquals(Press.STARTED, budget.press(Mode.WARLOCK_STRAFE, 100, 60));
        int updates = 1;
        for (int tick = 101; tick < 160; tick++) if (budget.propel(tick)) updates++;
        assertEquals(30, updates);
        assertEquals(0, budget.remaining(), EPS);
    }

    @Test void repeatedResumesHaveAnActivationCapEvenWithFuelRemaining() {
        Budget budget = new Budget();
        for (int i = 0; i < 3; i++) {
            assertEquals(Press.STARTED, budget.press(Mode.WARLOCK_BURST, i * 2, 60));
            assertEquals(Press.STOPPED, budget.press(Mode.WARLOCK_BURST, i * 2 + 1, 60));
        }
        assertTrue(budget.remaining() > .9);
        assertEquals(Press.REJECTED, budget.press(Mode.WARLOCK_BURST, 6, 60));
    }

    @Test void menuCleanupCannotTurnATripleJumpIntoAFreshHighJump() {
        Budget budget = new Budget();
        assertEquals(Press.STARTED, budget.press(Mode.HUNTER_TRIPLE, 1, 0));
        budget.cancel();
        assertEquals(Press.REJECTED, budget.press(Mode.HUNTER_HIGH, 2, 0));
        assertEquals(Press.STARTED, budget.press(Mode.HUNTER_TRIPLE, 3, 0));
        assertEquals(Press.REJECTED, budget.press(Mode.HUNTER_TRIPLE, 4, 0));
        assertTrue(budget.observe(5, true));
        assertEquals(Press.STARTED, budget.press(Mode.HUNTER_HIGH, 6, 0));
    }

    @Test void landingResetsFuelAndResumeCount() {
        Budget budget = new Budget();
        budget.press(Mode.WARLOCK_BALANCED, 0, 60);
        for (int tick = 1; tick < 70; tick++) budget.propel(tick);
        assertEquals(0, budget.remaining(), EPS);
        budget.observe(70, true);
        assertEquals(1, budget.remaining(), EPS);
        assertEquals(0, budget.starts());
        assertNull(budget.active());
        assertEquals(Press.STARTED, budget.press(Mode.TITAN_CATAPULT, 71, 18));
    }

    @Test void blinkCadenceAndChargesSurviveMenuCleanupAndLanding() {
        Budget budget = new Budget();
        assertEquals(Press.STARTED, budget.press(Mode.HUNTER_BLINK, 0, 0));
        budget.cancel();
        assertEquals(Press.REJECTED, budget.press(Mode.HUNTER_BLINK, 5, 0));
        assertEquals(Press.STARTED, budget.press(Mode.HUNTER_BLINK, 6, 0));
        budget.observe(7, true);
        assertEquals(Press.REJECTED, budget.press(Mode.WARLOCK_BLINK, 12, 0));
        assertEquals(Press.STARTED, budget.press(Mode.WARLOCK_BLINK, 50, 0));
    }

    @Test void blinkRechargesBothChargesInMidairAfterTheLastAcceptedUse() {
        Budget budget = new Budget();
        assertEquals(Press.STARTED, budget.press(Mode.HUNTER_BLINK, 0, 0));
        assertEquals(Press.STARTED, budget.press(Mode.HUNTER_BLINK, 6, 0));
        budget.observe(49, false);
        assertEquals(Press.REJECTED, budget.press(Mode.HUNTER_BLINK, 49, 0));
        budget.observe(50, false);
        assertEquals(Press.STARTED, budget.press(Mode.HUNTER_BLINK, 50, 0));
        assertEquals(Press.STARTED, budget.press(Mode.HUNTER_BLINK, 56, 0));
        assertEquals(Press.REJECTED, budget.press(Mode.HUNTER_BLINK, 99, 0));
        assertEquals(Press.STARTED, budget.press(Mode.HUNTER_BLINK, 100, 0));
        assertEquals(1, budget.remaining(), EPS);
        assertEquals(0, budget.starts());
    }

    @Test void blinkChargesAndNormalJumpFuelAreIndependentInBothDirections() {
        Budget normalSpent = new Budget();
        assertEquals(Press.STARTED, normalSpent.press(Mode.HUNTER_HIGH, 0, 0));
        assertEquals(0, normalSpent.remaining(), EPS);
        assertEquals(Press.STARTED, normalSpent.press(Mode.HUNTER_BLINK, 1, 0));
        assertEquals(Press.STARTED, normalSpent.press(Mode.WARLOCK_BLINK, 7, 0));
        assertEquals(Press.REJECTED, normalSpent.press(Mode.HUNTER_TRIPLE, 8, 0));
        assertEquals(Press.STARTED, normalSpent.press(Mode.WARLOCK_BLINK, 51, 0));
        assertEquals(0, normalSpent.remaining(), EPS);

        Budget blinkSpent = new Budget();
        assertEquals(Press.STARTED, blinkSpent.press(Mode.HUNTER_BLINK, 0, 0));
        assertEquals(Press.STARTED, blinkSpent.press(Mode.HUNTER_BLINK, 6, 0));
        assertEquals(Press.STARTED, blinkSpent.press(Mode.HUNTER_HIGH, 7, 0));
        assertEquals(0, blinkSpent.remaining(), EPS);
    }

    @Test void normalJumpActivityAndClassSwitchDoNotRestartBlinkRecharge() {
        Budget budget = new Budget();
        assertEquals(Press.STARTED, budget.press(Mode.HUNTER_BLINK, 0, 0));
        assertEquals(Press.STARTED, budget.press(Mode.HUNTER_BLINK, 6, 0));
        assertEquals(Press.STARTED, budget.press(Mode.TITAN_HIGH, 7, 24));
        budget.cancel(); // The menu/class-change cleanup stops thrust, preserving both pools.
        for (int tick = 8; tick <= 49; tick++) budget.observe(tick, false);
        assertEquals(Press.REJECTED, budget.press(Mode.WARLOCK_BLINK, 49, 0));
        budget.observe(50, false);
        assertEquals(Press.STARTED, budget.press(Mode.WARLOCK_BLINK, 50, 0));
        assertEquals(1 - 1.0 / 24, budget.remaining(), EPS);
        assertEquals(1, budget.starts());
    }

    @Test void blinkVectorBoundsRangeAndVerticalOffset() {
        Displacement forward = blinkVector(0, 0, 1, 5.25, 2.5);
        assertEquals(5.25, forward.length(), EPS);
        assertEquals(2.5, blinkVector(0, 1, 0, 5.25, 2.5).y(), EPS);
        Displacement diagonal = blinkVector(1, 1, 1, 5.25, 2.5);
        assertTrue(diagonal.length() <= 5.25);
        assertTrue(diagonal.y() <= 2.5);
    }

    @Test void blinkSweepStopsBeforeAThinWallEvenWhenEndpointIsBeyondIt() {
        Displacement safe = sweepBlink(new Displacement(5.25, 0, 0), (from, to) ->
                !(Math.min(from.x(), to.x()) - .3 <= 1.01 && Math.max(from.x(), to.x()) + .3 >= 1));
        assertTrue(safe.x() > .5 && safe.x() < .7);
    }

    @Test void blinkSweepRespectsFullPlayerHeightAndWorldBoundary() {
        Displacement ceiling = sweepBlink(new Displacement(0, 2.5, 0), (from, to) -> Math.max(from.y(), to.y()) + 1.8 < 2.1);
        assertTrue(ceiling.y() <= .3 + EPS);
        Displacement border = sweepBlink(new Displacement(5.25, 0, 0), (from, to) -> Math.max(from.x(), to.x()) + .3 <= 2);
        assertTrue(border.x() <= 1.7);
        assertEquals(0, sweepBlink(new Displacement(1, 0, 0), (from, to) -> false).length(), EPS);
    }

    @Test void malformedTuningIsBounded() {
        assertEquals(.12, finite(Double.NaN, .12, .06, .5), EPS);
        assertEquals(.5, finite(10, .12, .06, .5), EPS);
        assertEquals(.06, finite(-10, .12, .06, .5), EPS);
    }
}
