package kim.biryeong.destiny.weapon;

/** Actual reload completion after a confirmed kill grants six paid emissions, not six hits.
 * No timed Memento expiry; stow clears loaded shots but retains pending kill/Firefly windows.
 */
public final class AceCycle {
    public static final int KILL_WINDOW = 72, EMPOWERED_ROUNDS = 6, FIREFLY_DURATION = 120;
    private long killedAt = -1, fireflyAt = -1;
    private int rounds;
    public void killed(long tick, boolean precision) {
        if (tick < 0) throw new IllegalArgumentException("Negative kill tick");
        killedAt = tick;
        if (precision) fireflyAt = tick;
    }
    /** Only a real completed reload with a positive ammunition transfer calls this. */
    public boolean reloaded(long tick) {
        if (killedAt < 0 || tick < killedAt || tick - killedAt > KILL_WINDOW) return false;
        rounds = EMPOWERED_ROUNDS;
        killedAt = -1;
        return true;
    }
    public boolean shot() {
        if (rounds == 0) return false;
        rounds--;
        return true;
    }
    public int rounds() { return rounds; }
    /** Stow loses loaded empowered shots, but retains the sourced pending kill and Firefly window. */
    public void stowed() { rounds = 0; }
    public boolean killEligible(long tick) { return killedAt >= 0 && tick >= killedAt && tick - killedAt <= KILL_WINDOW; }
    public int fireflyRemaining(long tick) {
        if (fireflyAt < 0 || tick < fireflyAt || tick - fireflyAt >= FIREFLY_DURATION) return 0;
        return FIREFLY_DURATION - (int)(tick - fireflyAt);
    }
}
