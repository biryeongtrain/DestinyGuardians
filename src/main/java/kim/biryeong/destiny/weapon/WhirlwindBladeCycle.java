package kim.biryeong.destiny.weapon;

import java.util.ArrayDeque;
import java.util.Collections;
import java.util.IdentityHashMap;
import java.util.Set;

/** Paid contact snapshots and a separate live stack epoch. Queries never advance either. */
public final class WhirlwindBladeCycle {
    private static final int CONTACT_LIMIT = 128, TARGET_LIMIT = 256;
    private Object epoch = new Object(), liveEpoch = new Object();
    private long observed = -1, deadline = -1;
    private int stacks;
    private final ArrayDeque<Contact> contacts = new ArrayDeque<>();
    public static final class Contact {
        private final WhirlwindBladeCycle source;
        private final Object epoch, liveEpoch;
        private final long tick;
        private final int stacks;
        private final Set<Object> targets = Collections.newSetFromMap(new IdentityHashMap<>());
        private Contact(WhirlwindBladeCycle source, long tick) {
            this.source = source; epoch = source.epoch; liveEpoch = source.liveEpoch;
            this.tick = tick; stacks = source.stacks(tick);
        }
    }
    private boolean timeValid(long tick) { return tick >= 0 && tick >= observed && tick <= Long.MAX_VALUE - WhirlwindBladeProfile.durationTicks(); }
    private boolean valid(long tick, Contact c) {
        return timeValid(tick) && c != null && c.source == this && c.epoch == epoch
            && tick >= c.tick && contacts.contains(c);
    }
    public Contact capture(long tick) {
        if (!timeValid(tick)) { clear(); return null; }
        update(tick, true);
        if (contacts.size() == CONTACT_LIMIT) contacts.removeFirst();
        var c = new Contact(this, tick); contacts.addLast(c); return c;
    }
    public int stacks(long tick) { return timeValid(tick) && tick < deadline ? stacks : 0; }
    public int remaining(long tick) { return stacks(tick) > 0 ? (int)(deadline - tick) : 0; }
    public int capturedStacks(long tick, Contact c) { return valid(tick, c) ? c.stacks : 0; }
    /** Actual positive loss only; one target can advance at most once per shared paid contact. */
    public boolean confirmed(long tick, Contact c, Object target, float actualLoss, boolean held) {
        if (!valid(tick, c) || target == null || !Float.isFinite(actualLoss) || actualLoss <= 0
            || c.targets.size() >= TARGET_LIMIT || !c.targets.add(target)) return false;
        observed = tick;
        if (!held || c.liveEpoch != liveEpoch) return false;
        stacks = Math.min(WhirlwindBladeProfile.maxStacks(), stacks(tick) + 1);
        deadline = tick + WhirlwindBladeProfile.durationTicks();
        return true;
    }
    public void update(long tick, boolean held) {
        if (!timeValid(tick)) { clear(); return; }
        observed = tick;
        if (!held) resetLive(tick);
        else if (tick >= deadline) { stacks = 0; deadline = -1; }
    }
    public void stowing(long tick) { resetLive(tick); }
    public void blocking(long tick) { resetLive(tick); }
    private void resetLive(long tick) {
        if (!timeValid(tick)) { clear(); return; }
        observed = tick; stacks = 0; deadline = -1; liveEpoch = new Object();
    }
    /** Source edit/lifecycle revokes already-paid authority; ordinary live resets do not. */
    public void clear() {
        epoch = new Object(); liveEpoch = new Object(); contacts.clear();
        stacks = 0; observed = deadline = -1;
    }
}
