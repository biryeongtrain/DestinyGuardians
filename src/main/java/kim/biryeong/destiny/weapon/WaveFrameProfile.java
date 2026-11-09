package kim.biryeong.destiny.weapon;

import com.google.gson.Gson;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.*;

/** Exact selected intrinsic identities; Minecraft terrain/speed/damage adaptation is explicit in W78 data. */
public final class WaveFrameProfile {
    public record Profile(String id, long hash, long intrinsicHash, double length, double width,
                          double speed, double height, double stepUp, double stepDown,
                          float directMultiplier, float waveMultiplier) {
        public Profile {
            if (id == null || hash <= 0 || intrinsicHash <= 0 || !finite(length,width,speed,height,stepUp,stepDown)
                    || length < 1 || length > 24 || width < .5 || width > 8 || speed < .25 || speed > 2
                    || height < .1 || height > 3 || stepUp < 0 || stepUp > 1 || stepDown < 0 || stepDown > 2
                    || !Float.isFinite(directMultiplier) || directMultiplier < 0 || directMultiplier > 1
                    || !Float.isFinite(waveMultiplier) || waveMultiplier <= 0 || waveMultiplier > 3)
                throw new IllegalArgumentException("Unsafe W78 wave profile");
        }
    }
    private record Data(String stage, Profile[] weapons) {}
    private static final Map<String,Profile> ALL = load();
    private WaveFrameProfile() {}
    private static boolean finite(double... values) { for (double v:values) if(!Double.isFinite(v))return false; return true; }
    private static Map<String,Profile> load() {
        var input=WaveFrameProfile.class.getResourceAsStream("/destiny/weapons/w78-wave.json");
        if(input==null)throw new IllegalStateException("Missing W78 wave profiles");
        try(var reader=new InputStreamReader(input,StandardCharsets.UTF_8)) {
            var data=new Gson().fromJson(reader,Data.class);
            if(data==null||!"W78".equals(data.stage)||data.weapons==null||data.weapons.length!=2)
                throw new IllegalStateException("Invalid W78 data");
            var result=new LinkedHashMap<String,Profile>();
            for(var p:data.weapons) {
                var entry=WeaponCatalog.find(p.id).orElseThrow();
                if(WeaponCharacteristics.of(entry).bungieHash()!=p.hash
                        ||!(entry.family().equals("grenade_launcher")&&entry.frame().equals("wave")
                        ||entry.family().equals("heavy_grenade_launcher")&&entry.frame().equals("compressed_wave"))
                        ||result.putIfAbsent(p.id,p)!=null)throw new IllegalStateException("Invalid W78 intrinsic: "+p.id);
            }
            var forbearance = WeaponCatalog.find("forbearance").orElse(null);
            if (forbearance != null && forbearance.family().equals("grenade_launcher")
                    && forbearance.frame().equals("wave")
                    && WeaponCharacteristics.of(forbearance).bungieHash() == 613334176L) {
                var p = result.get("deafening_whisper");
                result.put(forbearance.id(), new Profile(forbearance.id(), 613334176L, 1395789926L,
                        p.length(), p.width(), p.speed(), p.height(), p.stepUp(), p.stepDown(),
                        p.directMultiplier(), p.waveMultiplier()));
            }
            return Map.copyOf(result);
        } catch(java.io.IOException e) { throw new IllegalStateException(e); }
    }
    public static Optional<Profile> of(WeaponCatalog.Entry entry) { return Optional.ofNullable(ALL.get(entry.id())); }
    public static List<Profile> all() { return ALL.values().stream().sorted(Comparator.comparing(Profile::id)).toList(); }

    /** Swept oriented ground strip vs a target's world AABB, all four 2D SAT axes.
     * X/Z directions must be a unit vector. Vertical contact includes standing feet, not airborne boxes above the crest.
     */
    public static boolean intersects(double fx,double fz,double ax,double ay,double az,double bx,double by,double bz,
                                     double width,double height,double minX,double minY,double minZ,double maxX,double maxY,double maxZ) {
        if(!finite(fx,fz,ax,ay,az,bx,by,bz,width,height,minX,minY,minZ,maxX,maxY,maxZ)
                ||Math.abs(fx*fx+fz*fz-1)>1e-5||width<=0||height<=0||minX>maxX||minY>maxY||minZ>maxZ)return false;
        if(maxY<Math.min(ay,by)||minY>Math.max(ay,by)+height)return false;
        double halfLength=Math.hypot(bx-ax,bz-az)/2+.001,halfWidth=width/2;
        double dx=(minX+maxX-ax-bx)/2,dz=(minZ+maxZ-az-bz)/2;
        double ex=(maxX-minX)/2,ez=(maxZ-minZ)/2;
        if(Math.abs(dx)>ex+Math.abs(fx)*halfLength+Math.abs(fz)*halfWidth)return false;
        if(Math.abs(dz)>ez+Math.abs(fz)*halfLength+Math.abs(fx)*halfWidth)return false;
        if(Math.abs(dx*fx+dz*fz)>halfLength+ex*Math.abs(fx)+ez*Math.abs(fz))return false;
        return Math.abs(-dx*fz+dz*fx)<=halfWidth+ex*Math.abs(fz)+ez*Math.abs(fx);
    }
}
