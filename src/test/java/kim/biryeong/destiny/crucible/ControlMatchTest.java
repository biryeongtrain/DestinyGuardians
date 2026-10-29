package kim.biryeong.destiny.crucible;

import org.junit.jupiter.api.Test;

import java.util.HashMap;
import java.util.Map;
import java.util.Set;
import java.util.UUID;

import static kim.biryeong.destiny.crucible.ControlMatch.EndReason.*;
import static kim.biryeong.destiny.crucible.ControlMatch.Phase.*;
import static kim.biryeong.destiny.crucible.ControlMatch.Team.*;
import static org.junit.jupiter.api.Assertions.*;

class ControlMatchTest {
    private static final UUID A = id(1), B = id(2), A2 = id(3), B2 = id(4), OUTSIDER = id(999);
    private static UUID id(long value) { return new UUID(0, value); }
    private static ControlMatch match(int limit, int duration, int intro, int results, int reward) {
        return new ControlMatch(new ControlMatch.Config(limit, duration, intro, results, 2, 3, reward, 600));
    }
    private static ControlMatch playing(int reward) {
        var match = match(150, 1000, 0, 2, reward);
        match.join(A);
        match.join(B);
        match.tick(Map.of());
        assertEquals(PLAYING, match.phase());
        return match;
    }
    private static void ticks(ControlMatch match, int count, Map<String, Set<UUID>> occupants) {
        for (int tick = 0; tick < count; tick++) match.tick(occupants);
    }
    private static void capture(ControlMatch match, String zone, UUID player) {
        ticks(match, 3, Map.of(zone, Set.of(player)));
    }
    private static ControlMatch.ZoneSnapshot zone(ControlMatch match, String id) {
        return match.snapshot().zones().get(id);
    }
    private static int score(ControlMatch match, ControlMatch.Team team) {
        return match.snapshot().scores().get(team);
    }

    @Test void aloneWaitsAndTwoTeamsStartWithExactIntroAndMatchTicks() {
        var match = match(150, 4, 2, 2, 1);
        assertEquals(ALPHA, match.join(A));
        ticks(match, 500, Map.of("A", Set.of(A)));
        assertEquals(WAITING, match.phase());
        assertNull(zone(match, "A").owner());
        assertEquals(BRAVO, match.join(B));
        match.tick(Map.of());
        assertEquals(INTRO, match.phase());
        assertEquals(2, match.snapshot().remainingTicks());
        assertEquals(0, match.kill(A, B));
        match.tick(Map.of());
        assertEquals(INTRO, match.phase());
        match.tick(Map.of("A", Set.of(A)));
        assertEquals(PLAYING, match.phase());
        assertEquals(4, match.snapshot().remainingTicks());
        assertEquals(0, zone(match, "A").progressTicks());
        ticks(match, 3, Map.of());
        assertEquals(PLAYING, match.phase());
        match.tick(Map.of());
        assertEquals(RESULTS, match.phase());
        assertEquals(TIME_LIMIT, match.snapshot().endReason());
        assertNull(match.snapshot().winner());
        assertEquals(507, match.snapshot().tick());
    }

    @Test void noPlayerCapAndIdempotentJoinDoNotResetLifeOrTeam() {
        var match = playing(0);
        long life = match.life(A);
        for (int i = 3; i <= 101; i++) match.join(id(i));
        assertEquals(101, match.members().size());
        assertEquals(51, match.members().values().stream().filter(t -> t == ALPHA).count());
        assertEquals(50, match.members().values().stream().filter(t -> t == BRAVO).count());
        assertEquals(ALPHA, match.join(A));
        assertEquals(life, match.life(A));
        assertEquals(0, match.snapshot().phaseTicks());
    }

    @Test void lateJoinFillsSmallerTeamAndReconnectKeepsOldTeamWhenBalanced() {
        var match = playing(0);
        match.join(A2);
        match.join(B2);
        assertTrue(match.leave(A));
        assertEquals(ALPHA, match.join(A));
        assertEquals(PLAYING, match.phase());
        match.leave(A);
        assertEquals(ALPHA, match.join(id(5)));
        assertEquals(ALPHA, match.join(id(6)));
        assertEquals(BRAVO, match.join(A), "reconnect must not grow the larger old team");
        assertFalse(match.leave(OUTSIDER));
        assertNull(match.team(OUTSIDER));
    }

