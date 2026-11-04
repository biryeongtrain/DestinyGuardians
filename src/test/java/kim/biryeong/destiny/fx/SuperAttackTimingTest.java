package kim.biryeong.destiny.fx;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class SuperAttackTimingTest {
    @Test void windupHasExactlyOneContactAndRejectsDuplicateInput() {
        for (int ticks : new int[]{SuperAttackTiming.ARC_CONTACT, SuperAttackTiming.SOLAR_CONTACT}) {
            var timing = new SuperAttackTiming();
            assertTrue(timing.request(ticks));
            for (int i = 1; i < ticks; i++) {
                assertFalse(timing.request(ticks));
                assertFalse(timing.advance());
            }
            assertTrue(timing.advance());
            for (int i = 0; i < 40; i++) assertFalse(timing.advance());
            assertFalse(timing.pending());
        }
    }
    @Test void cancellationNeverProducesLateContact() {
        var timing = new SuperAttackTiming();
        timing.request(5);
        timing.advance();
        timing.cancel();
        for (int i = 0; i < 40; i++) assertFalse(timing.advance());
        assertTrue(timing.request(3));
        assertThrows(IllegalArgumentException.class, () -> timing.request(0));
    }
    @Test void firstPersonSummonRecoilAndDissolveReturnToSameNeutralPose() {
        var start = GoldenGunHandPose.sample(0, -1, 200, -1);
        var ready = GoldenGunHandPose.sample(10, -1, 190, -1);
        var kick = GoldenGunHandPose.sample(20, 0, 180, -1);
        var recovered = GoldenGunHandPose.sample(26, 6, 174, -1);
        var gone = GoldenGunHandPose.sample(40, 20, 160, 6);
        assertTrue(start.size() < ready.size() && start.y() > ready.y());
        assertEquals(420, ready.size());
        assertTrue(kick.y() < ready.y() && kick.roll() < 0);
        assertEquals(ready, recovered);
        assertEquals(1, gone.size());
        assertTrue(gone.y() > ready.y());
    }
}
