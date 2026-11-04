package kim.biryeong.destiny.weapon;

import com.google.gson.Gson;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.*;

/** Base Explosive Payload only. Sourced conversion and local radial policy are kept separate.
 * Damage is Minecraft HP, never a conversion of Destiny's displayed damage units. */
public final class PayloadProfile {
    public static final String ID="explosive_payload";
    public static final long HASH=3038247973L;
    public record Source(String authority,String url,String sha256) {}
    public record Perk(String id,long hash,double convertedBodyFraction,double pveExplosionMultiplier,
                       double radiusMeters,double radialFloor,String radialPolicy,Source mechanicsSource) {}
    private record Data(String stage,Perk perk,WeaponPerks.Roll[] weapons) {}
    private static final Set<WeaponPerks.Roll> EXPECTED=Set.of(
        new WeaponPerks.Roll("distant_relation",2034817450L,4,HASH,3824767299L),
        new WeaponPerks.Roll("patron_of_lost_causes",2723241847L,4,HASH,120674550L),
        new WeaponPerks.Roll("long_arm",8293111L,4,HASH,619833418L),
        new WeaponPerks.Roll("bite_of_the_fox",1403800851L,4,HASH,2442672691L),
        new WeaponPerks.Roll("apostate",2164448701L,4,HASH,2826016044L));
    private static final Data DATA=load();
    private PayloadProfile() {}
    private static Data load() {
        var stream=PayloadProfile.class.getResourceAsStream("/destiny/weapons/w80-payload.json");
        if(stream==null)throw new IllegalStateException("Missing W80 Explosive Payload profile");
        try(var reader=new InputStreamReader(stream,StandardCharsets.UTF_8)) {
            var d=new Gson().fromJson(reader,Data.class);
            if(d==null||!"W80".equals(d.stage)||d.perk==null||d.weapons==null)
                throw new IllegalStateException("Invalid W80 profile");
            var p=d.perk;
            if(!ID.equals(p.id)||p.hash!=HASH||!Double.isFinite(p.convertedBodyFraction)
                    ||p.convertedBodyFraction!=.5
                    ||!Double.isFinite(p.pveExplosionMultiplier)||p.pveExplosionMultiplier!=1.3
                    ||!Double.isFinite(p.radiusMeters)||p.radiusMeters!=3
                    ||!Double.isFinite(p.radialFloor)||p.radialFloor!=.25
                    ||!"local_linear_floor_nearest_aabb".equals(p.radialPolicy)
                    ||p.mechanicsSource==null||!"community".equals(p.mechanicsSource.authority)
                    ||p.mechanicsSource.url==null||!p.mechanicsSource.url.startsWith("https://")
                    ||p.mechanicsSource.sha256==null||!p.mechanicsSource.sha256.matches("[0-9a-f]{64}"))
                throw new IllegalStateException("Invalid W80 mechanics/provenance");
            var seen=new HashSet<WeaponPerks.Roll>();
            for(var roll:d.weapons) {
                if(roll==null||!EXPECTED.contains(roll)||!seen.add(roll))throw new IllegalStateException("Invalid W80 socket");
                var entry=WeaponCatalog.find(roll.id()).orElseThrow();
                var meta=WeaponCharacteristics.of(entry);
                if(meta.bungieHash()!=roll.hash()||meta.exotic()
                        ||!Set.of("scout_rifle","sniper_rifle").contains(entry.family()))
                    throw new IllegalStateException("W80 weapon identity drift");
            }
            if(!seen.equals(EXPECTED))throw new IllegalStateException("Incomplete W80 official sockets");
            return d;
        } catch(java.io.IOException e) {throw new IllegalStateException(e);}
    }
    public static Perk perk() {return DATA.perk;}
    public static List<WeaponPerks.Roll> rolls() {return List.of(DATA.weapons);}
    public static double radius() {return DATA.perk.radiusMeters;}
    /** The converted fraction is subtracted from BODY damage, preserving the unconverted crit bonus. */
    public static float impact(float base,double criticalMultiplier,boolean critical,double shotFalloff) {
        if(!Float.isFinite(base)||base<=0||!Double.isFinite(criticalMultiplier)||criticalMultiplier<1
                ||criticalMultiplier>5||!Double.isFinite(shotFalloff)||shotFalloff<0||shotFalloff>1)return 0;
        return (float)(base*((critical?criticalMultiplier:1)-DATA.perk.convertedBodyFraction)*shotFalloff);
    }
    /** Explosion cannot crit. Exemption from bullet-distance attenuation is an explicit local policy;
     * the retained current source did not establish that exemption. */
    public static float explosion(float base) {
        return !Float.isFinite(base)||base<=0?0:(float)(base*DATA.perk.convertedBodyFraction*DATA.perk.pveExplosionMultiplier);
    }
    /** Authored radial attenuation, not a claim that a source measured this exact curve. */
    public static float splash(double distance) {
        if(!Double.isFinite(distance)||distance<0||distance>radius())return 0;
        return (float)Math.max(DATA.perk.radialFloor,1-distance/radius());
    }
}