    @Test void introDepartureCancelsCountdownAndPlayingDepartureWaitsBeforeForfeit() {
        var match = match(150, 100, 3, 2, 0);
        match.join(A); match.join(B); match.tick(Map.of());
        match.leave(B);
        assertEquals(WAITING, match.phase());
        assertNull(match.snapshot().endReason());
        match.join(B); match.tick(Map.of()); ticks(match, 3, Map.of());
        match.leave(A);
        assertEquals(PLAYING, match.phase());
        assertTrue(match.paused());
        assertEquals(600, match.snapshot().forfeitRemainingTicks());
        ticks(match, 599, Map.of());
        assertEquals(PLAYING, match.phase());
        assertEquals(599, match.snapshot().forfeitTicks());
        match.tick(Map.of());
        assertEquals(RESULTS, match.phase());
        assertEquals(BRAVO, match.snapshot().winner());
        assertEquals(FORFEIT, match.snapshot().endReason());
        match.join(A);
        assertEquals(RESULTS, match.phase(), "reconnect cannot undo the result");
    }

    @Test void graceFreezesCaptureScoreAndMatchTimeWhileMonotonicServerTicksAdvance() {
        var match = playing(1);
        capture(match, "A", A);
        match.tick(Map.of("B", Set.of(A)));
        var before = match.snapshot();
        match.leave(B);
        assertTrue(match.snapshot().paused(), "pause is visible even before the next tick");
        assertEquals(0, match.snapshot().forfeitTicks());
        ticks(match, 599, Map.of("B", Set.of(A), "C", Set.of(A)));
        var paused = match.snapshot();
        assertEquals(before.tick() + 599, paused.tick());
        assertEquals(before.phaseTicks(), paused.phaseTicks());
        assertEquals(before.remainingTicks(), paused.remainingTicks());
        assertEquals(before.scores(), paused.scores());
        assertEquals(before.zones(), paused.zones());
        assertEquals(599, paused.forfeitTicks());
        assertEquals(1, paused.forfeitRemainingTicks());
        assertEquals(0, match.kill(null, A));
        assertFalse(match.alive(A), "runtime death lifecycle is still tracked during pause");
        assertTrue(match.respawn(A));
        assertEquals(before.scores(), match.snapshot().scores());
        match.tick(Map.of());
        assertEquals(RESULTS, match.phase());
        assertEquals(FORFEIT, match.snapshot().endReason());
        assertEquals(ALPHA, match.snapshot().winner());
        assertEquals(600, match.snapshot().forfeitTicks());
        assertFalse(match.snapshot().paused());
        assertEquals(0, match.snapshot().forfeitRemainingTicks());
    }

    @Test void lastGraceTickReconnectCancelsForfeitAndResumesPreservedCaptureAndTimer() {
        var match = playing(1);
        ticks(match, 2, Map.of("A", Set.of(A)));
        int activeTicks = match.snapshot().phaseTicks();
        match.leave(B);
        ticks(match, 599, Map.of());
        assertEquals(BRAVO, match.join(B));
        assertFalse(match.paused());
        assertEquals(0, match.snapshot().forfeitTicks());
        assertEquals(0, match.snapshot().forfeitRemainingTicks());
        match.tick(Map.of("A", Set.of(A)));
        assertEquals(PLAYING, match.phase());
        assertEquals(activeTicks + 1, match.snapshot().phaseTicks());
        assertEquals(ALPHA, zone(match, "A").owner());
        assertEquals(1, score(match, ALPHA));
        assertNull(match.snapshot().endReason());
    }

    @Test void differentLateJoinCancelsGraceAndNextTeamLossGetsFreshCountdown() {
        var match = playing(0);
        match.leave(B);
        ticks(match, 400, Map.of());
        assertEquals(BRAVO, match.join(OUTSIDER));
        assertFalse(match.paused());
        assertEquals(0, match.snapshot().forfeitTicks());
        match.leave(OUTSIDER);
        ticks(match, 599, Map.of());
        assertEquals(PLAYING, match.phase(), "separate outages do not accumulate toward forfeit");
        match.tick(Map.of());
        assertEquals(RESULTS, match.phase());
        assertEquals(FORFEIT, match.snapshot().endReason());
    }

