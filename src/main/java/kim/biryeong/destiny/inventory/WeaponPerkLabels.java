package kim.biryeong.destiny.inventory;

import com.google.gson.Gson;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.Map;

/** UI taxonomy only. Availability and actual gameplay remain owned by WeaponPerks. */
public final class WeaponPerkLabels {
    private record Label(String name, String description, boolean damage) {}
    private record Data(Map<String, Label> perks) {}
    private static final Map<String, Label> ALL = load();
    private WeaponPerkLabels() {}
    private static Map<String, Label> load() {
        var input = WeaponPerkLabels.class.getResourceAsStream("/destiny/weapons/w228-perks-ko.json");
        if (input == null) throw new IllegalStateException("Missing Korean perk labels");
        try (var reader = new InputStreamReader(input, StandardCharsets.UTF_8)) {
            return Map.copyOf(new Gson().fromJson(reader, Data.class).perks());
        } catch (java.io.IOException e) { throw new IllegalStateException(e); }
    }
    public static boolean damage(String id) { var label = ALL.get(id); return label != null && label.damage(); }
    public static String name(String id) { var label = ALL.get(id); return label == null ? id : label.name(); }
    public static String description(String id) { var label = ALL.get(id); return label == null ? "" : label.description(); }
}
