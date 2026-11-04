package kim.biryeong.destiny.weapon;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class RelentlessStrikesCycleW194Test {
    @Test void successiveHitsUseEachGapAndAllowSameTargetOnLaterPaidContacts() {
        var c = new RelentlessStrikesCycle(); var target = new Object();
        long gap = RelentlessStrikesProfile.windowTicks();
        assertEquals(0, c.confirmed(0, c.capture(0), target, 1));
        assertEquals(0, c.confirmed(gap, c.capture(gap), target, 1));
        assertEquals(1, c.confirmed(2 * gap, c.capture(2 * gap), target, 1));
        assertEquals(0, c.progress(2 * gap));
    }
    @Test void expiredGapRestartsInsteadOfAwardingAndReadsCannotConsumeProgress() {
        var c = new RelentlessStrikesCycle();
        c.confirmed(0, c.capture(0), new Object(), 1);
        long late = RelentlessStrikesProfile.windowTicks() + 1;
        assertEquals(0, c.progress(late));
        assertEquals(1, c.progress(0), "future count query cannot mutate state");
        assertEquals(0, c.confirmed(late, c.capture(late), new Object(), 1));
        assertEquals(1, c.progress(late));
        c.update(late + 1); // ordinary stow does not call clear
        assertEquals(1, c.progress(late + 1));
    }
    @Test void oneCleaveCountsDistinctTargetsAndCasterDirectSplashCannotDoubleCount() {
        var c = new RelentlessStrikesCycle(); var contact = c.capture(0); var target = new Object();
        assertEquals(0, c.confirmed(0, contact, target, 1));
        assertEquals(0, c.confirmed(0, contact, target, 1));
        assertEquals(1, c.progress(0));
        assertEquals(0, c.confirmed(0, contact, new Object(), 1));
        assertEquals(1, c.confirmed(0, contact, new Object(), 1));
        assertEquals(0, c.confirmed(0, contact, target, 1));
        assertEquals(0, c.progress(0));
    }
    @Test void rejectedLossCannotCountOrPoisonLaterActualLoss() {
        var c = new RelentlessStrikesCycle(); var contact = c.capture(0); var target = new Object();
        for (double loss : new double[]{0, -1, Double.NaN, Double.POSITIVE_INFINITY})
            assertEquals(0, c.confirmed(0, contact, target, loss));
        assertEquals(0, c.progress(0));
        c.confirmed(0, contact, target, 0.01);
        assertEquals(1, c.progress(0));
    }
    @Test void sourceClearRollbackAndForeignContactRevokeAuthority() {
        var c = new RelentlessStrikesCycle(); var foreign = new RelentlessStrikesCycle();
        var old = c.capture(10); c.confirmed(10, old, new Object(), 1);
        c.clear();
        assertEquals(0, c.confirmed(11, old, new Object(), 1));
        assertEquals(0, c.confirmed(11, foreign.capture(10), new Object(), 1));
        var current = c.capture(20); c.update(19);
        assertEquals(0, c.confirmed(20, current, new Object(), 1));
        assertEquals(0, c.progress(20));
    }
    @Test void ledgerBoundsFailClosedWithoutReacceptingAnEvictedContact() {
        var c = new RelentlessStrikesCycle(); var oldest = c.capture(0);
        for (int i = 0; i < 128; i++) c.capture(0);
        assertEquals(0, c.confirmed(0, oldest, new Object(), 1));
        assertEquals(0, c.progress(0));
        var contact = c.capture(0); var first = new Object(); c.confirmed(0, contact, first, 1);
        for (int i = 1; i < 256; i++) c.confirmed(0, contact, new Object(), 1);
        int before = c.progress(0);
        assertEquals(0, c.confirmed(0, contact, new Object(), 1));
        assertEquals(0, c.confirmed(0, contact, first, 1));
        assertEquals(before, c.progress(0));
    }
}
