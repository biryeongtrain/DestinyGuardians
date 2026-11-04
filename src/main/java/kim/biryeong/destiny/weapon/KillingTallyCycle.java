package kim.biryeong.destiny.weapon;

import java.util.Collections;
import java.util.IdentityHashMap;
import java.util.Set;

/** Original paid source epoch; no timer, ammunition, Minecraft objects or query mutation. */
public final class KillingTallyCycle {
    public static final int MAX_STACKS = 3;
    public static final int MAX_CORPSES_PER_EMISSION = 256;
    private Object epoch = new Object(), liveEpoch = new Object();
    private long observed = -1;
    private int count;

    public static final class Emission {
        private final KillingTallyCycle source;
        private final Object epoch, liveEpoch;
        private final long capturedAt;
        private final int stacks;
        private final Set<Object> corpses = Collections.newSetFromMap(new IdentityHashMap<>());
        private Emission(KillingTallyCycle source, long tick) {
            this.source = source; epoch = source.epoch; liveEpoch = source.liveEpoch;
            capturedAt = tick; stacks = source.count;
        }
    }
    private boolean timeValid(long tick) { return tick >= 0 && tick >= observed; }
    private boolean valid(long tick, Emission e) {
        return timeValid(tick) && e != null && e.source == this && e.epoch == epoch && tick >= e.capturedAt;
    }
    /** Trusted paid emission, before its own direct/splash damage and final blows. */
    public Emission capture(long tick) {
        if (!timeValid(tick)) return null;
        observed = tick;
        return new Emission(this, tick);
    }
    public int stacks(long tick) { return timeValid(tick) ? count : 0; }
    /** Frozen stack count survives ordinary live reset; source lifecycle revokes it. */
    public int capturedStacks(long tick, Emission e) { return valid(tick, e) ? e.stacks : 0; }
    /** Actual paid final blow only. One token for every direct/splash contact; bounded identity
     * ledger never evicts. Delayed pre-reset emissions cannot re-bank stacks after stow/reload. */
    public boolean killed(long tick, Emission e, Object corpse, boolean held) {
        if (!valid(tick, e) || corpse == null || e.corpses.size() >= MAX_CORPSES_PER_EMISSION
                || !e.corpses.add(corpse)) return false;
        observed = tick;
        if (held && e.liveEpoch == liveEpoch) count = Math.min(MAX_STACKS, count + 1);
        return true;
    }
    /** Accepted manual reload or explicit positive Marksman refill policy, not any ammo change. */
    public void reloadStarted(long tick) { resetLive(tick); }
    public void stowing(long tick) { resetLive(tick); }
    private void resetLive(long tick) {
        if (!timeValid(tick)) { clear(); return; }
        observed = tick; count = 0; liveEpoch = new Object();
    }
    public void update(long tick, boolean held) {
        if (!timeValid(tick)) { clear(); return; }
        if (!held) resetLive(tick); else observed = tick;
    }
    /** Source loss/edit/lifecycle: permanently revoke even already paid emissions. */
    public void clear() {
        epoch = new Object(); liveEpoch = new Object(); observed = -1; count = 0;
    }
}

