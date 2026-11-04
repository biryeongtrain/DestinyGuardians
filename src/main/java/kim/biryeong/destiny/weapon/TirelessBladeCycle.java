package kim.biryeong.destiny.weapon;

import java.util.ArrayDeque;
import java.util.Collections;
import java.util.IdentityHashMap;
import java.util.Set;

/** Source epoch and bounded paid-contact ledger. All mutations are main-server-thread owned. */
public final class TirelessBladeCycle {
    private static final int CONTACT_LIMIT = 128, TARGET_LIMIT = 256;
    private Object epoch = new Object();
    private long observed = -1;
    private int progress;
    private final ArrayDeque<Contact> contacts = new ArrayDeque<>();
    /** One entitlement per player lifecycle, shared across distinct source swords.
     * Source clear/edit/cleanup must retain this object; only an actual new life replaces it. */
    public static final class Spawn {
        private boolean firstAvailable = true;
    }
    private final Spawn spawn;
    public TirelessBladeCycle() { this(new Spawn()); }
    public TirelessBladeCycle(Spawn spawn) { this.spawn = java.util.Objects.requireNonNull(spawn); }
    private final Set<Object> killedTargets = Collections.newSetFromMap(new IdentityHashMap<>());
    public static final class Contact {
        private final TirelessBladeCycle source;
        private final Object epoch;
        private final long acceptedTick;
        private final Set<Object> targets = Collections.newSetFromMap(new IdentityHashMap<>());
        private Contact(TirelessBladeCycle source, long tick) {
            this.source = source; epoch = source.epoch; acceptedTick = tick;
        }
    }
    private boolean timeValid(long tick) { return tick >= 0 && tick >= observed; }
    public Contact capture(long tick) {
        if (!timeValid(tick)) { clear(); return null; }
        update(tick);
        if (contacts.size() == CONTACT_LIMIT) {
            contacts.removeFirst();
            killedTargets.clear();
            for (var c : contacts) killedTargets.addAll(c.targets);
        }
        var contact = new Contact(this, tick);
        contacts.addLast(contact);
        return contact;
    }
    private boolean accept(long tick, Contact contact, Object target) {
        if (!timeValid(tick)) { clear(); return false; }
        if (contact == null || contact.source != this || contact.epoch != epoch
            || tick < contact.acceptedTick || !contacts.contains(contact) || target == null
            || contact.targets.size() >= TARGET_LIMIT || contact.targets.contains(target)) return false;
        observed = tick;
        contact.targets.add(target);
        return true;
    }
    /** Master calls only after attributable positive-loss final blows, never generic death.
     * A retained corpse cannot count under another paid contact either. */
    public int killed(long tick, Contact contact, Object target) {
        if (!timeValid(tick)) { clear(); return 0; }
        if (killedTargets.contains(target) || !accept(tick, contact, target)) return 0;
        killedTargets.add(target);
        if (spawn.firstAvailable) {
            spawn.firstAvailable = false; progress = 0;
            return TirelessBladeProfile.returnRounds();
        }
        if (++progress < TirelessBladeProfile.kills()) return 0;
        progress = 0;
        return TirelessBladeProfile.returnRounds();
    }
    /** Pure count: no event acceptance, epoch creation, ammo grant, or state change. */
    public int progress(long tick) { return timeValid(tick) ? progress : 0; }
    public void update(long tick) {
        if (!timeValid(tick)) { clear(); return; }
        observed = tick;
    }
    public void clear() {
        epoch = new Object(); contacts.clear(); observed = -1; progress = 0;
        killedTargets.clear(); // Deliberately does not rearm spawn.firstAvailable.
    }
}
