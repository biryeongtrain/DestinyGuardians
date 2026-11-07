package kim.biryeong.destiny.fx;

import com.google.gson.*;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.*;

/** W330 source-only overlays and their explicitly provisional contact contracts. */
public final class MeleeSuperAnimationTiming {
    public static final String ARC_RESOURCE="/destiny/animation/arc_staff_w330.animation.json";
    public static final String SPECTRAL_RESOURCE="/destiny/animation/spectral_blades_w330.animation.json";
    private MeleeSuperAnimationTiming() { }
    private static final class Sources {
        static final Map<String,JsonObject> FILES=load();
        static final Map<String,JsonObject> CLIPS=clips();
        static final Map<String,String> VALIDATION_ERRORS=validate();
        static Map<String,String> validate() {
            var errors=new HashMap<String,String>();
            for(var file:FILES.entrySet())try {
                for(var clip:file.getValue().getAsJsonArray("animations"))SourceAnimationGrid.compile(clip.getAsJsonObject());
            } catch(RuntimeException e) {errors.put(file.getKey(),e.getMessage()==null?e.getClass().getSimpleName():e.getMessage());}
            return Map.copyOf(errors);
        }
        static Map<String,JsonObject> load() {
            var result=new LinkedHashMap<String,JsonObject>();
            for(String path:List.of(ARC_RESOURCE,SPECTRAL_RESOURCE))try(var in=MeleeSuperAnimationTiming.class.getResourceAsStream(path)) {
                if(in==null)continue;
                var source=JsonParser.parseReader(new InputStreamReader(in,StandardCharsets.UTF_8)).getAsJsonObject();
                if(source.get("schema_version").getAsInt()!=1||!source.has("animations"))
                    throw new IllegalArgumentException("Unsupported W330 source "+path);
                result.put(path,source);
            } catch(java.io.IOException e) {throw new IllegalStateException("Cannot read W330 source "+path,e);}
            return Map.copyOf(result);
        }
        static Map<String,JsonObject> clips() {
            var result=new HashMap<String,JsonObject>();
            for(var source:FILES.values())for(var value:source.getAsJsonArray("animations")) {
                var clip=value.getAsJsonObject();String name=clip.get("name").getAsString();
                if(result.put(name,clip)!=null)throw new IllegalArgumentException("Duplicate W330 clip "+name);
            }
            return Map.copyOf(result);
        }
    }
    /** Content-addressed generated model names cannot silently retain an older source overlay. */
    public static String revision(String path) {
        var source=Sources.FILES.get(path);if(source==null)return "unavailable";
        try {return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256")
                .digest(source.toString().getBytes(StandardCharsets.UTF_8))).substring(0,12);}
        catch(java.security.NoSuchAlgorithmException e){throw new IllegalStateException(e);}
    }
    public static JsonArray overlay(JsonArray original,String path) {
        require(path);
        var result=original.deepCopy();var source=Sources.FILES.get(path);
        for(var value:source.getAsJsonArray("animations")) {
            var clip=value.getAsJsonObject();String name=clip.get("name").getAsString();boolean replaced=false;
            for(int i=0;i<result.size();i++)if(name.equals(result.get(i).getAsJsonObject().get("name").getAsString())) {
                result.set(i,clip.deepCopy());replaced=true;break;
            }
            if(!replaced)result.add(clip.deepCopy());
        }
        return result;
    }
    public static boolean available(String path) {
        try {require(path);return true;}
        catch(IllegalStateException e) {kim.biryeong.destiny.DestinyGuardians.LOGGER.error(e.getMessage());return false;}
    }
    /** Targeted new motions must never silently activate using only the pre-W330 clips. */
    public static void require(String path) {
        var source=Sources.FILES.get(path);
        if(source==null)throw new IllegalStateException("Required W330 source overlay is missing: "+path);
        if(Sources.VALIDATION_ERRORS.containsKey(path))throw new IllegalStateException(
                "Malformed required W330 source overlay: "+path+": "+Sources.VALIDATION_ERRORS.get(path));
        String prefix=path.equals(ARC_RESOURCE)?"h15_super_arc_":"w230_hunter_spectral_blades_";
        var phases=path.equals(ARC_RESOURCE)?List.of("start","start_air","attack","attack_weak_2","attack_weak_3","attack_air")
                :List.of("start","start_air","attack","attack2","attack3","attack_air","attack3_air","heavy","heavy_air");
        for(String phase:phases) {
            var clip=Sources.CLIPS.get(prefix+phase);
            if(clip==null||number(clip,"length",0)<=0||!clip.has("destiny_quaternion_sampling")
                    ||!clip.get("destiny_quaternion_sampling").getAsBoolean())
                throw new IllegalStateException("Required W330 source clip missing/malformed: "+prefix+phase);
            if((phase.startsWith("attack")||phase.startsWith("heavy"))
                    &&(!clip.has("destiny_contact_seconds")||!clip.has("destiny_recovery_seconds")
                    ||!clip.has("destiny_contact_provisional")||!clip.get("destiny_contact_provisional").getAsBoolean()))
                throw new IllegalStateException("W330 contact must declare its provisional source-kinematic timing: "+prefix+phase);
            if(phase.startsWith("attack")||phase.startsWith("heavy")) {
                double length=number(clip,"length",0),contact=number(clip,"destiny_contact_seconds",0),
                        recovery=number(clip,"destiny_recovery_seconds",0);
                if(contact>length||recovery<contact||recovery>length+1e-6)
                    throw new IllegalStateException("W330 contact/recovery exceeds its source motion: "+prefix+phase);
            }
        }
    }
    public static boolean has(String clip) {return Sources.CLIPS.containsKey(clip);}
    private static double number(JsonObject clip,String field,double fallback) {
        if(clip==null||!clip.has(field))return fallback;
        double value=clip.get(field).getAsDouble();
        if(!Double.isFinite(value)||value<0)throw new IllegalArgumentException("Invalid W330 "+field);
        return value;
    }
    public static int entryBlendTicks(String name) {return (int)Math.clamp(number(Sources.CLIPS.get(name),"destiny_entry_blend_ticks",1),0,4);}
    public static int exitBlendTicks(String name) {return has(name)?(int)Math.clamp(number(Sources.CLIPS.get(name),"destiny_exit_blend_ticks",2),0,4):0;}
    public static int durationTicks(String name,int fallback) {
        var clip=Sources.CLIPS.get(name);return clip==null?fallback:seconds(number(clip,"length",0))+entryBlendTicks(name);
    }
    public static int playbackTicks(String name,int fallback) {return has(name)?durationTicks(name,fallback)+exitBlendTicks(name):fallback;}
    public static int contactTicks(String name,int fallback) {
        var clip=Sources.CLIPS.get(name);if(clip==null||!clip.has("destiny_contact_seconds"))return fallback;
        return Math.clamp(seconds(number(clip,"destiny_contact_seconds",0))+entryBlendTicks(name),1,durationTicks(name,fallback));
    }
    public static int recoveryTicks(String name,int fallback) {
        var clip=Sources.CLIPS.get(name);if(clip==null)return fallback;
        return Math.max(contactTicks(name,1),seconds(number(clip,"destiny_recovery_seconds",number(clip,"length",0)))+entryBlendTicks(name));
    }
    public static int arcDeploySwingTicks(int fallback) {
        var source=Sources.FILES.get(ARC_RESOURCE);if(source==null||!source.has("destiny_deploy_swing_seconds"))return fallback;
        return seconds(number(source,"destiny_deploy_swing_seconds",0))+entryBlendTicks("h15_super_arc_start");
    }
    public static String arcAttack(boolean grounded,int combo) {
        String phase=!grounded?"h15_super_arc_attack_air":switch(Math.floorMod(combo,3)) {
            case 1->"h15_super_arc_attack_weak_2";case 2->"h15_super_arc_attack_weak_3";default->"h15_super_arc_attack";
        };
        return has(phase)?phase:"h15_super_arc_attack";
    }
    public static String spectralAttack(boolean grounded,boolean heavy,int combo) {
        String phase=heavy?(grounded?"heavy":"heavy_air"):grounded?switch(Math.floorMod(combo,3)) {
            case 1->"attack2";case 2->"attack3";default->"attack";
        }:Math.floorMod(combo,3)==2?"attack3_air":"attack_air";
        String clip="w230_hunter_spectral_blades_"+phase;
        return has(clip)?phase:heavy?"attack3":Math.floorMod(combo,2)==1?"attack2":"attack";
    }
    private static int seconds(double value) {return Math.max(0,(int)Math.ceil(value*20-1e-8));}
}
