package kim.biryeong.destiny.weapon;

import com.google.gson.Gson;
import java.io.IOException;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.HashMap;
import java.util.Map;
import java.util.Objects;
import java.util.OptionalDouble;
import java.util.OptionalInt;
import java.util.stream.Collectors;

/** Pure W46 base timing data; no live-stack, perks, ammo mutation or scheduling.
 * Official W40 stats and historical community curves have independent provenance.
 * See art/weapons/w46/README.md for units, missing values and reload limitations.
 */
public final class WeaponTiming {
    private WeaponTiming() {}

    /**
     * Cadence is fractional 20 Hz FIRING LOCKOUT measured after the first bolt.
     * For fusion/LFR it includes bolt span + recovery, EXCLUDES the next charge;
     * callers apply chargeTicks separately. Normal cadence is 1200/official RPM;
     * pulse/burst-sidearm cadence uses verified end delay + within-burst span.
     * Charge/draw are ceil(official milliseconds/50). Reload durations are ceil
     * of historical approximate curve seconds*20, NOT the Reload Speed stat.
     * Shell classification is a gameplay assumption, not established by the
     * Oracle quadratic; exposes per-round model duration, initial delay unknown.
     * supported=false swords retain magazine-as-ammo-capacity but no timing.
     */
    public record Timing(boolean supported, OptionalInt magazine, OptionalInt rpm,
                         OptionalInt chargeMillis, OptionalInt drawMillis,
                         OptionalDouble cadenceTicks, OptionalDouble burstSpacingTicks,
                         int burstSize, boolean sharedBurstAmmo,
                         OptionalInt chargeTicks, OptionalInt drawTicks,
                         OptionalInt reloadTicks, boolean shellReload,
                         OptionalInt reloadPerRoundTicks, OptionalInt reloadInitialTicks) {
        public Timing {
            for (var value : new OptionalInt[]{magazine, rpm, chargeMillis, drawMillis,
                    chargeTicks, drawTicks, reloadTicks, reloadPerRoundTicks, reloadInitialTicks}) {
                Objects.requireNonNull(value, "optional timing");
                if (value.isPresent() && value.getAsInt() <= 0)
                    throw new IllegalArgumentException("Nonpositive W46 timing");
            }
            Objects.requireNonNull(cadenceTicks, "cadenceTicks");
            Objects.requireNonNull(burstSpacingTicks, "burstSpacingTicks");
            if (cadenceTicks.isPresent() && (!Double.isFinite(cadenceTicks.getAsDouble())
                    || cadenceTicks.getAsDouble() <= 0)
                    || burstSpacingTicks.isPresent() && (!Double.isFinite(burstSpacingTicks.getAsDouble())
                    || burstSpacingTicks.getAsDouble() < 0)
                    || burstSize < 1 || burstSize > 9
                    || shellReload && reloadTicks.isPresent()
                    || !shellReload && (reloadPerRoundTicks.isPresent() || reloadInitialTicks.isPresent())
                    || chargeMillis.isPresent() != chargeTicks.isPresent()
                    || drawMillis.isPresent() != drawTicks.isPresent())
                throw new IllegalArgumentException("Unsafe W46 timing");
            if (chargeMillis.isPresent() && chargeTicks.getAsInt() != (chargeMillis.getAsInt() + 49L) / 50
                    || drawMillis.isPresent() && drawTicks.getAsInt() != (drawMillis.getAsInt() + 49L) / 50)
                throw new IllegalArgumentException("W46 charge/draw tick conversion drift");
        }
    }

    private record Raw(boolean supported, Integer magazine, Integer rpm,
                       Integer chargeMillis, Integer drawMillis,
                       Double cadenceTicks, Double burstSpacingTicks,
                       int burstSize, boolean sharedBurstAmmo,
                       Integer chargeTicks, Integer drawTicks,
                       Integer reloadTicks, boolean shellReload,
                       Integer reloadPerRoundTicks, Integer reloadInitialTicks) {
        Timing timing() {
            return new Timing(supported, optional(magazine), optional(rpm), optional(chargeMillis),
                    optional(drawMillis), optional(cadenceTicks), optional(burstSpacingTicks),
                    burstSize, sharedBurstAmmo, optional(chargeTicks), optional(drawTicks),
                    optional(reloadTicks), shellReload, optional(reloadPerRoundTicks), optional(reloadInitialTicks));
        }
    }
    private record Definition(String id, Raw timing) {}
    private static final Map<String, Timing> ALL = load();

    /** Every selected catalog ID resolves, including explicitly unsupported swords. */
    public static Timing forEntry(WeaponCatalog.Entry entry) {
        Objects.requireNonNull(entry, "entry");
        var result = ALL.get(entry.id());
        if (result == null) throw new IllegalArgumentException("Unknown W46 weapon: " + entry.id());
        return result;
    }

    public static Timing of(WeaponCatalog.Entry entry) { return forEntry(entry); }

    private static OptionalInt optional(Integer value) {
        return value == null ? OptionalInt.empty() : OptionalInt.of(value);
    }
    private static OptionalDouble optional(Double value) {
        return value == null ? OptionalDouble.empty() : OptionalDouble.of(value);
    }

    private static Map<String, Timing> load() {
        var stream = WeaponTiming.class.getResourceAsStream("/destiny/weapons/w46-timing.json");
        if (stream == null) throw new IllegalStateException("Missing W46 timing profiles");
        try (var reader = new InputStreamReader(stream, StandardCharsets.UTF_8)) {
            var definitions = WeaponExotics.append(new Gson().fromJson(reader, Definition[].class), "timing", Definition.class);
            if (definitions == null) throw new IllegalStateException("Empty W46 timing profiles");
            Map<String, Timing> result = new HashMap<>();
            for (var row : definitions) {
                if (row == null || row.id() == null || row.timing() == null)
                    throw new IllegalStateException("Invalid W46 timing row");
                var entry = WeaponCatalog.find(row.id()).orElseThrow(
                        () -> new IllegalStateException("Unknown W46 weapon: " + row.id()));
                var timing = row.timing().timing();
                if (timing.supported() == "sword".equals(entry.family()))
                    throw new IllegalStateException("W46 support mismatch: " + row.id());
                if (result.putIfAbsent(row.id(), timing) != null)
                    throw new IllegalStateException("Duplicate W46 weapon: " + row.id());
            }
            if (!result.keySet().equals(WeaponCatalog.all().stream()
                    .map(WeaponCatalog.Entry::id).collect(Collectors.toSet())))
                throw new IllegalStateException("Incomplete W46 timing catalog");
            return Map.copyOf(result);
        } catch (IOException e) {
            throw new IllegalStateException("Unreadable W46 timing profiles", e);
        }
    }
}
