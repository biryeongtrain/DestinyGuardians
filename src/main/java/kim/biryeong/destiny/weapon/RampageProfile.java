package kim.biryeong.destiny.weapon;

import com.google.gson.Gson;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.*;

/** Exact base-trait sockets, official gradual decay, separately attributed community timings/damage. */
public final class RampageProfile {
    public static final String ID = "rampage";
    public static final long HASH = 3425386926L;
    public record Perk(String id,long hash,int decayTicks,List<Float> multipliers,String timingSource) {
        public Perk { multipliers=List.copyOf(multipliers); }
    }
    private record Data(String stage,Perk perk,WeaponPerks.Roll[] weapons) {}
    private static final Data DATA=load();
    private RampageProfile() {}
    private static Data load() {
        var input=RampageProfile.class.getResourceAsStream("/destiny/weapons/w66-rampage.json");
        if(input==null)throw new IllegalStateException("Missing W66 Rampage data");
        try(var reader=new InputStreamReader(input,StandardCharsets.UTF_8)) {
            var d=new Gson().fromJson(reader,Data.class);
            if(d==null || !"W66".equals(d.stage) || d.perk==null || !ID.equals(d.perk.id)
                    || d.perk.hash!=HASH || d.perk.decayTicks<1 || d.perk.decayTicks>1200
                    || d.perk.multipliers.size()!=4 || d.perk.multipliers.getFirst()!=1f
                    || d.perk.timingSource==null || d.perk.timingSource.isBlank()
                    || d.weapons==null || d.weapons.length==0)
                throw new IllegalStateException("Invalid W66 Rampage profile");
            float previous=0;
            for(float value:d.perk.multipliers) {
                if(!Float.isFinite(value) || value<=previous || value>2)
                    throw new IllegalStateException("Invalid Rampage multiplier");
                previous=value;
            }
            var seen=new HashSet<String>();
            for(var r:d.weapons) {
                var e=WeaponCatalog.find(r.id()).orElseThrow();
                if(r.hash()!=WeaponCharacteristics.of(e).bungieHash() || r.perkHash()!=HASH
                        || r.socket()<0 || r.socket()>63 || r.plugSetHash()<=0
                        || WeaponCharacteristics.of(e).exotic() || !seen.add(r.id()+":"+r.socket()))
                    throw new IllegalStateException("Invalid W66 trait socket "+r);
            }
            return d;
        } catch(java.io.IOException e) {throw new IllegalStateException(e);}
    }
    public static Perk perk() { return DATA.perk; }
    public static List<WeaponPerks.Roll> rolls() { return List.of(DATA.weapons); }
    public static float multiplier(int stacks) { return DATA.perk.multipliers.get(stacks); }
}
