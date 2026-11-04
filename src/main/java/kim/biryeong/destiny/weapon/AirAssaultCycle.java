package kim.biryeong.destiny.weapon;

/** Air Assault: weapon kills add 1 stack (2 when airborne), max 2, shared 5s timer refreshed by kills. */
public final class AirAssaultCycle {
    private final TimedBuffCycle buff = new TimedBuffCycle();
    private int stacks;
    public void killed(long now, boolean airborne, int airborneStacks, int maxStacks, int duration) {
        int base = buff.active(now) ? stacks : 0;
        stacks = Math.min(maxStacks, base + (airborne ? airborneStacks : 1));
        buff.activate(now, duration);
    }
    public int stacks(long now) { return buff.active(now) ? stacks : 0; }
    public long remaining(long now) { return buff.remaining(now); }
    public void stowed() { buff.clear(); stacks = 0; }
}
