package kim.biryeong.destiny.weapon;

import com.google.gson.Gson;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.*;

/** Pinned community hip-fire curves, evaluated with the selected item's official Range stat.
 * See art/weapons/w43/extraction.json. Distances map metres to blocks; damage remains Minecraft HP.
 * Not an ADS system, original damage calibration, or a claim of current exact Destiny balance. */
public final class WeaponBallistics {
    public static final double MAX_TRACE = 96;
    private record Formula(String id, double offsetStart, double vppStart, double offsetEnd,
                           double vppEnd, double floor, double precision) {}
    public record Profile(double start, double end, double floor, double precision) {
        public Profile {
            if (!Double.isFinite(start) || !Double.isFinite(end) || !Double.isFinite(floor)
                    || !Double.isFinite(precision) || start < 0 || end <= start
                    || floor <= 0 || floor > 1 || precision < 1 || precision > 5)
                throw new IllegalArgumentException("Unsafe ballistics profile");
        }
        public double falloff(double distance) {
            if (!Double.isFinite(distance)) return 0;
            if (distance <= start) return 1;
            if (distance >= end) return floor;
            return 1 - (1 - floor) * (distance - start) / (end - start);
        }
        public float damage(float base, double distance, boolean critical) {
            if (!Float.isFinite(base) || base <= 0) return 0;
            return (float)(base * falloff(distance) * (critical ? precision : 1));
        }
    }
    private static final Map<String,Formula> FORMULAS=new HashMap<>();
    private static final Map<String, Profile> ALL = load();
    private WeaponBallistics() {}
    private static Map<String, Profile> load() {
        var stream = WeaponBallistics.class.getResourceAsStream("/destiny/weapons/w43-ballistics.json");
        if (stream == null) throw new IllegalStateException("Missing W43 ballistics");
        try (var reader = new InputStreamReader(stream, StandardCharsets.UTF_8)) {
            Map<String, Profile> result = new LinkedHashMap<>();
            for (var f : WeaponExotics.append(new Gson().fromJson(reader, Formula[].class), "ballistics", Formula.class)) {
                var entry = WeaponCatalog.find(f.id()).orElseThrow();
                Integer range = WeaponCharacteristics.of(entry).stats().get("1240592695");
                // Bow/sword/explosive sentinel curves can be range-independent. Never silently
                // invent a Range stat for a curve that actually requires it.
                if (range == null && (f.vppStart != 0 || f.vppEnd != 0))
                    throw new IllegalStateException("Missing Range: " + f.id());
                int stat = range == null ? 0 : Math.clamp(range, 0, 100);
                var profile = new Profile(f.offsetStart + f.vppStart * stat,
                        f.offsetEnd + f.vppEnd * stat, f.floor, f.precision);
                if (result.putIfAbsent(f.id(), profile) != null) throw new IllegalStateException("Duplicate ballistics");
                FORMULAS.put(f.id(),f);
            }
            if (result.size() != WeaponCatalog.all().size()) throw new IllegalStateException("Incomplete ballistics");
            return Map.copyOf(result);
        } catch (java.io.IOException e) { throw new IllegalStateException(e); }
    }
    public static Profile of(WeaponCatalog.Entry entry) { return Objects.requireNonNull(ALL.get(entry.id())); }
    /** Sum legal bonuses first, clamp Range once, preserve range-independent sentinel curves. */
    public static Profile withRangeBonus(WeaponCatalog.Entry entry,int totalBonus) {
        if(totalBonus==0)return of(entry);
        var f=Objects.requireNonNull(FORMULAS.get(entry.id()));
        var range=WeaponCharacteristics.of(entry).stats().get("1240592695");
        if(range==null)return of(entry);
        int stat=(int)Math.clamp((long)range+totalBonus,0L,100L);
        return new Profile(f.offsetStart+f.vppStart*stat,f.offsetEnd+f.vppEnd*stat,f.floor,f.precision);
    }
    public static double traceRange(WeaponProfile profile) {
        return profile.mode() == WeaponProfile.Mode.MELEE || profile.blastRadius() > 0 ? profile.range() : MAX_TRACE;
    }
}
