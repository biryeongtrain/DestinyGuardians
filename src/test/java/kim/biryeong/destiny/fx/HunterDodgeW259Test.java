package kim.biryeong.destiny.fx;

import com.google.gson.*;
import net.minecraft.world.entity.player.Input;
import org.junit.jupiter.api.Test;
import java.nio.file.*;
import java.util.*;
import static org.junit.jupiter.api.Assertions.*;

class HunterDodgeW259Test {
    @Test void twoKindsSelectAllFourDirectionsAndKeepDiagonalPolicy() {
        Input[] inputs = {Input.EMPTY,
                new Input(false,true,false,false,false,false,false),
                new Input(false,false,true,false,false,false,false),
                new Input(false,false,false,true,false,false,false)};
        String[] directions = {"forward","back","left","right"};
        for (int i=0;i<inputs.length;i++) {
            assertEquals("h15_roll_"+directions[i],PlayerAnimations.dodgeAnimation(inputs[i],false));
            assertEquals("h15_dodge_marksman_"+directions[i],PlayerAnimations.dodgeAnimation(inputs[i],true));
        }
        assertEquals("h15_dodge_marksman_forward",PlayerAnimations.dodgeAnimation(
                new Input(true,false,true,false,false,false,false),true));
    }
    @Test void sourceClipsRemainDistinctAndKeepOriginalDurationOnEngineGrid() throws Exception {
        var root=JsonParser.parseString(Files.readString(Path.of(
                "src/main/resources/destiny/animation/hunter_dodge_w259.animation.json"))).getAsJsonObject();
        var clips=new HashMap<String,JsonObject>();
        for (var value:root.getAsJsonArray("animations")) {
            var clip=value.getAsJsonObject();assertNull(clips.put(clip.get("name").getAsString(),clip));
            double length=clip.get("length").getAsDouble();
            assertTrue(Math.abs(length-1)<1e-8||Math.abs(length-29d/30)<1e-8);
            assertEquals("once",clip.get("loop").getAsString());
            var compiled=SourceAnimationGrid.compile(clip);
            assertEquals(length,compiled.get("length").getAsDouble());
            for (var animator:compiled.getAsJsonObject("animators").entrySet()) {
                var channels=new HashMap<String,List<Double>>();
                for(var k:animator.getValue().getAsJsonObject().getAsJsonArray("keyframes")) {
                    var key=k.getAsJsonObject();
                    channels.computeIfAbsent(key.get("channel").getAsString(),x->new ArrayList<>()).add(key.get("time").getAsDouble());
                }
                for(var times:channels.values()) {
                    Collections.sort(times);assertEquals(0d,times.getFirst());assertEquals(length,times.getLast());
                    for(int i=1;i<times.size()-1;i++)assertEquals(.025,times.get(i)-times.get(i-1),1e-8);
                }
            }
        }
        assertEquals(8,clips.size());
        for(String d:List.of("forward","back","left","right")) {
            var roll=clips.get("h15_roll_"+d);var step=clips.get("h15_dodge_marksman_"+d);
            assertNotNull(roll);assertNotNull(step);
            // The animator data, not just clip names, must differ by dodge type.
            assertNotEquals(roll.get("animators"),step.get("animators"));
        }
    }
}
