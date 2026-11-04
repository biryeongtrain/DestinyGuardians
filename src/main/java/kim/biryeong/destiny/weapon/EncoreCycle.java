package kim.biryeong.destiny.weapon;

import java.util.Collections;
import java.util.IdentityHashMap;
import java.util.Set;

/** One original weapon/source epoch. Tick queries are pure; time continues through stow.
 * Attribution and positive actual final-blow confirmation belong to the paid damage caller.
 */
public final class EncoreCycle {
    public static final int DURATION_TICKS = 140;
    public static final int MAX_STACKS = 4;
    /** Local fail-closed memory bound per paid emission; never evict and readmit old corpses. */
    public static final int MAX_CORPSES_PER_EMISSION = 256;
    private Object epoch = new Object();
    private long observed = -1, lastKill = -1, deadline = -1;
    private int count;

    public static final class Emission {
        private final EncoreCycle source;
        private final Object epoch;
        private final Set<Object> corpses = Collections.newSetFromMap(new IdentityHashMap<>());
        private Emission(EncoreCycle source) { this.source = source; epoch = source.epoch; }
    }

    private boolean timeValid(long tick) {
        return tick >= 0 && tick >= observed && tick <= Long.MAX_VALUE - DURATION_TICKS;
    }
    /** Paid emission only. Capture never grants stacks or refreshes the window. */
    public Emission capture(long tick) {
        if (!timeValid(tick)) return null;
        observed = tick;
        return new Emission(this);
    }
    /** Same emission must be carried through direct/pellet/splash callbacks. Corpse identity,
     * rather than mutable equality or a lifetime ledger, suppresses repeated kill callbacks.
     */
    public boolean killed(long tick, Emission emission, Object corpse, boolean precision) {
        if (!timeValid(tick) || corpse == null || emission == null || emission.source != this
            || emission.epoch != epoch || emission.corpses.size() >= MAX_CORPSES_PER_EMISSION
            || !emission.corpses.add(corpse)) return false;
        count = Math.min(MAX_STACKS, stacks(tick) + (precision ? 2 : 1));
        observed = lastKill = tick;
        deadline = tick + DURATION_TICKS;
        return true;
    }
    public int stacks(long tick) {
        return tick >= 0 && tick >= observed && tick >= lastKill && tick < deadline ? count : 0;
    }
    public int remaining(long tick) { return stacks(tick) == 0 ? 0 : (int)(deadline - tick); }
    /** Lifecycle writer. Clock rollback revokes all earlier paid tokens permanently. */
    public void update(long tick) {
        if (!timeValid(tick)) { clear(); return; }
        observed = tick;
        if (tick >= deadline) { count = 0; deadline = -1; }
    }
    public void clear() {
        epoch = new Object();
        observed = lastKill = deadline = -1;
        count = 0;
    }
}
