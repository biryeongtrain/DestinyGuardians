package kim.biryeong.destiny.activity.reinforcement;

import java.util.*;

/** Generation-owned selected spawn pads. A completed warning never replaces a live collision recheck.
 * P is the activity's selected pad, B its collision reservation. Values must be immutable.
 */
public final class SpawnWarnings<K, P, B> {
    public record Pending<P, B>(long generation, P point, B body, long readyAt) {
        public boolean ready(long tick) { return tick >= readyAt; }
    }
    private final Map<K, Pending<P, B>> pending = new LinkedHashMap<>();
    public Pending<P, B> get(long generation, K slot) {
        var value = pending.get(slot);
        return value != null && value.generation() == generation ? value : null;
    }
    public void begin(long generation, K slot, P point, B body, long tick, int lead) {
        if (lead < 1) throw new IllegalArgumentException("Missing spawn warning interval");
        pending.put(Objects.requireNonNull(slot), new Pending<>(generation,
                Objects.requireNonNull(point), Objects.requireNonNull(body), Math.addExact(tick, lead)));
    }
    public List<B> reservations(K exceptSlot) {
        return pending.entrySet().stream().filter(e -> !e.getKey().equals(exceptSlot)).map(e -> e.getValue().body()).toList();
    }
    public void remove(K slot) { pending.remove(slot); }
    public List<K> retain(long generation, Set<K> slots) {
        var removed = pending.entrySet().stream().filter(e -> e.getValue().generation() != generation
                || !slots.contains(e.getKey())).map(Map.Entry::getKey).toList();
        removed.forEach(pending::remove); return removed;
    }
    public void clear() { pending.clear(); }
}
