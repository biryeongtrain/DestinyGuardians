package kim.biryeong.destiny.weapon;

import java.lang.ref.ReferenceQueue;
import java.lang.ref.WeakReference;
import java.util.*;

/** Paid final-blow clock. Stow/tick preserves tokens; only lifecycle clear revokes the epoch. */
public final class SteadyHandsCycle {
    public static final int MAX_CORPSES_PER_EMISSION = 256;
    private Object epoch = new Object();
    private long observed = -1, until = -1;
    private final ReferenceQueue<Object> collected = new ReferenceQueue<>();
    private final Set<Corpse> credited = new HashSet<>();
    // Weak identity keys retain duplicate protection while a target can still be presented,
    // without retaining every dead entity or imposing a source-lifetime kill limit.
    private static final class Corpse extends WeakReference<Object> {
        private final int hash;
        Corpse(Object target, ReferenceQueue<Object> queue) { super(target, queue); hash = System.identityHashCode(target); }
        @Override public int hashCode() { return hash; }
        @Override public boolean equals(Object other) {
            return this == other || other instanceof Corpse c && get() != null && get() == c.get();
        }
    }
    public static final class Emission {
        private final SteadyHandsCycle source;
        private final Object epoch;
        private final long capturedAt;
        private final Set<Object> corpses = Collections.newSetFromMap(new IdentityHashMap<>());
        private Emission(SteadyHandsCycle source, long tick) {
            this.source = source; epoch = source.epoch; capturedAt = tick;
        }
    }
    private boolean timeValid(long tick) { return tick >= 0 && tick >= observed; }
    public Emission capture(long tick) {
        if (!timeValid(tick)) { clear(); return null; }
        update(tick);
        return new Emission(this, tick);
    }
    /** Caller proves paid positive actual damage and eligible enemy final blow. */
    public boolean killed(long tick, Emission emission, Object corpse) {
        if (!timeValid(tick) || emission == null || emission.source != this || emission.epoch != epoch
            || tick < emission.capturedAt || corpse == null) return false;
        update(tick);
        var key = new Corpse(corpse, collected);
        if (emission.corpses.size() >= MAX_CORPSES_PER_EMISSION || emission.corpses.contains(corpse)
            || credited.contains(key)) return false;
        emission.corpses.add(corpse); credited.add(key);
        int duration = remaining(tick) > 0 ? SteadyHandsProfile.refreshTicks() : SteadyHandsProfile.initialTicks();
        until = tick > Long.MAX_VALUE - duration ? Long.MAX_VALUE : tick + duration;
        return true;
    }
    /** Pure projection: even a far-future probe cannot expire writer state or revoke authority. */
    public int remaining(long tick) {
        return timeValid(tick) && tick < until ? (int)Math.min(SteadyHandsProfile.initialTicks(), until - tick) : 0;
    }
    public void update(long tick) {
        if (!timeValid(tick)) { clear(); return; }
        observed = tick;
        for (var ref = collected.poll(); ref != null; ref = collected.poll()) credited.remove(ref);
    }
    public void clear() {
        epoch = new Object(); observed = -1; until = -1; credited.clear();
        while (collected.poll() != null) { /* release queued weak keys */ }
    }
}
