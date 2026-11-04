package kim.biryeong.destiny.weapon;

import com.google.gson.Gson;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.List;

/** Base Trait only, DDC row152. Reuses the existing intrinsic Izanagi clock/resistance. */
public final class NoDistractionsProfile {
    public static final String ID = "no_distractions";
    public static final long HASH = 2866798147L;
    private record Perk(String id, long hash, double adsSeconds, int procTicks, float resistance) {}
    private record Data(String stage, Perk perk, List<WeaponPerks.Roll> weapons) {}
    private static final Data DATA = load();
    private NoDistractionsProfile() {}

    /** Initialization reads only this resource, never the live catalog or trait registry. */
    private static Data load() {
        var stream = NoDistractionsProfile.class.getResourceAsStream("/destiny/weapons/w194-no-distractions.json");
        if (stream == null) throw new IllegalStateException("Missing W194 No Distractions");
        try (var reader = new InputStreamReader(stream, StandardCharsets.UTF_8)) {
            var data = new Gson().fromJson(reader, Data.class);
            var expected = List.of(
                new WeaponPerks.Roll("biting_winds", 1621657423L, 3, HASH, 3968704963L),
                new WeaponPerks.Roll("bite_of_the_fox", 1403800851L, 3, HASH, 563442205L),
                new WeaponPerks.Roll("beloved", 3107853529L, 3, HASH, 1196545279L),
                new WeaponPerks.Roll("apostate", 2164448701L, 3, HASH, 1306932196L),
                new WeaponPerks.Roll("fixed_odds", 2194955522L, 3, HASH, 4227334000L));
            if (data == null || !"W194".equals(data.stage) || data.perk == null
                    || !ID.equals(data.perk.id) || data.perk.hash != HASH || data.perk.adsSeconds != 1
                    || data.perk.procTicks != WeaponFlinchState.PROC_TICKS
                    || data.perk.resistance != WeaponFlinchState.NO_DISTRACTIONS_RESISTANCE
                    || !expected.equals(data.weapons))
                throw new IllegalStateException("Invalid W194 No Distractions base mechanics/exact five sockets");
            return new Data(data.stage, data.perk, List.copyOf(data.weapons));
        } catch (java.io.IOException e) { throw new IllegalStateException(e); }
    }

    public static List<WeaponPerks.Roll> rolls() { return DATA.weapons; }
    public static boolean supports(WeaponCatalog.Entry entry) {
        return entry != null && WeaponCatalog.find(entry.id()).filter(entry::equals).isPresent()
            && DATA.weapons.stream().anyMatch(r -> r.id().equals(entry.id())
                && r.hash() == WeaponCharacteristics.of(entry).bungieHash());
    }
}
