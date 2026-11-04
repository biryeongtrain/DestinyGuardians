package kim.biryeong.destiny.weapon;

/** Refreshed all-or-nothing stack window, independent of Minecraft. Server thread owned. */
public final class AdrenalineJunkieCycle {
    public static final int MAX_STACKS = 5;
    public static final int DURATION_TICKS = 90;
    private static final float[] MULTIPLIERS = {1f, 1.067f, 1.133f, 1.2f, 1.266f, 1.333f};
    private int count;
    private long deadline = -1;
    private long observed = -1;

    /** Immutable emission value; later kills, expiry and stow cannot change it. */
    public record Snapshot(float multiplier) {}

    /** Read-only queries fail closed for negative/backward time and at the exact deadline. */
    public int stacks(long tick) {
        return tick >= 0 && tick >= observed && tick < deadline ? count : 0;
    }
    public int remaining(long tick) { return stacks(tick) == 0 ? 0 : (int) (deadline - tick); }
    public float multiplier(long tick) { return MULTIPLIERS[stacks(tick)]; }
    public Snapshot capture(long tick) { return new Snapshot(multiplier(tick)); }

    /** Observe monotonic server time without extending a window. All stacks expire together. */
    public void update(long tick) {
        if (tick < 0 || tick < observed) return;
        observed = tick;
        if (tick >= deadline) { count = 0; deadline = -1; }
    }

    /** Caller has verified actual positive damage and this source's actual weapon final blow. */
    public boolean killed(long tick) { return grant(tick, false); }
    /** Accepted grenade's actual final blow grants all five, including refresh while capped. */
    public boolean grenadeKilled(long tick) { return grant(tick, true); }
    private boolean grant(long tick, boolean grenade) {
        if (tick < 0 || tick < observed || tick > Long.MAX_VALUE - DURATION_TICKS) return false;
        count = grenade ? MAX_STACKS : Math.min(MAX_STACKS, stacks(tick) + 1);
        observed = tick;
        deadline = tick + DURATION_TICKS;
        return true;
    }

    /** Explicit source revocation removes live stacks; retaining the clock prevents backward-time revival. */
    public void clear() { count = 0; deadline = -1; }
}
