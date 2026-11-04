package kim.biryeong.destiny.weapon;

/** Slideways/Slideshot: slide grants a timed buff behind an activation cooldown. Slideshot's buff
 * also ends after its first paid emission. Pure; refill is performed by the runtime on true.
 */
public final class SlideBuffCycle {
    private final TimedBuffCycle buff = new TimedBuffCycle();
    private long cooldownUntil = Long.MIN_VALUE;
    /** @return true when this slide activated (caller refills the magazine once). */
    public boolean slide(long now, int duration, int cooldown) {
        if (now < cooldownUntil) return false;
        buff.activate(now, duration);
        cooldownUntil = now + cooldown;
        return true;
    }
    public boolean active(long now) { return buff.active(now); }
    public long remaining(long now) { return buff.remaining(now); }
    public void shot() { buff.clear(); }
    public void stowed() { buff.clear(); }
    /** ceil(fraction * magazine), at least one round. */
    public static int refillRounds(int magazine, double fraction) {
        if (magazine <= 0) return 0;
        return Math.max(1, (int) Math.ceil(magazine * fraction - 1e-9));
    }
}
