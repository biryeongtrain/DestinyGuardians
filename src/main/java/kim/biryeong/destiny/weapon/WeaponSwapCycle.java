package kim.biryeong.destiny.weapon;

/** Identity-based, server-clock-only weapon switching. Initial observation is already equipped.
 * Same-tick retargets keep an unfinished stow; cancelling a draw starts that item's stow.
 * These interruption rules are authored, not claimed to be measured D2 animation internals. */
public final class WeaponSwapCycle {
    public enum Phase { NONE, STOW, READY }
    private Object selected;
    private boolean initialized;
    private long stowAt, stowUntil, readyAt;
    public boolean select(Object identity, long tick, int outgoingStow, int incomingReady) {
        if (tick < 0 || tick > Long.MAX_VALUE - 2400 || outgoingStow < 0 || outgoingStow > 1200
                || incomingReady < 0 || incomingReady > 1200) throw new IllegalArgumentException("Unsafe swap clock");
        if (!initialized) { initialized = true; selected = identity; return false; }
        if (selected == identity) return false;
        selected = identity;
        if (tick >= stowUntil) {
            stowAt = tick;
            stowUntil = tick + outgoingStow;
        }
        readyAt = stowUntil + incomingReady;
        return true;
    }
    public long remaining(long tick) { return Math.max(0, readyAt - tick); }
    public Phase phase(long tick) {
        return tick < stowUntil ? Phase.STOW : tick < readyAt ? Phase.READY : Phase.NONE;
    }
    /** Read-only cosmetic clock. Never moves or grants the gameplay ready deadline. */
    public float progress(long tick) {
        return switch (phase(tick)) {
            case STOW -> Math.clamp((tick - stowAt) / (float)Math.max(1, stowUntil - stowAt), 0, 1);
            case READY -> Math.clamp((tick - stowUntil) / (float)Math.max(1, readyAt - stowUntil), 0, 1);
            case NONE -> 1;
        };
    }
}
