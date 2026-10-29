package kim.biryeong.destiny.fx;

/** Scope is only held while an owned BetterModel limb advances on the server thread. */
public final class ServerPoseSampling {
    // Two 25ms animation evaluations share one authoritative 50ms tick. Only the
    // final evaluation should restart the client's display interpolation.
    private static final ThreadLocal<Boolean> PUBLISH = new ThreadLocal<>();
    private ServerPoseSampling() { }
    public static boolean active() { return PUBLISH.get() != null; }
    public static boolean publishing() { return Boolean.TRUE.equals(PUBLISH.get()); }
    /** BM adds 1ms before rounding its integer delay. That bias is not elapsed time. */
    public static float reachedFraction(float frame, int remaining) {
        int duration = Math.round(frame);
        return duration <= 0 ? 1 : 1f - Math.clamp(remaining / (float) duration, 0f, 1f);
    }
    public static void run(Runnable action) {
        run(true, action);
    }
    public static void run(boolean publish, Runnable action) {
        Boolean previous = PUBLISH.get();
        PUBLISH.set(publish);
        try { action.run(); } finally {
            if (previous != null) PUBLISH.set(previous); else PUBLISH.remove();
        }
    }
}