    @Test void remainingTeamDeparturesOrJoinsCannotExtendTheGraceDeadline() {
        var match = playing(0);
        match.join(A2); match.join(B2);
        match.leave(B); match.leave(B2);
        ticks(match, 250, Map.of());
        match.leave(A2);
        assertEquals(250, match.snapshot().forfeitTicks());
        assertEquals(ALPHA, match.join(A), "duplicate member join cannot cancel grace");
        ticks(match, 349, Map.of());
        assertEquals(599, match.snapshot().forfeitTicks());
        match.tick(Map.of());
        assertEquals(RESULTS, match.phase());
    }

    @Test void allLeavingDuringGraceFullyResetsCountdownWithoutResettingMonotonicTicks() {
        var match = playing(1);
        capture(match, "A", A);
        match.leave(B); ticks(match, 321, Map.of());
        long previousTick = match.snapshot().tick();
        match.leave(A);
        var empty = match.snapshot();
        assertEquals(WAITING, empty.phase());
        assertEquals(previousTick, empty.tick());
        assertEquals(0, empty.forfeitTicks());
        assertEquals(0, empty.forfeitRemainingTicks());
        assertFalse(empty.paused());
        assertNull(empty.endReason()); assertNull(empty.winner());
        assertTrue(empty.members().isEmpty());
        assertEquals(0, score(match, ALPHA));
        assertTrue(empty.zones().values().stream().allMatch(z -> z.owner() == null && z.progress() == 0));
        ticks(match, 600, Map.of());
        assertEquals(WAITING, match.phase());
        match.join(A); match.join(B); match.tick(Map.of());
        match.leave(A); ticks(match, 599, Map.of());
        assertEquals(PLAYING, match.phase());
        match.tick(Map.of());
        assertEquals(BRAVO, match.snapshot().winner());
    }

    @Test void configurableGraceUsesItsOwnBoundaryEvenWhenMatchTimerWouldExpireFirst() {
        var match = new ControlMatch(new ControlMatch.Config(150, 1, 0, 2, 2, 3, 1, 3));
        match.join(A); match.join(B); match.tick(Map.of());
        match.leave(A);
        ticks(match, 2, Map.of());
        assertEquals(PLAYING, match.phase());
        assertEquals(1, match.snapshot().remainingTicks());
        assertEquals(1, match.snapshot().forfeitRemainingTicks());
        match.tick(Map.of());
        assertEquals(FORFEIT, match.snapshot().endReason());
        assertEquals(BRAVO, match.snapshot().winner());
    }

    @Test void emptySessionResetsScoresZonesResultAndMembershipWithoutRewindingClock() {
        var match = playing(1);
        capture(match, "A", A);
        assertEquals(1, match.kill(A, B));
        long tick = match.snapshot().tick(), life = match.life(A);
        match.leave(A); match.leave(B);
        var snapshot = match.snapshot();
        assertEquals(WAITING, snapshot.phase());
        assertTrue(snapshot.members().isEmpty());
        assertEquals(0, score(match, ALPHA));
        assertNull(snapshot.winner()); assertNull(snapshot.endReason());
        assertTrue(snapshot.zones().values().stream().allMatch(z -> z.owner() == null && z.progress() == 0));
        assertEquals(tick, snapshot.tick());
        match.join(A); match.join(B); match.tick(Map.of());
        assertTrue(match.life(A) > life);
        assertEquals(2, match.snapshot().round());
    }

    @Test void neutralCaptureRewardsOnceAndDoesNotGeneratePassivePoints() {
        var match = playing(1);
        match.tick(Map.of("A", Set.of(A)));
        assertEquals(ALPHA, zone(match, "A").capturingTeam());
        assertEquals(1.0 / 3, zone(match, "A").progress(), 1e-9);
        match.tick(Map.of("A", Set.of(A)));
        assertNull(zone(match, "A").owner());
        match.tick(Map.of("A", Set.of(A)));
        assertEquals(ALPHA, zone(match, "A").owner());
        assertEquals(1, score(match, ALPHA));
        ticks(match, 50, Map.of("A", Set.of(A)));
        assertEquals(1, score(match, ALPHA));
        assertNull(zone(match, "A").capturingTeam());
    }

