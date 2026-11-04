package kim.biryeong.destiny.fx;

import com.google.gson.*;
import net.minecraft.client.resources.model.cuboid.CuboidModel;
import org.junit.jupiter.api.Test;
import java.io.*;
import java.nio.file.*;
import java.util.*;
import static org.junit.jupiter.api.Assertions.*;

class SuperPropsH27Test {
    static JsonObject model(String name) throws Exception {
        try(var in=SuperPropsH27Test.class.getResourceAsStream("/assets/destiny/models/item/"+name+".json")) {
            assertNotNull(in);return JsonParser.parseReader(new InputStreamReader(in,java.nio.charset.StandardCharsets.UTF_8)).getAsJsonObject();
        }
    }
    static List<JsonObject> es(JsonObject m) {
        return java.util.stream.StreamSupport.stream(m.getAsJsonArray("elements").spliterator(),false).map(JsonElement::getAsJsonObject).toList();
    }
    static double a(JsonObject e,String key,int axis){return e.getAsJsonArray(key).get(axis).getAsDouble();}
    static String name(JsonObject e){return e.get("name").getAsString();}
    @Test void threeModelsParseNativelyAndEditableGeometryMatches() throws Exception {
        for(String n:List.of("arc_staff_h27","shadow_bow_h27_drawn","shadow_bow_h27")) {
            var m=model(n);assertNotNull(CuboidModel.fromStream(new StringReader(m.toString())));
            var b=JsonParser.parseString(Files.readString(Path.of("art/blockbench/supers/"+n+".bbmodel"))).getAsJsonObject();
            assertEquals(es(m).size(),es(b).size());assertTrue(es(m).size()<450);
            for(int i=0;i<es(m).size();i++) {
                var e=es(m).get(i);var src=es(b).get(i);
                assertEquals(e.get("from"),src.get("from"));assertEquals(e.get("to"),src.get("to"));assertEquals(e.get("name"),src.get("name"));
                for(int k=0;k<3;k++){assertTrue(a(e,"from",k)<a(e,"to",k));assertTrue(a(e,"from",k)>=-16&&a(e,"to",k)<=32);}
            }
            var tex=Files.readAllBytes(Path.of("src/main/resources/assets/destiny/textures/item/supers/"+n+".png"));
            assertArrayEquals(tex,Base64.getDecoder().decode(b.getAsJsonArray("textures").get(0).getAsJsonObject().get("source").getAsString().split(",",2)[1]));
        }
    }
    @Test void staffHasSolidUpperBladeOpenLowerBladeAndNonGlowingWrappedGrip() throws Exception {
        var m=model("arc_staff_h27");assertEquals(model("arc_staff_h24").get("display"),m.get("display"));
        var e=es(m);assertEquals(42,e.stream().filter(x->name(x).startsWith("upper_spear_")).count());
        assertTrue(e.stream().anyMatch(x->name(x).startsWith("lower_slot_rail_")));
        double y=-13.5;
        assertFalse(e.stream().anyMatch(x->a(x,"from",0)<8&&a(x,"to",0)>8&&a(x,"from",1)<y&&a(x,"to",1)>y));
        var grip=e.stream().filter(x->name(x).startsWith("grip_diagonal_")).toList();assertEquals(28,grip.size());
        for(var x:grip){assertNotEquals(0,x.getAsJsonObject("rotation").get("angle").getAsDouble());assertEquals(0,x.get("light_emission").getAsInt());}
        var shaft=e.getFirst();for(double hand:new double[]{8,12})assertTrue(a(shaft,"from",1)<hand&&a(shaft,"to",1)>hand);
    }
    @Test void bowPreservesNativeHandRecipeNockAndStringGeometryAcrossRelease() throws Exception {
        var before=model("shadow_bow_h22_drawn");var now=model("shadow_bow_h27_drawn");
        assertEquals(before.get("display"),now.get("display"));
        var tail=es(now).subList(es(now).size()-5,es(now).size());
        for(int i=0;i<5;i++)for(String key:List.of("from","to","rotation"))assertEquals(es(before).get(201+i).get(key),tail.get(i).get(key));
        assertEquals(16.24,a(tail.get(2),"to",0),1e-8);
        assertEquals(32,es(now).stream().filter(x->name(x).startsWith("inward_spur_")).count());
        var limbs=es(now).stream().filter(x->name(x).startsWith("curved_limb_")).toList();assertEquals(120,limbs.size());
        assertTrue(limbs.stream().mapToDouble(x->a(x,"from",0)).max().orElseThrow()-limbs.stream().mapToDouble(x->a(x,"from",0)).min().orElseThrow()>4);
        var rest=es(model("shadow_bow_h27"));assertEquals(es(now).subList(0,272),rest.subList(0,272));
        assertFalse(rest.stream().anyMatch(x->name(x).endsWith("nocked_shaft")));
    }
    @Test void energyRootsTrackNewCurvedLimbsButNockDoesNotMove() {
        var s=SuperEnergyGeometry.bow(0);assertEquals(6,s.size());assertEquals(7.35,s.get(0).from().x);assertEquals(13,s.get(0).from().y);
        assertEquals(7.35,s.get(1).from().x);assertEquals(3,s.get(1).from().y);assertEquals(16.24,s.get(2).to().x);
    }
}
