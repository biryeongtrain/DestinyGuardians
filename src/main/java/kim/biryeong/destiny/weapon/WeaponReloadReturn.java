package kim.biryeong.destiny.weapon;

/** Cosmetic clock for an existing source-pose bank. No ammo, firing or reload deadlines.
 * The full source clip spans gameplay duration + six ticks, leaving its authored tail
 * visible after credit. The endpoint is published for one tick before retiring the route.
 */
public final class WeaponReloadReturn {
    public static final int RETURN_TICKS = 6;
    private final float gameplayFraction;
    private long completedAt = Long.MIN_VALUE;

    public WeaponReloadReturn(int gameplayTicks) {
        int duration = Math.max(1, gameplayTicks);
        gameplayFraction = (float) (duration / (duration + (double) RETURN_TICKS));
    }

    /** Called only by the successful gameplay completion hook, never inferred from a selector. */
    public void complete(long tick) {
        if (!completed()) completedAt = tick;
    }
    public boolean completed() { return completedAt != Long.MIN_VALUE; }
    public boolean active(long tick) {
        return completed() && tick >= completedAt && tick - completedAt <= RETURN_TICKS;
    }
    public float progress(long tick, float gameplayProgress) {
        if (!completed()) {
            float p = Float.isFinite(gameplayProgress) ? Math.clamp(gameplayProgress, 0, 1) : 0;
            return p * gameplayFraction;
        }
        float tail = Math.clamp((tick - completedAt) / (float) RETURN_TICKS, 0, 1);
        return gameplayFraction + (1 - gameplayFraction) * tail;
    }
}
