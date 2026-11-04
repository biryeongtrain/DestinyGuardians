package kim.biryeong.destiny.weapon;

/** Read-only snapshot of an accepted fusion/linear charge or an unfinished bolt burst.
 * Elapsed ticks and bolt counts come from the authoritative runtime; this value owns no clock.
 */
public record WeaponChargeState(Phase phase, float progress, int emittedBolts, int totalBolts) {
    public enum Phase { IDLE, CHARGING, BURSTING }

    private static final WeaponChargeState IDLE = new WeaponChargeState(Phase.IDLE, 0, 0, 0);

    public WeaponChargeState {
        if (phase == null || !Float.isFinite(progress) || progress < 0 || progress > 1)
            throw new IllegalArgumentException("Invalid charge phase/progress");
        boolean valid = switch (phase) {
            case IDLE -> progress == 0 && emittedBolts == 0 && totalBolts == 0;
            case CHARGING -> emittedBolts == 0 && totalBolts >= 1 && totalBolts <= 9;
            case BURSTING -> progress == 1 && totalBolts >= 2 && totalBolts <= 9
                    && emittedBolts >= 1 && emittedBolts < totalBolts;
        };
        if (!valid) throw new IllegalArgumentException("Invalid charge bolt counts/state");
    }

    public static WeaponChargeState idle() { return IDLE; }

    /** Saturates at full charge, including elapsed values beyond the integer tick range. */
    public static WeaponChargeState charging(long elapsed, int duration, int totalBolts) {
        if (elapsed < 0 || duration <= 0)
            throw new IllegalArgumentException("Charge requires nonnegative elapsed ticks and positive duration");
        float progress = Math.min(elapsed, (long) duration) / (float) duration;
        return new WeaponChargeState(Phase.CHARGING, progress, 0, totalBolts);
    }

    /** Only active, uncompleted bursts are represented; the runtime returns idle after completion. */
    public static WeaponChargeState bursting(int emitted, int total) {
        return new WeaponChargeState(Phase.BURSTING, 1, emitted, total);
    }
}
