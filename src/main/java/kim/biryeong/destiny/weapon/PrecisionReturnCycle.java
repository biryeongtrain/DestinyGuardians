package kim.biryeong.destiny.weapon;

/** Consecutive timed precision events, not a total-volley window. Queries never refresh time. */
public final class PrecisionReturnCycle {
    private final int required, window;
    private int count;
    private long lastHit = -1;
    public PrecisionReturnCycle(int required, int windowTicks) {
        if (required < 2 || required > 16 || windowTicks < 1 || windowTicks > 1200)
            throw new IllegalArgumentException("Unsafe precision-return cycle");
        this.required = required; this.window = windowTicks;
    }
    public int progress(long tick) {
        return lastHit < 0 || tick < lastHit || tick - lastHit >= window ? 0 : count;
    }
    /** True consumes exactly one completed group, even if a full magazine cannot accept a return. */
    public boolean hit(long tick) {
        if (tick < 0 || tick < lastHit) return false;
        count = progress(tick) + 1;
        lastHit = tick;
        if (count < required) return false;
        count = 0;
        return true;
    }
}
