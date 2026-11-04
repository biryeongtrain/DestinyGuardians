package kim.biryeong.destiny.strike.devils;

import org.junit.jupiter.api.Test;

import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

import static kim.biryeong.destiny.strike.devils.DevilsRecovery.*;
import static org.junit.jupiter.api.Assertions.*;

class DevilsRecoveryTest {
    static final UUID A = new UUID(0, 1), B = new UUID(0, 2), C = new UUID(0, 3);
    static final class Fixture implements Host {
        final List<Revival> requested = new ArrayList<>(), cancelled = new ArrayList<>();
        final List<Long> wipes = new ArrayList<>();
        final DevilsRecovery recovery = new DevilsRecovery(UUID.randomUUID(), List.of(A, B, C), this);
        boolean accept = true, finishImmediately;
        Fixture(DevilsPlan.Zone zone) {
            recovery.reset(1, zone);
            for (UUID p : List.of(A, B, C)) recovery.presence(p, true, true);
        }
        @Override public boolean revive(Revival revival) {
            requested.add(revival);
            if (accept && finishImmediately) recovery.revived(revival);
            return accept;
        }
        @Override public void cancel(Revival revival) {
            cancelled.add(revival);
            assertFalse(recovery.revived(revival), "cancelled presentation is never success");
        }
        @Override public void wipe(long generation) { wipes.add(generation); }
        void ticks(int n) { for (int i = 0; i < n; i++) recovery.tick(); }
        DownToken down(UUID player) { return recovery.down(player, recovery.snapshot().generation()).orElseThrow(); }
        Member member(UUID id) { return recovery.snapshot().members().stream().filter(m -> m.player().equals(id)).findFirst().orElseThrow(); }
        void hold(UUID helper, DownToken down, int count) {
            for (int i = 0; i < count; i++) { assertTrue(recovery.hold(helper, down)); recovery.tick(); }
        }
    }

    @Test void oneToThreeUniquePlayersAndExplicitInitialGenerationRequired() {
        Host host = new Host() { public boolean revive(Revival r) { return false; } public void wipe(long g) { } };
        assertThrows(IllegalArgumentException.class, () -> new DevilsRecovery(UUID.randomUUID(), List.of(), host));
        assertThrows(IllegalArgumentException.class, () -> new DevilsRecovery(UUID.randomUUID(), List.of(A, B, C, UUID.randomUUID()), host));
        assertDoesNotThrow(() -> new DevilsRecovery(UUID.randomUUID(), List.of(A), host));
        assertDoesNotThrow(() -> new DevilsRecovery(UUID.randomUUID(), List.of(A, B), host));
        assertThrows(IllegalArgumentException.class, () -> new DevilsRecovery(UUID.randomUUID(), List.of(A, A, C), host));
        var policy = new DevilsRecovery(UUID.randomUUID(), List.of(A, B, C), host);
        assertTrue(policy.down(A, 0).isEmpty());
        assertTrue(policy.reset(1, DevilsPlan.Zone.RY));
        assertFalse(policy.reset(1, DevilsPlan.Zone.RF));
        assertFalse(policy.reset(0, DevilsPlan.Zone.RF));
    }

    @Test void rocketyardSelfReviveUnlocksAtFiveSecondsAndWaitsForAcknowledgement() {
        var f = new Fixture(DevilsPlan.Zone.RY); DownToken down = f.down(A);
        f.ticks(99); assertTrue(f.requested.isEmpty()); assertEquals(1, f.member(A).readyIn());
        f.recovery.tick(); assertTrue(f.requested.isEmpty()); assertTrue(f.recovery.self(down));
        assertEquals(1, f.requested.size());
        assertEquals(Method.SELF, f.requested.getFirst().method());
        assertEquals(State.REVIVING, f.member(A).state()); assertEquals(2, f.recovery.snapshot().living());
        f.ticks(14); assertTrue(f.recovery.revived(f.requested.getFirst()));
        assertEquals(State.ALIVE, f.member(A).state()); assertEquals(3, f.recovery.snapshot().living());
        assertFalse(f.recovery.self(down)); assertFalse(f.recovery.revived(f.requested.getFirst()));
    }

    @Test void otherThreeZonesRequireThirtySecondsAndAnExplicitSelfRequest() {
        for (var zone : List.of(DevilsPlan.Zone.RF, DevilsPlan.Zone.BL, DevilsPlan.Zone.SP)) {
            var f = new Fixture(zone); DownToken down = f.down(A);
            f.ticks(599); assertFalse(f.recovery.self(down)); f.recovery.tick();
            assertTrue(f.requested.isEmpty()); assertTrue(f.recovery.self(down));
            assertEquals(Method.SELF, f.requested.getFirst().method());
            assertFalse(f.recovery.self(down));
            assertTrue(f.recovery.revived(f.requested.getFirst()));
        }
    }

