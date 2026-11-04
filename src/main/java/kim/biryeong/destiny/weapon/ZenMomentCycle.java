package kim.biryeong.destiny.weapon;

/** Pure refresh-all hit window in HALF-stack units. Cap/aggregation are authored policy;
 * elapsed tick queries never refresh it. Time rollback is inert and a new confirmed hit resets it. */
public final class ZenMomentCycle {
    private int units;
    private long lastHit = -1, until = -1;
    public boolean confirmed(long tick, int increment, float actualPositiveDamage) {
        if (tick < 0 || tick > Long.MAX_VALUE - ZenMomentProfile.DURATION_TICKS
                || increment < 2 || increment > 4 || !Float.isFinite(actualPositiveDamage)
                || actualPositiveDamage <= 0) return false;
        units = Math.min(ZenMomentProfile.MAX_STACK_UNITS, stackUnits(tick) + increment);
        lastHit = tick; until = tick + ZenMomentProfile.DURATION_TICKS;
        return true;
    }
    public int stackUnits(long tick) { return remaining(tick) > 0 ? units : 0; }
    public int remaining(long tick) {
        return tick >= 0 && tick >= lastHit && until > tick
                && until - tick <= ZenMomentProfile.DURATION_TICKS ? (int)(until - tick) : 0;
    }
    public float flinchScalar(long tick) { return ZenMomentProfile.flinchScalar(stackUnits(tick)); }
}
