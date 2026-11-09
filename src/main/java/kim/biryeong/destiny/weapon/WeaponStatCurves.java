package kim.biryeong.destiny.weapon;

import com.google.gson.Gson;
import java.util.*;

/** Shared original Destiny stat curves (W46 formulas, w43 mapping, w40 base stats) for perks that
 * grant stat bonuses or duration multipliers. Scaling is a RATIO on the incoming duration, so it
 * composes with the existing perk chains: ticks = ceil(base * seconds(stat+bonus)/seconds(stat) * scalar).
 * Stats clamp to 0..100 (fractional bonuses are evaluated without rounding). Unknown weapons are neutral.
 */
public final class WeaponStatCurves {
    record Quadratic(double evpp, double vpp, double offset) {
        double seconds(double stat) { return evpp * stat * stat + vpp * stat + offset; }
    }
    record Curve(String id, long hash, String family, int baseHandlingStat, int baseReloadStat,
                 Quadratic reload, Quadratic ready, Quadratic stow, Quadratic ads) {}
    private record Data(String stage, String source, Curve[] curves) {}
    private static final Map<String, Curve> CURVES = load();
    private WeaponStatCurves() {}

    private static Map<String, Curve> load() {
        var data = new Gson().fromJson(BatchAPerkData.read("/destiny/weapons/w320-batch-a-curves.json"), Data.class);
        if (data == null || !"W320".equals(data.stage) || data.curves == null || data.curves.length == 0)
            throw new IllegalStateException("Invalid W320 stat curves");
        var result = new HashMap<String, Curve>();
        for (var c : WeaponExotics.appendExpansion(LegendaryWeapons.append(Arrays.asList(data.curves), "curves", Curve.class), "curves", Curve.class)) {
            if (c == null || c.id == null || result.putIfAbsent(c.id, c) != null || c.reload == null || c.ready == null
                || c.stow == null || c.ads == null || c.baseHandlingStat < 0 || c.baseHandlingStat > 100
                || c.baseReloadStat < 0 || c.baseReloadStat > 100)
                throw new IllegalStateException("Invalid W320 stat curve " + (c == null ? null : c.id));
            for (var q : List.of(c.reload, c.ready, c.stow, c.ads))
                for (int stat = 0; stat <= 100; stat++)
                    if (!(q.seconds(stat) > 0) || q.seconds(stat) > 60) throw new IllegalStateException("Unsafe curve " + c.id);
        }
        return Map.copyOf(result);
    }
    public static boolean supports(String id) { return CURVES.containsKey(id); }
    static double stat(int base, double bonus) { return Math.clamp(base + bonus, 0.0, 100.0); }
    /** Single ceil of the scaled duration; neutral input returns the base unchanged. */
    static int scale(int baseTicks, double ratio) {
        if (baseTicks <= 0 || !Double.isFinite(ratio) || ratio <= 0 || Math.abs(ratio - 1) < 1e-12) return baseTicks;
        return Math.max(1, (int) Math.ceil(baseTicks * ratio - 1e-9));
    }
    private static double ratio(Quadratic q, int base, double bonus, double scalar, boolean stowFloor) {
        double from = q.seconds(base), to = q.seconds(stat(base, bonus));
        if (stowFloor) { from = Math.max(from, q.seconds(100)); to = Math.max(to, q.seconds(100)); }
        return to / from * scalar;
    }
    public static int handlingTicks(String id, boolean ready, int baseTicks, double bonus, double scalar) {
        var c = CURVES.get(id);
        if (c == null || (bonus == 0 && scalar == 1)) return baseTicks;
        return scale(baseTicks, ratio(ready ? c.ready : c.stow, c.baseHandlingStat, bonus, scalar, !ready));
    }
    public static int adsTicks(String id, int baseTicks, double bonus, double scalar) {
        var c = CURVES.get(id);
        if (c == null || (bonus == 0 && scalar == 1)) return baseTicks;
        return Math.max(Math.min(baseTicks, 2), scale(baseTicks, ratio(c.ads, c.baseHandlingStat, bonus, scalar, false)));
    }
    public static int reloadTicks(String id, int baseTicks, double bonus, double scalar) {
        var c = CURVES.get(id);
        if (c == null || (bonus == 0 && scalar == 1)) return baseTicks;
        return scale(baseTicks, ratio(c.reload, c.baseReloadStat, bonus, scalar, false));
    }
}
