package kim.biryeong.destiny.hud;

import java.util.Objects;

/** Presentation only. Uses server ticks, never update-call counts or mutable world time. */
public final class SuperHudCue {
    public static final int READY_TICKS = 56;
    public static final int CAST_TICKS = 12;
    private boolean initialized;
    private Object loadout;
    private boolean wasReady;
    private boolean wasActive;
    private boolean showingReady;
    private boolean showingCast;
    private int readyAt;
    private int castAt;

    public void sample(int tick, Object equippedSuper, boolean ready, boolean active) {
        ready &= !active && equippedSuper != null;
        if (!initialized || !Objects.equals(loadout, equippedSuper)) {
            initialized = true;
            loadout = equippedSuper;
            wasReady = ready;
            wasActive = active;
            showingReady = showingCast = false;
            return; // Joining/respawning/changing subclass at 100% is not a new charge event.
        }
        if (!ready || active || age(tick, readyAt) >= READY_TICKS) showingReady = false;
        // A one-shot super (e.g. Shadowshot) can end immediately after firing.
        // Let its short release finish; lifecycle/loadout reset still cancels it.
        if (age(tick, castAt) >= CAST_TICKS) showingCast = false;
        if (ready && !wasReady) {
            readyAt = tick;
            showingReady = true;
        }
        if (active && !wasActive) {
            castAt = tick;
            showingCast = true;
        }
        wasReady = ready;
        wasActive = active;
    }

    private static int age(int now, int start) { return now - start; }
    public int readyAge(int tick) { return showingReady ? age(tick, readyAt) : -1; }
    public int castAge(int tick) { return showingCast ? age(tick, castAt) : -1; }
}
