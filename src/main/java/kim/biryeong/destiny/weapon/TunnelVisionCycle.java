package kim.biryeong.destiny.weapon;

/** Tunnel Vision: finishing a reload within the window after this weapon's final blow grants a
 * refreshable buff. The kill is spent by the activating reload. */
public final class TunnelVisionCycle {
    private final TimedBuffCycle buff = new TimedBuffCycle();
    private long lastKill = Long.MIN_VALUE;
    public void killed(long now) { lastKill = now; }
    public boolean reloadFinished(long now, int window, int duration) {
        if (lastKill == Long.MIN_VALUE || now < lastKill || now - lastKill > window) return false;
        lastKill = Long.MIN_VALUE;
        buff.activate(now, duration);
        return true;
    }
    public boolean active(long now) { return buff.active(now); }
    public long remaining(long now) { return buff.remaining(now); }
}
