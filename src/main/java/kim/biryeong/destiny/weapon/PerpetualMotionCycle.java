package kim.biryeong.destiny.weapon;

/** Tick-sampled motion progress: 2s/10s, with .5s slow grace. Brief slow intervals pause
 * progress; this integration policy and a reset across missing samples are local, not a D2 stopwatch claim. */
public final class PerpetualMotionCycle {
    private long last = -1;
    private int movingTicks, slowTicks;
    public void sample(long tick, boolean moving) {
        if (tick < 0) throw new IllegalArgumentException("Negative motion tick");
        if (tick == last) return;
        if (last >= 0 && (tick < last || tick - last != 1)) { movingTicks=0; slowTicks=0; }
        last=tick;
        if (moving) { slowTicks=0; movingTicks=Math.min(200,movingTicks+1); }
        else if (++slowTicks >= 10) { movingTicks=0; slowTicks=10; }
    }
    public int stacks() { return movingTicks >= 200 ? 2 : movingTicks >= 40 ? 1 : 0; }
    public int movingTicks() { return movingTicks; }
    public int slowTicks() { return slowTicks; }
    public void reset() { last=-1; movingTicks=0; slowTicks=0; }
}