    @Test void enemyZoneMustBeNeutralizedThenCapturedOnSeparateTicks() {
        var match = playing(1);
        capture(match, "A", A);
        match.tick(Map.of("A", Set.of(B)));
        assertEquals(ALPHA, zone(match, "A").owner());
        assertEquals(.5, zone(match, "A").progress());
        match.tick(Map.of("A", Set.of(B)));
        assertNull(zone(match, "A").owner());
        assertEquals(0, zone(match, "A").progressTicks());
        assertEquals(BRAVO, zone(match, "A").capturingTeam());
        assertEquals(0, score(match, BRAVO));
        ticks(match, 2, Map.of("A", Set.of(B)));
        assertNull(zone(match, "A").owner());
        match.tick(Map.of("A", Set.of(B)));
        assertEquals(BRAVO, zone(match, "A").owner());
        assertEquals(1, score(match, BRAVO));
    }

    @Test void contestedFreezesEvenWithNumericalAdvantageAndResumesWithoutReward() {
        var match = playing(1); match.join(A2);
        match.tick(Map.of("B", Set.of(A)));
        ticks(match, 10, Map.of("B", Set.of(A, A2, B)));
        assertTrue(zone(match, "B").contested());
        assertEquals(1, zone(match, "B").progressTicks());
        assertEquals(0, score(match, ALPHA));
        ticks(match, 2, Map.of("B", Set.of(A, A2)));
        assertFalse(zone(match, "B").contested());
        assertEquals(ALPHA, zone(match, "B").owner());
        assertEquals(1, score(match, ALPHA), "reward is per team, not per occupant");
    }

    @Test void emptyOrDefendedZoneClearsPartialProgressAndOpposingCaptureStartsFresh() {
        var match = playing(0);
        ticks(match, 2, Map.of("A", Set.of(A)));
        match.tick(Map.of("A", Set.of(B)));
        assertEquals(BRAVO, zone(match, "A").capturingTeam());
        assertEquals(1, zone(match, "A").progressTicks());
        match.tick(Map.of());
        assertNull(zone(match, "A").capturingTeam());
        assertEquals(0, zone(match, "A").progressTicks());
        capture(match, "A", A);
        match.tick(Map.of("A", Set.of(B)));
        match.tick(Map.of("A", Set.of(A)));
        assertEquals(ALPHA, zone(match, "A").owner());
        assertEquals(0, zone(match, "A").progressTicks());
    }

    @Test void outsidersDeadPlayersAndUnknownZonesCannotCaptureOrContest() {
        var match = playing(0);
        assertEquals(1, match.kill(A, B));
        ticks(match, 3, Map.of("A", Set.of(A, B, OUTSIDER), "C", Set.of(OUTSIDER), "D", Set.of(A)));
        assertEquals(ALPHA, zone(match, "A").owner());
        assertFalse(zone(match, "A").contested());
        assertNull(zone(match, "C").owner());
        assertEquals(Set.of("A", "B", "C"), match.snapshot().zones().keySet());
        assertFalse(match.respawn(OUTSIDER));
    }

    @Test void killsScaleWithZeroOneTwoThreeOwnedZonesAndNeutralizationImmediatelyRemovesBonus() {
        var match = playing(0);
        assertEquals(1, match.kill(A, B)); match.respawn(B);
        capture(match, "A", A);
        assertEquals(1, match.kill(A, B)); match.respawn(B);
        capture(match, "B", A);
        assertEquals(2, match.kill(A, B)); match.respawn(B);
        capture(match, "C", A);
        assertEquals(3, match.kill(A, B)); match.respawn(B);
        ticks(match, 2, Map.of("C", Set.of(B)));
        assertEquals(2, match.kill(A, B));
        assertEquals(9, score(match, ALPHA));
    }

    @Test void duplicateDeathsAndOldLifeCallbacksCannotScoreAcrossRespawnOrReconnect() {
        var match = playing(0); match.join(B2); match.join(A2);
        long first = match.life(B);
        assertEquals(1, match.kill(A, B, first));
        assertEquals(0, match.kill(A, B, first));
        assertFalse(match.alive(B));
        assertTrue(match.respawn(B));
        long second = match.life(B);
        assertTrue(second > first);
        assertFalse(match.respawn(B));
        assertEquals(second, match.life(B));
        assertEquals(0, match.kill(A, B, first));
        assertTrue(match.alive(B));
        assertEquals(1, match.kill(A, B, second));
        match.leave(B); match.join(B);
        assertEquals(0, match.kill(A, B, second));
        assertTrue(match.alive(B));
        assertEquals(2, score(match, ALPHA));
    }

