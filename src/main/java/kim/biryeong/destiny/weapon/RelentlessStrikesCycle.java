package kim.biryeong.destiny.weapon;

import java.util.ArrayDeque;
import java.util.Collections;
import java.util.IdentityHashMap;
import java.util.Set;

/** Source epoch and bounded paid-contact ledger. All mutations are main-server-thread owned. */
public final class RelentlessStrikesCycle {
    private static final int CONTACT_LIMIT = 128, TARGET_LIMIT = 256;
    private Object epoch = new Object();
    private long observed = -1;
    private int progress;
    private final ArrayDeque<Contact> contacts = new ArrayDeque<>();
    private long lastHit = -1;
    public static final class Contact {
        private final RelentlessStrikesCycle source;
        private final Object epoch;
        private final long acceptedTick;
        private final Set<Object> targets = Collections.newSetFromMap(new IdentityHashMap<>());
        private Contact(RelentlessStrikesCycle source, long tick) {
            this.source = source; epoch = source.epoch; acceptedTick = tick;
        }
    }
    private boolean timeValid(long tick) { return tick >= 0 && tick >= observed; }
    public Contact capture(long tick) {
        if (!timeValid(tick)) { clear(); return null; }
        update(tick);
        if (contacts.size() == CONTACT_LIMIT) contacts.removeFirst();
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
    /** Only positive actual HP/absorption loss from a paid sword contact is a hit.
     * Each successive gap is inclusive, rather than a first-to-third window. */
    public int confirmed(long tick, Contact contact, Object target, double actualLoss) {
        if (!Double.isFinite(actualLoss) || actualLoss <= 0 || !accept(tick, contact, target)) return 0;
        if (lastHit >= 0 && tick - lastHit > RelentlessStrikesProfile.windowTicks()) progress = 0;
        lastHit = tick;
        if (++progress < RelentlessStrikesProfile.hits()) return 0;
        progress = 0; lastHit = -1;
        return RelentlessStrikesProfile.returnRounds();
    }
    /** Pure count: no event acceptance, epoch creation, ammo grant, or state change. */
    public int progress(long tick) { return timeValid(tick) && (lastHit < 0 || tick - lastHit <= RelentlessStrikesProfile.windowTicks()) ? progress : 0; }
    public void update(long tick) {
        if (!timeValid(tick)) { clear(); return; }
        if (lastHit >= 0 && tick - lastHit > RelentlessStrikesProfile.windowTicks()) { progress = 0; lastHit = -1; }
        observed = tick;
    }
    public void clear() {
        epoch = new Object(); contacts.clear(); observed = -1; progress = 0;
        lastHit = -1;
    }
}
