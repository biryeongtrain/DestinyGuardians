package kim.biryeong.destiny.weapon;

/** One LOCAL owner-wide refill clock, shared by all selected sources. Server thread owned.
 * A valid full/no-reserve proc still spends the opportunity; ammo transfer belongs to the wrapper.
 */
public final class GraveRobberCycle {
    public static final int COOLDOWN_TICKS = 60;
    private long observed = -1;
    private long activated = -1;

    /** Observations fail closed on negative/regressing time without erasing a paid cooldown. */
    public boolean update(long tick) {
        if (tick < 0 || tick < observed) return false;
        observed = tick;
        return true;
    }

    /** Powered hits include nonlethal hits. Unpowered melee requires a final blow. */
    public boolean confirmed(long tick, boolean powered, boolean killed) {
        if ((!powered && !killed) || !update(tick) || remaining(tick) > 0) return false;
        activated = tick;
        return true;
    }

    /** Pure query. Ordered nonnegative subtraction avoids overflowing tick + cooldown. */
    public int remaining(long tick) {
        if (tick < 0 || tick < observed || activated < 0 || tick < activated) return 0;
        long elapsed = tick - activated;
        return elapsed >= COOLDOWN_TICKS ? 0 : COOLDOWN_TICKS - (int) elapsed;
    }

    /** True lifecycle cleanup only; selection edits and ordinary stow never call this. */
    public void clear() { observed = -1; activated = -1; }
}
