package kim.biryeong.destiny.weapon;

/** Observation-owned proximity clock. Reads never acquire an ally or extend linger. */
public final class EnsembleCycle {
    public static final int LINGER_TICKS = 30;
    private long observed = -1;
    private long lostAt = -1;
    private boolean nearby;

    /** Loss starts at the first negative observation, including a loss in the same tick. */
    public void update(long tick, boolean eligible, boolean allyNearby) {
        if (!eligible || tick < 0 || observed >= 0 && tick < observed) {
            clear();
            return;
        }
        observed = tick;
        if (allyNearby) lostAt = -1;
        else if (nearby) lostAt = tick;
        nearby = allyNearby;
    }

    /** While near an ally this reports available linger, rather than a running deadline. */
    public int remaining(long tick) {
        if (observed < 0 || tick < observed) return 0;
        if (nearby) return LINGER_TICKS;
        // Ordered nonnegative subtraction avoids deadline overflow.
        if (lostAt < 0 || tick - lostAt >= LINGER_TICKS) return 0;
        return LINGER_TICKS - (int)(tick - lostAt);
    }

    public boolean active(long tick) { return remaining(tick) > 0; }
    public void clear() { observed = -1; lostAt = -1; nearby = false; }
}
