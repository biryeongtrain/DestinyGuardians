package kim.biryeong.destiny.weapon;

/** W327 base-perk state. One instance belongs to one equipped weapon identity.
 * Reads never advance timers, grant effects or refresh durations. */
public final class PerkExpansionStatsCycle {
    private static final int[] ENLIGHTENED = {0, 2, 7, 12, 15, 20, 25, 30, 35, 38, 40, 45, 50};
    private long clock = -1, sprintStart = -1, eddyUntil = -1, enlightenedUntil = -1,
            offhandUntil = -1, combatStart = -1, lastDamage = -1, floatUntil = -1;
    private int enlightenedStacks;
    private boolean sprinting, held, amplified, enemyNearby, allyNearby, floatPrimed;

    private static long deadline(long tick, int duration) {
        return tick > Long.MAX_VALUE - duration ? Long.MAX_VALUE : tick + duration;
    }
    private void advance(long tick) {
        if (tick < 0) throw new IllegalArgumentException("Negative perk clock");
        if (tick < clock) reset();
        clock = tick;
        if (enlightenedUntil <= tick) enlightenedStacks = 0;
        if (lastDamage >= 0 && tick - lastDamage > 60) { combatStart = -1; floatPrimed = false; }
        if (!floatPrimed && combatStart >= 0 && tick - combatStart >= 120) {
            floatPrimed = true;
            floatUntil = deadline(tick, 200);
        }
    }
    public void sample(long tick, boolean held, boolean sprinting, boolean amplified,
                       boolean enemyNearby, boolean allyNearby) {
        advance(tick);
        this.enemyNearby = enemyNearby; this.allyNearby = allyNearby;
        this.amplified = amplified; this.held = held;
        boolean sprint = held && sprinting;
        if (!sprint) sprintStart = -1;
        else {
            if (!this.sprinting) {
                sprintStart = tick;
                if (eddyUntil > tick) eddyUntil = deadline(tick, 60);
            }
            if (tick - sprintStart >= 30) eddyUntil = deadline(tick, 60);
        }
        this.sprinting = sprint;
    }
    /** One accepted direct hit per paid emission; HC grants three stacks, known automatic families one. */
    public void hit(long tick, int stacks) {
        if (stacks < 1) return;
        advance(tick);
        enlightenedStacks = Math.min(12, enlightenedStacks + Math.min(stacks, 12));
        enlightenedUntil = deadline(tick, 40);
    }
    public void kill(long tick) { advance(tick); offhandUntil = deadline(tick, 140); }
    public void damage(long tick) {
        advance(tick);
        if (combatStart < 0) { combatStart = tick; floatPrimed = false; }
        lastDamage = tick;
        if (floatUntil > tick) floatUntil = deadline(tick, 200);
    }
    /** Only Offhand Strike and the sprint window are revoked by stow. */
    public void stowed(long tick) {
        advance(tick); held = sprinting = amplified = false;
        sprintStart = eddyUntil = offhandUntil = -1;
    }
    public void reset() {
        clock = sprintStart = eddyUntil = enlightenedUntil = offhandUntil = combatStart = lastDamage = floatUntil = -1;
        enlightenedStacks = 0;
        sprinting = held = amplified = enemyNearby = allyNearby = floatPrimed = false;
    }
    private int remaining(long tick, long until, int max) {
        return tick < 0 || tick < clock || until <= tick ? 0 : (int) Math.min(max, until - tick);
    }
    public int enlightenedRemaining(long tick) { return remaining(tick, enlightenedUntil, 40); }
    public int enlightenedStacks(long tick) { return enlightenedRemaining(tick) > 0 ? enlightenedStacks : 0; }
    public int enlightenedBonus(long tick) { return ENLIGHTENED[enlightenedStacks(tick)]; }
    public int offhandRemaining(long tick) { return remaining(tick, offhandUntil, 140); }
    public int floatRemaining(long tick) { return remaining(tick, floatUntil, 200); }
    public int eddyRemaining(long tick) { return held && amplified && tick >= clock ? 60 : remaining(tick, eddyUntil, 60); }
    public int eddyReload(long tick) { return eddyRemaining(tick) > 0 ? held && amplified ? 60 : 20 : 0; }
    public boolean keepAway(long tick) { return tick >= clock && clock >= 0 && !enemyNearby; }
    public boolean alone(long tick) { return tick >= clock && clock >= 0 && !allyNearby; }
}
