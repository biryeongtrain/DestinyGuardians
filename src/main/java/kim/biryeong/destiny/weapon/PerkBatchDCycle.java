package kim.biryeong.destiny.weapon;

/** Pure per-owner W323 batch D timers. Sources are opaque item identities; ticks are server ticks.
 * Backward ticks are ignored for refreshes so a stale event cannot extend a buff. */
public final class PerkBatchDCycle {
    public record Config(int counterWindow, int counterTicks, float counterMultiplier,
                         int flashCooldown, int valiantTicks, int tiltTicks,
                         int unstoppableTicks, float unstoppableMultiplier,
                         int moaX1Ticks, float moaX1, int moaX2Ticks, float moaX2) {
        public static Config profile() {
            return new Config(PerkBatchDProfile.ticks(PerkBatchDProfile.COUNTERATTACK, "windowTicks"),
                    PerkBatchDProfile.ticks(PerkBatchDProfile.COUNTERATTACK, "durationTicks"),
                    (float) PerkBatchDProfile.value(PerkBatchDProfile.COUNTERATTACK, "damageMultiplier"),
                    PerkBatchDProfile.ticks(PerkBatchDProfile.FLASH_COUNTER, "cooldownTicks"),
                    PerkBatchDProfile.ticks(PerkBatchDProfile.VALIANT_CHARGE, "windowTicks"),
                    PerkBatchDProfile.ticks(PerkBatchDProfile.TILTING, "durationTicks"),
                    PerkBatchDProfile.ticks(PerkBatchDProfile.UNSTOPPABLE_FORCE, "durationTicks"),
                    (float) PerkBatchDProfile.value(PerkBatchDProfile.UNSTOPPABLE_FORCE, "damageMultiplier"),
                    PerkBatchDProfile.ticks(PerkBatchDProfile.MASTER_OF_ARMS, "x1Ticks"),
                    (float) PerkBatchDProfile.value(PerkBatchDProfile.MASTER_OF_ARMS, "x1Multiplier"),
                    PerkBatchDProfile.ticks(PerkBatchDProfile.MASTER_OF_ARMS, "x2Ticks"),
                    (float) PerkBatchDProfile.value(PerkBatchDProfile.MASTER_OF_ARMS, "x2Multiplier"));
        }
    }
    /** Which selected traits the guarding item carries when a hit is blocked. */
    public record Guard(boolean counterattack, boolean flashCounter, boolean valiant, boolean tilting, boolean unstoppable) {}
    private final Config config;
    private long observed = Long.MIN_VALUE, guardStart = -1;
    private Object guardSource;
    private long counterUntil = -1, flashReadyAt = Long.MIN_VALUE, valiantUntil = -1, tiltUntil = -1, unstoppableUntil = -1;
    private Object counterSource, valiantSource, tiltSource, unstoppableSource, tranceSource;
    private long moaX1Until = -1, moaX2Until = -1;

    public PerkBatchDCycle(Config config) { this.config = java.util.Objects.requireNonNull(config); }

    private boolean forward(long tick) {
        if (tick < 0 || tick < observed) return false;
        observed = tick; return true;
    }
    /** Once per tick with the held item and whether its guard (sword) or shield (glaive) is up. */
    public void guard(long tick, Object held, boolean guarding) {
        if (!forward(tick)) return;
        if (!guarding || held == null) { guardStart = -1; guardSource = null; tiltUntil = -1; tiltSource = null; }
        else if (guardStart < 0 || guardSource != held) { guardStart = tick; guardSource = held; }
        if (tranceSource != null && tranceSource != held) tranceSource = null; // Removed on stow.
    }
    /** A genuinely blocked hit. Returns true when Flash Counter must emit a blast now. */
    public boolean blocked(long tick, Object source, Guard perks) {
        if (source == null || perks == null || !forward(tick)) return false;
        boolean fresh = guardStart >= 0 && guardSource == source && tick - guardStart <= config.counterWindow;
        if (perks.counterattack && fresh) { counterUntil = tick + config.counterTicks; counterSource = source; }
        if (perks.valiant) { valiantUntil = tick + config.valiantTicks; valiantSource = source; }
        if (perks.tilting) { tiltUntil = tick + config.tiltTicks; tiltSource = source; }
        if (perks.unstoppable) { unstoppableUntil = tick + config.unstoppableTicks; unstoppableSource = source; }
        if (perks.flashCounter && tick >= flashReadyAt) { flashReadyAt = tick + config.flashCooldown; return true; }
        return false;
    }
    public float counterMultiplier(long tick, Object source) {
        return source != null && source == counterSource && tick >= 0 && tick < counterUntil ? config.counterMultiplier : 1f;
    }
    public float unstoppableMultiplier(long tick, Object source) {
        return source != null && source == unstoppableSource && tick >= 0 && tick < unstoppableUntil ? config.unstoppableMultiplier : 1f;
    }
    /** True only while the same shield is still up (guard() clears it when lowered). */
    public boolean tilting(long tick, Object held) {
        return held != null && held == tiltSource && guardSource == held && tick >= 0 && tick < tiltUntil;
    }
    /** The next light swing of the same sword consumes Valiant Charge. */
    public boolean consumeValiant(long tick, Object held) {
        boolean active = held != null && held == valiantSource && tick >= 0 && tick < valiantUntil;
        if (active || held == valiantSource) { valiantUntil = -1; valiantSource = null; }
        return active;
    }
    public void swordKill(Object source) { if (source != null) tranceSource = source; }
    public boolean trance(Object held) { return held != null && held == tranceSource; }
    public void weaponKill(long tick) {
        if (!forward(tick)) return;
        if (tick < moaX1Until) moaX2Until = tick + config.moaX2Ticks;
        moaX1Until = tick + config.moaX1Ticks;
    }
    public float moaMultiplier(long tick) {
        if (tick < 0) return 1f;
        return tick < moaX2Until ? config.moaX2 : tick < moaX1Until ? config.moaX1 : 1f;
    }
    /** Source edit/removal: revoke every buff tied to that item; Master of Arms is owner-wide. */
    public void changed(Object source) {
        if (source == null) return;
        if (counterSource == source) { counterSource = null; counterUntil = -1; }
        if (valiantSource == source) { valiantSource = null; valiantUntil = -1; }
        if (tiltSource == source) { tiltSource = null; tiltUntil = -1; }
        if (unstoppableSource == source) { unstoppableSource = null; unstoppableUntil = -1; }
        if (tranceSource == source) tranceSource = null;
        if (guardSource == source) { guardSource = null; guardStart = -1; }
    }
    public boolean idle(long tick) {
        return guardStart < 0 && tranceSource == null && tick >= counterUntil && tick >= valiantUntil && tick >= tiltUntil
                && tick >= unstoppableUntil && tick >= moaX1Until && tick >= moaX2Until && tick >= flashReadyAt;
    }
}
