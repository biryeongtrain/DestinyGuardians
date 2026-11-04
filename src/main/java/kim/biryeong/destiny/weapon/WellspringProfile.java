package kim.biryeong.destiny.weapon;

import com.google.gson.Gson;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Set;

/** Base DDC row247. Exact pinned randomized trait sockets; enhanced values are excluded.
 * Loading this definition never enters the shared weapon registry/catalog initialization path.
 */
public final class WellspringProfile {
    public static final String ID = "wellspring";
    public static final long HASH = 3592538738L;
    private record Perk(String id, long hash, int energyPercent) {}
    private record Data(String stage, Perk perk, List<WeaponPerks.Roll> weapons) {}
    private static final Data DATA = load();
    private WellspringProfile() {}
    private static Data load() {
        var stream = WellspringProfile.class.getResourceAsStream("/destiny/weapons/w191-wellspring.json");
        if (stream == null) throw new IllegalStateException("Missing W191 Wellspring");
        try (var reader = new InputStreamReader(stream, StandardCharsets.UTF_8)) {
            var data = new Gson().fromJson(reader, Data.class);
            if (data == null || !"W191".equals(data.stage) || data.perk == null
                || !ID.equals(data.perk.id) || data.perk.hash != HASH || data.perk.energyPercent != 8
                || data.weapons == null || data.weapons.size() != 6)
                throw new IllegalStateException("Invalid Wellspring definition");
            var expected = Set.of(
                new WeaponPerks.Roll("long_arm",8293111L,3,HASH,3056706286L),
                new WeaponPerks.Roll("high_albedo",1197486957L,4,HASH,718633408L),
                new WeaponPerks.Roll("brass_attacks",2121785039L,4,HASH,3403850295L),
                new WeaponPerks.Roll("apostate",2164448701L,4,HASH,2826016044L),
                new WeaponPerks.Roll("dream_breaker",2931957300L,4,HASH,1206254527L),
                new WeaponPerks.Roll("deafening_whisper",981718087L,4,HASH,3588287812L));
            if (!expected.equals(Set.copyOf(data.weapons)))
                throw new IllegalStateException("Invalid Wellspring sockets");
            return new Data(data.stage, data.perk, List.copyOf(data.weapons));
        } catch (java.io.IOException e) { throw new IllegalStateException(e); }
    }
    public static List<WeaponPerks.Roll> rolls() { return DATA.weapons; }
    public static boolean supports(WeaponCatalog.Entry entry) {
        return entry != null && WeaponCatalog.find(entry.id()).filter(entry::equals).isPresent()
            && DATA.weapons.stream().anyMatch(r -> r.id().equals(entry.id())
                && r.hash() == WeaponCharacteristics.of(entry).bungieHash());
    }
    public static int energyPercent() { return DATA.perk.energyPercent; }
}
