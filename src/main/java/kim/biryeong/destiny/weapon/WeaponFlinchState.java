package kim.biryeong.destiny.weapon;

/** Pure No Distractions clock and bounded authored camera impulse, not a reconstructed D2 angle.
 * No delayed camera recovery is queued: subsequent mouse input is never pulled back. */
public final class WeaponFlinchState {
    public static final int PROC_TICKS = 20;
    public static final float NO_DISTRACTIONS_RESISTANCE = .35f;
    private boolean aiming, active;
    private long since, last = Long.MIN_VALUE;

    /** Actual ADS input interval, including the entry animation. A same-tick release still resets. */
    public void tick(long now, boolean ads) {
        if (!ads || (last != Long.MIN_VALUE && now < last)) reset();
        last = now;
        if (!ads) return;
        if (!aiming) { aiming = true; since = now; }
        if (now - since >= PROC_TICKS) active = true;
    }
    /** Firing interrupts only the unearned wind-up; an earned buff lasts until ADS ends. */
    public void shot(long now) {
        if (aiming && !active) since = now;
    }
    public boolean active() { return active; }
    public void reset() { aiming = false; active = false; since = 0; last = Long.MIN_VALUE; }

    /** Multiplicative resistances. 100-Stability endpoints are historical official; the linear
     * (stability-20)/80 interpolation/extrapolation below is explicitly local, not a sourced curve. */
    public static float magnitude(float actualLoss, float maxHealth, float stability,
                                  float maxStabilityResistance, float ads, boolean noDistractions) {
        if (!Float.isFinite(actualLoss) || actualLoss <= 0 || !Float.isFinite(maxHealth) || maxHealth <= 0
                || !Float.isFinite(stability) || !Float.isFinite(maxStabilityResistance) || !Float.isFinite(ads)) return 0;
        float resistance = (Math.clamp(stability, 0, 100)-20) / 80 * Math.clamp(maxStabilityResistance, 0, 1);
        float local = (.20f + 1.80f * Math.clamp(actualLoss / maxHealth * 2, 0, 1))
                * (1 + .35f * Math.clamp(ads, 0, 1));
        return local * (1 - resistance) * (noDistractions ? 1 - NO_DISTRACTIONS_RESISTANCE : 1);
    }
}
