package kim.biryeong.destiny.weapon;

import com.google.gson.Gson;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.List;

/** Pinned W200 base Trait only; exact canonical pools, enhanced/exotic/default selection excluded. */
public final class UnrelentingProfile {
    public static final String ID = "unrelenting";
    public static final long HASH = 3108830275L;
    public record Perk(String id, long hash, int windowTicks, int rankAndFileProgress,
                       int powerfulProgress, int guardianProgress, int healHP,
                       float localHealMaxHealthFraction, String destinyRegenerationRate,
                       float localRegenerationMaxHealthPerTick) {}
    private record Data(String stage, Perk perk, List<WeaponPerks.Roll> weapons) {}
    private static final Data DATA = load();
    private UnrelentingProfile() {}
    private static void check(boolean ok) {
        if (!ok) throw new IllegalStateException("Invalid W200 Unrelenting profile");
    }
    private static Data load() {
        var stream = UnrelentingProfile.class.getResourceAsStream("/destiny/weapons/w200-unrelenting.json");
        check(stream != null);
        try (var reader = new InputStreamReader(stream, StandardCharsets.UTF_8)) {
            var d = new Gson().fromJson(reader, Data.class);
            check(d != null && "W200".equals(d.stage) && d.perk != null
                && ID.equals(d.perk.id) && d.perk.hash == HASH
                && d.perk.windowTicks == 100 && d.perk.rankAndFileProgress == 34
                && d.perk.powerfulProgress == 100 && d.perk.guardianProgress == 67
                && d.perk.healHP == 65 && d.perk.localHealMaxHealthFraction == .325f
                && "unknown".equals(d.perk.destinyRegenerationRate)
                && d.perk.localRegenerationMaxHealthPerTick == .01f
                && List.of(new WeaponPerks.Roll("cold_denial", 1216130969L, 4, HASH, 720537379L),
                    new WeaponPerks.Roll("aishas_embrace", 2638190703L, 3, HASH, 7997267L),
                    new WeaponPerks.Roll("farewell", 541188001L, 4, HASH, 3819615926L),
                    new WeaponPerks.Roll("high_albedo", 1197486957L, 4, HASH, 718633408L),
                    new WeaponPerks.Roll("biting_winds", 1621657423L, 4, HASH, 2763203653L),
                    new WeaponPerks.Roll("whispering_slab", 211938782L, 4, HASH, 967526625L),
                    new WeaponPerks.Roll("hollow_words", 607191995L, 4, HASH, 1485010760L),
                    new WeaponPerks.Roll("coriolis_force", 3512349612L, 4, HASH, 753624012L),
                    new WeaponPerks.Roll("deafening_whisper", 981718087L, 4, HASH, 3588287812L),
                    new WeaponPerks.Roll("canis_major", 2066434718L, 4, HASH, 2791121719L),
                    new WeaponPerks.Roll("dimensional_hypotrochoid", 1311684613L, 3, HASH, 3235863202L),
                    new WeaponPerks.Roll("code_duello", 2496242052L, 4, HASH, 147528717L),
                    new WeaponPerks.Roll("goldtusk", 3371413057L, 3, HASH, 1162279549L)).equals(d.weapons));
            return new Data(d.stage, d.perk, List.copyOf(d.weapons));
        } catch (java.io.IOException e) { throw new IllegalStateException(e); }
    }
    public static Perk perk() { return DATA.perk; }
    public static List<WeaponPerks.Roll> rolls() { return DATA.weapons; }
    public static boolean supports(WeaponCatalog.Entry entry) {
        return entry != null && WeaponCatalog.find(entry.id()).filter(entry::equals).isPresent()
            && !WeaponCharacteristics.of(entry).exotic()
            && DATA.weapons.stream().anyMatch(r -> r.id().equals(entry.id())
                && r.hash() == WeaponCharacteristics.of(entry).bungieHash());
    }
    public static int windowTicks() { return DATA.perk.windowTicks; }
    public static int progress(UnrelentingCycle.Rank rank) {
        return switch (rank) {
            case RANK_AND_FILE -> DATA.perk.rankAndFileProgress;
            case POWERFUL -> DATA.perk.powerfulProgress;
            case GUARDIAN -> DATA.perk.guardianProgress;
        };
    }
    public static float healFraction() { return DATA.perk.localHealMaxHealthFraction; }
    public static float regenerationFraction() { return DATA.perk.localRegenerationMaxHealthPerTick; }
}
