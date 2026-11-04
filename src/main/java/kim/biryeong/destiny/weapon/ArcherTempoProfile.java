package kim.biryeong.destiny.weapon;

import com.google.gson.Gson;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.*;

/** Base Archer's Tempo only: exact official sockets, official .75 scalar, community 3s/stow window.
 * Raw W46 milliseconds are scaled BEFORE 20 Hz quantization. No enhanced/catalyst override.
 */
public final class ArcherTempoProfile {
    public static final String ID = "archers_tempo";
    public static final long HASH = 201365942L;
    public record Perk(String id,long hash,int durationTicks,double drawScalar,String timingSource) {}
    public record Timing(String id,int baseDrawMs,int baseDrawTicks,int acceleratedTicks) {}
    private record Data(String stage,Perk perk,WeaponPerks.Roll[] weapons,Timing[] timings) {}
    private static final Data DATA = load();
    private static final Map<String,Timing> TIMINGS = index();
    private ArcherTempoProfile() {}
    private static Data load() {
        var input=ArcherTempoProfile.class.getResourceAsStream("/destiny/weapons/w73-archers-tempo.json");
        if(input==null)throw new IllegalStateException("Missing W73 Archer's Tempo profile");
        try(var reader=new InputStreamReader(input,StandardCharsets.UTF_8)) {
            var d=new Gson().fromJson(reader,Data.class);
            if(d==null || !"W73".equals(d.stage) || d.perk==null || !ID.equals(d.perk.id)
                    || d.perk.hash!=HASH || d.perk.durationTicks!=ArcherTempoCycle.DURATION || d.perk.drawScalar!=.75
                    || d.perk.timingSource==null || d.perk.timingSource.isBlank()
                    || d.weapons==null || d.weapons.length==0 || d.timings==null)
                throw new IllegalStateException("Invalid W73 profile");
            var seen=new HashSet<String>();
            for(var row:d.weapons) {
                var e=WeaponCatalog.find(row.id()).orElseThrow();var c=WeaponCharacteristics.of(e);
                if(!e.family().equals("bow") || c.exotic() || row.hash()!=c.bungieHash() || row.perkHash()!=HASH
                        || row.socket()<0 || row.socket()>63 || row.plugSetHash()<=0 || !seen.add(row.id()+":"+row.socket()))
                    throw new IllegalStateException("Invalid W73 socket "+row);
            }
            return d;
        } catch(java.io.IOException e) { throw new IllegalStateException(e); }
    }
    private static Map<String,Timing> index() {
        var map=new HashMap<String,Timing>();
        for(var row:DATA.timings) {
            var e=WeaponCatalog.find(row.id).orElseThrow();var base=WeaponTiming.forEntry(e);
            if(row.baseDrawMs!=base.drawMillis().orElseThrow() || row.baseDrawTicks!=base.drawTicks().orElseThrow()
                    || row.acceleratedTicks!=acceleratedTicks(row.baseDrawMs) || map.putIfAbsent(row.id,row)!=null)
                throw new IllegalStateException("Invalid W73 timing "+row);
        }
        var ids=WeaponCatalog.all().stream().filter(e->e.family().equals("bow")).map(WeaponCatalog.Entry::id)
                .collect(java.util.stream.Collectors.toSet());
        if(!map.keySet().equals(ids))throw new IllegalStateException("Incomplete W73 draw timings");
        return Map.copyOf(map);
    }
    public static int acceleratedTicks(int rawMillis) {
        if(rawMillis<1 || rawMillis>60000)throw new IllegalArgumentException("Unsafe bow draw milliseconds");
        return (int)Math.ceil(rawMillis*.75/50);
    }
    public static Perk perk() { return DATA.perk; }
    public static List<WeaponPerks.Roll> rolls() { return List.of(DATA.weapons); }
    public static Timing timing(WeaponCatalog.Entry e) {
        var row=TIMINGS.get(e.id());if(row==null)throw new IllegalArgumentException("No W73 draw timing "+e.id());return row;
    }
    public static WeaponProfile accelerated(WeaponCatalog.Entry e,WeaponProfile p) {
        if(rolls().stream().noneMatch(r->r.id().equals(e.id())) || !e.family().equals("bow") || p.mode()!=WeaponProfile.Mode.PROJECTILE
                || p.chargeTicks()!=timing(e).baseDrawTicks)throw new IllegalArgumentException("Expected base bow profile");
        return new WeaponProfile(p.mode(),p.damage(),p.intervalTicks(),p.magazine(),p.reserve(),p.reloadTicks(),p.range(),
                timing(e).acceleratedTicks,p.burst(),p.pellets(),p.spread(),p.speed(),p.gravity(),p.blastRadius(),p.automatic(),
                p.infiniteReserve(),p.cadenceTicks(),p.burstSpacingTicks(),p.sharedBurstAmmo(),p.shellReload(),p.firstReloadTicks(),p.roundsPerInsert());
    }
}
