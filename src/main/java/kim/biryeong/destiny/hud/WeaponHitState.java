package kim.biryeong.destiny.hud;

import java.util.Objects;

/** Immutable, bounded confirmation policy. Durations are authored HUD tuning, not measured D2 timings.
 * Only a finite positive observed HP+absorption loss may confirm a hit. No precision inference.
 * Reads never consume, advance or refresh a cue; the adapter retires sessions on clock rollback.
 */
public final class WeaponHitState {
    public static final int HIT_TICKS = 4;
    public static final int KILL_TICKS = 7;
    public enum Cue { NONE, HIT, KILL }

    private static final WeaponHitState IDLE = new WeaponHitState(Cue.NONE, 0);
    private final Cue cue;
    private final long confirmedAt;

    private WeaponHitState(Cue cue, long confirmedAt) {
        this.cue = cue;
        this.confirmedAt = confirmedAt;
    }

    public static WeaponHitState idle() { return IDLE; }

    /** Same-tick pellet order cannot downgrade a kill. Ordinary hits during a live kill are
     * deliberately coalesced away, including their timers: they cannot keep red feedback alive.
     * Another actual kill may refresh red; after expiry an ordinary hit starts white normally.
     */
    public WeaponHitState confirm(long now, float observedPositiveDamage, boolean killed) {
        if (!Float.isFinite(observedPositiveDamage) || observedPositiveDamage <= 0) return this;
        Cue active = cueAt(now);
        if (!killed && active == Cue.KILL) return this;
        Cue next = killed ? Cue.KILL : Cue.HIT;
        if (next == cue && now == confirmedAt) return this;
        return new WeaponHitState(next, now);
    }

    /** Half-open lifetime [confirmation, confirmation + duration); subtraction also rejects overflow. */
    public Cue cueAt(long now) {
        if (cue == Cue.NONE || now < confirmedAt) return Cue.NONE;
        long age = now - confirmedAt;
        int duration = cue == Cue.KILL ? KILL_TICKS : HIT_TICKS;
        return age >= 0 && age < duration ? cue : Cue.NONE;
    }

    /** Pure identity policy shared with the adapter; UUID equality is insufficient after respawn,
     * reconnect, level transfer or server replacement. These are identity tokens, never value keys.
     */
    public static final class Binding {
        private final Object player, connection, level, server;

        public Binding(Object player, Object connection, Object level, Object server) {
            this.player = Objects.requireNonNull(player);
            this.connection = Objects.requireNonNull(connection);
            this.level = Objects.requireNonNull(level);
            this.server = Objects.requireNonNull(server);
        }

        public boolean matches(Object player, Object connection, Object level, Object server) {
            return this.player == player && this.connection == connection
                    && this.level == level && this.server == server;
        }
    }
}
