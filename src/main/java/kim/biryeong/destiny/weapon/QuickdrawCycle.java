package kim.biryeong.destiny.weapon;

/** Server tick cycle with identity semantics. Only a real selection can arm it.
 * Cancellation is permanent until another identity is selected; reads never mutate.
 */
public final class QuickdrawCycle {
    private Object source;
    private long started;
    private boolean active;
    public void selected(Object incoming, long tick, boolean eligible) {
        if (incoming == source) return;
        source = incoming;
        active = incoming != null && eligible && tick >= 0 && tick <= Long.MAX_VALUE - QuickdrawProfile.DURATION_TICKS;
        started = tick;
    }
    public void aimInput(boolean pressed) { if (pressed) active = false; }
    public void update(long tick, boolean valid, boolean ads) {
        if (!valid || ads || tick < started || tick - started >= QuickdrawProfile.DURATION_TICKS) active = false;
    }
    public int remaining(Object identity, long tick) {
        return active && identity == source && tick >= started && tick - started < QuickdrawProfile.DURATION_TICKS
            ? QuickdrawProfile.DURATION_TICKS - (int)(tick - started) : 0;
    }
    public void clear() { source = null; active = false; }
}
