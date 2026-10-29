package kim.biryeong.destiny.fx;

import com.google.gson.*;
import java.nio.charset.StandardCharsets;
import java.util.*;

/** Compile owned linear source curves to BetterModel's25ms evaluation grid.
 * Dense authored keys are retained in source files. BM consumes at most one key per
 * evaluation; passing sub-frame keys directly stretches the action beyond its length. */
public final class SourceAnimationGrid {
    private SourceAnimationGrid() { }
    public static JsonObject compile(JsonObject source) {
        JsonObject clip=source.deepCopy();
        double length=clip.get("length").getAsDouble();
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
                // Unknown/effect curves keep native handling. Our imported limb curves are numeric linear.
                if(!Set.of("rotation","position","scale").contains(channel.getKey())
                        ||keys.stream().anyMatch(k->!linearNumeric(k))) {keys.forEach(output::add);continue;}
                var times=new ArrayList<Double>();times.add(0d);
                for(int frame=1;frame/40d<length-.001;frame++)times.add(frame/40d);
                if(length>0)times.add(length);
                int index=0;
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
                    for(String axis:List.of("x","y","z")) {
                        double start=from.get(axis).getAsDouble(),end=to.get(axis).getAsDouble();
                        point.addProperty(axis,start+(end-start)*mix);
                    }
                    output.add(sample);
                }
            }
            animator.add("keyframes",output);
        }
        return clip;
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
