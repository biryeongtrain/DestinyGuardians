package kim.biryeong.destiny.weapon;

/** Actual combat events, not trigger intent. update may activate, reads never refresh a deadline. */
public final class FrenzyCycle {
    private final int activation, grace, duration;
    private long start = -1, lastDamage = -1, until = -1, clock = -1;
    private boolean activated;
    public FrenzyCycle(int activation, int grace, int duration) {
        if (activation < 1 || grace < 1 || duration < 1) throw new IllegalArgumentException("Invalid Frenzy duration");
        this.activation=activation; this.grace=grace; this.duration=duration;
    }
    private long deadline(long tick) { return tick > Long.MAX_VALUE-duration ? Long.MAX_VALUE : tick+duration; }
    public void update(long tick) {
        if (tick < 0) throw new IllegalArgumentException("Negative combat clock");
        if (clock > tick) reset();
        clock=tick;
        if (lastDamage < 0) return;
        // Exactly five seconds without another real event ends the priming encounter.
        if (tick-lastDamage >= grace) { start=-1; activated=false; return; }
        if (start >= 0 && !activated && tick-start >= activation) {
            activated=true; until=Math.max(until,deadline(tick));
        }
    }
    public void damage(long tick) {
        update(tick);
        if (start < 0) { start=tick; activated=false; }
        lastDamage=tick;
        if (remaining(tick)>0) until=deadline(tick);
    }
    public int remaining(long tick) {
        return tick < 0 || tick < clock || until <= tick ? 0 : (int)Math.min(duration,until-tick);
    }
    public int combatTicks(long tick) {
        return tick < 0 || tick < clock || start < 0 || lastDamage < 0 || tick-lastDamage >= grace
                ? 0 : (int)Math.min(activation,tick-start);
    }
    public void reset() { start=lastDamage=until=clock=-1; activated=false; }
}
