package kim.biryeong.destiny.weapon;

/** One original owned stack's observed ready/stow clock. Queries never observe time or arm.
 * First sight establishes the current posture, never an invented historical stow interval.
 * Only a real stowed-to-held transition can activate. Exact buff deadlines are expired.
 */
public final class BackupPlanCycle {
    public static final int DURATION_TICKS = 40;
    public static final int STOW_TICKS = 60;
    private long observed = -1;
    private long stowedAt = -1;
    private long deadline = -1;
    private boolean initialized;
    private boolean held;

    private void invalidate() {
        initialized = false;
        held = false;
        stowedAt = deadline = -1;
    }
    private boolean event(long tick) {
        if (tick < 0 || tick < observed || tick > Long.MAX_VALUE - STOW_TICKS) {
            invalidate();
            return false;
        }
        observed = tick;
        return true;
    }
    /** Accepted incoming selection, before computing ready duration. Duplicate calls do nothing. */
    public boolean selecting(long tick) {
        if (!event(tick)) return false;
        if (initialized && held) return false;
        boolean activate = initialized && stowedAt >= 0 && tick - stowedAt >= STOW_TICKS;
        initialized = held = true;
        stowedAt = -1;
        deadline = activate ? tick + DURATION_TICKS : -1;
        return activate;
    }
    /** Capture the outgoing duration before this call. Repeated stow observations retain origin. */
    public void stowing(long tick) {
        if (!event(tick)) return;
        if (!initialized || held) stowedAt = tick;
        initialized = true;
        held = false;
        deadline = -1;
    }
    /** Observe all eligible equipped stacks, including ones currently stowed. Initial held bind
     * does not activate. Observed command/inventory selection changes follow the same clock.
     */
    public void update(long tick, boolean currentlyHeld) {
        if (currentlyHeld) selecting(tick);
        else stowing(tick);
    }
    public int remaining(long tick) {
        return !initialized || !held || tick < 0 || tick < observed || tick >= deadline
            ? 0 : (int)(deadline - tick);
    }
    /** Exactly one runtime callback per successful paid emission, never input/charge/dry fire.
     * Fusion rifles do not refresh. An expired LFR window cannot be revived by a late shot.
     */
    public boolean paidEmission(long tick, boolean linearFusion) {
        if (!event(tick) || !linearFusion || remaining(tick) == 0) return false;
        deadline = tick + DURATION_TICKS;
        return true;
    }
    /** Owner/source lifecycle invalidation must discard all accumulated stow credit. */
    public void clear() { invalidate(); observed = -1; }
}
