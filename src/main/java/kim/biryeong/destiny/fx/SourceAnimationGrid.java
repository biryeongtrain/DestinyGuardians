package kim.biryeong.destiny.fx;

import com.google.gson.*;
import java.nio.charset.StandardCharsets;
import java.util.*;
import org.joml.Quaternionf;
import org.joml.Vector3f;

/** Compile owned linear source curves to BetterModel's25ms evaluation grid.
 * Dense authored keys are retained in source files. BM consumes at most one key per
 * evaluation; passing sub-frame keys directly stretches the action beyond its length. */
public final class SourceAnimationGrid {
    private SourceAnimationGrid() { }
    public static JsonObject compile(JsonObject source) {
        JsonObject clip=source.deepCopy();
        double length=clip.get("length").getAsDouble();
        boolean quaternion=clip.has("destiny_quaternion_sampling")&&clip.get("destiny_quaternion_sampling").getAsBoolean();
        for(var entry:clip.getAsJsonObject("animators").entrySet()) {
            var animator=entry.getValue().getAsJsonObject();
            if(!animator.has("keyframes"))continue;
            var channels=new LinkedHashMap<String,List<JsonObject>>();
            for(var value:animator.getAsJsonArray("keyframes")) {
                var key=value.getAsJsonObject();
                channels.computeIfAbsent(key.get("channel").getAsString(),k->new ArrayList<>()).add(key);
            }
            var output=new JsonArray();
            for(var channel:channels.entrySet()) {
                var keys=channel.getValue();keys.sort(Comparator.comparingDouble(k->k.get("time").getAsDouble()));
                if(quaternion&&channel.getKey().equals("rotation")&&keys.stream().anyMatch(k->!linearNumeric(k)))
                    throw new IllegalArgumentException("Opt-in W330 rotations require finite linear numeric keys");
                // Unknown/effect curves keep native handling. Our imported limb curves are numeric linear.
                if(!Set.of("rotation","position","scale").contains(channel.getKey())
                        ||keys.stream().anyMatch(k->!linearNumeric(k))) {keys.forEach(output::add);continue;}
                var times=new ArrayList<Double>();times.add(0d);
                for(int frame=1;frame/40d<length-.001;frame++)times.add(frame/40d);
                if(length>0)times.add(length);
                int index=0;
                Vector3f previousEuler=null;
                for(double time:times) {
                    while(index+1<keys.size()&&keys.get(index+1).get("time").getAsDouble()<=time)index++;
                    var before=keys.get(index);var after=keys.get(Math.min(index+1,keys.size()-1));
                    double a=before.get("time").getAsDouble(),b=after.get("time").getAsDouble();
                    double mix=b<=a?0:Math.clamp((time-a)/(b-a),0,1);
                    var sample=before.deepCopy();sample.addProperty("time",time);
                    sample.addProperty("uuid",UUID.nameUUIDFromBytes((clip.get("name").getAsString()+"/"+entry.getKey()
                            +"/"+channel.getKey()+"/"+time).getBytes(StandardCharsets.UTF_8)).toString());
                    var point=sample.getAsJsonArray("data_points").get(0).getAsJsonObject();
                    var from=before.getAsJsonArray("data_points").get(0).getAsJsonObject();
                    var to=after.getAsJsonArray("data_points").get(0).getAsJsonObject();
                    if(quaternion&&channel.getKey().equals("rotation")) {
                        // W330 exports target Blockbench Rz*Ry*Rx quaternions. BM3.5.1 has no
                        // quaternion_interpolation field: bake once here, preserving rotation_global.
                        var rotation=quaternion(before).slerp(quaternion(after),(float)mix).normalize();
                        Vector3f reference=previousEuler==null?new Vector3f(from.get("x").getAsFloat(),
                                from.get("y").getAsFloat(),from.get("z").getAsFloat()):previousEuler;
                        var euler=continuousEuler(rotation,reference);previousEuler=euler;
                        point.addProperty("x",euler.x);point.addProperty("y",euler.y);point.addProperty("z",euler.z);
                        sample.remove("destiny_quaternion");
                    } else for(String axis:List.of("x","y","z")) {
                        double start=from.get(axis).getAsDouble(),end=to.get(axis).getAsDouble();
                        point.addProperty(axis,start+(end-start)*mix);
                    }
                    output.add(sample);
                }
            }
            animator.add("keyframes",output);
        }
        if(quaternion) {
            clip.remove("destiny_quaternion_sampling");
            clip.addProperty("destiny_quaternion_baked_hz",40);
        }
        return clip;
    }

    private static Quaternionf quaternion(JsonObject key) {
        if(!key.has("destiny_quaternion")||key.getAsJsonArray("destiny_quaternion").size()!=4)
            throw new IllegalArgumentException("Opt-in W330 rotation is missing its target quaternion");
        var q=key.getAsJsonArray("destiny_quaternion");var result=new Quaternionf(q.get(0).getAsFloat(),
                q.get(1).getAsFloat(),q.get(2).getAsFloat(),q.get(3).getAsFloat());
        if(!Float.isFinite(result.lengthSquared())||result.lengthSquared()<1e-8)
            throw new IllegalArgumentException("Invalid W330 rotation quaternion");
        return result.normalize();
    }
    /** Equivalent Euler branches are chosen relative to the preceding pose, including gimbal crossings. */
    static Vector3f continuousEuler(Quaternionf rotation,Vector3f previous) {
        var canonical=rotation.getEulerAnglesZYX(new Vector3f()).mul((float)(180/Math.PI));
        var alternate=new Vector3f(canonical.x+180,180-canonical.y,canonical.z+180);
        nearest(canonical,previous);nearest(alternate,previous);
        return canonical.distanceSquared(previous)<=alternate.distanceSquared(previous)?canonical:alternate;
    }
    private static void nearest(Vector3f angles,Vector3f reference) {
        angles.x+=360*Math.round((reference.x-angles.x)/360);
        angles.y+=360*Math.round((reference.y-angles.y)/360);
        angles.z+=360*Math.round((reference.z-angles.z)/360);
    }

    private static boolean linearNumeric(JsonObject key) {
        if(!key.has("interpolation")||!"linear".equals(key.get("interpolation").getAsString())
                ||!key.has("data_points")||!key.get("data_points").isJsonArray()
                ||key.getAsJsonArray("data_points").size()!=1
                ||!key.getAsJsonArray("data_points").get(0).isJsonObject())return false;
        var point=key.getAsJsonArray("data_points").get(0).getAsJsonObject();
        for(String axis:List.of("x","y","z")) {
            var value=point.get(axis);
            if(value==null||!value.isJsonPrimitive())return false;
            var number=value.getAsJsonPrimitive();
            if(!number.isNumber()&&!number.isString())return false;
            try {if(!Double.isFinite(number.getAsDouble()))return false;}
            catch(NumberFormatException ignored) {return false;}
        }
        return true;
    }
}
