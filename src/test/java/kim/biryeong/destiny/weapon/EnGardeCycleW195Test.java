package kim.biryeong.destiny.weapon;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class EnGardeCycleW195Test {
    @Test void blockedIncomingWaitsForRealReadyAndQueriesCannotArmOrRefresh() {
        var ready = new EnGardeCycle.Readiness(); var c = new EnGardeCycle(ready); var sword = new Object();
        c.update(0, true, ready.observe(0, sword, false));
        assertEquals(0, c.remaining(0));
        assertFalse(c.capturedActive(0, c.capture(0)));
        c.update(2, true, ready.observe(2, sword, true));
        assertTrue(c.remaining(2) > 0);
        long end = 2L + EnGardeProfile.durationTicks();
        assertTrue(c.remaining(end - 1) > 0);
        assertEquals(0, c.remaining(end));
        assertTrue(c.remaining(2) > 0); // no mutation from a future query
        c.update(3, true, ready.observe(3, sword, true));
        assertEquals(0, c.remaining(end));
        c.update(end + 100, true, ready.observe(end + 100, sword, true));
        assertEquals(0, c.remaining(end + 100));
    }
    @Test void paidSnapshotSurvivesExpiryAndStowButNotSameTickSourceEdit() {
        var ready = new EnGardeCycle.Readiness(); var c = new EnGardeCycle(ready); var sword = new Object();
        c.update(0, true, ready.observe(0, sword, true)); var paid = c.capture(0);
        c.stowing(1); ready.stowing(sword);
        assertEquals(0, c.remaining(1));
        assertTrue(c.capturedActive(100, paid));
        c.changed(1);
        assertFalse(c.capturedActive(1, paid));
        assertFalse(new EnGardeCycle().capturedActive(1, paid));
    }
    @Test void editRebindRetainsConsumedIncomingIdentityEvenAfterCooldown() {
        var ready = new EnGardeCycle.Readiness(); var sword = new Object();
        var old = new EnGardeCycle(ready);
        old.update(0, true, ready.observe(0, sword, true)); var paid = old.capture(0);
        old.changed(0);
        var replacement = new EnGardeCycle(ready);
        replacement.update(0, true, ready.observe(0, sword, true));
        assertEquals(0, replacement.remaining(0));
        long later = EnGardeProfile.provisionalCooldownTicks() + 1L;
        replacement.update(later, true, ready.observe(later, sword, true));
        assertEquals(0, replacement.remaining(later));
        assertFalse(old.capturedActive(later, paid));
        ready.stowing(sword);
        replacement.update(later, true, ready.observe(later, sword, true));
        assertTrue(replacement.remaining(later) > 0);
    }
    @Test void cooldownStartsAtRemovalAndCooldownReadyIsConsumedWithoutQueuedProc() {
        var ready = new EnGardeCycle.Readiness(); var c = new EnGardeCycle(ready); var sword = new Object();
        c.update(0, true, ready.observe(0, sword, true));
        c.stowing(1); ready.stowing(sword);
        c.update(2, true, ready.observe(2, sword, true));
        assertEquals(0, c.remaining(2));
        long boundary = 1L + EnGardeProfile.provisionalCooldownTicks();
        c.update(boundary, true, ready.observe(boundary, sword, true));
        assertEquals(0, c.remaining(boundary));
        ready.stowing(sword);
        c.update(boundary, true, ready.observe(boundary, sword, true));
        assertTrue(c.remaining(boundary) > 0);
    }
    @Test void exactExpirySchedulesCooldownFromDeadlineEvenWithSparseUpdates() {
        var ready = new EnGardeCycle.Readiness(); var c = new EnGardeCycle(ready); var sword = new Object();
        c.update(0, true, ready.observe(0, sword, true));
        long boundary = (long)EnGardeProfile.durationTicks() + EnGardeProfile.provisionalCooldownTicks();
        c.update(boundary, true, false); ready.stowing(sword);
        c.update(boundary, true, ready.observe(boundary, sword, true));
        assertTrue(c.remaining(boundary) > 0);
    }
    @Test void rollbackAndBoundedContactEvictionRevokeSnapshots() {
        var ready = new EnGardeCycle.Readiness(); var c = new EnGardeCycle(ready);
        c.update(10, true, ready.observe(10, new Object(), true)); var old = c.capture(10);
        for (int i = 0; i < 128; i++) c.capture(10);
        assertFalse(c.capturedActive(10, old));
        var current = c.capture(11); c.update(10, true, false);
        assertFalse(c.capturedActive(11, current));
    }
}
