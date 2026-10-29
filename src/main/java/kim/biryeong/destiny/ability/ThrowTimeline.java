package kim.biryeong.destiny.ability;

/** Monotonic one-shot release; skipped ticks catch up without duplicating the emission. */
public final class ThrowTimeline {
    private final long start;
    private final int release, duration;
    private boolean emitted, cancelled;
    public ThrowTimeline(long start, int release, int duration) {
        if (release < 1 || duration <= release) throw new IllegalArgumentException("Invalid throw timing");
        this.start = start; this.release = release; this.duration = duration;
    }
    public boolean release(long now, boolean valid) {
        if (!valid) cancelled = true;
        if (cancelled || emitted || now < start + release || now >= start + duration) return false;
        emitted = true;
        return true;
    }
    public boolean finished(long now) { return cancelled || now >= start + duration; }
    public int age(long now) { return (int) Math.clamp(now - start, 0L, duration); }
    public boolean emitted() { return emitted; }
}
