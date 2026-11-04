package kim.biryeong.destiny.weapon;

import java.util.Collections;
import java.util.IdentityHashMap;
import java.util.Set;

/** One original paid source epoch. Queries never advance time or change the buff. */
public final class AdagioCycle {
    public static final int DURATION_TICKS = 140;
    public static final float DAMAGE_MULTIPLIER = 1.3f;
    /** Local fail-closed bound; no eviction that could readmit an old corpse. */
    public static final int MAX_CORPSES_PER_EMISSION = 256;
    private Object epoch = new Object();
    private long observed = -1, deadline = -1;

    public static final class Emission {
        private final AdagioCycle source;
        private final Object epoch;
        private final long capturedAt;
        private final float multiplier;
        private final Set<Object> corpses = Collections.newSetFromMap(new IdentityHashMap<>());
        private Emission(AdagioCycle source, long tick) {
            this.source = source;
            epoch = source.epoch;
            capturedAt = tick;
            multiplier = source.remaining(tick) > 0 ? DAMAGE_MULTIPLIER : 1f;
        }
    }

    private boolean timeValid(long tick) {
        return tick >= 0 && tick >= observed && tick <= Long.MAX_VALUE - DURATION_TICKS;
    }
    private boolean tokenValid(long tick, Emission emission) {
        return tick >= 0 && tick >= observed && emission != null && emission.source == this
            && emission.epoch == epoch && tick >= emission.capturedAt;
    }
    /** AFTER payment, BEFORE damage/final-blow callbacks. Never grants or refreshes the buff. */
    public Emission capture(long tick) {
        if (!timeValid(tick)) return null;
        var emission = new Emission(this, tick);
        observed = tick;
        return emission;
    }
    /** Immutable paid scalar survives expiry and stow, but not invalidation of its source epoch. */
    public float multiplier(long tick, Emission emission) {
        return tokenValid(tick, emission) ? emission.multiplier : 1f;
    }
    /** Direct and splash MUST share one emission. A stowed final blow consumes its corpse
     * callback without banking a buff to carry into a later re-equip.
     */
    public boolean killed(long tick, Emission emission, Object corpse, boolean held) {
        if (!timeValid(tick) || !tokenValid(tick, emission) || corpse == null
            || emission.corpses.size() >= MAX_CORPSES_PER_EMISSION
            || !emission.corpses.add(corpse)) return false;
        observed = tick;
        deadline = held ? tick + DURATION_TICKS : -1;
        return true;
    }
    public int remaining(long tick) {
        return tick >= 0 && tick >= observed && tick < deadline ? (int)(deadline - tick) : 0;
    }
    /** Lifecycle writer. Natural expiry/stow preserves emissions; rollback revokes them. */
    public void update(long tick, boolean held) {
        if (!timeValid(tick)) { clear(); return; }
        observed = tick;
        if (!held || tick >= deadline) deadline = -1;
    }
    public void stowing(long tick) { update(tick, false); }
    public void clear() {
        epoch = new Object();
        observed = deadline = -1;
    }
}
