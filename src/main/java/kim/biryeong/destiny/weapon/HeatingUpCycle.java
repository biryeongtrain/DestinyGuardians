package kim.biryeong.destiny.weapon;

/** Pure, server-thread-owned stack window. Time continues while the source is stowed. */
public final class HeatingUpCycle {
    public static final int DURATION_TICKS = 110;
    public static final int MAX_STACKS = 2;
    private int count;
    private long lastKill = -1, deadline = -1;

    /** Read-only: negative/backward ticks fail closed; the exact deadline is expired. */
    public int stacks(long tick) {
        return tick >= 0 && tick >= lastKill && tick < deadline ? count : 0;
    }

    public int remaining(long tick) { return stacks(tick) == 0 ? 0 : (int) (deadline - tick); }

    /** Caller confirms a distinct, paid weapon final blow before invoking this method.
     * Attribution, duplicate suppression, reload and source identity belong to the master runtime.
     * Every accepted kill refreshes all stacks, including at cap; overflow is rejected unchanged.
     */
    public boolean killed(long tick) {
        if (tick < 0 || tick < lastKill || tick > Long.MAX_VALUE - DURATION_TICKS) return false;
        count = Math.min(MAX_STACKS, stacks(tick) + 1);
        lastKill = tick;
        deadline = tick + DURATION_TICKS;
        return true;
    }
}
