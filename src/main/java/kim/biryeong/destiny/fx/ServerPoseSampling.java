package kim.biryeong.destiny.fx;

/** Scope is only held while an owned BetterModel limb advances on the server thread. */
public final class ServerPoseSampling {
    // Two 25ms animation evaluations share one authoritative 50ms tick. Only the
    // final evaluation should restart the client's display interpolation.
    private static final ThreadLocal<Boolean> PUBLISH = new ThreadLocal<>();
    private static final ThreadLocal<Integer> SMOOTHING = new ThreadLocal<>();
    private ServerPoseSampling() { }
    public static boolean active() { return PUBLISH.get() != null; }
    public static boolean publishing() { return Boolean.TRUE.equals(PUBLISH.get()); }
    public static int smoothingTicks() {
        Integer ticks = SMOOTHING.get();
        return ticks == null ? 1 : ticks;
    }
    /** Two display ticks for super limbs, including ready/move loops; other animation policies stay unchanged. */
    static int animationSmoothingTicks(String animation) {
        if (animation == null) return 1;
        String name = animation.startsWith("h15_") ? animation.substring(4) : animation;
        return name.startsWith("super_") || name.startsWith("w229_") || name.startsWith("w230_")
                || animation.equals("h15_revive_combat") ? 2 : 1;
    }
    /** Visual smoothing only; authoritative pose evaluation remains unchanged. */
    public static void withSmoothing(int ticks, Runnable action) {
        if (ticks < 1 || ticks > 2) throw new IllegalArgumentException("Unsupported pose smoothing");
        Integer previous = SMOOTHING.get();
        SMOOTHING.set(ticks);
        try { action.run(); } finally {
            if (previous == null) SMOOTHING.remove(); else SMOOTHING.set(previous);
        }
    }
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
