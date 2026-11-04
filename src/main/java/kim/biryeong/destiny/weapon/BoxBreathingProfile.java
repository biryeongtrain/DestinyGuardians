package kim.biryeong.destiny.weapon;

import com.google.gson.Gson;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.List;

/** Exact pinned base Trait and original canonical weapon/socket/plug-set tuples only. */
public final class BoxBreathingProfile {
    public static final String ID = "box_breathing";
    public static final long HASH = 2551157718L;
    public record Perk(String id, long hash, int procTicks, float precisionMultiplier, double aimAssistFalloffScalar) {}
    private record Data(String stage, Perk perk, List<WeaponPerks.Roll> weapons) {}
    private static final Data DATA = load();
    private BoxBreathingProfile() {}
    private static void check(boolean ok) {
        if (!ok) throw new IllegalStateException("Invalid W195 Box Breathing profile");
    }
    private static Data load() {
        var stream = BoxBreathingProfile.class.getResourceAsStream("/destiny/weapons/w195-box-breathing.json");
        check(stream != null);
        try (var reader = new InputStreamReader(stream, StandardCharsets.UTF_8)) {
            var d = new Gson().fromJson(reader, Data.class);
            check(d != null && "W195".equals(d.stage) && d.perk != null
                && ID.equals(d.perk.id) && d.perk.hash == HASH && d.perk.procTicks == BoxBreathingCycle.PROC_TICKS && d.perk.precisionMultiplier == 1.4f && d.perk.aimAssistFalloffScalar == 1.1
                && List.of(new WeaponPerks.Roll("beloved", 3107853529L, 4, HASH, 887157889L),
                    new WeaponPerks.Roll("apostate", 2164448701L, 4, HASH, 2826016044L)).equals(d.weapons));
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
}
