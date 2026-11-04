package kim.biryeong.destiny.weapon;

/** Weapon final blows -> actual reload completion -> overwriteable damage window.
 * Pure server-thread state: no ammo, owners, tasks or Minecraft dependencies.
 */
public final class MultikillClipCycle {
    public static final int MAX_STACKS = 3;
    public static final int CHAIN_GAP_TICKS = 70;
    public static final int RELOAD_WINDOW_TICKS = 72;
    public static final int DURATION_TICKS = 100;
    private static final float[] MULTIPLIERS = {1f, 1.17f, 1.33f, 1.5f};
    private int kills;
    private long lastKill = -1;
    private int count;
    private long deadline = -1;
    private long observed = -1;

    /** Paid emission value is immutable across later reloads, expiry and ordinary stow. */
    public record Snapshot(float multiplier) {}

    /** HUD and damage reads never create, consume or extend a kill chain or live buff. */
    public int stacks(long tick) {
        return tick >= 0 && tick >= observed && tick < deadline ? count : 0;
    }
    public int remaining(long tick) { return stacks(tick) == 0 ? 0 : (int) (deadline - tick); }
    public Snapshot capture(long tick) { return new Snapshot(MULTIPLIERS[stacks(tick)]); }
    private boolean monotonic(long tick) { return tick >= 0 && tick >= observed; }

    /** Preserve the last kill through the inclusive reload window, including ticks 71 and 72. */
    public void update(long tick) {
        if (!monotonic(tick)) return;
        observed = tick;
        if (tick >= deadline) { count = 0; deadline = -1; }
        if (lastKill >= 0 && tick - lastKill > RELOAD_WINDOW_TICKS) { kills = 0; lastKill = -1; }
    }

    /** Caller verifies positive actual weapon damage and a distinct confirmed final blow. */
    public boolean killed(long tick) {
        if (!monotonic(tick)) return false;
        update(tick);
        kills = lastKill >= 0 && tick - lastKill <= CHAIN_GAP_TICKS
                ? Math.min(MAX_STACKS, kills + 1) : 1;
        lastKill = tick;
        return true;
    }

    /** Positive real ammo insertion only (ordinary reload or explicit Marksman Dodge policy).
     * Each qualifying completion consumes the chain and overwrites even a stronger live buff.
     * A completion with no qualifying chain preserves the current buff and deadline.
     */
    public boolean reloaded(long tick) {
        if (!monotonic(tick) || tick > Long.MAX_VALUE - DURATION_TICKS) return false;
        update(tick);
        if (kills == 0 || lastKill < 0 || tick - lastKill > RELOAD_WINDOW_TICKS) return false;
        count = kills;
        deadline = tick + DURATION_TICKS;
        kills = 0;
        lastKill = -1;
        return true;
    }

    /** Stow clears both live buff and pending kills; retain the monotonic clock guard. */
    public void clear() { kills = 0; lastKill = -1; count = 0; deadline = -1; }
}
