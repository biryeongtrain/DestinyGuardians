package kim.biryeong.destiny.weapon;

/** One transient stow window. No wall-clock/offline progress or speculative ammunition. */
public final class WeaponHolsterCycle {
    private long deadline;
    private long lastTick;
    private boolean stowed;
    private boolean attempted;

    /** Returns one attempt per uninterrupted stow; drawing cancels, even in the same tick. */
    public boolean observe(long tick, boolean held, int delay) {
        if (delay < 1 || delay > 1200) throw new IllegalArgumentException("Unsafe holster delay");
        if (held) {
            stowed = false;
            attempted = false;
            lastTick = tick;
            return false;
        }
        if (!stowed || tick < lastTick) {
            stowed = true;
            attempted = false;
            deadline = tick > Long.MAX_VALUE - delay ? Long.MAX_VALUE : tick + delay;
        }
        lastTick = tick;
        if (attempted || tick < deadline) return false;
        attempted = true; // Commit before the inventory mutation/callback.
        return true;
    }
}