    @Test void environmentalFriendlyAndSelfDeathsConsumeLifeWithoutScoringButOutsidersAreRejected() {
        var match = playing(0); match.join(A2);
        assertEquals(0, match.kill(OUTSIDER, B)); assertTrue(match.alive(B));
        assertEquals(0, match.kill(A, OUTSIDER));
        assertEquals(0, match.kill(null, B)); assertFalse(match.alive(B));
        assertEquals(0, match.kill(A, B));
        match.respawn(B);
        assertEquals(0, match.kill(A, A2)); assertFalse(match.alive(A2));
        assertEquals(0, match.kill(B, B)); assertFalse(match.alive(B));
        assertEquals(0, score(match, ALPHA)); assertEquals(0, score(match, BRAVO));
    }

    @Test void deadKillerCanReceiveAnAuthoritativelyAttributedProjectileTrade() {
        var match = playing(0);
        assertEquals(1, match.kill(B, A));
        assertEquals(1, match.kill(A, B));
        assertEquals(1, score(match, ALPHA)); assertEquals(1, score(match, BRAVO));
    }

    @Test void scoreLimitEndsImmediatelyAndResultsRejectFurtherCombatAndCapture() {
        var match = match(1, 100, 0, 2, 0);
        match.join(A); match.join(B); match.tick(Map.of());
        assertEquals(1, match.kill(A, B));
        assertEquals(RESULTS, match.phase());
        assertEquals(ALPHA, match.snapshot().winner());
        assertEquals(SCORE_LIMIT, match.snapshot().endReason());
        assertFalse(match.respawn(B));
        assertEquals(0, match.kill(B, A));
        match.tick(Map.of("A", Set.of(A)));
        assertNull(zone(match, "A").owner());
        assertEquals(RESULTS, match.phase());
        match.tick(Map.of());
        assertEquals(WAITING, match.phase());
        assertEquals(0, score(match, ALPHA));
        match.tick(Map.of());
        assertEquals(PLAYING, match.phase());
        assertEquals(2, match.snapshot().round());
    }

    @Test void simultaneousCaptureLimitIsResolvedAfterAllZonesAndCanDraw() {
        var match = match(1, 100, 0, 2, 1);
        match.join(A); match.join(B); match.tick(Map.of());
        ticks(match, 3, Map.of("A", Set.of(A), "C", Set.of(B)));
        assertEquals(RESULTS, match.phase());
        assertEquals(SCORE_LIMIT, match.snapshot().endReason());
        assertEquals(1, score(match, ALPHA)); assertEquals(1, score(match, BRAVO));
        assertNull(match.snapshot().winner());
    }

    @Test void timerUsesFinalTickScoringAndScoreLimitTakesPrecedenceOverTimeLimit() {
        for (int limit : new int[] {1, 150}) {
            var match = match(limit, 3, 0, 2, 1);
            match.join(A); match.join(B); match.tick(Map.of());
            ticks(match, 3, Map.of("B", Set.of(B)));
            assertEquals(RESULTS, match.phase());
            assertEquals(BRAVO, match.snapshot().winner());
            assertEquals(limit == 1 ? SCORE_LIMIT : TIME_LIMIT, match.snapshot().endReason());
        }
    }

    @Test void restartRebalancesDeparturesAndInvalidatesPreviousRoundDeathTokens() {
        var match = match(150, 1, 0, 0, 0);
        match.join(A); match.join(B); match.join(A2); match.join(B2); match.join(id(5));
        match.tick(Map.of());
        long life = match.life(A);
        match.leave(B2); // 3:1, no mid-game team switch
        assertEquals(ALPHA, match.team(A2));
        match.tick(Map.of());
        assertEquals(RESULTS, match.phase());
        match.tick(Map.of());
        assertEquals(WAITING, match.phase());
        match.tick(Map.of());
        assertEquals(PLAYING, match.phase());
        assertEquals(2, match.members().values().stream().filter(t -> t == ALPHA).count());
        assertEquals(2, match.members().values().stream().filter(t -> t == BRAVO).count());
        assertTrue(match.life(A) > life);
        assertEquals(0, match.kill(B, A, life));
    }

