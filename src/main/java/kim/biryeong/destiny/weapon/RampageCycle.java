package kim.biryeong.destiny.weapon;

/** Three refreshable stacks, decaying one at a time. Queries do not advance or pause time. */
public final class RampageCycle {
    private int count;
    private long nextDecay = -1;
    private static void duration(int ticks) {
        if (ticks < 1 || ticks > 1200) throw new IllegalArgumentException("Unsafe Rampage duration");
    }
    public int stacks(long tick, int decayTicks) {
        duration(decayTicks);
        if (count == 0 || tick < 0 || tick < nextDecay - decayTicks) return 0;
        long lost = tick < nextDecay ? 0 : 1 + (tick - nextDecay) / decayTicks;
        return (int)Math.max(0, count - lost);
    }
    public int remaining(long tick, int decayTicks) {
        if (stacks(tick,decayTicks) == 0) return 0;
        return tick < nextDecay ? (int)(nextDecay-tick)
                : decayTicks - (int)((tick-nextDecay)%decayTicks);
    }
    public boolean killed(long tick, int decayTicks) {
        duration(decayTicks);
        if (tick < 0 || tick > Long.MAX_VALUE-decayTicks || nextDecay >= 0 && tick < nextDecay-decayTicks)
            return false;
        count = Math.min(3, stacks(tick,decayTicks)+1);
        nextDecay = tick+decayTicks;
        return true;
    }
}
