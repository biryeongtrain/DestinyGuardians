package kim.biryeong.destiny.weapon;

import java.util.HashSet;
import java.util.Set;
import java.util.UUID;

/** Pure tick state for one original stack/edit epoch. Queries never advance time.
 * A contact is consumed once per accepted melee and target. Stow cancels melee epochs
 * and handling. Paid projectile corpse ledgers belong to individual runtime tokens.
 * Exact deadlines are expired.
 */
public final class PugilistCycle {
    public static final int DURATION_TICKS = 60;
    private Object heldEpoch = new Object();
    private long observed = -1;
    private long deadline = -1;

    public static final class Melee {
        private final PugilistCycle source;
        private final Object epoch;
        private final Set<UUID> contacts = new HashSet<>();
        private Melee(PugilistCycle source) { this.source = source; epoch = source.heldEpoch; }
    }
    private boolean event(long tick) {
        if (tick < 0 || tick < observed || tick > Long.MAX_VALUE - DURATION_TICKS) return false;
        observed = tick;
        return true;
    }
    public Melee meleeAccepted(long tick) { return event(tick) ? new Melee(this) : null; }
    /** Only call after positive actual melee HP/absorption loss, not accepted input alone. */
    public boolean meleeConfirmed(long tick, Melee melee, UUID target) {
        if (target == null || melee == null || melee.source != this || melee.epoch != heldEpoch
            || !event(tick) || !melee.contacts.add(target)) return false;
        deadline = tick + DURATION_TICKS;
        return true;
    }
    public int remaining(long tick) {
        return tick < 0 || tick < observed || tick >= deadline ? 0 : (int)(deadline - tick);
    }
    public void update(long tick) {
        if (!event(tick)) stow();
        else if (tick >= deadline) deadline = -1;
    }
    public void stow() { deadline = -1; heldEpoch = new Object(); }
    public void clear() { stow(); observed = -1; }
}
