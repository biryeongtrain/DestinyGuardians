package kim.biryeong.destiny.weapon;

import com.google.gson.Gson;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.*;

/** Both base official Full Auto hashes. DDC row103, enhanced excluded. */
public final class FullAutoProfile {
    public static final String ID="full_auto_trigger_system";
    private record Perk(String id,List<Long> hashes,double shotgunRecoveryScalar,
                        int legacyStabilityBonus,List<String> legacyStabilityWeapons) {}
    private record Data(String stage,Perk perk,List<WeaponPerks.Roll> weapons) {}
    private static final Data DATA=load();
    private FullAutoProfile() {}
    private static Data load() {
        var stream=FullAutoProfile.class.getResourceAsStream("/destiny/weapons/w191-full-auto-trigger-system.json");
        if(stream==null)throw new IllegalStateException("Missing W191 Full Auto");
        try(var r=new InputStreamReader(stream,StandardCharsets.UTF_8)) {
            var d=new Gson().fromJson(r,Data.class);
            if(d==null||!"W191".equals(d.stage)||d.perk==null||!ID.equals(d.perk.id)
                    ||!Set.copyOf(d.perk.hashes).equals(Set.of(4267945040L,2117683199L))
                    ||d.perk.shotgunRecoveryScalar!=.9||d.perk.legacyStabilityBonus!=5
                    ||!d.perk.legacyStabilityWeapons.equals(List.of("lonesome"))||d.weapons==null||d.weapons.size()!=10)
                throw new IllegalStateException("Invalid W191 Full Auto");
            var sockets=new HashSet<String>();
            for(var row:d.weapons)if(!d.perk.hashes.contains(row.perkHash())||row.socket()<0||row.plugSetHash()<=0
                    ||!sockets.add(row.id()+":"+row.socket()))throw new IllegalStateException("Invalid Full Auto socket");
            return new Data(d.stage,d.perk,List.copyOf(d.weapons));
        }catch(java.io.IOException e){throw new IllegalStateException(e);}
    }
    public static List<WeaponPerks.Roll> rolls(){return DATA.weapons;}
    public static boolean supports(WeaponCatalog.Entry e){return e!=null&&WeaponCatalog.find(e.id()).filter(e::equals).isPresent()
            &&DATA.weapons.stream().anyMatch(r->r.id().equals(e.id())&&r.hash()==WeaponCharacteristics.of(e).bungieHash());}
    public static int stabilityBonus(WeaponCatalog.Entry e){return supports(e)&&DATA.perk.legacyStabilityWeapons.contains(e.id())?DATA.perk.legacyStabilityBonus:0;}
    /** Apply once to a fresh BASE profile at the accepted shot, before the cadence is paid.
     * No live retiming of an earlier shot, no integer rounding before WeaponCycle. */
    public static WeaponProfile firingProfile(WeaponCatalog.Entry e,WeaponProfile b){
        if(!supports(e)||!e.family().equals("shotgun"))return b;
        double cadence=b.cadenceTicks()*DATA.perk.shotgunRecoveryScalar;
        return new WeaponProfile(b.mode(),b.damage(),(int)Math.ceil(cadence),b.magazine(),b.reserve(),b.reloadTicks(),
                b.range(),b.chargeTicks(),b.burst(),b.pellets(),b.spread(),b.speed(),b.gravity(),b.blastRadius(),
                b.automatic(),b.infiniteReserve(),cadence,b.burstSpacingTicks(),b.sharedBurstAmmo(),b.shellReload(),
                b.firstReloadTicks(),b.roundsPerInsert());
    }
}
