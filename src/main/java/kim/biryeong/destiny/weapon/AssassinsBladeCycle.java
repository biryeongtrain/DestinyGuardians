package kim.biryeong.destiny.weapon;

import java.util.Collections;
import java.util.IdentityHashMap;
import java.util.Set;

/** Source-backed five-second buff; ordinary stow retains live benefits and paid authority. */
public final class AssassinsBladeCycle {
    public static final int MAX_CORPSES_PER_EMISSION = 256;
    private Object epoch = new Object();
    private long observed = -1, until = -1;
    public static final class Emission {
        private final AssassinsBladeCycle source;
        private final Object epoch;
        private final long capturedAt;
        private final boolean active;
        private final Set<Object> corpses = Collections.newSetFromMap(new IdentityHashMap<>());
        private Emission(AssassinsBladeCycle source, long tick) {
            this.source = source; epoch = source.epoch; capturedAt = tick;
            active = source.remaining(tick) > 0;
        }
    }
    private boolean timeValid(long tick) { return tick >= 0 && tick >= observed; }
    private boolean valid(long tick, Emission emission) {
        return timeValid(tick) && emission != null && emission.source == this
            && emission.epoch == epoch && tick >= emission.capturedAt;
    }
    /** Actual paid sword acceptance, before its own kill. */
    public Emission capture(long tick) {
        if (!timeValid(tick)) { clear(); return null; }
        observed = tick;
        return new Emission(this, tick);
    }
    public float multiplier(long tick, Emission emission) {
        return valid(tick, emission) && emission.active ? AssassinsBladeProfile.damageMultiplier() : 1f;
    }
    /** Trusted positive-loss sword final blow. Direct/splash share this never-evicting ledger. */
    public boolean killed(long tick, Emission emission, Object corpse) {
        if (!valid(tick, emission) || corpse == null
            || emission.corpses.size() >= MAX_CORPSES_PER_EMISSION || !emission.corpses.add(corpse)) return false;
        observed = tick;
        until = tick > Long.MAX_VALUE - AssassinsBladeProfile.durationTicks()
            ? Long.MAX_VALUE : tick + AssassinsBladeProfile.durationTicks();
        return true;
    }
    /** Pure expiry projection; does not revoke tokens, bind sources or advance time. */
    public int remaining(long tick) {
        return timeValid(tick) && tick < until ? (int) Math.min(AssassinsBladeProfile.durationTicks(), until - tick) : 0;
    }
    public void update(long tick) {
        if (!timeValid(tick)) { clear(); return; }
        observed = tick;
    }
    public void clear() { epoch = new Object(); observed = -1; until = -1; }
}
