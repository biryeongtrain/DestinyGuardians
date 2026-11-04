package kim.biryeong.destiny.weapon;

import com.google.gson.Gson;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.*;

/** Base DDC row246, exact five socket pools and existing historical handling curves. */
public final class WellRoundedProfile {
    public static final String ID="well_rounded";
    public static final long HASH=744594675L;
    private record Perk(String id,long hash,int durationTicks,int maximumStacks,
                        int rangePerStack,int stabilityPerStack,int handlingPerStack) {}
    private record Quadratic(double evpp,double vpp,double offset) {
        double seconds(int stat) { return evpp*stat*stat+vpp*stat+offset; }
    }
    private record Curve(String id,int baseHandling,Quadratic ready,Quadratic stow,Quadratic ads) {}
    private record Companion(String id,String perk,WeaponPerks.Roll roll) {}
    private record Data(String stage,Perk perk,List<WeaponPerks.Roll> weapons,List<Curve> curves,List<Companion> coSelections) {}
    private static final Gson GSON=new Gson();
    private static final List<WeaponPerks.Roll> EXPECTED=List.of(
        new WeaponPerks.Roll("ammit_ar2",2119346509L,3,HASH,1723759242L),
        new WeaponPerks.Roll("allied_demand",1532276803L,3,HASH,3275836355L),
        new WeaponPerks.Roll("mindbender_s_ambition_adept",912150785L,4,HASH,4054654930L),
        new WeaponPerks.Roll("stormchaser",3652506829L,3,HASH,897699284L),
        new WeaponPerks.Roll("retraced_path",548958835L,3,HASH,2945646047L));
    // Raw JSON only during static initialization; never recurse through WeaponPerks/WeaponCatalog.
    private static final Map<String,WeaponCatalog.Entry> CATALOG=catalog();
    private static final Data DATA=load();
    private WellRoundedProfile() {}
    private static <T>T read(String path,Class<T> type) {
        var in=WellRoundedProfile.class.getResourceAsStream(path);
        if(in==null)throw new IllegalStateException("Missing Well-Rounded resource "+path);
        try(var reader=new InputStreamReader(in,StandardCharsets.UTF_8)) { return GSON.fromJson(reader,type); }
        catch(java.io.IOException e) { throw new IllegalStateException(e); }
    }
    private static Map<String,WeaponCatalog.Entry> catalog() {
        var out=new HashMap<String,WeaponCatalog.Entry>();
        for(var e:read("/destiny/weapons/w30.json",WeaponCatalog.Entry[].class))out.put(e.id(),e);
        return Map.copyOf(out);
    }
    private static void check(boolean ok,String why) { if(!ok)throw new IllegalStateException("Invalid W192 Well-Rounded: "+why); }
    private static Data load() {
        var d=read("/destiny/weapons/w192-well-rounded.json",Data.class);
        check(d!=null&&"W192".equals(d.stage)&&d.perk!=null,"definition");
        check(d.perk.equals(new Perk(ID,HASH,300,2,10,10,10))&&EXPECTED.equals(d.weapons),"base values/sockets");
        check(d.curves!=null&&d.curves.size()==5&&d.coSelections!=null,"curves");
        for(var c:d.curves)check(CATALOG.containsKey(c.id)&&c.baseHandling>=0&&c.baseHandling<=100
            &&c.ready!=null&&c.stow!=null&&c.ads!=null,"handling curve");
        return new Data(d.stage,d.perk,List.copyOf(d.weapons),List.copyOf(d.curves),List.copyOf(d.coSelections));
    }
    public static List<WeaponPerks.Roll> rolls() { return DATA.weapons; }
    public static boolean supports(WeaponCatalog.Entry entry) {
        return entry!=null&&entry.equals(CATALOG.get(entry.id()))&&EXPECTED.stream().anyMatch(r->r.id().equals(entry.id()));
    }
    static boolean compatible(WeaponCatalog.Entry entry,String perk,WeaponPerks.Roll roll) {
        String name=SnapshotAimProfile.ID.equals(perk)?"snapshot":perk;
        return supports(entry)&&DATA.coSelections.stream().anyMatch(c->c.id.equals(entry.id())&&c.perk.equals(name)&&c.roll.equals(roll));
    }
    private static Curve curve(WeaponCatalog.Entry entry) {
        if(!supports(entry))throw new IllegalArgumentException("Unsupported Well-Rounded source");
        return DATA.curves.stream().filter(c->c.id.equals(entry.id())).findFirst().orElseThrow();
    }
    private static int ticks(double seconds) {
        check(Double.isFinite(seconds)&&seconds>0,"safe timing");
        return Math.max(1,(int)Math.ceil(seconds*20));
    }
    public static int handlingTicks(WeaponCatalog.Entry entry,int bonus,double scalar,boolean ready) {
        var c=curve(entry);int stat=(int)Math.clamp((long)c.baseHandling+bonus,0L,100L);
        return ticks((ready?c.ready.seconds(stat):Math.max(c.stow.seconds(stat),c.stow.seconds(100)))*scalar);
    }
    public static int adsTicks(WeaponCatalog.Entry entry,int bonus,boolean snapshotEntering) {
        var c=curve(entry);int stat=(int)Math.clamp((long)c.baseHandling+bonus,0L,100L);
        // The only legal Snapshot companion is the special-ammo Mindbender shotgun: W68 .8.
        if(snapshotEntering&&!entry.id().equals("mindbender_s_ambition_adept"))throw new IllegalArgumentException("Unproved Snapshot pair");
        return Math.clamp(ticks(c.ads.seconds(stat)*(snapshotEntering?.8:1)),snapshotEntering?1:2,20);
    }
}
