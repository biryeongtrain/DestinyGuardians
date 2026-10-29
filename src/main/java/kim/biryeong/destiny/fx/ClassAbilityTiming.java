package kim.biryeong.destiny.fx;

import com.google.gson.JsonParser;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.util.*;
import kim.biryeong.destiny.weapon.SwordTiming;

/** Source seconds plus the SAME entry blend used by PlayerAnimations. */
public final class ClassAbilityTiming {
    public record Timing(int contactTicks,int durationTicks) { }
    private static final Map<String,Timing> CLIPS=load();
    private ClassAbilityTiming() { }
    public static Timing of(String clip) {
        var timing=CLIPS.get(clip.startsWith("h15_")?clip:"h15_"+clip);
        if(timing==null)throw new IllegalArgumentException("Unknown source class clip "+clip);
        return timing;
    }
    private static Map<String,Timing> load() {
        try(var input=ClassAbilityTiming.class.getResourceAsStream("/destiny/animation/class_ability_w255.timing.json")) {
            if(input==null)throw new IOException("Missing source class timing");
            var document=JsonParser.parseReader(new InputStreamReader(input,StandardCharsets.UTF_8)).getAsJsonObject();
            var clips=new HashMap<String,Timing>();
            for(var value:document.getAsJsonArray("clips")) {
                var c=value.getAsJsonObject();
                int contact=(int)Math.ceil(c.get("contactSeconds").getAsDouble()*20-1e-7)+SwordTiming.START_TICKS;
                int duration=(int)Math.ceil(c.get("durationSeconds").getAsDouble()*20-1e-7)+SwordTiming.START_TICKS;
                if(contact<1||duration<=contact)throw new IOException("Invalid source phase");
                clips.put(c.get("name").getAsString(),new Timing(contact,duration));
            }
            return Map.copyOf(clips);
        } catch(IOException e) {throw new IllegalStateException(e);}
    }
}
