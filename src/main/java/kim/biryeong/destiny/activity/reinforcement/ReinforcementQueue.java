package kim.biryeong.destiny.activity.reinforcement;

import java.util.*;
import java.util.function.Predicate;

/** Server-thread, encounter-owned FIFO. The activity supplies its active clock and admission caps.
 * Reservation is not arrival: call arrived only after the runtime actually accepts an actor.
 * Create one instance per encounter owner, never a global mutable singleton.
 */
public final class ReinforcementQueue<P> {
    public record Entry<P>(String id, P payload, int gap, long notBefore) { }
    private final Deque<Entry<P>> pending = new ArrayDeque<>();
    private final Set<String> scheduled = new HashSet<>(), arrived = new HashSet<>();
    private long lastArrival = Long.MIN_VALUE / 2;

    public boolean enqueue(String id, P payload, int gap, long notBefore) {
        Objects.requireNonNull(id); Objects.requireNonNull(payload);
        if (gap < 0) throw new IllegalArgumentException("Negative reinforcement gap");
        if (!scheduled.add(id)) return false;
        pending.addLast(new Entry<>(id, payload, gap, notBefore));
        return true;
    }
    /** Admission must include reserved/lost actors as well as living actors. */
    public P reserve(long tick, Predicate<P> admission) {
        var next = pending.peekFirst();
        if (next == null || tick < next.notBefore() || tick - lastArrival < next.gap()
                || !admission.test(next.payload())) return null;
        pending.removeFirst();
        lastArrival = tick;
        return next.payload();
    }
    /** First accepted member advances the spacing clock; retries/remaining members do not. */
    public void arrived(String id, long tick, int warningTicks) {
        if (warningTicks < 0) throw new IllegalArgumentException("Negative warning");
        if (scheduled.contains(id) && arrived.add(id)) lastArrival = Math.max(lastArrival, tick - warningTicks);
    }
    public boolean hasArrived(String id) { return arrived.contains(id); }
    public int size() { return pending.size(); }
    public void cancelQueued(Predicate<P> predicate) { pending.removeIf(e -> predicate.test(e.payload())); }
    /** Cancel pending packs without allowing their IDs to be re-enqueued in this encounter. */
    public void cancelQueued() { pending.clear(); }
    /** Owner must invalidate old generation callbacks before resetting. */
    public void reset() {
        pending.clear(); scheduled.clear(); arrived.clear(); lastArrival = Long.MIN_VALUE / 2;
    }
}
