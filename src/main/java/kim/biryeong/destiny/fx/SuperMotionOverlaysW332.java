package kim.biryeong.destiny.fx;

import com.google.gson.*;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.*;

/** Source visual overlays only. Gameplay release, charge, recovery and damage clocks remain with their sessions. */
public final class SuperMotionOverlaysW332 {
    public static final String RESOURCE="/destiny/animation/super_motion_w332.animation.json";
    private static final Set<String> REQUIRED=Set.of("h15_super_void_attack","h15_super_void_attack_air",
            "w230_warlock_nova_warp_charge_idle","w230_warlock_nova_warp_charge_exit","w229_warlock_solar_start_air");
    private SuperMotionOverlaysW332() { }
    private static final class Source {
        static final JsonObject FILE=load();
        static final Map<String,JsonObject> CLIPS=clips();
        static final String ERROR=validate();
        static JsonObject load() {
            try(var in=SuperMotionOverlaysW332.class.getResourceAsStream(RESOURCE)) {
                return in==null?null:JsonParser.parseReader(new InputStreamReader(in,StandardCharsets.UTF_8)).getAsJsonObject();
            } catch(java.io.IOException e) {throw new IllegalStateException("Cannot read "+RESOURCE,e);}
        }
        static Map<String,JsonObject> clips() {
            if(FILE==null)return Map.of();
            if(!FILE.has("schema_version")||FILE.get("schema_version").getAsInt()!=1||!FILE.has("animations"))
                throw new IllegalStateException("Unsupported W332 source overlay schema");
            var result=new HashMap<String,JsonObject>();
            for(var value:FILE.getAsJsonArray("animations")) {
                var clip=value.getAsJsonObject();String name=clip.get("name").getAsString();
                if(!REQUIRED.contains(name)||result.put(name,clip)!=null)throw new IllegalStateException("Foreign/duplicate W332 source clip: "+name);
            }
            return Map.copyOf(result);
        }
        static String validate() {
            try {
                if(!CLIPS.keySet().containsAll(REQUIRED))throw new IllegalStateException("Missing required W332 source clips: "+REQUIRED);
                for(var clip:CLIPS.values()) {
                    double length=clip.get("length").getAsDouble();
                    if(!Double.isFinite(length)||length<=0||!clip.has("destiny_quaternion_sampling")
                            ||!clip.get("destiny_quaternion_sampling").getAsBoolean())throw new IllegalStateException("Invalid W332 source clip");
                    SourceAnimationGrid.compile(clip);
                }
                return null;
            } catch(RuntimeException e) {return e.getMessage()==null?e.getClass().getSimpleName():e.getMessage();}
        }
    }
    public static void require() {
        if(Source.ERROR!=null)throw new IllegalStateException("Required W332 visual overlay unavailable: "+Source.ERROR);
    }
    public static boolean available() {
        try{require();return true;}catch(IllegalStateException e){kim.biryeong.destiny.DestinyGuardians.LOGGER.error(e.getMessage());return false;}
    }
    public static boolean has(String clip) {return Source.CLIPS.containsKey(clip);}
    public static String revision() {
        if(Source.FILE==null)return "unavailable";
        try{return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256")
                .digest(Source.FILE.toString().getBytes(StandardCharsets.UTF_8))).substring(0,12);}
        catch(java.security.NoSuchAlgorithmException e){throw new IllegalStateException(e);}
    }
    /** Prefix selection keeps Hunter and class-limb rigs separate without copying or mutating the source JSON. */
    public static JsonArray overlay(JsonArray original,String prefix) {
        require();var result=original.deepCopy();
        for(var value:Source.FILE.getAsJsonArray("animations")) {
            var clip=value.getAsJsonObject();String name=clip.get("name").getAsString();
            if(!name.startsWith(prefix))continue;
            boolean replaced=false;
            for(int i=0;i<result.size();i++)if(name.equals(result.get(i).getAsJsonObject().get("name").getAsString())) {
                result.set(i,clip.deepCopy());replaced=true;break;
            }
            if(!replaced)result.add(clip.deepCopy());
        }
        return result;
    }
    private static int blend(String name,String field,int fallback) {
        var clip=Source.CLIPS.get(name);return clip==null||!clip.has(field)?fallback:Math.clamp(clip.get(field).getAsInt(),0,4);
    }
    public static int entryBlendTicks(String name){return blend(name,"destiny_entry_blend_ticks",1);}
    public static int exitBlendTicks(String name){return blend(name,"destiny_exit_blend_ticks",2);}
    public static int playbackTicks(String name,int fallback) {
        var clip=Source.CLIPS.get(name);return clip==null?fallback:(int)Math.ceil(clip.get("length").getAsDouble()*20-1e-8)
                +entryBlendTicks(name)+exitBlendTicks(name);
    }
}
