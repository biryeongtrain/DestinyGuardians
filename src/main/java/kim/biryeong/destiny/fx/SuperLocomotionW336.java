package kim.biryeong.destiny.fx;

import com.google.gson.*;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.*;
import java.util.function.Predicate;

/** Source-backed visual locomotion only; no entity movement or gameplay clocks. */
public final class SuperLocomotionW336 {
    public static final String HUNTER_RESOURCE="/destiny/animation/super_locomotion_hunter_w336.animation.json";
    public static final String CLASSES_RESOURCE="/destiny/animation/super_locomotion_classes_w336.animation.json";
    public static final String TITAN_RUNNING_RESOURCE="/destiny/animation/titan_running_w338.animation.json";
    private static final List<String> RESOURCE_ORDER=List.of(HUNTER_RESOURCE,CLASSES_RESOURCE,TITAN_RUNNING_RESOURCE);
    private static final Set<String> CLASS_BASES=Set.of("w230_hunter_spectral_blades","w229_titan_arc","w229_titan_solar",
            "w229_titan_void","w230_titan_burning_maul","w229_warlock_arc","w229_warlock_solar","w230_warlock_nova_warp");
    private SuperLocomotionW336() { }
    private static final class Sources {
        static final Map<String,JsonObject> FILES=load();
        static final Map<String,JsonObject> CLIPS=index();
        static Map<String,JsonObject> load() {
            var result=new LinkedHashMap<String,JsonObject>();
            for(String path:RESOURCE_ORDER)try(var in=SuperLocomotionW336.class.getResourceAsStream(path)) {
                if(in==null)continue; // An absent optional overlay keeps the existing authored fallback.
                var file=JsonParser.parseReader(new InputStreamReader(in,StandardCharsets.UTF_8)).getAsJsonObject();
                if(path.equals(TITAN_RUNNING_RESOURCE))requireR3(file,path);else requireR2(file,path);
                result.put(path,file);
            } catch(java.io.IOException e){throw new IllegalStateException("Cannot read W336 locomotion source: "+path,e);}
            return Map.copyOf(result);
        }
        static Map<String,JsonObject> index() {return indexSources(FILES);}
    }
    /** Explicit resource order is required: Map.copyOf iteration order is unspecified. */
    static Map<String,JsonObject> indexSources(Map<String,JsonObject> files) {
        var result=new HashMap<String,JsonObject>();var owners=new HashMap<String,String>();
        for(String path:files.keySet())if(!RESOURCE_ORDER.contains(path))
            throw new IllegalStateException("Foreign locomotion resource: "+path);
        for(String path:RESOURCE_ORDER) {
            var file=files.get(path);if(file==null)continue;
            boolean r3=path.equals(TITAN_RUNNING_RESOURCE);
            if(r3)requireR3(file,path);else requireR2(file,path);
            var seen=new HashSet<String>();
            for(var value:file.getAsJsonArray("animations")) {
                var clip=value.getAsJsonObject();String name=clip.get("name").getAsString();
                boolean hunter=name.equals("h15_super_arc")||name.startsWith("h15_super_arc_move_")||name.equals("h15_super_arc_air")
                        ||name.startsWith("w230_hunter_spectral_blades_");
                if(!seen.add(name)||!validName(name)||(path.equals(HUNTER_RESOURCE)!=hunter)
                        ||(!r3&&clip.has("source_revision")&&!"R2".equals(clip.get("source_revision").getAsString())))
                    throw new IllegalStateException("Foreign/duplicate W336 locomotion clip: "+name);
                if(result.containsKey(name)&&!(r3&&CLASSES_RESOURCE.equals(owners.get(name))))
                    throw new IllegalStateException("Foreign/duplicate W336 locomotion clip: "+name);
                double length=clip.get("length").getAsDouble();
                if(!Double.isFinite(length)||length<=0||!"loop".equals(clip.get("loop").getAsString()))
                    throw new IllegalStateException("Invalid W336 loop period: "+name);
                requireFamily(clip);result.put(name,clip);owners.put(name,path);
            }
        }
        return Map.copyOf(result);
    }
    /** R3 is a narrow run-only replacement, never a general third source family. */
    static void requireR3(JsonObject source,String path) {
        if(!TITAN_RUNNING_RESOURCE.equals(path)||!source.has("schema_version")||source.get("schema_version").getAsInt()!=1
                ||!source.has("source_revision")||!"R3".equals(source.get("source_revision").getAsString())
                ||!source.has("animations")||!source.get("animations").isJsonArray()||source.getAsJsonArray("animations").size()!=12)
            throw new IllegalStateException("Unsupported/non-R3 Titan running source: "+path);
        var seen=new HashSet<String>();
        for(var value:source.getAsJsonArray("animations")) {
            var clip=value.getAsJsonObject();String name=clip.has("name")?clip.get("name").getAsString():"";
            String family=name.startsWith("w229_titan_solar_move_")?"hammer_of_sol":"unarmed_fists_candidate";
            String base=name.startsWith("w229_titan_arc_move_")?"w229_titan_arc":name.startsWith("w229_titan_solar_move_")?"w229_titan_solar":name.startsWith("w229_titan_void_move_")?"w229_titan_void":"";
            String direction=base.isEmpty()?"":name.substring(base.length()+6);
            boolean hammer=family.equals("hammer_of_sol");
            String action=switch(direction){case "forward"->family+"__set0_point4";case "backward"->family+(hammer?"__set3_point1":"__set1_point1");case "left"->family+"__set2_point1";case "right"->family+(hammer?"__set1_point1":"__set3_point1");default->"";};
            if(base.isEmpty()||action.isEmpty()||!seen.add(name)||!clip.has("source_revision")||!"R3".equals(clip.get("source_revision").getAsString())
                    ||!clip.has("destiny_source_family")||!family.equals(clip.get("destiny_source_family").getAsString())
                    ||!clip.has("destiny_source_composed_action")||!action.equals(clip.get("destiny_source_composed_action").getAsString())
                    ||!clip.has("destiny_source_period_seconds")||!clip.has("length")
                    ||!Double.isFinite(clip.get("length").getAsDouble())||clip.get("length").getAsDouble()<=0
                    ||Math.abs(clip.get("length").getAsDouble()-clip.get("destiny_source_period_seconds").getAsDouble())>1e-9
                    ||!Double.isFinite(clip.get("destiny_source_period_seconds").getAsDouble())
                    ||!clip.has("loop")||!"loop".equals(clip.get("loop").getAsString()))
                throw new IllegalStateException("Foreign/duplicate/unmarked R3 Titan running clip: "+name);
        }
    }
    static void requireR2(JsonObject source,String path) {
        if(!source.has("schema_version")||source.get("schema_version").getAsInt()!=1||!source.has("animations")
                ||!source.get("animations").isJsonArray()||!source.has("source_revision")
                ||!"R2".equals(source.get("source_revision").getAsString()))
            throw new IllegalStateException("Unsupported/non-R2 W336 locomotion source: "+path);
    }
    static void requireFamily(JsonObject clip) {
        String name=clip.get("name").getAsString();
        if(name.startsWith("w230_hunter_spectral_blades_")&&(!clip.has("destiny_source_family")
                ||!"spectral_blades".equals(clip.get("destiny_source_family").getAsString())))
            throw new IllegalStateException("W336 Spectral requires the R2 named spectral_blades family: "+name);
    }
    private static boolean validName(String name) {
        for(String base:CLASS_BASES)if(name.startsWith(base+"_"))
            return Set.of("idle","air","move","move_forward","move_backward","move_left","move_right").contains(name.substring(base.length()+1));
        return name.equals("h15_super_arc")||name.equals("h15_super_arc_air")
                ||Set.of("h15_super_arc_move_forward","h15_super_arc_move_backward","h15_super_arc_move_left","h15_super_arc_move_right").contains(name);
    }
    public static String revision(String...paths) {
        try {
            var digest=MessageDigest.getInstance("SHA-256");
            for(String path:paths)digest.update((path+Sources.FILES.getOrDefault(path,new JsonObject())).getBytes(StandardCharsets.UTF_8));
            return HexFormat.of().formatHex(digest.digest()).substring(0,12);
        } catch(java.security.NoSuchAlgorithmException e){throw new IllegalStateException(e);}
    }
    public static JsonArray overlay(JsonArray original,String prefix) {
        var result=original.deepCopy();
        for(String path:RESOURCE_ORDER) {
            var file=Sources.FILES.get(path);if(file==null)continue;
            for(var value:file.getAsJsonArray("animations")) {
                var clip=value.getAsJsonObject();String name=clip.get("name").getAsString();if(!name.startsWith(prefix))continue;
                boolean replaced=false;
                for(int i=0;i<result.size();i++)if(name.equals(result.get(i).getAsJsonObject().get("name").getAsString())) {
                    result.set(i,clip.deepCopy());replaced=true;break;
                }
                if(!replaced)result.add(clip.deepCopy());
            }
        }
        return result;
    }
    public static boolean hasFamily(String loop) {return loop!=null&&Sources.CLIPS.containsKey(idle(loop));}
    static boolean floating(String loop) {
        var clip=Sources.CLIPS.get(idle(loop));
        return clip!=null&&clip.has("destiny_floating_locomotion")&&clip.get("destiny_floating_locomotion").getAsBoolean();
    }
    private static String idle(String loop) {return loop.equals("super_arc")||loop.equals("h15_super_arc")?"h15_super_arc":loop;}
    public enum Direction { IDLE, FORWARD, BACKWARD, LEFT, RIGHT }
    /** One instance per Playback: direction/stop hysteresis cannot leak between sessions. */
    public static final class Motion {
        private Direction direction=Direction.IDLE;
        private int stopped;
        private long lastTick=Long.MIN_VALUE;
        public Direction sample(double dx,double dz,float yaw,long tick) {
            if(lastTick==tick)return direction;lastTick=tick;
            double distance=dx*dx+dz*dz;
            if(!Double.isFinite(distance)||!Float.isFinite(yaw)||distance>4) {direction=Direction.IDLE;stopped=0;return direction;}
            double threshold=direction==Direction.IDLE?.000225:.000064;
            if(distance<=threshold) {
                if(++stopped>=2)direction=Direction.IDLE;
                return direction;
            }
            stopped=0;double radians=Math.toRadians(yaw);
            double forward=-Math.sin(radians)*dx+Math.cos(radians)*dz;
            double left=Math.cos(radians)*dx+Math.sin(radians)*dz;
            Direction candidate=Math.abs(forward)>=Math.abs(left)?(forward>=0?Direction.FORWARD:Direction.BACKWARD)
                    :(left>=0?Direction.LEFT:Direction.RIGHT);
            double best=Math.max(Math.abs(forward),Math.abs(left));
            double previous=switch(direction){case FORWARD->forward;case BACKWARD->-forward;case LEFT->left;case RIGHT->-left;default->0;};
            if(previous<best*.8)direction=candidate;
            return direction;
        }
    }
    /** Caller retains priority one-shots; this only chooses the ready underlay after they finish. */
    static String select(String loop,Direction direction,boolean grounded,Predicate<String> available) {
        return select(loop,direction,grounded,false,available);
    }
    static String select(String loop,Direction direction,boolean grounded,boolean floating,Predicate<String> available) {
        String idle=idle(loop),base=idle.equals("h15_super_arc")?idle:idle.endsWith("_idle")?idle.substring(0,idle.length()-5):idle;
        if(floating) {
            if(direction!=Direction.IDLE&&available.test(base+"_move"))return base+"_move";
            if(available.test(idle))return idle;
        }
        if(!grounded&&available.test(base+"_air"))return base+"_air";
        if(grounded&&direction!=Direction.IDLE) {
            String clip=base+"_move_"+direction.name().toLowerCase(Locale.ROOT);
            if(available.test(clip))return clip;
            if(available.test(base+"_move"))return base+"_move";
        }
        return available.test(idle)?idle:null;
    }
}
