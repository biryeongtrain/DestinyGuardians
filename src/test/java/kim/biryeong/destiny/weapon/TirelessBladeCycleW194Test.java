package kim.biryeong.destiny.weapon;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class TirelessBladeCycleW194Test {
    @Test void firstKillThenPairsWithNoInventedStowTimeout() {
        var c = new TirelessBladeCycle();
        assertEquals(1, c.killed(0, c.capture(0), new Object()));
        assertEquals(0, c.killed(1, c.capture(1), new Object()));
        c.update(10000); // ordinary stow keeps the original source and counter
        assertEquals(1, c.progress(10000));
        assertEquals(1, c.killed(10001, c.capture(10001), new Object()));
        assertEquals(0, c.progress(10001));
    }
    @Test void firstKillEntitlementIsSharedAcrossSourcesAndSurvivesSourceClear() {
        var spawn = new TirelessBladeCycle.Spawn();
        var a = new TirelessBladeCycle(spawn); var b = new TirelessBladeCycle(spawn);
        assertEquals(1, a.killed(0, a.capture(0), new Object()));
        a.clear(); // source edit/cleanup invalidates tokens, never rearms the life entitlement
        assertEquals(0, a.killed(1, a.capture(1), new Object()));
        assertEquals(0, b.killed(1, b.capture(1), new Object()));
        assertEquals(1, b.killed(2, b.capture(2), new Object()));
        var replacement = new TirelessBladeCycle(spawn);
        assertEquals(0, replacement.killed(3, replacement.capture(3), new Object()));
        var respawned = new TirelessBladeCycle(new TirelessBladeCycle.Spawn());
        assertEquals(1, respawned.killed(4, respawned.capture(4), new Object()));
    }
    @Test void cleaveCountsEachFinalBlowOnceAndCasterReplayCannotGrant() {
        var c = new TirelessBladeCycle(); var contact = c.capture(0); var corpse = new Object();
        assertEquals(1, c.killed(0, contact, corpse));
        assertEquals(0, c.killed(0, contact, corpse));
        assertEquals(0, c.killed(0, c.capture(0), corpse));
        assertEquals(0, c.killed(0, contact, new Object()));
        assertEquals(1, c.progress(0));
        assertEquals(1, c.killed(0, contact, new Object()));
    }
    @Test void sourceEpochForeignTokenAndRollbackCannotCountOrRearmFirstReward() {
        var c = new TirelessBladeCycle(); var foreign = new TirelessBladeCycle();
        var old = c.capture(10); assertEquals(1, c.killed(10, old, new Object()));
        c.clear();
        assertEquals(0, c.killed(11, old, new Object()));
        assertEquals(0, c.killed(11, foreign.capture(10), new Object()));
        assertEquals(0, c.progress(11));
        var current = c.capture(20); c.update(19);
        assertEquals(0, c.killed(20, current, new Object()));
        assertEquals(0, c.killed(20, c.capture(20), new Object()));
        assertEquals(1, c.progress(20));
    }
    @Test void countOnlyQueriesAndInvalidEventsCannotSpendInitialReward() {
        var c = new TirelessBladeCycle(); var contact = c.capture(0);
        assertEquals(0, c.progress(10000)); assertEquals(0, c.progress(0));
        assertEquals(0, c.killed(0, null, new Object()));
        assertEquals(0, c.killed(0, contact, null));
        assertEquals(1, c.killed(0, contact, new Object()));
    }
    @Test void ledgerBoundsFailClosedAndDoNotKeepEvictedContactAuthority() {
        var c = new TirelessBladeCycle(); var old = c.capture(0);
        for (int i = 0; i < 128; i++) c.capture(0);
        assertEquals(0, c.killed(0, old, new Object()));
        var contact = c.capture(0); var first = new Object();
        assertEquals(1, c.killed(0, contact, first));
        for (int i = 1; i < 256; i++) c.killed(0, contact, new Object());
        int before = c.progress(0);
        assertEquals(0, c.killed(0, contact, new Object()));
        assertEquals(0, c.killed(0, contact, first));
        assertEquals(before, c.progress(0));
    }
}
