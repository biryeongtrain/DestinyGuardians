package kim.biryeong.destiny.weapon;

/**
 * Pure server-tick sword state for one bound item. The caller persists energy and
 * remaining recharge delay per item and supplies ammunition/attack readiness.
 * All constants are authored Minecraft tuning, not exact Destiny stat values.
 */
public final class SwordCycle {
    public static final int CAPACITY = 100_000;
    /** Authored: ten seconds of continuous guard at 20 TPS from full to empty. */
    public static final int GUARD_DRAIN_PER_TICK = 500;
    /** Authored: eighty non-guard ticks (four seconds at 20 TPS) to refill after delay. */
    public static final int REGEN_PER_TICK = 1_250;
    /** Authored: twenty ticks after the last active guard tick or heavy attack. */
    public static final int RECHARGE_DELAY = 20;
    public static final int COMBO_WINDOW = 30;

    private int energy;
    private int combo;
    private boolean guarding;
    private long lastTick = Long.MIN_VALUE;
    private long comboAt;
    // Anchor plus bounded duration avoids overflowing tick + RECHARGE_DELAY.
    private long rechargeAt;
    private int rechargeDelay;

    /** Binds an item with no saved recharge delay; never carries another item's delay. */
    public void bind(int stored, long tick) {
        bind(stored, 0, tick);
    }

    /** Restores the item's snapshot at the current tick without stowed/offline catch-up. */
    public void bind(int stored, int remainingDelay, long tick) {
        energy = Math.max(0, Math.min(CAPACITY, stored));
        rechargeAt = tick;
        rechargeDelay = Math.max(0, Math.min(RECHARGE_DELAY, remainingDelay));
        lastTick = tick;
        stop();
    }

    /** Clears transient actions without granting energy or erasing recharge recovery. */
    public void stop() {
        guarding = false;
        combo = 0;
    }

    public int energy() { return energy; }
    /** W323 perk refund (Duelist's Trance): adds energy, never above capacity; no delay/combo change. */
    public void restore(int amount) {
        if (amount > 0) energy = (int) Math.min(CAPACITY, (long) energy + amount);
    }
    public boolean guarding() { return guarding; }
    public int combo() { return combo; }

    /** Read-only snapshot, clamped to the authored delay even for a backward query. */
    public int rechargeRemaining(long tick) {
        if (rechargeDelay == 0) return 0;
        if (tick <= rechargeAt) return rechargeDelay;
        long elapsed = tick - rechargeAt;
        // A negative difference here means the positive elapsed time overflowed long.
        return elapsed < 0 || elapsed >= rechargeDelay ? 0 : rechargeDelay - (int) elapsed;
    }

    /**
     * Advances one guard drain or regeneration step, even after a large gap.
     * Duplicate/backward ticks change nothing. Active guard refreshes the authored
     * recharge delay and cannot regenerate; incoming hits do not affect energy.
     * An empty item may recharge here, then become eligible to guard next tick.
     */
    public void tick(long tick, boolean wantsGuard, boolean hasAmmo, boolean attackReady) {
        if (tick <= lastTick) return;
        lastTick = tick;
        if (wantsGuard && hasAmmo && attackReady && energy > 0) {
            energy = Math.max(0, energy - GUARD_DRAIN_PER_TICK);
            guarding = energy > 0;
            delayRecharge(tick);
        } else {
            guarding = false;
            if (rechargeRemaining(tick) == 0) {
                energy = Math.min(CAPACITY, energy + REGEN_PER_TICK);
            }
        }
        expireCombo(tick);
    }

    /**
     * Returns available energy in [0, 1] before spending it, without implicit recharge.
     * This is a snapshot, not a linear damage multiplier: any positive value permits
     * the caller's full-power heavy; only zero selects its weak heavy.
     */
    public double heavy(long tick) {
        double available = (double) energy / CAPACITY;
        energy = 0;
        stop();
        delayRecharge(tick);
        return available;
    }

    /** Accepted light swing: returns 1/2/3; the caller applies its finisher multiplier. */
    public int light(long tick) {
        expireCombo(tick);
        combo = combo % 3 + 1;
        comboAt = tick;
        guarding = false;
        return combo;
    }

    private void delayRecharge(long tick) {
        rechargeAt = tick;
        rechargeDelay = RECHARGE_DELAY;
    }

    private void expireCombo(long tick) {
        if (combo == 0) return;
        long elapsed = tick - comboAt;
        if (tick < comboAt || elapsed < 0 || elapsed > COMBO_WINDOW) combo = 0;
    }
}
