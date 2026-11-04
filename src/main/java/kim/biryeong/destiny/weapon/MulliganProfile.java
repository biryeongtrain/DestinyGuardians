package kim.biryeong.destiny.weapon;

import com.google.gson.Gson;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.List;

/** Base Mulligan, user DDC row150; enhanced probability is excluded. */
public final class MulliganProfile {
    public static final String ID="mulligan";
    public static final long HASH=3513791699L;
    private static final List<WeaponPerks.Roll> EXPECTED=List.of(
        new WeaponPerks.Roll("patron_of_lost_causes", 2723241847L, 3, HASH, 2564227946L),
        new WeaponPerks.Roll("hammerhead", 603242241L, 4, HASH, 2479293397L));
    private record Perk(String id,long hash,int primaryChancePercent,int otherChancePercent,int generatedRounds) {}
    private record Data(String stage,Perk perk,List<WeaponPerks.Roll> weapons) {}
    private static final Data DATA=load();
    private MulliganProfile() {}
    private static Data load() {
        var in=MulliganProfile.class.getResourceAsStream("/destiny/weapons/w194-mulligan.json");
        if(in==null)throw new IllegalStateException("Missing W194 Mulligan");
        try(var reader=new InputStreamReader(in,StandardCharsets.UTF_8)) {
            var d=new Gson().fromJson(reader,Data.class);
            if(d==null || !"W194".equals(d.stage) || !new Perk(ID,HASH,35,20,1).equals(d.perk)
                || !EXPECTED.equals(d.weapons))throw new IllegalStateException("Invalid W194 Mulligan");
            return new Data(d.stage,d.perk,List.copyOf(d.weapons));
        } catch(java.io.IOException e) { throw new IllegalStateException(e); }
    }
    public static List<WeaponPerks.Roll> rolls() { return DATA.weapons; }
    public static boolean supports(WeaponCatalog.Entry e) {
        return e!=null && WeaponCatalog.find(e.id()).filter(e::equals).isPresent()
            && !WeaponCharacteristics.of(e).exotic() && WeaponProfile.forEntry(e).mode()==WeaponProfile.Mode.HITSCAN && EXPECTED.stream().anyMatch(r->r.id().equals(e.id())
                && r.hash()==WeaponCharacteristics.of(e).bungieHash());
    }
    public static int chancePercent(WeaponCatalog.Entry e) {
        if(!supports(e))return 0;
        return WeaponCharacteristics.of(e).ammo()==WeaponAmmoType.PRIMARY?DATA.perk.primaryChancePercent:DATA.perk.otherChancePercent;
    }
}
