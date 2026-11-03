package kim.biryeong.destiny.activity.reinforcement;

import org.junit.jupiter.api.Test;
import java.util.*;
import static org.junit.jupiter.api.Assertions.*;

class SpawnAttemptBudgetTest {
    @Test void blockedEntriesYieldToOtherPadsWithinBoundedTicks() {
        var budget = new SpawnAttemptBudget<String>(2);
        var attempts = new ArrayList<String>();
        var entries = List.of("blocked-a", "blocked-b", "clear-a", "clear-b", "clear-c");
        for (int i = 0; i < 3; i++) budget.run(entries, x -> x, x -> true, x -> { attempts.add(x); return true; });
        assertEquals(List.of("blocked-a", "blocked-b", "clear-a", "clear-b", "clear-c", "blocked-a"), attempts);
    }
    @Test void ownerInvalidationStopsSnapshotAndResetRestartsAtFirstEligible() {
        var budget = new SpawnAttemptBudget<Integer>(2);
        var calls = new ArrayList<Integer>();
        budget.run(List.of(1, 2, 3), x -> x, x -> true, x -> { calls.add(x); budget.reset(); return false; });
        assertEquals(List.of(1), calls);
        budget.run(List.of(1, 2, 3), x -> x, x -> x != 2, x -> { calls.add(x); return true; });
        assertEquals(List.of(1, 1, 3), calls);
    }
    @Test void removedCursorAndEmptyQueueAreSafe() {
        var budget = new SpawnAttemptBudget<Integer>(1);
        budget.run(List.of(1), x -> x, x -> true, x -> true);
        budget.run(List.<Integer>of(), x -> x, x -> true, x -> fail("Empty queue"));
        var calls = new ArrayList<Integer>();
        budget.run(List.of(2, 3), x -> x, x -> true, x -> { calls.add(x); return true; });
        assertEquals(List.of(2), calls);
    }
}
