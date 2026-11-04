package kim.biryeong.destiny.weapon;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class AmbitiousAssassinCycleW193Test {
    @Test void creditHasNoInventedStowExpiryAndIsConsumedOnceAtReloadCredit() {
        var c=new AmbitiousAssassinCycle();var e=c.capture(1);var corpse=new Object();
        assertTrue(c.killed(2,e,corpse));assertFalse(c.killed(2,e,corpse));
        c.update(10000);assertEquals(1,c.kills(10000));
        var reload=c.acceptedReload(10000);
        assertTrue(c.killed(10001,c.capture(10001),new Object()));
        assertEquals(2,c.finish(10002,reload));assertEquals(0,c.kills(10002));
        assertEquals(0,c.finish(10003,reload));
    }
    @Test void cancelledAcceptedReloadDoesNotConsumeKills() {
        var c=new AmbitiousAssassinCycle();c.killed(0,c.capture(0),new Object());
        c.acceptedReload(1); // Caller cancels: finish is deliberately never invoked.
        assertEquals(1,c.kills(1000));
        assertEquals(1,c.finish(1001,c.acceptedReload(1000)));
    }
    @Test void sourceEpochAndRollbackPermanentlyRevokeOldTokens() {
        var c=new AmbitiousAssassinCycle();var e=c.capture(10);var r=c.acceptedReload(11);
        c.update(5);assertFalse(c.killed(12,e,new Object()));assertEquals(0,c.finish(12,r));
        assertTrue(c.killed(12,c.capture(12),new Object()));
        c.clear();assertEquals(0,c.kills(12));
    }
    @Test void cappedCounterAndPerEmissionLedgerStayBoundedWithoutReadmittingCorpses() {
        var c=new AmbitiousAssassinCycle();var e=c.capture(0);
        for(int i=0;i<256;i++)assertTrue(c.killed(1,e,new Object()));
        assertFalse(c.killed(1,e,new Object()));assertEquals(15,c.kills(1));
        assertEquals(15,c.finish(2,c.acceptedReload(1)));
    }
    @Test void foreignEmissionAndReloadCannotGrantOrSpendCredit() {
        var a=new AmbitiousAssassinCycle();var b=new AmbitiousAssassinCycle();
        assertFalse(a.killed(1,b.capture(0),new Object()));
        a.killed(1,a.capture(0),new Object());
        assertEquals(0,a.finish(2,b.acceptedReload(1)));assertEquals(1,a.kills(2));
    }
}
