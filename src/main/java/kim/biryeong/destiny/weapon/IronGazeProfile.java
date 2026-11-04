package kim.biryeong.destiny.weapon;

import com.google.gson.Gson;
import java.io.IOException;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.List;

/** BASIC DDC Weapon Perks row127. Aim Assist is source-only, with no simulated spread effect.
 * Class initialization reads JSON only; canonical registry checks occur lazily in supports. */
public final class IronGazeProfile {
    public static final String ID = "iron_gaze";
    public static final long HASH = 4152709778L;
    private record Perk(String id, long hash, int rangeBonus, int aimAssistBonus, String aimAssistPolicy) {}
    private record Data(String stage, Perk perk, List<WeaponPerks.Roll> weapons) {}
    private static final Data DATA = load();
    private IronGazeProfile() {}

    private static Data load() {
        var in = IronGazeProfile.class.getResourceAsStream("/destiny/weapons/w226-iron-gaze.json");
        if (in == null) throw new IllegalStateException("Missing W226 Iron Gaze");
        try (var reader = new InputStreamReader(in, StandardCharsets.UTF_8)) {
            var d = new Gson().fromJson(reader, Data.class);
            var expected = new WeaponPerks.Roll("bite_of_the_fox", 1403800851L, 4, HASH, 2442672691L);
            if (d == null || !"W226".equals(d.stage) || d.perk == null
                || !ID.equals(d.perk.id) || d.perk.hash != HASH || d.perk.rangeBonus != -20
                || d.perk.aimAssistBonus != 20 || !"source-only; unsimulated".equals(d.perk.aimAssistPolicy)
                || !List.of(expected).equals(d.weapons))
                throw new IllegalStateException("Invalid W226 BASIC Iron Gaze");
            return new Data(d.stage, d.perk, List.copyOf(d.weapons));
        } catch (IOException e) { throw new IllegalStateException(e); }
    }
    public static List<WeaponPerks.Roll> rolls() { return DATA.weapons; }
    public static boolean supports(WeaponCatalog.Entry entry) {
        return entry != null && WeaponCatalog.find(entry.id()).filter(entry::equals).isPresent()
            && DATA.weapons.stream().anyMatch(r -> r.id().equals(entry.id())
                && r.hash() == WeaponCharacteristics.of(entry).bungieHash())
            && !WeaponCharacteristics.of(entry).exotic();
    }
    public static int rangeBonus() { return DATA.perk.rangeBonus; }
}
