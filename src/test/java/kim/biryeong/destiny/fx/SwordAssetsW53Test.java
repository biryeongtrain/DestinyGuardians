package kim.biryeong.destiny.fx;

import com.google.gson.*;
import kim.biryeong.destiny.weapon.SwordProfile;
import org.junit.jupiter.api.Test;
import java.nio.file.*;
import java.io.*;
import java.util.*;
import static org.junit.jupiter.api.Assertions.*;

/** Asset/installer contracts, not native Minecraft animation or visual fidelity evidence. */
class SwordAssetsW53Test {
    private static final Set<String> EXPECTED=Set.of("h15_sword_light_1","h15_sword_light_2","h15_sword_light_3",
            "h15_sword_uppercut","h15_sword_dash","h15_sword_slam","h15_sword_vortex","h15_sword_caster");
    private JsonArray clips() throws IOException {
        try(var stream=getClass().getResourceAsStream(SwordModelAssets.RESOURCE)) {
            assertNotNull(stream);
            return JsonParser.parseReader(new InputStreamReader(stream,java.nio.charset.StandardCharsets.UTF_8))
                    .getAsJsonObject().getAsJsonArray("animations");
        }
    }
    @Test void actualEightClipsHaveBoundedFiniteFullBodyChannels() throws Exception {
        var names=new HashSet<String>();
        for(var entry:clips()) {
            var clip=entry.getAsJsonObject();String name=clip.get("name").getAsString();
            assertTrue(names.add(name));
            double length=clip.get("length").getAsDouble();
            assertTrue(length>0&&length<=(name.contains("light_")?.55:1.2),name);
            var bones=new HashSet<String>();
            for(var e:clip.getAsJsonObject("animators").asMap().values()) {
                var animator=e.getAsJsonObject();bones.add(animator.get("name").getAsString());
                for(var k:animator.getAsJsonArray("keyframes")) {
                    var frame=k.getAsJsonObject();double time=frame.get("time").getAsDouble();
                    assertTrue(Double.isFinite(time)&&time>=0&&time<=length+1e-6);
                    for(var p:frame.getAsJsonArray("data_points"))for(String axis:List.of("x","y","z"))
                        assertTrue(Double.isFinite(p.getAsJsonObject().get(axis).getAsDouble()),name);
                }
            }
            assertTrue(bones.containsAll(Set.of("player_root","pc_chest","pra_right_arm","pri_right_item",
                    "pla_left_arm","prl_right_leg","pll_left_leg")),name);
        }
        assertEquals(EXPECTED,names);
    }
    @Test void sourceArtPreservesHunterRigAndEveryInheritedClip() throws Exception {
        var base=JsonParser.parseString(Files.readString(Path.of("art/blockbench/animations/guardian_hunter_h26_r2.bbmodel"))).getAsJsonObject();
        var art=JsonParser.parseString(Files.readString(Path.of("art/blockbench/animations/guardian_sword_w53.bbmodel"))).getAsJsonObject();
        for(String field:base.keySet())if(!Set.of("name","model_identifier","animations").contains(field))
            assertEquals(base.get(field),art.get(field),field);
        var byName=new HashMap<String,JsonElement>();
        for(var a:art.getAsJsonArray("animations"))assertNull(byName.put(a.getAsJsonObject().get("name").getAsString(),a));
        for(var a:base.getAsJsonArray("animations"))assertEquals(a,byName.remove(a.getAsJsonObject().get("name").getAsString()));
        assertEquals(EXPECTED,byName.keySet());
        for(var a:clips())assertEquals(a,byName.get(a.getAsJsonObject().get("name").getAsString()));
    }
    @Test void installerUsesDistinctModelNameAndRemapsWithoutEditingTemplate() throws Exception {
        var template=JsonParser.parseString("{\"groups\":[],\"elements\":[{\"name\":\"skin\"}],\"animations\":[{\"name\":\"artist_idle\"}]}").getAsJsonObject();
        var names=new HashSet<String>();
        for(var a:clips())for(var animator:a.getAsJsonObject().getAsJsonObject("animators").asMap().values()) {
            String name=animator.getAsJsonObject().get("name").getAsString();
            if(names.add(name)) {
                var group=new JsonObject();group.addProperty("name",name);group.addProperty("uuid",UUID.randomUUID().toString());
                template.getAsJsonArray("groups").add(group);
            }
        }
        var before=template.deepCopy();var model=SwordModelAssets.buildModel(template,clips());
        assertEquals(before,template);
        assertEquals(before.get("groups"),model.get("groups"));assertEquals(before.get("elements"),model.get("elements"));
        assertNotEquals(HunterModelAssets.MODEL_NAME,SwordModelAssets.MODEL_NAME);
        assertEquals(SwordModelAssets.MODEL_NAME,model.get("name").getAsString());
        assertEquals(9,model.getAsJsonArray("animations").size());
    }
    @Test void installerRejectsEmptyForeignOrIncompatibleSkeleton() throws Exception {
        var template=JsonParser.parseString("{\"groups\":[],\"animations\":[]}").getAsJsonObject();
        assertThrows(IllegalArgumentException.class,()->SwordModelAssets.buildModel(template,new JsonArray()));
        assertThrows(IllegalArgumentException.class,()->SwordModelAssets.buildModel(template,clips()));
        var foreign=JsonParser.parseString("[{\"name\":\"h15_super_arc\"}]").getAsJsonArray();
        assertThrows(IllegalArgumentException.class,()->SwordModelAssets.buildModel(template,foreign));
    }
    @Test void acceptedSelectorHasThreeLightAndFiveHeavyShapesWithoutChangingGameplayProfiles() {
        for(var shape:SwordProfile.Shape.values()) {
            assertEquals("sword_light_1",SwordPresentation.clip(shape,false,0));
            assertEquals("sword_light_2",SwordPresentation.clip(shape,false,2));
            assertEquals("sword_light_3",SwordPresentation.clip(shape,false,4));
            assertTrue(EXPECTED.contains("h15_"+SwordPresentation.clip(shape,true,1)));
        }
    }
}
