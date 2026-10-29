package kim.biryeong.destiny.weapon;

import com.google.gson.Gson;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.*;

/** Relative ADS ratios from pinned original Data Compendium exports, not absolute D2 locomotion.
 * W244 keeps these sourced base ratios, then separately applies the user's native-zoom movement policy.
 * The historical Shift neutralizer is retained as a pure W75 reference only; live ADS leaves crouch untouched.
 * Precision HC's 0.775 is derived from a 10% reduction of the ordinary 0.25 penalty.
 */
public final class WeaponAimMovementProfile {
    public static final double NATIVE_SNEAK_BASE = .3;
    private record Row(String id, double scalar, String rule) { }
    private record Data(String stage, List<Row> weapons) { }
    private static final Map<String, Row> ROWS = load();
    private WeaponAimMovementProfile() { }

    private static Map<String, Row> load() {
        var stream = WeaponAimMovementProfile.class.getResourceAsStream("/destiny/weapons/w75-aim-movement.json");
        if (stream == null) throw new IllegalStateException("Missing W75 aim movement data");
        try (var reader = new InputStreamReader(stream, StandardCharsets.UTF_8)) {
            Data d = new Gson().fromJson(reader, Data.class);
            if (!"W75".equals(d.stage()) || d.weapons() == null) throw new IllegalStateException("Invalid W75 data");
            Map<String, Row> result = new LinkedHashMap<>();
            for (Row r : WeaponExotics.append(d.weapons().toArray(Row[]::new), "aimMovement", Row.class)) {
                var e = WeaponCatalog.find(r.id()).orElseThrow();
                String rule = e.family().equals("sidearm") ? "sidearm"
                        : e.family().equals("hand_cannon") && e.frame().equals("precision") ? "precision_hand_cannon" : "ordinary";
                double scalar = switch (rule) { case "sidearm" -> .85; case "precision_hand_cannon" -> .775; default -> .75; };
                if (!WeaponAimProfile.supports(e) || !rule.equals(r.rule()) || r.scalar() != scalar
                        || result.putIfAbsent(r.id(), r) != null) throw new IllegalStateException("Invalid W75 row: " + r.id());
            }
            if (!result.keySet().equals(WeaponCatalog.all().stream().filter(WeaponAimProfile::supports)
                    .map(WeaponCatalog.Entry::id).collect(java.util.stream.Collectors.toSet())))
                throw new IllegalStateException("Incomplete W75 ADS movement");
            return Map.copyOf(result);
        } catch (java.io.IOException e) { throw new IllegalStateException(e); }
    }
    public static double scalar(WeaponCatalog.Entry e) {
        Row r = ROWS.get(e.id());
        if (r == null || !e.equals(WeaponCatalog.find(r.id()).orElseThrow()))
            throw new IllegalArgumentException("Unsupported ADS weapon");
        return r.scalar();
    }
    public static double neutralizerAmount() { return 1 / NATIVE_SNEAK_BASE - 1; }
    public static double modifierAmount(double scalar) {
        if (!Double.isFinite(scalar) || scalar <= 0 || scalar > 1)
            throw new IllegalArgumentException("Invalid relative ADS scalar");
        return scalar - 1;
    }
}
