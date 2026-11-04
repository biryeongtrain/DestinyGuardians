package kim.biryeong.destiny.weapon;

import com.google.gson.Gson;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.*;

/** Sourced normal-bow perfect-window clock; informational, not a late-shot damage model.
 * Oracle's community formula is pinned in W74; Bungie corroborates lightweight endpoints.
 * Ceil to 20 TPS; interval starts at the accepted full draw and is half open.
 * Neither arbitrary max hold nor damage/accuracy decay is inferred from this window.
 */
public final class WeaponBowWindow {
    public enum Phase { IDLE, DRAWING, PERFECT, LATE }
    public record State(Phase phase, float progress, int windowTicks, long fullDrawAge) { }
    private record Row(String id, long hash, String frame, int stability, int windowMicros, int windowTicks) { }
    private record Data(String stage, List<Row> weapons) { }
    private static final State IDLE = new State(Phase.IDLE, 0, 0, -1);
    private static final Map<String, Row> ROWS = load();
    private WeaponBowWindow() { }

    /** Exact integer microseconds avoid a floating-point ceil error on whole-tick endpoints. */
    public static int windowMicros(String frame, int stability) {
        int s = Math.clamp(stability, 0, 100);
        return switch (frame) {
            case "precision" -> 300_000 + 2_500 * s;
            case "lightweight" -> 500_000 + 3_000 * s;
            default -> throw new IllegalArgumentException("Unsupported normal bow frame: " + frame);
        };
    }
    private static Map<String, Row> load() {
        var stream = WeaponBowWindow.class.getResourceAsStream("/destiny/weapons/w74-bow-window.json");
        if (stream == null) throw new IllegalStateException("Missing W74 bow window data");
        try (var reader = new InputStreamReader(stream, StandardCharsets.UTF_8)) {
            Data data = new Gson().fromJson(reader, Data.class);
            if (!"W74".equals(data.stage()) || data.weapons() == null) throw new IllegalStateException("Invalid W74 data");
            Map<String, Row> result = new LinkedHashMap<>();
            for (Row r : data.weapons()) {
                var e = WeaponCatalog.find(r.id()).orElseThrow();
                var official = WeaponCharacteristics.of(e);
                int micros = windowMicros(r.frame(), r.stability());
                if (!e.family().equals("bow") || !e.frame().equals(r.frame()) || official.bungieHash() != r.hash()
                        || !Objects.equals(official.stats().get("155624089"), r.stability())
                        || r.windowMicros() != micros || r.windowTicks() != (micros + 49_999) / 50_000
                        || result.putIfAbsent(r.id(), r) != null)
                    throw new IllegalStateException("Invalid bow window: " + r.id());
            }
            if (!result.keySet().equals(WeaponCatalog.family("bow").stream().map(WeaponCatalog.Entry::id)
                    .collect(java.util.stream.Collectors.toSet()))) throw new IllegalStateException("Incomplete W74 normal bows");
            return Map.copyOf(result);
        } catch (java.io.IOException e) { throw new IllegalStateException(e); }
    }
    public static State idle() { return IDLE; }
    public static int windowTicks(WeaponCatalog.Entry entry) {
        Row row = ROWS.get(entry.id());
        if (row == null || !entry.equals(WeaponCatalog.find(row.id()).orElseThrow()))
            throw new IllegalArgumentException("Not a supported normal bow");
        return row.windowTicks();
    }
    public static State state(WeaponCatalog.Entry entry, int acceptedDrawTicks, long elapsed) {
        return state(entry, acceptedDrawTicks, elapsed, 0);
    }
    /** A live stat bonus changes only the existing informational stability window, never draw/damage. */
    public static State state(WeaponCatalog.Entry entry, int acceptedDrawTicks, long elapsed, int stabilityBonus) {
        int window = windowTicks(entry);
        if (stabilityBonus < 0 || stabilityBonus > 100) throw new IllegalArgumentException("Unsafe stability bonus");
        if (stabilityBonus > 0) {
            Row row = ROWS.get(entry.id());
            int micros = windowMicros(row.frame(), Math.min(100, row.stability() + stabilityBonus));
            window = (micros + 49_999) / 50_000;
        }
        if (acceptedDrawTicks < 1 || acceptedDrawTicks > 1200) throw new IllegalArgumentException("Invalid accepted draw duration");
        if (elapsed < 0) return IDLE;
        if (elapsed < acceptedDrawTicks)
            return new State(Phase.DRAWING, elapsed / (float) acceptedDrawTicks, window, -1);
        long age = elapsed - acceptedDrawTicks;
        return new State(age < window ? Phase.PERFECT : Phase.LATE, 1, window, age);
    }
}
