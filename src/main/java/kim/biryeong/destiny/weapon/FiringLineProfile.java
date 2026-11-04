package kim.biryeong.destiny.weapon;

import com.google.gson.Gson;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.HashSet;
import java.util.List;

/** W191 base Firing Line, DDC row 96. Metres map to blocks; enhanced handling is excluded. */
public final class FiringLineProfile {
    public static final String ID = "firing_line";
    public static final long HASH = 1771339417L;
    private record Perk(String id, long hash, double radiusBlocks, int requiredAllies,
                        float precisionMultiplier) {}
    private record Data(String stage, Perk perk, List<WeaponPerks.Roll> weapons) {}
    private static final Data DATA = load();

    private FiringLineProfile() {}

    private static Data load() {
        var stream = FiringLineProfile.class.getResourceAsStream("/destiny/weapons/w191-firing-line.json");
        if (stream == null) throw new IllegalStateException("Missing W191 Firing Line");
        try (var reader = new InputStreamReader(stream, StandardCharsets.UTF_8)) {
            var data = new Gson().fromJson(reader, Data.class);
            var expected = List.of(
                new WeaponPerks.Roll("line_in_the_sand", 946443267L, 4, HASH, 3257645194L),
                new WeaponPerks.Roll("stormchaser", 3652506829L, 4, HASH, 4213354588L),
                new WeaponPerks.Roll("fixed_odds", 2194955522L, 4, HASH, 1686775256L));
            if (data == null || !"W191".equals(data.stage) || data.perk == null
                    || !ID.equals(data.perk.id) || data.perk.hash != HASH
                    || data.perk.radiusBlocks != 15 || data.perk.requiredAllies != 2
                    || data.perk.precisionMultiplier != 1.20f || data.weapons == null
                    || data.weapons.size() != expected.size()
                    || !new HashSet<>(data.weapons).equals(new HashSet<>(expected)))
                throw new IllegalStateException("Invalid W191 Firing Line definition/socket pool");
            // Do not consult WeaponPerks' registry while it is loading this profile.
            return new Data(data.stage, data.perk, List.copyOf(data.weapons));
        } catch (java.io.IOException e) { throw new IllegalStateException(e); }
    }

    public static List<WeaponPerks.Roll> rolls() { return DATA.weapons; }
    public static double radiusBlocks() { return DATA.perk.radiusBlocks; }
    public static int requiredAllies() { return DATA.perk.requiredAllies; }
    public static float precisionMultiplier() { return DATA.perk.precisionMultiplier; }
    public static boolean supports(WeaponCatalog.Entry entry) {
        return entry != null && WeaponCatalog.find(entry.id()).filter(entry::equals).isPresent()
            && DATA.weapons.stream().anyMatch(r -> r.id().equals(entry.id())
                && r.hash() == WeaponCharacteristics.of(entry).bungieHash());
    }
}
