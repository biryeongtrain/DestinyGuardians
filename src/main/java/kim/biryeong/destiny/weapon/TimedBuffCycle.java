package kim.biryeong.destiny.weapon;

/** Pure server-tick buff window shared by W320 timed traits. No wall clock, no player state. */
public final class TimedBuffCycle {
    private long until = Long.MIN_VALUE;
    public boolean active(long now) { return now < until; }
    public long remaining(long now) { return active(now) ? until - now : 0; }
    /** Starts or refreshes to exactly duration ticks from now. */
    public void activate(long now, int duration) { until = now + Math.max(0, duration); }
    /** Starts at initial ticks, or extends a running window by add ticks, never above cap remaining. */
    public void extend(long now, int initial, int add, int cap) {
        long next = active(now) ? until + add : now + initial;
        until = Math.min(next, now + cap);
    }
    public void clear() { until = Long.MIN_VALUE; }
}
