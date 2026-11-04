package kim.biryeong.destiny.weapon;

/** Bounded rapid-final-blow window. Reads never grant stacks or refresh their deadline. */
public final class FeedingFrenzyCycle {
    public static final int MAX_STACKS = 5;
    private int count;
    private long lastKill = -1;
    private long until = -1;

    private static void duration(int ticks) {
        if (ticks < 1 || ticks > 1200) throw new IllegalArgumentException("Unsafe Feeding Frenzy duration");
    }

    public int stacks(long tick, int durationTicks) {
        duration(durationTicks);
        return tick >= 0 && lastKill >= 0 && tick >= lastKill && until > tick
                && until - tick <= durationTicks ? count : 0;
    }

    public int remaining(long tick, int durationTicks) {
        return stacks(tick, durationTicks) > 0 ? (int)(until - tick) : 0;
    }

    /** Confirmed source-weapon final blows only; at expiry a new chain starts at one. */
    public boolean killed(long tick, int durationTicks) {
        duration(durationTicks);
        if (tick < 0 || tick < lastKill || tick > Long.MAX_VALUE - durationTicks) return false;
        count = Math.min(MAX_STACKS, stacks(tick, durationTicks) + 1);
        lastKill = tick;
        until = tick + durationTicks;
        return true;
    }

    public void clear() { count = 0; lastKill = -1; until = -1; }
}
