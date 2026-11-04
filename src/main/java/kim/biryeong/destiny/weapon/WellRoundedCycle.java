package kim.biryeong.destiny.weapon;

/** Accepted ability events; queries never extend the inclusive expiry deadline. */
public final class WellRoundedCycle {
    public static final int DURATION_TICKS = 300, MAX_STACKS = 2;
    private int stacks;
    private long started=Long.MAX_VALUE;
    private long until = Long.MIN_VALUE;
    public void used(long now, int amount) {
        if (now < 0 || amount <= 0) return;
        stacks = Math.min(MAX_STACKS, stacks(now) + Math.min(MAX_STACKS, amount));
        started=now;
        until = now > Long.MAX_VALUE-DURATION_TICKS ? Long.MAX_VALUE : now+DURATION_TICKS;
    }
    public int remaining(long now) {
        return now < started || now >= until ? 0 : (int)Math.min(DURATION_TICKS, until-now);
    }
    public int stacks(long now) { return remaining(now)>0 ? stacks : 0; }
}
