package kim.biryeong.destiny.weapon;

/** Main-thread event-time window. Queries are pure; capture freezes pre-trace state.
 * These six sources are direct hitscan: confirmation/damage must belong to the capture tick. */
public final class HeadseekerCycle {
    private long observed = -1, deadline = -1, epoch;
    public static final class Emission {
        private final HeadseekerCycle source;
        private final long tick, epoch;
        private final boolean active;
        private boolean credited;
        private Emission(HeadseekerCycle source, long tick, boolean active) {
            this.source = source; this.tick = tick; this.epoch = source.epoch; this.active = active;
        }
    }
    private boolean time(long tick) { return tick >= 0 && tick >= observed; }
    public int remaining(long tick) {
        return time(tick) && tick < deadline ? (int)(deadline - tick) : 0;
    }
    /** Writer observation retires a rolled-back timeline; read-only queries cannot heal it. */
    public void update(long tick) {
        if (!time(tick)) clear();
        observed = tick;
    }
    public Emission capture(long tick) {
        if (!time(tick)) { update(tick); return null; }
        update(tick);
        return new Emission(this, tick, remaining(tick) > 0);
    }
    private boolean valid(long tick, Emission emission) {
        return time(tick) && emission != null && emission.source == this
                && emission.epoch == epoch && emission.tick == tick;
    }
    /** Once per paid emission; precision/invalid loss never activates, refreshes or consumes credit. */
    public boolean confirmed(long tick, Emission emission, boolean precision, float actual) {
        if (!valid(tick, emission) || precision || emission.credited || !Float.isFinite(actual)
                || actual <= 0 || tick > Long.MAX_VALUE - HeadseekerProfile.DURATION_TICKS) return false;
        emission.credited = true;
        observed = tick; deadline = tick + HeadseekerProfile.DURATION_TICKS;
        return true;
    }
    public boolean boosted(long tick, Emission emission) {
        return valid(tick, emission) && emission.active;
    }
    /** Increase only (total - body), preserving the source's actual base critical multiplier. */
    static float precisionDamage(float totalPrecision, double baseCritMultiplier, boolean active) {
        if (!active || !Float.isFinite(totalPrecision) || totalPrecision <= 0
                || !Double.isFinite(baseCritMultiplier) || baseCritMultiplier < 1) return totalPrecision;
        double result = totalPrecision + (totalPrecision - totalPrecision / baseCritMultiplier) * .2;
        return result <= Float.MAX_VALUE ? (float)result : totalPrecision;
    }
    public void clear() { epoch++; observed = -1; deadline = -1; }
}
