package kim.biryeong.destiny.activity.presentation;

import java.util.Objects;
import java.util.UUID;

/** One activity's restriction and delayed wipe ownership. No scheduler or player/global state. */
public final class ActivityFailureState implements AutoCloseable {
    // User-selected 023D-00001176 cue is11.14s;230ticks retains the full cue plus a short end gap.
    public static final int WIPE_PRESENTATION_TICKS = 230;
    public record Wipe(UUID activity, long generation, long serial) { }
    private final UUID activity;
    private long generation, serial;
    private String zone = "";
    private boolean restricted, closed, recoveryIssued;
    private Wipe wipe;
    private int wipeAge;

    public ActivityFailureState(UUID activity) { this.activity = Objects.requireNonNull(activity); }

    /** A new encounter/zone or leaving a restricted phase invalidates old recovery work first. */
    public boolean scope(long generation, String zone, boolean restricted) {
        Objects.requireNonNull(zone);
        if (closed || generation <= 0 || generation < this.generation) return false;
        if (generation != this.generation || !zone.equals(this.zone) || !restricted) {
            wipe = null; wipeAge = 0; recoveryIssued = false;
        }
        this.generation = generation; this.zone = zone; this.restricted = restricted;
        return true;
    }
    public boolean beginWipe(long expectedGeneration) {
        if (closed || !restricted || generation != expectedGeneration || wipe != null || recoveryIssued) return false;
        wipe = new Wipe(activity, generation, ++serial); wipeAge = 0;
        return true;
    }
    /** The owning server loop advances once per tick; offline/placement gaps cannot consume the scene. */
    public boolean tick(long expectedGeneration, boolean audienceReady) {
        if (closed || wipe == null || recoveryIssued || expectedGeneration != generation || !audienceReady) return false;
        if (++wipeAge < WIPE_PRESENTATION_TICKS) return false;
        recoveryIssued = true;
        return true;
    }
    public boolean owns(Wipe token) { return !closed && token != null && token.equals(wipe); }
    public boolean restricted() { return !closed && restricted; }
    public boolean wiping() { return !closed && wipe != null; }
    public long generation() { return generation; }
    public String zone() { return zone; }
    public Wipe wipe() { return wipe; }
    public int wipeAge() { return wipeAge; }
    public int remainingSeconds() { return (Math.max(0, WIPE_PRESENTATION_TICKS - wipeAge) + 19) / 20; }
    @Override public void close() { closed = true; restricted = false; wipe = null; }
}
