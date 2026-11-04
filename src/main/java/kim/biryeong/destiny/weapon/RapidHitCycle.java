package kim.biryeong.destiny.weapon;

/** Confirmed buffed hits refresh a bounded two-second window; observers never refresh it.
 * Whole-window refresh/expiry and non-consuming reload are explicit local policies.
 */
public final class RapidHitCycle {
    public static final int DURATION = 40;
    public static final int MAX_STACKS = 5;
    private int count;
    private long lastHit = -1, until = -1;

    public int stacks(long tick) {
        return tick >= 0 && lastHit >= 0 && tick >= lastHit && until > tick
                && until - tick <= DURATION ? count : 0;
    }
    public int remaining(long tick) { return stacks(tick) == 0 ? 0 : (int)(until - tick); }

    /** Misses, rejected damage and ordinary body damage are not buffed-hit confirmations. */
    public boolean confirmed(long tick, boolean buffed, float actualDamage) {
        if (!buffed || !Float.isFinite(actualDamage) || actualDamage <= 0 || tick < 0
                || tick < lastHit || tick > Long.MAX_VALUE - DURATION) return false;
        count = Math.min(MAX_STACKS, stacks(tick) + 1);
        lastHit = tick;
        until = tick + DURATION;
        return true;
    }
    public void clear() { count = 0; lastHit = -1; until = -1; }
}
