package kim.biryeong.destiny.weapon;

/** ADS-input clock, independent of scope interpolation; no numeric-only regression fixtures. */
public final class BoxBreathingCycle {
    public static final int PROC_TICKS = 30;
    private Object epoch = new Object();
    private long observed = -1, started = -1;
    public static final class Emission {
        private final BoxBreathingCycle source;
        private final Object epoch;
        private final long tick;
        private final boolean bonus;
        private Emission(BoxBreathingCycle c, long tick, boolean bonus) {
            source = c; epoch = c.epoch; this.tick = tick; this.bonus = bonus;
        }
    }
    private boolean timeValid(long tick) { return tick >= 0 && tick >= observed; }
    public void update(long tick, boolean actualAds, boolean hasAmmo) {
        if (!timeValid(tick)) { clear(); return; }
        observed = tick;
        if (!actualAds || !hasAmmo) started = -1;
        else if (started < 0) started = tick;
    }
    public boolean ready(long tick) {
        return timeValid(tick) && started >= 0 && tick - started >= PROC_TICKS;
    }
    /** AFTER payment, using the pre-payment count. Never poll the now-empty magazine here.
     * Master captures only a newly paid shot; supplementary emissions reuse NONE. */
    public Emission capture(long tick, int roundsBefore, boolean actualAds) {
        if (!timeValid(tick) || roundsBefore <= 0) return null;
        boolean bonus = actualAds && ready(tick);
        observed = tick;
        started = actualAds && roundsBefore > 1 ? tick : -1;
        return new Emission(this, tick, bonus);
    }
    /** Immutable paid snapshot survives natural live clock resets, including magazine empty. */
    public boolean boosted(long tick, Emission e) {
        return timeValid(tick) && e != null && e.source == this && e.epoch == epoch
            && tick >= e.tick && e.bonus;
    }
    /** Explicit release/stow/reload and source edits revoke the previous epoch. */
    public void released(long tick) {
        if (!timeValid(tick)) { clear(); return; }
        observed = tick; started = -1; epoch = new Object();
    }
    public void clear() { epoch = new Object(); observed = started = -1; }
}
