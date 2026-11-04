package kim.biryeong.destiny.weapon;

import java.util.*;

/** Actual-stack firing deadlines, never ammunition or pending shots. Expired entries are pruned.
 * Sword actor recovery is shared; ranged weapons do not inherit another ranged weapon's RPM.
 * The capacity fallback fails closed until its latest omitted deadline, never evicting a live lockout. */
public final class WeaponCadenceBank {
    public static final int CAPACITY = 128;
    private final Map<Object, Double> deadlines = new IdentityHashMap<>();
    private double actorUntil, overflowUntil;
    public void remember(Object stack, double deadline, long tick, boolean swordActor) {
        Objects.requireNonNull(stack);
        if (!Double.isFinite(deadline) || deadline < 0 || tick < 0 || deadline > tick + 1201d)
            throw new IllegalArgumentException("Unsafe cadence snapshot");
        deadlines.values().removeIf(value -> value <= tick);
        if (swordActor) { actorUntil = Math.max(actorUntil, deadline); return; }
        if (deadline <= tick) { deadlines.remove(stack); return; }
        if (deadlines.containsKey(stack) || deadlines.size() < CAPACITY) deadlines.put(stack, deadline);
        else overflowUntil = Math.max(overflowUntil, deadline);
    }
    /** Pure query; no wall-clock time, item mutation, scheduling, or rounding fractional cadence. */
    public double deadline(Object stack, long tick) {
        double result = Math.max(Math.max(deadlines.getOrDefault(stack, 0d), actorUntil), overflowUntil);
        return result > tick ? result : 0;
    }
    public int retainedClocks() { return deadlines.size(); }
}
