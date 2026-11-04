package kim.biryeong.destiny.weapon;

/** Precision counter and refreshed damage window. Server ticks, not persisted item data. */
public final class FocusedFuryCycle {
    private final int threshold;
    private int hits;
    private long deadline = -1, observed = -1;
    public FocusedFuryCycle(int threshold) {
        if (threshold < 1 || threshold > 1000) throw new IllegalArgumentException("precision threshold");
        this.threshold = threshold;
    }
    public int threshold() { return threshold; }
    public int progress(long tick) { return validTime(tick) ? hits : 0; }
    private boolean validTime(long tick) { return tick >= 0 && tick >= observed; }
    public int remaining(long tick) {
        return validTime(tick) && tick < deadline ? (int) (deadline - tick) : 0;
    }
    public void update(long tick) { if (validTime(tick)) observed = tick; }
    /** Counter resets do not erase an already earned window. */
    public void resetCounter(long tick) { if (validTime(tick)) { update(tick); hits = 0; } }
    /** One confirmed positive-damage precision emission, never one count per pellet/target. */
    public boolean precision(long tick) {
        if (!validTime(tick) || tick > Long.MAX_VALUE - 220) return false;
        update(tick);
        if (++hits < threshold) return false;
        hits = 0;
        deadline = tick + 220;
        return true;
    }
}
