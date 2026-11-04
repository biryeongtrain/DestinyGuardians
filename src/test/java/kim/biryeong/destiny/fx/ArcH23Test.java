package kim.biryeong.destiny.fx;

import com.google.gson.*;
import org.junit.jupiter.api.Test;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;
import static org.junit.jupiter.api.Assertions.*;

/** Saved animation contract, not a substitute for native pixels/physics. */
class ArcH23Test {
    private Map<String,JsonObject> clips(String version) throws Exception {
        try (var in=getClass().getResourceAsStream("/destiny/animation/hunter_"+version+".animation.json")) {
            assertNotNull(in);
            var out=new HashMap<String,JsonObject>();
            for(var v:JsonParser.parseReader(new InputStreamReader(in,StandardCharsets.UTF_8)).getAsJsonObject().getAsJsonArray("animations")) {
                var c=v.getAsJsonObject();assertNull(out.put(c.get("name").getAsString(),c));
            }
            return out;
        }
    }
    private JsonObject key(JsonObject c,String bone,String channel,double t) {
        for(var v:c.getAsJsonObject("animators").asMap().values()) {
            var a=v.getAsJsonObject(); if(!a.get("name").getAsString().equals(bone))continue;
            for(var k:a.getAsJsonArray("keyframes")) {
                var x=k.getAsJsonObject();
                if(x.get("channel").getAsString().equals(channel)&&Math.abs(x.get("time").getAsDouble()-t)<1e-8)
                    return x.getAsJsonArray("data_points").get(0).getAsJsonObject();
            }
        }
        throw new AssertionError(bone+channel+t);
    }
    @Test void preservesRigAndEighteenExistingClipsIncludingVoidAndSolar() throws Exception {
        var old=clips("h22");var now=clips("h23");assertEquals(20,now.size());
        for(var name:old.keySet())if(!name.equals("h15_super_arc_start"))assertEquals(old.get(name),now.get(name),name);
        var a=JsonParser.parseString(Files.readString(Path.of("art/blockbench/animations/guardian_hunter_h22.bbmodel"))).getAsJsonObject();
        var b=JsonParser.parseString(Files.readString(Path.of("art/blockbench/animations/guardian_hunter_h23_r2.bbmodel"))).getAsJsonObject();
        for(var e:a.entrySet())if(!Set.of("name","model_identifier","animations").contains(e.getKey()))assertEquals(e.getValue(),b.get(e.getKey()),e.getKey());
        // Historical H23 resource contract; active-version contract is tested by ArcH26Test.
    }
    @Test void singleSummonHoldsWideCrouchThenReturnsToReadyBeforeInputUnlock() throws Exception {
        var c=clips("h23");var start=c.get("h15_super_arc_start");var idle=c.get("h15_super_arc");
        assertEquals("once",start.get("loop").getAsString());
        assertEquals(18,start.get("length").getAsDouble()*20+1,1e-8);
        for(var v:start.getAsJsonObject("animators").asMap().values()) {
            String bone=v.getAsJsonObject().get("name").getAsString();
            assertEquals(key(start,bone,"rotation",.20),key(start,bone,"rotation",.45));
            assertEquals(key(idle,bone,"rotation",0),key(start,bone,"rotation",.85));
        }
        assertTrue(key(start,"prfl_right_foreleg","rotation",.20).get("x").getAsDouble() < -60);
        assertTrue(key(start,"pll_left_leg","rotation",.20).get("z").getAsDouble() < -30);
    }
    @Test void roamingLoopHasAlternatingLegsAndNoHorizontalRootMotion() throws Exception {
        var move=clips("h23").get("h15_super_arc_move");assertEquals("loop",move.get("loop").getAsString());
        assertEquals(.6,move.get("length").getAsDouble());
        for(String bone:List.of("prl_right_leg","pll_left_leg")) {
            assertEquals(key(move,bone,"rotation",0),key(move,bone,"rotation",.6));
            assertEquals(-key(move,bone,"rotation",.15).get("x").getAsDouble(),key(move,bone,"rotation",.45).get("x").getAsDouble(),1e-6);
        }
        for(var v:move.getAsJsonObject("animators").asMap().values())for(var k:v.getAsJsonObject().getAsJsonArray("keyframes")) {
            var x=k.getAsJsonObject();if(!x.get("channel").getAsString().equals("position"))continue;
            var p=x.getAsJsonArray("data_points").get(0).getAsJsonObject();assertEquals(0,p.get("x").getAsDouble());assertEquals(0,p.get("z").getAsDouble());
        }
    }
}
