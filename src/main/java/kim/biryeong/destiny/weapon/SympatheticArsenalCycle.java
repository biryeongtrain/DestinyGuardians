package kim.biryeong.destiny.weapon;

import java.util.Collections;
import java.util.IdentityHashMap;
import java.util.Set;

/** Paid final-blow ledger and accepted real reload authority. Never mutates ammunition. */
public final class SympatheticArsenalCycle {
    public static final int WINDOW_TICKS = 72;
    public static final int MAX_CORPSES_PER_EMISSION = 256;
    private Object epoch = new Object(), heldEpoch = new Object();
    private long observed = -1, lastKill = -1;
    private Reload activeReload;

    public static final class PaidToken {
        private final SympatheticArsenalCycle source;
        private final Object epoch, heldEpoch;
        private final long capturedAt;
        private final Set<Object> corpses = Collections.newSetFromMap(new IdentityHashMap<>());
        private PaidToken(SympatheticArsenalCycle source, long tick) {
            this.source = source; epoch = source.epoch; heldEpoch = source.heldEpoch; capturedAt = tick;
        }
    }
    public static final class Reload {
        private final SympatheticArsenalCycle source;
        private final Object epoch, heldEpoch;
        private final long acceptedAt;
        private Reload(SympatheticArsenalCycle source, long tick) {
            this.source = source; epoch = source.epoch; heldEpoch = source.heldEpoch; acceptedAt = tick;
        }
    }
    private boolean timeValid(long tick) { return tick >= 0 && tick >= observed; }
    public PaidToken capture(long tick) {
        if (!timeValid(tick)) return null;
        observed = tick; return new PaidToken(this, tick);
    }
    /** Caller verifies actual loss and attributable enemy final blow. Stowed/pre-stow kills
     * spend dedup credit but cannot bank eligibility for a later equip. */
    public boolean killed(long tick, PaidToken paid, Object corpse, boolean held) {
        if (!timeValid(tick) || paid == null || paid.source != this || paid.epoch != epoch
                || tick < paid.capturedAt || corpse == null
                || paid.corpses.size() >= MAX_CORPSES_PER_EMISSION || !paid.corpses.add(corpse)) return false;
        observed = tick;
        if (held && paid.heldEpoch == heldEpoch) lastKill = tick;
        return true;
    }
    /** Authority only AFTER WeaponCycle accepted a real reload. Never tests kill eligibility:
     * a kill may occur during this reload; only the positive ammo-credit boundary decides. */
    public Reload acceptedReload(long tick) {
        if (!timeValid(tick)) return null;
        observed = tick; activeReload = new Reload(this, tick); return activeReload;
    }
    /** One decision at the first genuine positive ammo credit, inclusive kill+72 boundary.
     * Zero/no-reserve credit does not trigger or consume. Positive ineligible credit retires
     * the reload authority too, preventing a later kill/replayed callback from activating it. */
    public boolean reloaded(long tick, Reload reload, int creditedRounds) {
        if (!timeValid(tick) || creditedRounds <= 0 || reload == null || reload != activeReload
                || reload.source != this || reload.epoch != epoch || reload.heldEpoch != heldEpoch
                || tick < reload.acceptedAt) return false;
        observed = tick; activeReload = null;
        if (!eligible(tick)) return false;
        lastKill = -1;
        return true;
    }
    public boolean eligible(long tick) {
        return timeValid(tick) && lastKill >= 0 && tick >= lastKill && tick - lastKill <= WINDOW_TICKS;
    }
    /** Window only, not a damage buff. Inclusive final tick still has one decision tick left. */
    public int remaining(long tick) { return eligible(tick) ? WINDOW_TICKS - (int)(tick - lastKill) + 1 : 0; }
    public void reloadCancelled() { activeReload = null; }
    public void stowing(long tick) {
        if (!timeValid(tick)) { clear(); return; }
        observed = tick; lastKill = -1; activeReload = null; heldEpoch = new Object();
    }
    public void update(long tick, boolean held) {
        if (!timeValid(tick)) { clear(); return; }
        if (!held) { stowing(tick); return; }
        observed = tick;
        if (!eligible(tick)) lastKill = -1;
    }
    public void clear() {
        epoch = new Object(); heldEpoch = new Object(); observed = lastKill = -1; activeReload = null;
    }
}

