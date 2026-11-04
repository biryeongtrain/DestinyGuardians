package kim.biryeong.destiny.weapon;

import com.google.gson.Gson;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Set;

/** Base DDC row227. Exact pinned randomized trait sockets; enhanced values are excluded.
 * Loading this definition never enters the shared weapon registry/catalog initialization path.
 */
public final class ThreshProfile {
    public static final String ID = "thresh";
    public static final long HASH = 2726471870L;
    private record Perk(String id, long hash, double energyPercent, double specialEnergyPercent,
                        List<String> specialEnergyFamilies) {}
    private record Data(String stage, Perk perk, List<WeaponPerks.Roll> weapons) {}
    private static final Data DATA = load();
    private ThreshProfile() {}
    private static Data load() {
        var stream = ThreshProfile.class.getResourceAsStream("/destiny/weapons/w191-thresh.json");
        if (stream == null) throw new IllegalStateException("Missing W191 Thresh");
        try (var reader = new InputStreamReader(stream, StandardCharsets.UTF_8)) {
            var data = new Gson().fromJson(reader, Data.class);
            if (data == null || !"W191".equals(data.stage) || data.perk == null
                || !ID.equals(data.perk.id) || data.perk.hash != HASH || data.perk.energyPercent != 1 || data.perk.specialEnergyPercent != 1.5
                || !List.of("fusion_rifle", "glaive", "shotgun", "sniper_rifle").equals(data.perk.specialEnergyFamilies)
                || data.weapons == null || data.weapons.size() != 6)
                throw new IllegalStateException("Invalid Thresh definition");
            var expected = Set.of(
                new WeaponPerks.Roll("farewell",541188001L,4,HASH,3819615926L),
                new WeaponPerks.Roll("apostate",2164448701L,4,HASH,2826016044L),
                new WeaponPerks.Roll("coriolis_force",3512349612L,4,HASH,753624012L),
                new WeaponPerks.Roll("dimensional_hypotrochoid",1311684613L,4,HASH,1092097342L),
                new WeaponPerks.Roll("abide_the_return",1644160541L,4,HASH,2761485963L),
                new WeaponPerks.Roll("crown_splitter",2782325302L,3,HASH,427353656L));
            if (!expected.equals(Set.copyOf(data.weapons)))
                throw new IllegalStateException("Invalid Thresh sockets");
            return new Data(data.stage, data.perk, List.copyOf(data.weapons));
        } catch (java.io.IOException e) { throw new IllegalStateException(e); }
    }
    public static List<WeaponPerks.Roll> rolls() { return DATA.weapons; }
    public static boolean supports(WeaponCatalog.Entry entry) {
        return entry != null && WeaponCatalog.find(entry.id()).filter(entry::equals).isPresent()
            && DATA.weapons.stream().anyMatch(r -> r.id().equals(entry.id())
                && r.hash() == WeaponCharacteristics.of(entry).bungieHash());
    }
    public static double energyPercent(WeaponCatalog.Entry entry) {
        if (!supports(entry)) return 0;
        return DATA.perk.specialEnergyFamilies.contains(entry.family())
            ? DATA.perk.specialEnergyPercent : DATA.perk.energyPercent;
    }
}
