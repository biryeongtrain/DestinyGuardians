package kim.biryeong.destiny.weapon;

import java.util.*;

/** Bait and Switch damage chain. Keys are weapon identities (the runtime uses ItemStack objects).
 * Each damage instance must follow the previous one within the chain window; once every equipped
 * weapon has dealt damage in one chain, the buff starts. While active the chain timer is disabled
 * and the buff cannot be refreshed. Persists through stow.
 */
public final class BaitAndSwitchCycle {
    private final TimedBuffCycle buff = new TimedBuffCycle();
    private final Set<Object> chain = Collections.newSetFromMap(new IdentityHashMap<>());
    private long last = Long.MIN_VALUE;
    /** @return true on the tick the buff activates. equipped must contain every equipped weapon key. */
    public boolean damaged(long now, Object weapon, Collection<?> equipped, int chainTicks, int duration) {
        if (buff.active(now)) return false;
        if (last == Long.MIN_VALUE || now < last || now - last > chainTicks) chain.clear();
        last = now;
        if (!containsIdentity(equipped, weapon)) return false;
        chain.add(weapon);
        if (equipped.isEmpty()) return false;
        for (var e : equipped) if (!chain.contains(e)) return false;
        buff.activate(now, duration);
        chain.clear();
        last = Long.MIN_VALUE;
        return true;
    }
    private static boolean containsIdentity(Collection<?> all, Object o) {
        for (var e : all) if (e == o) return true;
        return false;
    }
    public boolean active(long now) { return buff.active(now); }
    public long remaining(long now) { return buff.remaining(now); }
}
