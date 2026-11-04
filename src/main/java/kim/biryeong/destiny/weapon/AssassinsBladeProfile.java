package kim.biryeong.destiny.weapon;

import com.google.gson.Gson;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.List;

/** Pinned W195 base Trait only; exact canonical pools, enhanced/exotic/default selection excluded. */
public final class AssassinsBladeProfile {
    public static final String ID = "assassins_blade";
    public static final long HASH = 354401740L;
    public record Perk(String id, long hash, float damageMultiplier, int durationTicks, boolean persistsStow,
                       String movement, String destinyMovementAlgorithm) {}
    private record Data(String stage, Perk perk, List<WeaponPerks.Roll> weapons) {}
    private static final Data DATA = load();
    private AssassinsBladeProfile() {}
    private static void check(boolean ok) {
        if (!ok) throw new IllegalStateException("Invalid W195 AssassinsBlade profile");
    }
    private static Data load() {
        var stream = AssassinsBladeProfile.class.getResourceAsStream("/destiny/weapons/w195-assassins-blade.json");
        check(stream != null);
        try (var reader = new InputStreamReader(stream, StandardCharsets.UTF_8)) {
            var d = new Gson().fromJson(reader, Data.class);
            check(d != null && "W195".equals(d.stage) && d.perk != null
                && ID.equals(d.perk.id) && d.perk.hash == HASH
                && d.perk.damageMultiplier == 1.15f && d.perk.durationTicks == 100 && d.perk.persistsStow
                && "maximize Movement Speed".equals(d.perk.movement)
                && "unknown".equals(d.perk.destinyMovementAlgorithm)
                && List.of(new WeaponPerks.Roll("abide_the_return", 1644160541L, 3, HASH, 211008653L),
                    new WeaponPerks.Roll("abide_the_return", 1644160541L, 4, HASH, 2761485963L),
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
    public static float damageMultiplier() { return DATA.perk.damageMultiplier; }
    public static int durationTicks() { return DATA.perk.durationTicks; }
}
