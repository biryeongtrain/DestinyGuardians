package kim.biryeong.destiny.weapon;

/** Killing Wind: 5s on a weapon kill; further kills extend by 5s, never above 8s remaining. Stow clears. */
public final class KillingWindCycle {
    private final TimedBuffCycle buff = new TimedBuffCycle();
    public void killed(long now, int initial, int extend, int cap) { buff.extend(now, initial, extend, cap); }
    public boolean active(long now) { return buff.active(now); }
    public long remaining(long now) { return buff.remaining(now); }
    public void stowed() { buff.clear(); }
}