    @Test void snapshotsAndMembershipAreImmutableCopiesAndPresenceIsNotRetained() {
        var match = playing(0);
        var before = match.snapshot(); var members = match.members();
        var presence = new HashMap<String, Set<UUID>>(); presence.put("A", Set.of(A));
        match.tick(presence); presence.clear(); match.tick(presence); match.join(A2);
        assertEquals(0, zone(match, "A").progressTicks());
        assertEquals(2, before.members().size()); assertEquals(2, members.size());
        assertEquals(0, before.zones().get("A").progress());
        assertThrows(UnsupportedOperationException.class, () -> members.clear());
        assertThrows(UnsupportedOperationException.class, () -> before.members().clear());
        assertThrows(UnsupportedOperationException.class, () -> before.scores().clear());
        assertThrows(UnsupportedOperationException.class, () -> before.zones().clear());
    }

    @Test void sourcedScoreAndLocallyTunedTimerHaveExactBoundaries() {
        var scoring = new ControlMatch();
        scoring.join(A); scoring.join(B); scoring.tick(Map.of());
        ticks(scoring, scoring.config().introTicks(), Map.of());
        for (int i = 0; i < 149; i++) {
            assertEquals(1, scoring.kill(A, B));
            assertTrue(scoring.respawn(B));
        }
        assertEquals(PLAYING, scoring.phase());
        assertEquals(1, scoring.kill(A, B));
        assertEquals(150, score(scoring, ALPHA));
        assertEquals(RESULTS, scoring.phase());
        assertEquals(SCORE_LIMIT, scoring.snapshot().endReason());

        var timed = new ControlMatch();
        timed.join(A); timed.join(B); timed.tick(Map.of());
        ticks(timed, timed.config().introTicks(), Map.of());
        ticks(timed, 11999, Map.of());
        assertEquals(PLAYING, timed.phase());
        assertEquals(1, timed.snapshot().remainingTicks());
        timed.tick(Map.of());
        assertEquals(RESULTS, timed.phase());
        assertEquals(TIME_LIMIT, timed.snapshot().endReason());
        assertNull(timed.snapshot().winner());
    }

    @Test void invalidConfigurationFailsBeforeMatchStartsAndSourceVersusLocalDefaultsAreExplicit() {
        assertThrows(IllegalArgumentException.class, () -> match(0, 1, 0, 0, 0));
        assertThrows(IllegalArgumentException.class, () -> match(1, 0, 0, 0, 0));
        assertThrows(IllegalArgumentException.class, () -> match(1, 1, -1, 0, 0));
        assertThrows(IllegalArgumentException.class, () -> match(1, 1, 0, -1, 0));
        assertThrows(IllegalArgumentException.class, () -> match(1, 1, 0, 0, -1));
        assertThrows(IllegalArgumentException.class, () -> new ControlMatch.Config(1, 1, 0, 0, 0, 1, 0, 600));
        assertThrows(IllegalArgumentException.class, () -> new ControlMatch.Config(1, 1, 0, 0, 1, 0, 0, 600));
        assertThrows(IllegalArgumentException.class, () -> new ControlMatch.Config(1, 1, 0, 0, 1, 1, 0, 0));
        assertThrows(IllegalArgumentException.class, () -> new ControlMatch.Config(1, 1, 0, 0, 1, 1, 0, -1));
        assertEquals(400, ControlMatch.Config.defaults().introTicks());
        assertEquals(200, ControlMatch.Config.defaults().resultTicks());
        assertEquals(600, ControlMatch.Config.defaults().forfeitGraceTicks());
        assertEquals(100, ControlMatch.Config.defaults().neutralizeTicks());
        assertEquals(100, ControlMatch.Config.defaults().captureTicks());
        assertEquals(1, ControlMatch.Config.defaults().captureReward());
        assertEquals(150, ControlMatch.Config.defaults().scoreLimit());
        assertEquals(12000, ControlMatch.Config.defaults().matchTicks());
        assertThrows(NullPointerException.class, () -> new ControlMatch().join(null));
    }
}