    @Test void allyHoldRequiresSixtyConsecutiveTicksNotRepeatedCalls() {
        var f = new Fixture(DevilsPlan.Zone.RF); DownToken down = f.down(A);
        for (int i = 0; i < 100; i++) assertTrue(f.recovery.hold(B, down));
        f.recovery.tick(); assertEquals(1, f.member(A).holdTicks());
        f.hold(B, down, 29); assertEquals(30, f.member(A).holdTicks());
        f.recovery.tick(); assertEquals(0, f.member(A).holdTicks());
        f.hold(B, down, 59); assertTrue(f.requested.isEmpty()); f.hold(B, down, 1);
        assertEquals(1, f.requested.size()); assertEquals(Method.ALLY, f.requested.getFirst().method());
        assertEquals(B, f.requested.getFirst().ally());
    }

    @Test void switchingHelpersResetsProgressAndSimultaneousHelpersNeverCombine() {
        var f = new Fixture(DevilsPlan.Zone.SP); DownToken down = f.down(A);
        f.hold(B, down, 40); f.hold(C, down, 1); assertEquals(1, f.member(A).holdTicks());
        for (int i = 0; i < 59; i++) {
            f.recovery.hold(B, down); f.recovery.hold(C, down); f.recovery.tick();
        }
        assertTrue(f.requested.isEmpty()); assertEquals(59, f.member(A).holdTicks());
        f.hold(B, down, 1); assertEquals(1, f.requested.size());
    }

    @Test void downedForeignSelfAndDisconnectedHelpersCannotRevive() {
        var f = new Fixture(DevilsPlan.Zone.BL); DownToken a = f.down(A), b = f.down(B);
        assertFalse(f.recovery.hold(A, a)); assertFalse(f.recovery.hold(B, a));
        assertFalse(f.recovery.hold(UUID.randomUUID(), a));
        f.recovery.presence(C, false, false); assertFalse(f.recovery.hold(C, b));
        assertTrue(f.recovery.down(A, 99).isEmpty());
        var other = new Fixture(DevilsPlan.Zone.BL); assertFalse(other.recovery.self(a));
    }

    @Test void eightSecondsWithoutConnectedLivingMembersWipesOnce() {
        var f = new Fixture(DevilsPlan.Zone.RF); f.down(A); f.down(B); f.down(C);
        f.ticks(159); assertTrue(f.wipes.isEmpty()); assertEquals(1, f.recovery.snapshot().wipeRemaining());
        f.recovery.tick(); assertEquals(List.of(1L), f.wipes); assertTrue(f.recovery.snapshot().wipeIssued());
        f.ticks(1000); assertEquals(1, f.wipes.size());
        assertTrue(f.recovery.down(A, 1).isEmpty());
    }

    @Test void disconnectDoesNotCountAsAnImmortalLivingTeammate() {
        var f = new Fixture(DevilsPlan.Zone.RF); f.down(A);
        f.recovery.presence(B, false, false); f.recovery.presence(C, false, false);
        f.ticks(160); assertEquals(1, f.wipes.size());
    }

    @Test void wholePartyOfflinePausesDownAndWipeClocks() {
        var f = new Fixture(DevilsPlan.Zone.RF); f.down(A); f.down(B); f.down(C); f.ticks(80);
        for (UUID p : List.of(A, B, C)) f.recovery.presence(p, false, false);
        long clock = f.recovery.snapshot().tick(); f.ticks(3000);
        assertEquals(clock, f.recovery.snapshot().tick()); assertEquals(80, f.recovery.snapshot().wipeRemaining());
        assertTrue(f.recovery.snapshot().paused()); assertTrue(f.wipes.isEmpty());
        f.recovery.presence(A, true, true); f.ticks(79); assertTrue(f.wipes.isEmpty());
        f.recovery.tick(); assertEquals(1, f.wipes.size());
    }

    @Test void aLivingReconnectionCancelsTheWipeCountdown() {
        var f = new Fixture(DevilsPlan.Zone.RF); f.down(A); f.down(B); f.recovery.presence(C, false, false);
        f.ticks(150); f.recovery.presence(C, true, true);
        assertEquals(-1, f.recovery.snapshot().wipeRemaining());
        f.ticks(100); assertTrue(f.wipes.isEmpty());
        f.recovery.presence(C, false, false); f.ticks(159); assertTrue(f.wipes.isEmpty());
        f.recovery.tick(); assertEquals(1, f.wipes.size());
    }

    @Test void normalZoneWaitsForSelfRequestWithoutWipe() {
        var f = new Fixture(DevilsPlan.Zone.RY); f.down(A); f.down(B); f.down(C); f.ticks(600);
        assertTrue(f.requested.isEmpty()); assertTrue(f.wipes.isEmpty());
        for (UUID id : List.of(A, B, C)) assertTrue(f.recovery.self(f.recovery.token(id).orElseThrow()));
        assertEquals(3, f.requested.size()); f.ticks(14);
        for (Revival request : f.requested) assertTrue(f.recovery.revived(request));
        f.ticks(100); assertTrue(f.wipes.isEmpty()); assertEquals(3, f.recovery.snapshot().living());
    }

