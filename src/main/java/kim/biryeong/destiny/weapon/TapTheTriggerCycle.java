package kim.biryeong.destiny.weapon;

/** Only paid first emissions can start this window. Held automatic fire cannot refresh it.
 * Fusion paid bursts may refresh; their supplementary bolts never call paid(). */
public final class TapTheTriggerCycle {
    private long until = -1;
    private boolean armed = true;
    public void paid(long tick, boolean fusionBurst) {
        if (tick < 0) throw new IllegalArgumentException("Negative shot clock");
        if (armed || fusionBurst) {
            until = tick > Long.MAX_VALUE - 12 ? Long.MAX_VALUE : tick + 12;
            armed = false;
        }
    }
    /** A genuine native release, two-hand lease expiry, or cancelled firing work rearms. */
    public void released() { armed = true; }
    public int remaining(long tick) {
        return until <= tick || tick < 0 ? 0 : (int)Math.min(12, until - tick);
    }
    public void reset() { until = -1; armed = true; }
}
