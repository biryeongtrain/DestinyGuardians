package kim.biryeong.destiny.weapon;

import com.google.gson.Gson;
import java.io.IOException;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

/** Base Subsistence on seven exact official sockets; selection and reserve transfer belong to runtime. */
public final class SubsistenceProfile {
    public static final String ID = "subsistence";
    public static final long HASH = 1820235745L;
    private static final String RESOURCE = "/destiny/weapons/w167-subsistence.json";
    private record Perk(String id, long hash, int defaultPercent, int bonusPercent,
                        List<String> bonusFamilies, String rounding, boolean fromReserves,
                        boolean reloadAnimation, boolean triggersOnReload, String source) {}
    private record Data(String stage, Perk perk, List<WeaponPerks.Roll> weapons) {}
    private static final Set<WeaponPerks.Roll> EXPECTED = Set.of(
        roll("gnawing_hunger", 821154603L, 1144396384L),
        roll("steelfeather_repeater", 1251729046L, 473189353L),
        roll("long_arm", 8293111L, 3056706286L),
        roll("bug_out_bag", 2744715540L, 907333373L),
        roll("allied_demand", 1532276803L, 3275836355L),
        roll("farewell", 541188001L, 284168234L),
        roll("retraced_path", 548958835L, 2945646047L));
    private static final Data DATA = load();
    private SubsistenceProfile() {}

    private static WeaponPerks.Roll roll(String id, long hash, long pool) {
        return new WeaponPerks.Roll(id, hash, 3, HASH, pool);
    }

    private static Data load() {
        var stream = SubsistenceProfile.class.getResourceAsStream(RESOURCE);
        if (stream == null) throw new IllegalStateException("Missing W167 Subsistence profile");
        try (var reader = new InputStreamReader(stream, StandardCharsets.UTF_8)) {
            var data = new Gson().fromJson(reader, Data.class);
            var expectedPerk = new Perk(ID, HASH, 10, 17, List.of("submachine_gun", "auto_rifle"),
                "ceil", true, false, false, "art/weapons/w167/references/clarity-source.json");
            if (data == null || !"W167".equals(data.stage) || !expectedPerk.equals(data.perk)
                    || data.weapons == null || data.weapons.size() != EXPECTED.size()
                    || !new HashSet<>(data.weapons).equals(EXPECTED))
                throw new IllegalStateException("Invalid W167 Subsistence profile");
            for (var roll : data.weapons) {
                var entry = WeaponCatalog.find(roll.id()).orElseThrow();
                var meta = WeaponCharacteristics.of(entry);
                if (meta.exotic() || meta.bungieHash() != roll.hash())
                    throw new IllegalStateException("Invalid W167 Subsistence socket " + roll);
            }
            return new Data(data.stage, expectedPerk, List.copyOf(data.weapons));
        } catch (IOException e) {
            throw new IllegalStateException("Cannot read W167 Subsistence profile", e);
        }
    }

    public static List<WeaponPerks.Roll> rolls() { return DATA.weapons; }

    /** Canonical catalog membership rejects forged records sharing only a supported ID. */
    public static boolean supports(WeaponCatalog.Entry entry) {
        return entry != null && WeaponCatalog.find(entry.id()).filter(entry::equals).isPresent()
                && DATA.weapons.stream().anyMatch(r -> r.id().equals(entry.id()));
    }

    /** Requested rounds per weapon kill, before runtime clamps to magazine space and reserves.
     * This is a refill: it requires no reload animation and never triggers on-reload perks.
     */
    public static int refillRounds(WeaponCatalog.Entry entry, int capacity) {
        if (capacity <= 0 || !supports(entry)) return 0;
        int percent = DATA.perk.bonusFamilies.contains(entry.family())
            ? DATA.perk.bonusPercent : DATA.perk.defaultPercent;
        return (int) ((capacity * (long) percent + 99) / 100);
    }
}