    @Test void protectionLastsThreeSecondsAndAcceptedAttackImmediatelyCancelsIt() {
        var f = new Fixture(DevilsPlan.Zone.RY); f.finishImmediately = true; f.down(A); f.ticks(100); f.recovery.self(f.recovery.token(A).orElseThrow());
        assertTrue(f.recovery.protectedNow(A)); f.ticks(59); assertTrue(f.recovery.protectedNow(A));
        f.recovery.tick(); assertFalse(f.recovery.protectedNow(A));
        f.down(A); f.ticks(100); f.recovery.self(f.recovery.token(A).orElseThrow()); assertTrue(f.recovery.protectedNow(A));
        f.recovery.attacked(A, 99); assertTrue(f.recovery.protectedNow(A));
        f.recovery.attacked(A, 1); assertFalse(f.recovery.protectedNow(A));
    }

    @Test void generationsAndIndividualDeathsInvalidateLateCallbacks() {
        var f = new Fixture(DevilsPlan.Zone.RY); DownToken first = f.down(A); f.ticks(100); f.recovery.self(first); f.recovery.self(f.recovery.token(A).orElseThrow());
        Revival old = f.requested.getFirst(); assertTrue(f.recovery.reset(2, DevilsPlan.Zone.BL));
        assertEquals(List.of(old), f.cancelled); assertFalse(f.recovery.revived(old));
        assertFalse(f.recovery.hold(B, first)); assertFalse(f.recovery.self(first));
        DownToken next = f.down(A); assertNotEquals(first, next);
        f.hold(B, next, 60); Revival current = f.requested.getLast();
        assertTrue(f.recovery.revived(current));
        DownToken third = f.down(A); assertNotEquals(next, third);
        assertFalse(f.recovery.revived(current)); assertFalse(f.recovery.self(next));
        assertEquals(State.DOWN, f.member(A).state());
    }

    @Test void duplicateDownEventsDoNotRestartTheSelfClock() {
        var f = new Fixture(DevilsPlan.Zone.RF); DownToken down = f.down(A); f.ticks(500);
        assertEquals(down, f.down(A)); assertEquals(100, f.member(A).readyIn());
        f.ticks(100); assertTrue(f.recovery.self(down));
    }

    @Test void rejectedOrStalledRequestsRemainDownAndRetriesHaveNewIdentity() {
        var f = new Fixture(DevilsPlan.Zone.RY); f.accept = false; f.down(A); f.ticks(100); f.recovery.self(f.recovery.token(A).orElseThrow());
        assertEquals(State.DOWN, f.member(A).state()); assertEquals(1, f.requested.size());
        f.ticks(19); assertEquals(1, f.requested.size()); f.accept = true; f.recovery.tick(); f.recovery.self(f.recovery.token(A).orElseThrow());
        Revival current = f.requested.getLast(); assertNotEquals(f.requested.getFirst(), current);
        assertFalse(f.recovery.revived(f.requested.getFirst()));
        f.ticks(REVIVE_ACK_TICKS); assertEquals(State.DOWN, f.member(A).state());
        assertEquals(List.of(current), f.cancelled); assertFalse(f.recovery.revived(current));
        f.ticks(RETRY_TICKS); f.recovery.self(f.recovery.token(A).orElseThrow()); assertEquals(3, f.requested.size());
    }

    @Test void disconnectCancelsOnlyThatPendingRevivalAndNeverGrantsProtection() {
        var f = new Fixture(DevilsPlan.Zone.RY); f.down(A); f.down(B); f.ticks(100);
        f.recovery.self(f.recovery.token(A).orElseThrow()); f.recovery.self(f.recovery.token(B).orElseThrow());
        Revival a = f.requested.stream().filter(r -> r.down().player().equals(A)).findFirst().orElseThrow();
        Revival b = f.requested.stream().filter(r -> r.down().player().equals(B)).findFirst().orElseThrow();
        f.recovery.presence(A, false, false);
        assertEquals(List.of(a), f.cancelled); assertFalse(f.recovery.revived(a));
        assertTrue(f.recovery.revived(b)); assertTrue(f.recovery.protectedNow(B));
        assertEquals(State.DOWN, f.member(A).state());
    }

    @Test void closeIsIdempotentAndForeignTokensCannotCancelAnotherRun() {
        var f = new Fixture(DevilsPlan.Zone.RY); f.down(A); f.ticks(100); f.recovery.self(f.recovery.token(A).orElseThrow());
        var other = new Fixture(DevilsPlan.Zone.RY); other.down(A); other.ticks(100); other.recovery.self(other.recovery.token(A).orElseThrow());
        Revival foreign = other.requested.getFirst();
        assertFalse(f.recovery.revived(foreign)); assertFalse(f.recovery.failed(foreign));
        f.recovery.close(); f.recovery.close(); assertEquals(1, f.cancelled.size());
        assertFalse(f.recovery.revived(f.requested.getFirst())); assertFalse(f.recovery.reset(2, DevilsPlan.Zone.RY));
        f.ticks(1000); assertTrue(f.wipes.isEmpty()); assertTrue(f.recovery.snapshot().closed());
    }
}
