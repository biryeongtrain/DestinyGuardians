package kim.biryeong.destiny.weapon;

import java.util.Collections;
import java.util.HashSet;
import java.util.IdentityHashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;

/** Pure single-charge credit calculation used by the actual final-blow path.
 * The caller supplies only valid registered, equipped, matching-class ability slots.
 */
public final class WeaponEnergyCredit {
    private WeaponEnergyCredit() {}
    public record Cooldown<S>(S slot, int fullTicks, int remainingTicks) {}

    /** Freeze the uncharged count before applying any credit. A small remainder never redirects
     * its unused share to another slot. Return changed cooldowns only; charged slots stay absent.
     */
    public static <S> Map<S, Integer> cooldowns(List<Cooldown<S>> abilities, int percent) {
        if (percent <= 0 || percent > 100) return Map.of();
        var uncharged = abilities.stream().filter(a -> a.slot != null && a.fullTicks > 0 && a.remainingTicks > 0).toList();
        if (uncharged.isEmpty()) return Map.of();
        var seen = new HashSet<S>();
        for (var ability : uncharged)
            if (!seen.add(ability.slot)) throw new IllegalArgumentException("Duplicate energy slot");
        long divisor = 100L * uncharged.size();
        var result = new LinkedHashMap<S, Integer>();
        for (var ability : uncharged) {
            // Single ceil AFTER the split, from FULL authored cooldown, never remaining cooldown.
            long grant = ((long) ability.fullTicks * percent + divisor - 1) / divisor;
            result.put(ability.slot, (int) Math.max(0, ability.remainingTicks - grant));
        }
        return Map.copyOf(result);
    }

    public static float superEnergy(float current, double percent) {
        if (!Float.isFinite(current) || !Double.isFinite(percent) || percent <= 0 || percent > 100) return current;
        return (float) Math.clamp(current + percent / 100, 0, 1);
    }

    /** Identity follows the actual corpse object, independent of mutable entity equality/state.
     * Each paid emission owns one ledger shared by direct and payload/splash callbacks.
     */
    public static final class Corpses<T> {
        private final Set<T> seen = Collections.newSetFromMap(new IdentityHashMap<>());
        public boolean admit(T corpse) { return corpse != null && seen.add(corpse); }
    }
}
