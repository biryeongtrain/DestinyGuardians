package kim.biryeong.destiny.weapon;

/** Native-health episode ledger. No ammunition or player references; readers never advance it. */
public final class PulseMonitorCycle {
    public static final int LINGER_TICKS = 20;
    private long observed = -1, recoveredAt = -1;
    private boolean low;

    public static boolean lowHealth(float health, float maximum) {
        return Float.isFinite(health) && Float.isFinite(maximum) && health > 0 && maximum > 0
            && (double)health / maximum <= .30;
    }
    /** True exactly once on entering a low episode, including the first valid observation.
     * A full/empty-reserve magazine still consumes this episode's decision. */
    public boolean update(long tick, float health, float maximum) {
        if (tick < 0 || tick < observed || !Float.isFinite(health) || !Float.isFinite(maximum)
                || health <= 0 || maximum <= 0) { clear(); return false; }
        boolean next = lowHealth(health, maximum);
        boolean entered = next && !low;
        if (low && !next) recoveredAt = tick;
        if (next) recoveredAt = -1;
        observed = tick; low = next;
        return entered;
    }
    /** Caller supplies actual post-mitigation native HP loss, never attempted damage/absorption. */
    public boolean damaged(long tick, float actualLoss, float health, float maximum) {
        if (!Float.isFinite(actualLoss) || actualLoss <= 0) return false;
        return update(tick, health, maximum);
    }
    public boolean active(long tick) {
        return observed >= 0 && tick >= observed && (low
            || recoveredAt >= 0 && tick >= recoveredAt && tick - recoveredAt < LINGER_TICKS);
    }
    public void clear() { observed = recoveredAt = -1; low = false; }
}
