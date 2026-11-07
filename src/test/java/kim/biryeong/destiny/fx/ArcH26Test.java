package kim.biryeong.destiny.fx;

import com.google.gson.*;
import org.junit.jupiter.api.Test;
import java.nio.file.*;
import java.util.*;
import static org.junit.jupiter.api.Assertions.*;

/** Authored resource contract; live BM transforms and framebuffer have separate gates. */
class ArcH26Test {
    private JsonObject pack(String v) throws Exception {
        try(var in=getClass().getResourceAsStream("/destiny/animation/hunter_"+v+".animation.json")) {
            assertNotNull(in);return JsonParser.parseString(new String(in.readAllBytes(),java.nio.charset.StandardCharsets.UTF_8)).getAsJsonObject();
        }
    }
    private Map<String,JsonObject> clips(String v) throws Exception {
        var out=new HashMap<String,JsonObject>();
        for(var c:pack(v).getAsJsonArray("animations")){var o=c.getAsJsonObject();assertNull(out.put(o.get("name").getAsString(),o));}return out;
    }
    private double[] at(JsonObject clip,String bone,double time) {
        for(var v:clip.getAsJsonObject("animators").asMap().values()) {
            var a=v.getAsJsonObject();if(!a.get("name").getAsString().equals(bone))continue;
            for(var k:a.getAsJsonArray("keyframes")) {
                var key=k.getAsJsonObject();if(!key.get("channel").getAsString().equals("rotation")||Math.abs(key.get("time").getAsDouble()-time)>1e-7)continue;
                var p=key.getAsJsonArray("data_points").get(0).getAsJsonObject();return new double[]{p.get("x").getAsDouble(),p.get("y").getAsDouble(),p.get("z").getAsDouble()};
            }
        }
        throw new AssertionError(bone+" @ "+time);
    }
    @Test void archivedH26PreservesRigAndEighteenOtherClips() throws Exception {
        var old=clips("h23");var now=clips("h26");assertEquals(20,now.size());assertEquals(old.keySet(),now.keySet());
        for(var name:old.keySet())if(!Set.of("h15_super_arc_start","h15_super_arc_attack").contains(name))assertEquals(old.get(name),now.get(name),name);
        var before=JsonParser.parseString(Files.readString(Path.of("art/blockbench/animations/guardian_hunter_h23_r2.bbmodel"))).getAsJsonObject();
        var after=JsonParser.parseString(Files.readString(Path.of("art/blockbench/animations/guardian_hunter_h26_r2.bbmodel"))).getAsJsonObject();
        for(var e:before.entrySet())if(!Set.of("name","model_identifier","animations").contains(e.getKey()))assertEquals(e.getValue(),after.get(e.getKey()),e.getKey());
        assertEquals("guardian_hunter_h26_r2",pack("h26").get("model").getAsString());
    }
    @Test void archivedDeployContactAndRecoveryMatchH26ClipKeys() throws Exception {
        var c=clips("h26");var start=c.get("h15_super_arc_start");var attack=c.get("h15_super_arc_attack");
        // H26 is archived; W330 owns the live timing contract.
        assertEquals(11,1+start.get("length").getAsDouble()*20,1e-6);
        assertEquals(8,1+attack.get("length").getAsDouble()*20,1e-6);
        for(var v:attack.getAsJsonObject("animators").asMap().values()) {
            var bone=v.getAsJsonObject().get("name").getAsString();
            assertEquals(3,1+20*.10);at(attack,bone,.10);
        }
        assertEquals("once",start.get("loop").getAsString());
    }
    @Test void fastDriveHasLargeTorsoTurnAndPreservesCrouchedHeroThenSettles() throws Exception {
        var c=clips("h26");var a=c.get("h15_super_arc_attack");var s=c.get("h15_super_arc_start");var ready=c.get("h15_super_arc");
        assertTrue(at(a,"pc_chest",.10)[1]-at(a,"pc_chest",.05)[1]>50,"Torso snaps across the contact interval");
        assertTrue(at(s,"prfl_right_foreleg",.15)[0]<-60);assertTrue(at(s,"pll_left_leg",.15)[2]<-30);
        for(String bone:List.of("pra_right_arm","pc_chest","prl_right_leg","pli_left_item")) {
            assertArrayEquals(at(s,bone,.15),at(s,bone,.20),1e-6);
            assertArrayEquals(at(ready,bone,0),at(a,bone,.35),1e-6);
        }
        // Scalar Euler values can differ by one full turn; compare endpoint orientation modulo360.
        for(var v:s.getAsJsonObject("animators").asMap().values()) {
            var bone=v.getAsJsonObject().get("name").getAsString();var x=at(s,bone,.50);var y=at(ready,bone,0);
            for(int i=0;i<3;i++)assertEquals(0,Math.IEEEremainder(x[i]-y[i],360),1e-5,bone);
        }
    }
    @Test void finiteUniqueKeysKeepNoHorizontalRootMotion() throws Exception {
        var ids=new HashSet<String>();
        for(var c:clips("h26").values()) {
            assertTrue(ids.add(c.get("uuid").getAsString()));
            for(var v:c.getAsJsonObject("animators").asMap().values()) {
                var a=v.getAsJsonObject();var times=new HashSet<String>();
                for(var k:a.getAsJsonArray("keyframes")) {
                    var key=k.getAsJsonObject();assertTrue(ids.add(key.get("uuid").getAsString()));
                    assertTrue(times.add(key.get("channel").getAsString()+key.get("time")));
                    var point=key.getAsJsonArray("data_points").get(0).getAsJsonObject();
                    for(String axis:List.of("x","y","z"))assertTrue(Double.isFinite(point.get(axis).getAsDouble()));
                    if(key.get("channel").getAsString().equals("position")){assertEquals(0,point.get("x").getAsDouble());assertEquals(0,point.get("z").getAsDouble());}
                }
            }
        }
    }
}
