package kim.biryeong.destiny.fx;

/** H19 clip contact .30s plus BetterModel's one-tick start transition. Server ticks, not wall time. */
public final class ShadowshotTiming {
    public static final int DRAW_TICKS = 4;
    public static final int RELEASE_TICKS = 7;
    private int elapsed = -1;
    private boolean released;

    public boolean request() {
        if (elapsed >= 0) return false;
        elapsed = 0;
        return true;
    }

    public boolean requested() { return elapsed >= 0; }
    public boolean drawn() { return elapsed >= DRAW_TICKS && !released; }
    public boolean advance() {
        if (elapsed < 0 || released) return false;
        if (++elapsed < RELEASE_TICKS) return false;
        released = true;
        return true;
    }
}
