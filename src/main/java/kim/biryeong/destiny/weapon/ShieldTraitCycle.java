package kim.biryeong.destiny.weapon;

/** Shield-driven traits (W320). Shield HP is the Guardian shield pool (0..130).
 * Eye of the Storm: triggers at <= trigger shield, effect fraction (full-shield)/full linear,
 * persists until shield >= full. Fragile Focus: on while shields > 0, off at 0, back after
 * reactivate ticks at full shields.
 */
public final class ShieldTraitCycle {
    public static final double MAX_SHIELD = 130;
    private boolean eye;
    private boolean fragile = true;
    private long fullSince = Long.MIN_VALUE;
    public void sample(long now, double shield, int eyeTrigger, int eyeFull, int reactivateTicks) {
        if (!Double.isFinite(shield)) return;
        if (shield <= eyeTrigger) eye = true;
        else if (shield >= eyeFull) eye = false;
        if (shield <= 0) { fragile = false; fullSince = Long.MIN_VALUE; }
        else if (!fragile) {
            if (shield >= MAX_SHIELD - 1e-6) {
                if (fullSince == Long.MIN_VALUE) fullSince = now;
                if (now - fullSince >= reactivateTicks) fragile = true;
            } else fullSince = Long.MIN_VALUE;
        }
    }
    /** 0..1 linear effect, 0 when inactive. */
    public double eyeFraction(double shield, int eyeFull) {
        if (!eye || !Double.isFinite(shield)) return 0;
        return Math.clamp((eyeFull - shield) / eyeFull, 0.0, 1.0);
    }
    public boolean fragileActive() { return fragile; }
}
