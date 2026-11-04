package kim.biryeong.destiny.weapon;

import java.util.ArrayDeque;

/** Actual ready observations are independent of selected trait/source session lifetimes. */
public final class EnGardeCycle {
    private static final int CONTACT_LIMIT = 128;
    /** One per ServerPlayer identity. Survives source edits so an edit cannot invent a ready. */
    public static final class Readiness {
        private Object incoming;
        private boolean consumed;
        private long observed = -1, cooldownUntil = -1;
        public boolean observe(long tick, Object identity, boolean ready) {
            if (tick < 0 || tick < observed) { incoming = identity; consumed = true; return false; }
            observed = tick;
            if (incoming != identity) { incoming = identity; consumed = false; }
            if (identity == null || !ready || consumed) return false;
            consumed = true;
            return tick >= cooldownUntil;
        }
        public void stowing(Object identity) {
            if (incoming == identity) { incoming = null; consumed = false; }
        }
        private void removed(long tick) {
            cooldownUntil = Math.max(cooldownUntil, tick + EnGardeProfile.provisionalCooldownTicks());
        }
    }
    private final Readiness readiness;
    private Object epoch = new Object();
    private long observed = -1, deadline = -1;
    private final ArrayDeque<Contact> contacts = new ArrayDeque<>();
    public EnGardeCycle() { this(new Readiness()); }
    public EnGardeCycle(Readiness readiness) { this.readiness = java.util.Objects.requireNonNull(readiness); }
    public static final class Contact {
        private final EnGardeCycle source;
        private final Object epoch;
        private final long tick;
        private final boolean active;
        private Contact(EnGardeCycle source, long tick) {
            this.source = source; epoch = source.epoch; this.tick = tick; active = source.remaining(tick) > 0;
        }
    }
    private boolean timeValid(long tick) {
        return tick >= 0 && tick >= observed && tick <= Long.MAX_VALUE - EnGardeProfile.durationTicks() - EnGardeProfile.provisionalCooldownTicks();
    }
    /** Call after readiness.observe; blocked handling never supplies newlyReady=true. */
    public void update(long tick, boolean held, boolean newlyReady) {
        if (!timeValid(tick)) { clear(); return; }
        observed = tick;
        if (deadline >= 0 && (tick >= deadline || !held)) {
            readiness.removed(Math.min(tick, deadline)); deadline = -1;
        }
        if (held && newlyReady && tick >= readiness.cooldownUntil) deadline = tick + EnGardeProfile.durationTicks();
    }
    public void stowing(long tick) { update(tick, false, false); }
    public int remaining(long tick) { return timeValid(tick) && tick < deadline ? (int)(deadline - tick) : 0; }
    public Contact capture(long tick) {
        if (!timeValid(tick)) { clear(); return null; }
        observed = tick;
        if (contacts.size() == CONTACT_LIMIT) contacts.removeFirst();
        var c = new Contact(this, tick); contacts.addLast(c); return c;
    }
    public boolean capturedActive(long tick, Contact c) {
        return timeValid(tick) && c != null && c.source == this && c.epoch == epoch
            && tick >= c.tick && contacts.contains(c) && c.active;
    }
    /** Source change removes its live buff, retains owner readiness/cooldown, revokes tokens. */
    public void changed(long tick) { stowing(tick); clear(); }
    public void clear() { epoch = new Object(); observed = deadline = -1; contacts.clear(); }
}
