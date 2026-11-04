package kim.biryeong.destiny.weapon;

/** Refreshable precision-final-blow window. Queries never grant time or accelerate a reload. */
public final class OutlawCycle {
    private long until = Long.MIN_VALUE;
    public void precisionKilled(long tick, int duration) {
        if (duration < 1 || duration > 1200) throw new IllegalArgumentException("Unsafe Outlaw duration");
        if (tick < 0 || tick > Long.MAX_VALUE - duration) { until = Long.MIN_VALUE; return; }
        until = tick + duration;
    }
    public int remaining(long tick, int duration) {
        return tick >= 0 && duration > 0 && duration <= 1200 && until > tick && until - tick <= duration
                ? (int)(until - tick) : 0;
    }
}
