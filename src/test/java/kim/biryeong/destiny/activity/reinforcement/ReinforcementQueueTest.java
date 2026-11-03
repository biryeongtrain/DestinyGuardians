package kim.biryeong.destiny.activity.reinforcement;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class ReinforcementQueueTest {
    @Test void delayedArrivalSpacesNextPackAndRemainingMembersDoNotRestartGap() {
        var q = new ReinforcementQueue<Integer>();
        assertTrue(q.enqueue("a", 8, 100, 0));
        assertTrue(q.enqueue("b", 4, 100, 0));
        assertEquals(8, q.reserve(0, n -> true));
        q.arrived("a", 200, 40);
        q.arrived("a", 220, 40);
        assertNull(q.reserve(259, n -> true));
        assertEquals(4, q.reserve(260, n -> true));
    }
    @Test void capacityWaitDoesNotConsumePackAndCancellationKeepsIdempotency() {
        var q = new ReinforcementQueue<Integer>();
        q.enqueue("a", 8, 10, 20);
        assertNull(q.reserve(19, n -> true));
        assertNull(q.reserve(20, n -> n <= 4));
        assertEquals(1, q.size());
        q.cancelQueued();
        assertFalse(q.enqueue("a", 8, 10, 20));
        q.reset();
        assertTrue(q.enqueue("a", 8, 10, 20));
        assertEquals(8, q.reserve(20, n -> true));
    }
    @Test void encounterInstancesAreIndependentAndUnknownArrivalsDoNotDelayThem() {
        var first = new ReinforcementQueue<String>();
        var second = new ReinforcementQueue<String>();
        first.enqueue("same", "first", 100, 0);
        second.enqueue("same", "second", 100, 0);
        first.cancelQueued(x -> true);
        second.arrived("unknown", 500, 0);
        assertEquals("second", second.reserve(0, x -> true));
        assertNull(first.reserve(0, x -> true));
    }
}
