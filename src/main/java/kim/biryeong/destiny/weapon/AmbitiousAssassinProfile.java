package kim.biryeong.destiny.weapon;

import com.google.gson.Gson;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.List;

/** Base Ambitious Assassin, user DDC row16; enhanced reload stat is excluded. */
public final class AmbitiousAssassinProfile {
    public static final String ID="ambitious_assassin";
    public static final long HASH=2010801679L;
    private static final List<WeaponPerks.Roll> EXPECTED=List.of(
        new WeaponPerks.Roll("seventh_seraph_officer_revolver", 3037520408L, 3, HASH, 903350103L),
        new WeaponPerks.Roll("ammit_ar2", 2119346509L, 3, HASH, 1723759242L),
        new WeaponPerks.Roll("steelfeather_repeater", 1251729046L, 3, HASH, 473189353L),
        new WeaponPerks.Roll("blast_furnace", 3843477312L, 4, HASH, 169306153L),
        new WeaponPerks.Roll("distant_relation", 2034817450L, 4, HASH, 3824767299L),
        new WeaponPerks.Roll("high_albedo", 1197486957L, 3, HASH, 2797218184L),
        new WeaponPerks.Roll("coriolis_force", 3512349612L, 3, HASH, 2568674372L),
        new WeaponPerks.Roll("deafening_whisper", 981718087L, 3, HASH, 3110206796L),
        new WeaponPerks.Roll("edge_transit", 218335759L, 4, HASH, 2535579724L),
        new WeaponPerks.Roll("bellowing_giant", 2186258845L, 4, HASH, 1722393382L),
        new WeaponPerks.Roll("code_duello", 2496242052L, 4, HASH, 147528717L),
        new WeaponPerks.Roll("pyroclastic_flow", 1289324202L, 3, HASH, 528513254L),
        new WeaponPerks.Roll("hammerhead", 603242241L, 4, HASH, 2479293397L));
    private record Perk(String id,long hash,int primaryPercentPerKill,int otherPercentPerKill,
                        int maximumBonusPercent,boolean counterPersistsStow) {}
    private record Data(String stage,Perk perk,List<WeaponPerks.Roll> weapons) {}
    private static final Data DATA=load();
    private AmbitiousAssassinProfile() {}
    private static Data load() {
        var in=AmbitiousAssassinProfile.class.getResourceAsStream("/destiny/weapons/w193-ambitious-assassin.json");
        if(in==null)throw new IllegalStateException("Missing W193 Ambitious Assassin");
        try(var reader=new InputStreamReader(in,StandardCharsets.UTF_8)) {
            var d=new Gson().fromJson(reader,Data.class);
            if(d==null || !"W193".equals(d.stage) || !new Perk(ID,HASH,20,10,150,true).equals(d.perk)
                || !EXPECTED.equals(d.weapons))throw new IllegalStateException("Invalid W193 Ambitious Assassin");
            return new Data(d.stage,d.perk,List.copyOf(d.weapons));
        } catch(java.io.IOException e) { throw new IllegalStateException(e); }
    }
    public static List<WeaponPerks.Roll> rolls() { return DATA.weapons; }
    public static boolean supports(WeaponCatalog.Entry e) {
        return e!=null && WeaponCatalog.find(e.id()).filter(e::equals).isPresent()
            && !WeaponCharacteristics.of(e).exotic() && EXPECTED.stream().anyMatch(r->r.id().equals(e.id())
                && r.hash()==WeaponCharacteristics.of(e).bungieHash());
    }
    public static int target(WeaponCatalog.Entry e,int kills) {
        if(!supports(e))return 0;
        int base=WeaponProfile.forEntry(e).magazine();
        int perKill=WeaponCharacteristics.of(e).ammo()==WeaponAmmoType.PRIMARY?20:10;
        int bonus=Math.min(150,Math.clamp(kills,0,15)*perKill);
        return (int)Math.min(Integer.MAX_VALUE,((long)base*(100+bonus)+99)/100);
    }
}
