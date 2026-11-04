package kim.biryeong.destiny.weapon;

import java.util.Collections;
import java.util.IdentityHashMap;
import java.util.Set;

/** Source-owned final-blow credit survives stow. No invented kill-window timeout. */
public final class AmbitiousAssassinCycle {
    private Object epoch = new Object();
    private long observed = -1;
    private int kills;
    public static final class Emission {
        private final AmbitiousAssassinCycle source;
        private final Object epoch;
        private final Set<Object> corpses = Collections.newSetFromMap(new IdentityHashMap<>());
        private Emission(AmbitiousAssassinCycle s) { source=s; epoch=s.epoch; }
    }
    public static final class Reload {
        private final AmbitiousAssassinCycle source;
        private final Object epoch;
        private boolean spent;
        private Reload(AmbitiousAssassinCycle s) { source=s; epoch=s.epoch; }
    }
    private boolean valid(long tick) { return tick >= 0 && tick >= observed; }
    public Emission capture(long tick) {
        if (!valid(tick)) return null;
        observed=tick; return new Emission(this);
    }
    public boolean killed(long tick, Emission e, Object corpse) {
        if (!valid(tick) || e==null || e.source!=this || e.epoch!=epoch || corpse==null
            || e.corpses.size()>=256 || !e.corpses.add(corpse)) return false;
        observed=tick; kills=Math.min(15,kills+1); return true;
    }
    public Reload acceptedReload(long tick) {
        if (!valid(tick)) return null;
        observed=tick; return new Reload(this);
    }
    /** The real ammunition-credit boundary consumes credit once, including kills during reload. */
    public int finish(long tick, Reload r) {
        if (!valid(tick) || r==null || r.source!=this || r.epoch!=epoch || r.spent) return 0;
        observed=tick; r.spent=true;
        int result=kills; kills=0; return result;
    }
    public int kills(long tick) { return valid(tick)?kills:0; }
    public void update(long tick) { if (!valid(tick)) clear(); else observed=tick; }
    public void clear() { epoch=new Object(); observed=-1; kills=0; }
}
