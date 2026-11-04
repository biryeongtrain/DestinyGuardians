package kim.biryeong.destiny.weapon;

import com.google.gson.Gson;
import java.io.IOException;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.HashMap;
import java.util.Map;
import java.util.Objects;
import java.util.stream.Collectors;

/**
 * W44 base-item ADS data: official W40 stats plus pinned community handling curves.
 * Zoom is visual magnification; falloffScalar independently scales ADS falloff distances.
 * Stability retains the official 0..100 stat. RecoilDirection is metadata only: no exact
 * recoil pattern is reconstructed. Kick is degrees; bloom is dimensionless (0..1) and
 * recovery is normalized bloom/tick. All three are bounded Minecraft tuning.
 * See art/weapons/w44/extraction.json.
 */
public record WeaponAimProfile(int transitionTicks, float zoom, float falloffScalar,
                               float stability, int recoilDirection, float kick,
                               float bloomPerShot, float recoveryPerTick) {
    private static final WeaponAimProfile NEUTRAL =
            new WeaponAimProfile(2, 1, 1, 0, 0, 0, 0, 0);
    private static final Map<String, WeaponAimProfile> ALL = load();
    private record Definition(String id, WeaponAimProfile profile) {}

    public WeaponAimProfile {
        if (transitionTicks < 2 || transitionTicks > 20
                || !Float.isFinite(zoom) || zoom < 1 || zoom > 6
                || !Float.isFinite(falloffScalar) || falloffScalar < 1 || falloffScalar > 6
                || !Float.isFinite(stability) || stability < 0 || stability > 100
                || recoilDirection < 0 || recoilDirection > 100
                || !Float.isFinite(kick) || kick < 0 || kick > 2
                || !Float.isFinite(bloomPerShot) || bloomPerShot < 0 || bloomPerShot > .2f
                || !Float.isFinite(recoveryPerTick) || recoveryPerTick < 0 || recoveryPerTick > 1) {
            throw new IllegalArgumentException("Unsafe W44 aim profile");
        }
    }

    /** Every catalog entry has data; swords/glaives return a neutral profile. */
    public static WeaponAimProfile of(WeaponCatalog.Entry entry) {
        Objects.requireNonNull(entry, "entry");
        var profile = ALL.get(entry.id());
        if (profile == null) throw new IllegalArgumentException("Unknown W44 weapon: " + entry.id());
        return profile;
    }

    /** Unsupported swords/glaives have no ADS or recoil tuning. Null/unknown entries are unsupported. */
    public static boolean supports(WeaponCatalog.Entry entry) {
        return entry != null && ranged(entry) && ALL.containsKey(entry.id());
    }

    private static boolean ranged(WeaponCatalog.Entry entry) {
        return !"sword".equals(entry.family()) && !"glaive".equals(entry.family());
    }

    private static Map<String, WeaponAimProfile> load() {
        var stream = WeaponAimProfile.class.getResourceAsStream("/destiny/weapons/w44-aim.json");
        if (stream == null) throw new IllegalStateException("Missing W44 aim profiles");
        try (var reader = new InputStreamReader(stream, StandardCharsets.UTF_8)) {
            var definitions = WeaponExotics.append(new Gson().fromJson(reader, Definition[].class), "aim", Definition.class);
            if (definitions == null) throw new IllegalStateException("Empty W44 aim profiles");
            Map<String, WeaponAimProfile> result = new HashMap<>();
            for (var definition : definitions) {
                if (definition == null || definition.id() == null || definition.profile() == null)
                    throw new IllegalStateException("Invalid W44 aim definition");
                var entry = WeaponCatalog.find(definition.id()).orElseThrow(
                        () -> new IllegalStateException("Unknown W44 weapon: " + definition.id()));
                var profile = definition.profile();
                if (ranged(entry)) {
                    if (profile.kick() < .1f || profile.bloomPerShot() < .02f
                            || profile.recoveryPerTick() != .04f)
                        throw new IllegalStateException("Missing ranged aim tuning: " + entry.id());
                } else if (!NEUTRAL.equals(profile)) {
                    throw new IllegalStateException("Nonneutral unsupported aim profile: " + entry.id());
                }
                if (result.putIfAbsent(definition.id(), profile) != null)
                    throw new IllegalStateException("Duplicate W44 aim profile: " + definition.id());
            }
            if (!result.keySet().equals(WeaponCatalog.all().stream()
                    .map(WeaponCatalog.Entry::id).collect(Collectors.toSet())))
                throw new IllegalStateException("Incomplete W44 aim catalog");
            return Map.copyOf(result);
        } catch (IOException e) {
            throw new IllegalStateException("Unreadable W44 aim profiles", e);
        }
    }
}
