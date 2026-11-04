package kim.biryeong.destiny.weapon;

/** Accepted paid emissions only; queries neither create sessions nor advance time. */
public final class OpeningShotCycle {
    public static final int COOLDOWN_TICKS = 60;
    private Object epoch = new Object();
    private long observed = -1, lastShot = -1;
    public static final class Emission {
        private final OpeningShotCycle source;
        private final Object epoch;
        private final long tick;
        private final boolean bonus;
        private Emission(OpeningShotCycle c, long tick, boolean bonus) {
            source = c; epoch = c.epoch; this.tick = tick; this.bonus = bonus;
        }
    }
    private boolean timeValid(long tick) { return tick >= 0 && tick >= observed; }
    /** Every paid emission, including supplementary burst shots, restarts the quiet period. */
    public Emission capture(long tick, boolean firstOfBurst) {
        if (!timeValid(tick)) return null;
        boolean bonus = firstOfBurst && (lastShot < 0 || tick - lastShot >= COOLDOWN_TICKS);
        observed = lastShot = tick;
        return new Emission(this, tick, bonus);
    }
    public boolean boosted(long tick, Emission e) {
        return timeValid(tick) && e != null && e.source == this && e.epoch == epoch
            && tick >= e.tick && e.bonus;
    }
    public void update(long tick) {
        if (!timeValid(tick)) { clear(); return; }
        observed = tick;
    }
    /** Stow revokes old emissions but must not bypass the source's last-shot cooldown. */
    public void stowing(long tick) {
        if (!timeValid(tick)) { clear(); return; }
        observed = tick; epoch = new Object();
    }
    public void clear() { epoch = new Object(); observed = lastShot = -1; }
}
