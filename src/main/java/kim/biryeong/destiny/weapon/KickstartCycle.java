package kim.biryeong.destiny.weapon;

/** Kickstart: a slide after at least the required sprint streak grants a short damage/charge buff. */
public final class KickstartCycle {
    private final TimedBuffCycle buff = new TimedBuffCycle();
    public boolean slide(long now, int sprintTicks, int requiredSprint, int duration) {
        if (sprintTicks < requiredSprint) return false;
        buff.activate(now, duration);
        return true;
    }
    public boolean active(long now) { return buff.active(now); }
    public long remaining(long now) { return buff.remaining(now); }
}
