package kim.biryeong.destiny.weapon;

import com.google.gson.Gson;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.List;

/** Exact pinned base Trait and original canonical weapon/socket/plug-set tuples only. */
public final class OpeningShotProfile {
    public static final String ID = "opening_shot";
    public static final long HASH = 47981717L;
    public record Perk(String id, long hash, int cooldownTicks, int primaryPowerRange, int primaryPowerAimAssist, double primaryPowerAccuracy, double primaryPowerGrowth, int specialRange, int specialAimAssist, double specialAccuracy, double specialGrowth) {}
    private record Data(String stage, Perk perk, List<WeaponPerks.Roll> weapons) {}
    private static final Data DATA = load();
    private OpeningShotProfile() {}
    private static void check(boolean ok) {
        if (!ok) throw new IllegalStateException("Invalid W195 Opening Shot profile");
    }
    private static Data load() {
        var stream = OpeningShotProfile.class.getResourceAsStream("/destiny/weapons/w195-opening-shot.json");
        check(stream != null);
        try (var reader = new InputStreamReader(stream, StandardCharsets.UTF_8)) {
            var d = new Gson().fromJson(reader, Data.class);
            check(d != null && "W195".equals(d.stage) && d.perk != null
                && ID.equals(d.perk.id) && d.perk.hash == HASH && d.perk.cooldownTicks == OpeningShotCycle.COOLDOWN_TICKS && d.perk.primaryPowerRange == 25 && d.perk.primaryPowerAimAssist == 20 && d.perk.primaryPowerAccuracy == .95 && d.perk.primaryPowerGrowth == .9 && d.perk.specialRange == 13 && d.perk.specialAimAssist == 10 && d.perk.specialAccuracy == .975 && d.perk.specialGrowth == .95
                && List.of(new WeaponPerks.Roll("duke_mk_44", 2112909414L, 2, HASH, 3744182842L),
                    new WeaponPerks.Roll("austringer", 3055790362L, 4, HASH, 785215120L),
                    new WeaponPerks.Roll("bygones", 2712244741L, 3, HASH, 1760176771L),
                    new WeaponPerks.Roll("chattering_bone", 568515759L, 3, HASH, 216806616L),
                    new WeaponPerks.Roll("distant_relation", 2034817450L, 4, HASH, 3824767299L),
                    new WeaponPerks.Roll("patron_of_lost_causes", 2723241847L, 4, HASH, 120674550L),
                    new WeaponPerks.Roll("long_arm", 8293111L, 4, HASH, 619833418L),
                    new WeaponPerks.Roll("lonesome", 2199171672L, 4, HASH, 167712635L),
                    new WeaponPerks.Roll("dead_man_walking_xx7463", 3751622019L, 4, HASH, 1210839935L),
                    new WeaponPerks.Roll("whispering_slab", 211938782L, 4, HASH, 967526625L),
                    new WeaponPerks.Roll("bite_of_the_fox", 1403800851L, 4, HASH, 2442672691L),
                    new WeaponPerks.Roll("apostate", 2164448701L, 4, HASH, 2826016044L),
                    new WeaponPerks.Roll("first_in_last_out", 3616586446L, 4, HASH, 1439234589L),
                    new WeaponPerks.Roll("parcel_of_stardust_fell_to_earth", 2217366863L, 3, HASH, 2514419370L)).equals(d.weapons));
            return new Data(d.stage, d.perk, List.copyOf(d.weapons));
        } catch (java.io.IOException e) { throw new IllegalStateException(e); }
    }
    public static Perk perk() { return DATA.perk; }
    public static List<WeaponPerks.Roll> rolls() { return DATA.weapons; }
    public static boolean supports(WeaponCatalog.Entry entry) {
        return entry != null && WeaponCatalog.find(entry.id()).filter(entry::equals).isPresent()
            && DATA.weapons.stream().anyMatch(r -> r.id().equals(entry.id())
                && r.hash() == WeaponCharacteristics.of(entry).bungieHash());
    }
    private static boolean special(WeaponCatalog.Entry entry) {
        return WeaponCharacteristics.of(entry).ammo() == WeaponAmmoType.SPECIAL;
    }
    public static int rangeBonus(WeaponCatalog.Entry entry) { return special(entry) ? perk().specialRange : perk().primaryPowerRange; }
    public static int aimAssistBonus(WeaponCatalog.Entry entry) { return special(entry) ? perk().specialAimAssist : perk().primaryPowerAimAssist; }
    public static double accuracyScalar(WeaponCatalog.Entry entry) { return special(entry) ? perk().specialAccuracy : perk().primaryPowerAccuracy; }
    public static double growthScalar(WeaponCatalog.Entry entry) { return special(entry) ? perk().specialGrowth : perk().primaryPowerGrowth; }
}
