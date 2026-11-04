package kim.biryeong.destiny.weapon;

import java.util.HashSet;
import java.util.Set;
import java.util.UUID;

/** LOCAL: each new distinct target renews the collection window; duplicates never renew it.
 * The active buff cannot collect targets or refresh. Queries are read-only.
 */
public final class OneForAllCycle {
    private final int hitWindowTicks;
    private final int durationTicks;
    private final Set<UUID> targets = new HashSet<>();
    private long collectionDeadline = -1;
    private long activeDeadline = -1;
    private long lastEvent = -1;

    public OneForAllCycle() { this(60, 200); }

    public OneForAllCycle(int hitWindowTicks, int durationTicks) {
        if (hitWindowTicks < 1 || hitWindowTicks > 1200 || durationTicks < 1 || durationTicks > 1200)
            throw new IllegalArgumentException("Unsafe One for All timing");
        this.hitWindowTicks = hitWindowTicks;
        this.durationTicks = durationTicks;
    }

    /** Returns true only for a new qualifying target. The activating hit uses its earlier snapshot. */
    public boolean confirmed(long tick, UUID target) {
        if (target == null || tick < 0 || tick < lastEvent
                || tick > Long.MAX_VALUE - Math.max(hitWindowTicks, durationTicks)) return false;
        lastEvent = tick;
        if (remaining(tick) > 0) return false;
        if (tick >= collectionDeadline) targets.clear();
        if (!targets.add(target)) return false;
        if (targets.size() == 3) {
            targets.clear();
            collectionDeadline = -1;
            activeDeadline = tick + durationTicks;
        } else {
            collectionDeadline = tick + hitWindowTicks;
        }
        return true;
    }

    /** Collection count only: 0..2, and always zero during the active buff. */
    public int progress(long tick) {
        return tick < 0 || tick < lastEvent || remaining(tick) > 0 || tick >= collectionDeadline
                ? 0 : targets.size();
    }

    /** Active time only; exact deadline is expired. Invalid/backward time fails closed. */
    public int remaining(long tick) {
        return tick < 0 || tick < lastEvent || tick >= activeDeadline ? 0 : (int) (activeDeadline - tick);
    }

    public float multiplier(long tick) { return remaining(tick) > 0 ? 1.35f : 1f; }
}
