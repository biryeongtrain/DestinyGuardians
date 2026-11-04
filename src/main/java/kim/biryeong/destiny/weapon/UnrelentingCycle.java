package kim.biryeong.destiny.weapon;

import java.util.Collections;
import java.util.IdentityHashMap;
import java.util.Set;

/** Pure paid-final-blow state. Five seconds bounds the kill chain, never regeneration. */
public final class UnrelentingCycle {
    public enum Rank { RANK_AND_FILE, POWERFUL, GUARDIAN }
    public static final int MAX_CORPSES = 256;
    private Object epoch = new Object();
    private long observed = -1, lastKill = -1, regenerationTick = -1;
    private int progress;
    private boolean regenerating;
    // Bounded cross-emission duplicate protection for the current five-second chain window.
    private final IdentityHashMap<Object, Long> recentCorpses = new IdentityHashMap<>();
    public static final class Emission {
        private final UnrelentingCycle source;
        private final Object epoch;
        private final long capturedAt;
        private final Set<Object> corpses = Collections.newSetFromMap(new IdentityHashMap<>());
        private Emission(UnrelentingCycle source, long tick) {
            this.source = source; epoch = source.epoch; capturedAt = tick;
        }
    }
    private boolean timeValid(long tick) { return tick >= 0 && tick >= observed; }
    public Emission capture(long tick) {
        if (!timeValid(tick)) { clear(); return null; }
        update(tick);
        return new Emission(this, tick);
    }
    /** True only on a new proc. Caller must prove paid positive-loss enemy final blow. */
    public boolean killed(long tick, Emission emission, Object corpse, Rank rank) {
        if (!timeValid(tick) || emission == null || emission.source != this || emission.epoch != epoch
            || tick < emission.capturedAt || corpse == null || rank == null) return false;
        update(tick);
        if (emission.corpses.contains(corpse) || recentCorpses.containsKey(corpse)
            || emission.corpses.size() >= MAX_CORPSES || recentCorpses.size() >= MAX_CORPSES) return false;
        emission.corpses.add(corpse); recentCorpses.put(corpse, tick);
        lastKill = tick;
        progress += UnrelentingProfile.progress(rank);
        if (progress < 100) return false;
        progress = 0;
        regenerating = true;
        regenerationTick = tick; // First periodic heal is the NEXT real tick, not the proc tick.
        return true;
    }
    public void update(long tick) {
        if (!timeValid(tick)) { clear(); return; }
        observed = tick;
        int window = UnrelentingProfile.windowTicks();
        if (lastKill >= 0 && tick - lastKill > window) { progress = 0; lastKill = -1; }
        recentCorpses.values().removeIf(at -> tick - at > window);
    }
    /** At most one nominal server tick of healing per update; no backlog burst or fake expiry. */
    public float regeneration(long tick, float health, float maximum) {
        if (!timeValid(tick)) { clear(); return 0; }
        update(tick);
        if (!Float.isFinite(health) || !Float.isFinite(maximum) || health <= 0 || maximum <= 0
            || health >= maximum) { regenerating = false; return 0; }
        if (!regenerating || tick <= regenerationTick) return 0;
        regenerationTick = tick;
        return Math.min(maximum - health, maximum * UnrelentingProfile.regenerationFraction());
    }
    public void damaged(float actualLoss) {
        if (Float.isFinite(actualLoss) && actualLoss > 0) regenerating = false;
    }
    public void full() { regenerating = false; }
    /** Pure query: no expiry writer, healing, or binding. */
    public boolean active(long tick) { return timeValid(tick) && regenerating; }
    public int progress(long tick) {
        return timeValid(tick) && lastKill >= 0 && tick - lastKill <= UnrelentingProfile.windowTicks() ? progress : 0;
    }
    public void clear() {
        epoch = new Object(); observed = -1; lastKill = -1; regenerationTick = -1;
        progress = 0; regenerating = false; recentCorpses.clear();
    }
}
