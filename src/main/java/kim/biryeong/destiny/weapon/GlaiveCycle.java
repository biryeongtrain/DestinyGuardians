package kim.biryeong.destiny.weapon;

/** Server-tick glaive state. Fixed-point energy is per item; attack deadlines remain per owner. */
public final class GlaiveCycle {
    public static final int CAPACITY=100_000, HIT_ENERGY=25_000, REGEN_PER_TICK=50;
    // Minecraft tuning: eight seconds of continuous guard. Not a decoded Destiny stat curve.
    public static final int DRAIN_PER_TICK=625, MELEE_INTERVAL=12, COMBO_WINDOW=30, SHOT_TO_MELEE=4;
    private int energy, combo;
    private long lastTick=Long.MIN_VALUE, nextMeleeAt, comboAt=Long.MIN_VALUE, shotAt=Long.MIN_VALUE;
    private boolean guarding, exhausted;

    public void bind(int stored,long tick) {
        energy=Math.clamp(stored,0,CAPACITY);lastTick=tick;stop();
        // Do not reset nextMeleeAt/shotAt: swapping cannot erase attack recovery.
    }
    public void stop() { guarding=false;exhausted=false;combo=0;comboAt=Long.MIN_VALUE; }
    public int energy() { return energy; }
    public int combo() { return combo; }
    public boolean guarding() { return guarding&&energy>0; }
    public void hit() { energy=Math.min(CAPACITY,energy+HIT_ENERGY); }
    public void shot(long tick) { shotAt=tick; }
    /** Does not catch up offline/stowed time, nor advance twice when sampled twice in one tick. */
    public void tick(long tick,boolean wantsGuard,boolean reloading) {
        if(tick<=lastTick)return;
        lastTick=tick;
        if(!wantsGuard)exhausted=false;
        boolean can=wantsGuard&&!exhausted&&!reloading&&tick>=nextMeleeAt;
        if(can&&energy>0) {
            energy=Math.max(0,energy-DRAIN_PER_TICK);guarding=energy>0;
            if(energy==0)exhausted=true;
        } else {
            guarding=false;
            if(can)exhausted=true;
            if(!wantsGuard)energy=Math.min(CAPACITY,energy+REGEN_PER_TICK);
        }
        if(comboAt!=Long.MIN_VALUE&&tick-comboAt>COMBO_WINDOW)combo=0;
    }
    /** Accepted swing, including a miss, advances the combo but never consumes ammunition. */
    public int melee(long tick) {
        if(tick<nextMeleeAt||(shotAt!=Long.MIN_VALUE&&tick-shotAt<SHOT_TO_MELEE))return 0;
        if(comboAt==Long.MIN_VALUE||tick-comboAt>COMBO_WINDOW)combo=0;
        combo=(combo%3)+1;comboAt=tick;nextMeleeAt=tick+MELEE_INTERVAL;guarding=false;
        return combo==3?2:1;
    }
}
