package kim.biryeong.destiny.activity.reinforcement;

import java.util.*;
import java.util.function.*;

/** Fair bounded work across blocked and usable pads. No Minecraft or strike-specific types. */
public final class SpawnAttemptBudget<K> {
    private final int limit;
    private K last;
    public SpawnAttemptBudget(int limit) {
        if (limit < 1) throw new IllegalArgumentException("Missing spawn budget");
        this.limit = limit;
    }
    /** Return false from attempt after owner cancellation/reset to stop this snapshot immediately. */
    public <T> void run(Collection<T> entries, Function<T, K> key, Predicate<T> eligible, Predicate<T> attempt) {
        var order = List.copyOf(entries);
        int start = 0, attempts = 0;
        for (int i = 0; i < order.size(); i++) if (Objects.equals(key.apply(order.get(i)), last)) {
            start = i + 1; break;
        }
        for (int scanned = 0; scanned < order.size() && attempts < limit; scanned++) {
            T entry = order.get((start + scanned) % order.size());
            if (!eligible.test(entry)) continue;
            last = Objects.requireNonNull(key.apply(entry)); attempts++;
            if (!attempt.test(entry)) return;
        }
    }
    public void reset() { last = null; }
}
