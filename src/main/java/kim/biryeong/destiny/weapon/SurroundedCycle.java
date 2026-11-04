package kim.biryeong.destiny.weapon;

/** Held-only proximity state. Only observations change state; HUD queries never refresh it. */
public final class SurroundedCycle {
    public static final double RADIUS = 15;
    public static final int MINIMUM_ENEMIES = 3;
    public static final int LINGER_TICKS = 30;
    private long observed = -1;
    private long lostAt = -1;
    private boolean threshold;

    /** Local foot-point Euclidean sphere, including the boundary. No LOS test. */
    public static boolean withinRadius(double dx, double dy, double dz) {
        return Double.isFinite(dx) && Double.isFinite(dy) && Double.isFinite(dz)
                && dx * dx + dy * dy + dz * dz <= RADIUS * RADIUS;
    }

    public void update(long tick, int enemies) { update(tick, true, enemies); }

    /** A lost threshold starts a full linger at this observation, not at the last good tick. */
    public void update(long tick, boolean held, int enemies) {
        if (!held || enemies < 0 || tick < 0 || observed >= 0 && tick < observed) {
            clear();
            return;
        }
        observed = tick;
        boolean met = enemies >= MINIMUM_ENEMIES;
        if (met) lostAt = -1;
        else if (threshold) lostAt = tick;
        threshold = met;
    }

    public boolean active(long tick) { return remaining(tick) > 0; }

    /** Paid emission value; stowing/expiry of the live cycle cannot rewrite this immutable value.
     * Source ownership and edit-epoch revocation belong to the wrapper, not this proximity clock.
     */
    record Snapshot(float multiplier) {}
    Snapshot capture(long tick, float activeMultiplier) {
        if (activeMultiplier != 1.4f && activeMultiplier != 1.35f)
            throw new IllegalArgumentException("Unsupported Surrounded multiplier");
        return new Snapshot(active(tick) ? activeMultiplier : 1);
    }

    /** While the threshold holds, 30 denotes available linger, not a running deadline. */
    public int remaining(long tick) {
        if (observed < 0 || tick < observed) return 0;
        if (threshold) return LINGER_TICKS;
        // Subtraction of ordered nonnegative ticks cannot overflow. Never add a deadline.
        if (lostAt < 0 || tick - lostAt >= LINGER_TICKS) return 0;
        return LINGER_TICKS - (int) (tick - lostAt);
    }

    public void clear() { observed = -1; lostAt = -1; threshold = false; }
}
