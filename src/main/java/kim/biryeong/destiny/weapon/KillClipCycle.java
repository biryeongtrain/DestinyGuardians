package kim.biryeong.destiny.weapon;

/** Kill -> actual reload completion -> refreshable damage window. No ammo, owners, or tasks. */
public final class KillClipCycle {
    private long killedAt = Long.MIN_VALUE;
    private long buffUntil = Long.MIN_VALUE;
    public void killed(long tick) { killedAt = tick >= 0 ? tick : Long.MIN_VALUE; }
    public boolean reloaded(long tick, int window, int duration) {
        if (window < 1 || duration < 1 || window > 1200 || duration > 1200) throw new IllegalArgumentException("Unsafe perk timing");
        if (killedAt == Long.MIN_VALUE || tick < killedAt || tick - killedAt > window || tick > Long.MAX_VALUE - duration) return false;
        buffUntil = tick + duration;
        // Conservative authored policy: one kill authorizes one successful reload, not every shell.
        killedAt = Long.MIN_VALUE;
        return true;
    }
    public int remaining(long tick, int duration) {
        return tick >= 0 && duration > 0 && duration <= 1200 && buffUntil > tick && buffUntil - tick <= duration ? (int)(buffUntil - tick) : 0;
    }
}
