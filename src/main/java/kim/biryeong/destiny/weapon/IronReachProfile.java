package kim.biryeong.destiny.weapon;

import com.google.gson.Gson;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.List;

/** Base DDC row129: +20 Range, -20 Stability. Enhanced penalty is not used.
 * The falloff formula is the existing historical W43 mapping, not a new sandbox calibration.
 */
public final class IronReachProfile {
    public static final String ID = "iron_reach";
    public static final long HASH = 591790007L;
    private record Perk(String id, long hash, int rangeBonus, int stabilityBonus) {}
    private record Range(int base, double offsetStart, double vppStart, double offsetEnd,
                         double vppEnd, double floor, double precision) {}
    private record Data(String stage, Perk perk, List<WeaponPerks.Roll> weapons, Range range) {}
    private static final Data DATA = load();
    private IronReachProfile() {}
    private static Data load() {
        var stream = IronReachProfile.class.getResourceAsStream("/destiny/weapons/w190-iron-reach.json");
        if (stream == null) throw new IllegalStateException("Missing W190 Iron Reach");
        try (var reader = new InputStreamReader(stream, StandardCharsets.UTF_8)) {
            var data = new Gson().fromJson(reader, Data.class);
            var expected = new WeaponPerks.Roll("allied_demand",1532276803L,4,HASH,703779397L);
            if (data == null || !"W190".equals(data.stage) || data.perk == null
                || !ID.equals(data.perk.id) || data.perk.hash != HASH
                || data.perk.rangeBonus != 20 || data.perk.stabilityBonus != -20
                || data.weapons == null || data.weapons.size() != 1 || data.range == null)
                throw new IllegalStateException("Invalid Iron Reach definition");
            var roll = data.weapons.getFirst();
            if (!expected.equals(roll))
                throw new IllegalStateException("Invalid Iron Reach socket");
            return new Data(data.stage,data.perk,List.copyOf(data.weapons),data.range);
        } catch (java.io.IOException e) { throw new IllegalStateException(e); }
    }
    public static List<WeaponPerks.Roll> rolls() { return DATA.weapons; }
    public static boolean supports(WeaponCatalog.Entry e) {
        return e != null && WeaponCatalog.find(e.id()).filter(e::equals).isPresent()
            && DATA.weapons.stream().anyMatch(r -> r.id().equals(e.id())
                && r.hash() == WeaponCharacteristics.of(e).bungieHash());
    }
    public static int stabilityBonus() { return DATA.perk.stabilityBonus; }
    public static WeaponBallistics.Profile ballistics(WeaponCatalog.Entry entry) {
        if (!supports(entry)) throw new IllegalArgumentException("Unsupported Iron Reach entry");
        var r = DATA.range;
        int stat = Math.clamp(r.base + DATA.perk.rangeBonus,0,100);
        return new WeaponBallistics.Profile(r.offsetStart+r.vppStart*stat,
            r.offsetEnd+r.vppEnd*stat,r.floor,r.precision);
    }
}
