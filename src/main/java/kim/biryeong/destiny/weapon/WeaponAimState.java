package kim.biryeong.destiny.weapon;

/** Tick-based ADS/bloom. Recovery never rotates the player's camera back against mouse input. */
public final class WeaponAimState {
    private float progress, bloom;
    private long lastTick = Long.MIN_VALUE;
    private long lastShotTick = Long.MIN_VALUE;
    private int shots;
    public void tick(long tick, boolean aiming, int transitionTicks, float recovery) {
        tick(tick, aiming, transitionTicks, transitionTicks, recovery);
    }
    /** Entry traits do not implicitly speed up unverified ADS exit animations. */
    public void tick(long tick, boolean aiming, int enterTicks, int exitTicks, float recovery) {
        if (tick == lastTick) return;
        lastTick = tick;
        float step = 1f / Math.max(1, aiming ? enterTicks : exitTicks);
        progress = Math.clamp(progress + (aiming ? step : -step), 0f, 1f);
        if(lastShotTick==Long.MIN_VALUE || tick-lastShotTick>3)
            bloom = Math.max(0, bloom - (Float.isFinite(recovery) ? Math.clamp(recovery, 0, 1) : 0));
    }
    public void shot(float amount) {
        bloom = Math.clamp(bloom + (Float.isFinite(amount) ? amount : 0), 0, 1);
        lastShotTick=lastTick;
        shots++;
    }
    public float progress() { return progress; }
    public float bloom() { return bloom; }
    public int shots() { return shots; }
    public void reset() { progress = 0; bloom = 0; shots = 0; lastShotTick=Long.MIN_VALUE; }
    public static float zoomFov(float base, float zoom) {
        if (!Float.isFinite(base) || base < 1 || base >= 180 || !Float.isFinite(zoom) || zoom < 1)
            throw new IllegalArgumentException("Invalid zoom");
        return (float)Math.toDegrees(2 * Math.atan(Math.tan(Math.toRadians(base / 2)) / zoom));
    }
}
