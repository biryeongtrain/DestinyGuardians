package kim.biryeong.destiny.weapon;

import com.google.gson.Gson;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.*;

/** Base Handling stat + pinned historical community ready/stow curves, in 20 Hz ticks.
 * Unknown sword timing stays explicitly absent; this is not perk-modified D2 calibration. */
public record WeaponHandlingProfile(boolean supported, Integer handling, Integer readyTicks, Integer stowTicks) {
    private record Row(String id, WeaponHandlingProfile profile) {}
    private static final Map<String, WeaponHandlingProfile> ALL = load();
    public WeaponHandlingProfile {
        if (supported ? handling == null || handling < 0 || handling > 100
                || readyTicks == null || readyTicks < 1 || readyTicks > 1200
                || stowTicks == null || stowTicks < 1 || stowTicks > 1200
                : handling != null || readyTicks != null || stowTicks != null)
            throw new IllegalArgumentException("Unsafe handling profile");
    }
    public static WeaponHandlingProfile of(WeaponCatalog.Entry entry) {
        return Objects.requireNonNull(ALL.get(Objects.requireNonNull(entry).id()), "Unknown handling weapon");
    }
    private static Map<String, WeaponHandlingProfile> load() {
        var input = WeaponHandlingProfile.class.getResourceAsStream("/destiny/weapons/w58-handling.json");
        if (input == null) throw new IllegalStateException("Missing W58 handling");
        try (var reader = new InputStreamReader(input, StandardCharsets.UTF_8)) {
            Map<String, WeaponHandlingProfile> result = new HashMap<>();
            for (var row : WeaponExotics.append(new Gson().fromJson(reader, Row[].class), "handling", Row.class)) {
                var entry = WeaponCatalog.find(row.id()).orElseThrow();
                if (row.profile() == null || row.profile().supported() == entry.family().equals("sword")
                        || result.putIfAbsent(row.id(), row.profile()) != null)
                    throw new IllegalStateException("Invalid/duplicate W58 handling");
            }
            if (result.size() != WeaponCatalog.all().size()) throw new IllegalStateException("Incomplete W58 handling");
            return Map.copyOf(result);
        } catch (java.io.IOException e) { throw new IllegalStateException(e); }
    }
}
