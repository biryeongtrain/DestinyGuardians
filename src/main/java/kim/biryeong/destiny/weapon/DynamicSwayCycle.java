package kim.biryeong.destiny.weapon;

/** Paid-shot chain, explicit release, and opaque immutable shot snapshots. No invented timer. */
public final class DynamicSwayCycle {
    private Object epoch = new Object();
    private long observed = -1;
    private int count;
    public static final class Emission {
        private final DynamicSwayCycle source;
        private final Object epoch;
        private final long paidAt;
        private final int stacks;
        private Emission(DynamicSwayCycle source, long tick) {
            this.source = source; epoch = source.epoch; paidAt = tick; stacks = source.count;
        }
    }
    private boolean timeValid(long tick) { return tick >= 0 && tick >= observed; }
    /** Accepted actual payment only. Polling/duplicate input never reaches this writer. */
    public Emission paid(long tick) {
        if (!timeValid(tick)) { clear(); return null; }
        observed = tick;
        count = Math.min(DynamicSwayProfile.maxStacks(), count + 1);
        return new Emission(this, tick);
    }
    public int stacks(long tick) { return timeValid(tick) ? count : 0; }
    public int capturedStacks(long tick, Emission emission) {
        return timeValid(tick) && emission != null && emission.source == this
            && emission.epoch == epoch && tick >= emission.paidAt ? emission.stacks : 0;
    }
    /** Actual release/reload/cancel/lease expiry resets immediately, even within the paid tick. */
    public void released(long tick) {
        clear();
        if (tick >= 0) observed = tick;
    }
    /** Held gaps have no invented expiry. Unheld observation is a release fallback. */
    public void update(long tick, boolean held) {
        if (!timeValid(tick)) { clear(); return; }
        if (!held) released(tick); else observed = tick;
    }
    public void clear() { epoch = new Object(); observed = -1; count = 0; }
}
