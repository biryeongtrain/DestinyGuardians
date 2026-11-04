package kim.biryeong.destiny.weapon;

import com.google.gson.Gson;
import java.io.InputStreamReader;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.*;

/** Original base hash only; exact tuple whitelist and raw historical curves. No registry recursion. */
public final class PulseMonitorProfile {
    public static final String ID="pulse_monitor";
    public static final long HASH=972757866L;
    private static final Gson GSON=new Gson();
    private static final List<WeaponPerks.Roll> EXPECTED=List.of(
        new WeaponPerks.Roll("seventh_seraph_officer_revolver",3037520408L,3,HASH,903350103L),
        new WeaponPerks.Roll("cold_denial",1216130969L,3,HASH,330841869L),
        new WeaponPerks.Roll("dust_rock_blues",636912560L,3,HASH,3511609070L),
        new WeaponPerks.Roll("first_in_last_out",3616586446L,3,HASH,267999755L),
        new WeaponPerks.Roll("parcel_of_stardust_fell_to_earth",2217366863L,4,HASH,3424940310L),
        new WeaponPerks.Roll("dream_breaker",2931957300L,3,HASH,3785896921L),
        new WeaponPerks.Roll("coriolis_force",3512349612L,3,HASH,2568674372L),
        new WeaponPerks.Roll("edge_transit",218335759L,3,HASH,447678063L));
    private record Perk(String id,long hash,double healthThreshold,int handlingBonus,double handlingScalar,int lingerTicks) {}
    private record Quadratic(double evpp,double vpp,double offset) {
        double seconds(int stat) { return evpp*stat*stat+vpp*stat+offset; }
        boolean valid() { return Double.isFinite(evpp)&&Double.isFinite(vpp)&&Double.isFinite(offset); }
    }
    private record Curve(String id,int baseHandlingStat,Double snapshotScalar,Quadratic ready,Quadratic stow,Quadratic ads) {}
    private record Companion(String id,String perk,WeaponPerks.Roll roll) {}
    private record Data(String stage,Perk perk,List<WeaponPerks.Roll> weapons,List<Curve> curves,List<Companion> coSelections) {}
    private static final Map<String,WeaponCatalog.Entry> CATALOG=catalog();
    private static final Data DATA=load();
    private PulseMonitorProfile() {}
    private static <T> T read(String path,Class<T> type) {
        var stream=PulseMonitorProfile.class.getResourceAsStream(path);
        if(stream==null)throw new IllegalStateException("Missing Pulse Monitor resource "+path);
        try(var reader=new InputStreamReader(stream,StandardCharsets.UTF_8)) { return GSON.fromJson(reader,type); }
        catch(IOException e) { throw new IllegalStateException(e); }
    }
    private static Map<String,WeaponCatalog.Entry> catalog() {
        var map=new HashMap<String,WeaponCatalog.Entry>();
        for(var e:read("/destiny/weapons/w30.json",WeaponCatalog.Entry[].class))map.put(e.id(),e);
        return Map.copyOf(map);
    }
    private static void check(boolean ok,String detail) {
        if(!ok)throw new IllegalStateException("Invalid W200 Pulse Monitor: "+detail);
    }
    private static Data load() {
        var d=read("/destiny/weapons/w200-pulse-monitor.json",Data.class);
        check(d!=null && "W200".equals(d.stage) && d.perk!=null,"stage");
        var p=d.perk;
        check(ID.equals(p.id)&&p.hash==HASH&&p.healthThreshold==.30&&p.handlingBonus==50
            &&p.handlingScalar==.95&&p.lingerTicks==PulseMonitorCycle.LINGER_TICKS,"base mechanics");
        check(EXPECTED.equals(d.weapons)&&d.curves!=null&&d.curves.size()==8,"exact8 tuples/curves");
        var ids=new HashSet<String>();
        for(var c:d.curves) {
            boolean snapshot=c!=null && Set.of("dust_rock_blues","parcel_of_stardust_fell_to_earth").contains(c.id);
            check(c!=null&&ids.add(c.id)&&EXPECTED.stream().anyMatch(r->r.id().equals(c.id))
                &&c.baseHandlingStat>=0&&c.baseHandlingStat<=100
                &&Objects.equals(c.snapshotScalar,snapshot?.8:null)
                &&c.ready!=null&&c.ready.valid()&&c.stow!=null&&c.stow.valid()
                &&c.ads!=null&&c.ads.valid(),"raw curve identity");
        }
        var expectedPairs=Set.of(
            new Companion("dust_rock_blues","snapshot",new WeaponPerks.Roll("dust_rock_blues",636912560L,4,957782887L,1624251370L)),
            new Companion("parcel_of_stardust_fell_to_earth","threat_detector",new WeaponPerks.Roll("parcel_of_stardust_fell_to_earth",2217366863L,3,4071163871L,2514419370L)),
            new Companion("parcel_of_stardust_fell_to_earth","snapshot",new WeaponPerks.Roll("parcel_of_stardust_fell_to_earth",2217366863L,3,957782887L,2514419370L)),
            new Companion("dream_breaker","quickdraw",new WeaponPerks.Roll("dream_breaker",2931957300L,4,706527188L,1206254527L)),
            new Companion("dream_breaker","backup_plan",new WeaponPerks.Roll("dream_breaker",2931957300L,4,1600092898L,1206254527L)),
            new Companion("dream_breaker","frenzy",new WeaponPerks.Roll("dream_breaker",2931957300L,4,4104185692L,1206254527L)),
            new Companion("edge_transit","quickdraw",new WeaponPerks.Roll("edge_transit",218335759L,4,706527188L,2535579724L)));
        check(d.coSelections!=null&&d.coSelections.size()==7&&new HashSet<>(d.coSelections).equals(expectedPairs),"exact7 companion tuples");
        return new Data(d.stage,p,List.copyOf(d.weapons),List.copyOf(d.curves),List.copyOf(d.coSelections));
    }
    public static List<WeaponPerks.Roll> rolls() { return DATA.weapons; }
    public static boolean supports(WeaponCatalog.Entry entry) {
        return entry!=null&&entry.equals(CATALOG.get(entry.id()))&&EXPECTED.stream().anyMatch(r->r.id().equals(entry.id()));
    }
    public static int handlingBonus() { return DATA.perk.handlingBonus; }
    public static double handlingScalar() { return DATA.perk.handlingScalar; }
    public static double healthThreshold() { return DATA.perk.healthThreshold; }
    public static int lingerTicks() { return DATA.perk.lingerTicks; }
    public static boolean compatible(WeaponCatalog.Entry entry,String perk,WeaponPerks.Roll roll) {
        return supports(entry)&&DATA.coSelections.stream().anyMatch(c->c.id.equals(entry.id())&&c.perk.equals(perk)&&c.roll.equals(roll));
    }
    private static Curve curve(WeaponCatalog.Entry entry) {
        if(!supports(entry))throw new IllegalArgumentException("Noncanonical Pulse Monitor entry");
        return DATA.curves.stream().filter(c->c.id.equals(entry.id())).findFirst().orElseThrow();
    }
    private static int stat(Curve c,int bonus) { return (int)Math.clamp((long)c.baseHandlingStat+bonus,0L,100L); }
    private static int ticks(double seconds) {
        check(Double.isFinite(seconds)&&seconds>0&&seconds<=60,"safe timing");
        return Math.max(1,(int)Math.ceil(seconds*20));
    }
    /** totalBonus already includes Pulse +50 and every legal LIVE raw contributor.
     * rawScalar is the COMPLETE product: includes Pulse .95 exactly once, optional TD,
     * and ready-only Quickdraw .95. BP has no ready scalar. Never scale rounded ticks. */
    public static int handlingTicks(WeaponCatalog.Entry entry,int totalBonus,double rawScalar,boolean ready) {
        var c=curve(entry);
        if(!Double.isFinite(rawScalar)||rawScalar<=0||rawScalar>1)throw new IllegalArgumentException("Invalid raw duration product");
        int h=stat(c,totalBonus);
        double seconds=ready?c.ready.seconds(h):Math.max(c.stow.seconds(h),c.stow.seconds(100));
        return ticks(seconds*rawScalar);
    }
    /** Pulse's Handling changes ADS too; .95 is READY/STOW ONLY. Snapshot entry only. */
    public static int adsTicks(WeaponCatalog.Entry entry,int totalBonus,boolean snapshotEntering) {
        var c=curve(entry);
        if(snapshotEntering&&c.snapshotScalar==null)throw new IllegalArgumentException("No legal Snapshot pair");
        double seconds=c.ads.seconds(stat(c,totalBonus));
        if(snapshotEntering)seconds*=c.snapshotScalar;
        return Math.clamp(ticks(seconds),snapshotEntering?1:2,20);
    }
}
