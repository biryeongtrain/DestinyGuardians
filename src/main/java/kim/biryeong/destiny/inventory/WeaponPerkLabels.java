package kim.biryeong.destiny.inventory;

import com.google.gson.Gson;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.Map;

/** UI taxonomy only. Availability and actual gameplay remain owned by WeaponPerks. */
public final class WeaponPerkLabels {
    private record Label(String name, String description, boolean damage) {}
    private record Data(Map<String, Label> perks) {}
    private static final java.util.List<String> SOURCES = java.util.List.of("/destiny/weapons/w228-perks-ko.json",
            "/destiny/weapons/w323-batch-d-ko.json", // W323 batch D
            "/destiny/weapons/w320-perks-ko-a.json", // W320 batch A
            "/destiny/weapons/w322-batch-c-ko.json"); // W322 batch C
    private static final Map<String, Label> ALL = load();
    private WeaponPerkLabels() {}
    private static Map<String, Label> load() {
        var all = new java.util.HashMap<String, Label>();
        for (var path : SOURCES) {
            var input = WeaponPerkLabels.class.getResourceAsStream(path);
            if (input == null) throw new IllegalStateException("Missing Korean perk labels " + path);
            try (var reader = new InputStreamReader(input, StandardCharsets.UTF_8)) {
                for (var e : new Gson().fromJson(reader, Data.class).perks().entrySet())
                    if (all.putIfAbsent(e.getKey(), e.getValue()) != null) throw new IllegalStateException("Duplicate perk label " + e.getKey());
            } catch (java.io.IOException e) { throw new IllegalStateException(e); }
        }
        return Map.copyOf(all);
    }
    public static boolean damage(String id) { var extra = kim.biryeong.destiny.weapon.LegendaryPerks.trait(id); var label = extra != null && extra.added() ? new Label(extra.name(), extra.description(), extra.damage()) : ALL.get(id); return label != null && label.damage(); }
    public static String name(String id) { var extra = kim.biryeong.destiny.weapon.LegendaryPerks.trait(id); var label = extra != null && extra.added() ? new Label(extra.name(), extra.description(), extra.damage()) : ALL.get(id); return label == null ? id : label.name(); }
    public static String description(String id) { var extra = kim.biryeong.destiny.weapon.LegendaryPerks.trait(id); var label = extra != null && extra.added() ? new Label(extra.name(), extra.description(), extra.damage()) : ALL.get(id); return label == null ? "" : label.description(); }
}
