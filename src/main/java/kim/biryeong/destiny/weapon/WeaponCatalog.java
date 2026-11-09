package kim.biryeong.destiny.weapon;

import com.google.gson.Gson;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.*;

/** Curated visual prototypes, not damage/RPM balance definitions or exotic traits. */
public final class WeaponCatalog {
    public record Entry(String id, String family, String frame, String name,
                        String source_frame_label, String item_model) {}
    private static final List<Entry> ALL = load();
    private static final Map<String, Entry> BY_ID;
    static {
        Map<String, Entry> entries = new LinkedHashMap<>();
        for (Entry e : ALL) {
            if (e.id() == null || !e.id().matches("[a-z0-9_]+") || e.name() == null
                    || e.name().isBlank() || e.family() == null || e.frame() == null
                    || !Objects.equals(e.item_model(), "destiny:weapon/" + e.id())
                    || entries.putIfAbsent(e.id(), e) != null) {
                throw new IllegalStateException("Invalid/duplicate weapon catalog entry: " + e);
            }
        }
        BY_ID = Collections.unmodifiableMap(entries);
    }
    private WeaponCatalog() {}
    private static List<Entry> load() {
        var stream = WeaponCatalog.class.getResourceAsStream("/destiny/weapons/w30.json");
        if (stream == null) throw new IllegalStateException("Missing W30 weapon catalog");
        try (var reader = new InputStreamReader(stream, StandardCharsets.UTF_8)) {
            return WeaponExotics.append(new Gson().fromJson(reader, Entry[].class), "catalog", Entry.class);
        } catch (java.io.IOException e) {
            throw new IllegalStateException("Unreadable weapon catalog", e);
        }
    }
    public static List<Entry> all() { return ALL; }
    public static Optional<Entry> find(String id) { return Optional.ofNullable(BY_ID.get(id)); }
    public static List<Entry> family(String family) {
        return ALL.stream().filter(e -> e.family().equals(family)).toList();
    }
}
