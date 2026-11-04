package kim.biryeong.destiny.fx;

import com.google.gson.*;
import org.junit.jupiter.api.Test;
import java.nio.file.*;
import java.util.*;
import static org.junit.jupiter.api.Assertions.*;

/** Static authoring/installer contracts, not native framebuffer or exact Destiny timing proof. */
class SwordStanceW55Test {
    private JsonObject json(String path) throws Exception {
        return JsonParser.parseString(Files.readString(Path.of(path))).getAsJsonObject();
    }
    private JsonArray clips() throws Exception {
        return json("src/main/resources"+SwordStanceAssets.RESOURCE).getAsJsonArray("animations");
    }
    @Test void authoritativeGuardThenAirThenActualDisplacementSelectsStance() {
        assertEquals(SwordStance.GUARD,SwordStance.select(true,false,1));
        assertEquals(SwordStance.GUARD,SwordStance.select(true,true,0));
        assertEquals(SwordStance.AIR,SwordStance.select(false,false,0));
        assertEquals(SwordStance.AIR,SwordStance.select(false,false,1));
        assertEquals(SwordStance.IDLE,SwordStance.select(false,true,0));
        assertEquals(SwordStance.IDLE,SwordStance.select(false,true,.000225));
        assertEquals(SwordStance.MOVE,SwordStance.select(false,true,.000226));
        assertEquals(SwordStance.MOVE,SwordStance.select(false,true,64));
    }
    @Test void invalidAndTeleportDisplacementsNeverBecomeGaits() {
        for(double d:new double[]{-1,Double.NaN,Double.POSITIVE_INFINITY,Double.NEGATIVE_INFINITY,64.0001})
            assertEquals(SwordStance.IDLE,SwordStance.select(false,true,d));
    }
    @Test void clipNamesDoNotDependOnMachineLocale() {
        var saved=Locale.getDefault();
        try {
            Locale.setDefault(Locale.forLanguageTag("tr-TR"));
            assertEquals("sword_idle",SwordStance.IDLE.clip());
            assertEquals(Set.of("sword_idle","sword_move","sword_guard","sword_air"),
                    new HashSet<>(Arrays.stream(SwordStance.values()).map(SwordStance::clip).toList()));
        } finally {Locale.setDefault(saved);}
    }
    @Test void runtimeKeepsEveryAttackCueAndClipExactlyAndAddsOnlyFourLoops() throws Exception {
        var old=json("src/main/resources/destiny/animation/sword_w53.animation.json").getAsJsonArray("animations");
        var current=clips();
        assertEquals(12,current.size());
        for(int i=0;i<8;i++)assertEquals(old.get(i),current.get(i),"Original attack "+i);
        var names=new HashSet<String>();
        for(int i=8;i<12;i++) {
            var clip=current.get(i).getAsJsonObject();
            assertTrue(names.add(clip.get("name").getAsString()));
            assertEquals("loop",clip.get("loop").getAsString());
        }
        assertEquals(Set.of("h15_sword_idle","h15_sword_move","h15_sword_guard","h15_sword_air"),names);
    }
    @Test void newLoopsHaveFiniteFullBodyChannelsAndContinuousSeams() throws Exception {
        for(int i=8;i<12;i++) {
            var clip=clips().get(i).getAsJsonObject();
            double length=clip.get("length").getAsDouble();
            assertTrue(length>=.5&&length<=3);
            var names=new HashSet<String>();
            for(var a:clip.getAsJsonObject("animators").asMap().values()) {
                var animator=a.getAsJsonObject();String name=animator.get("name").getAsString();names.add(name);
                var first=new HashMap<String,JsonElement>();var last=new HashMap<String,JsonElement>();
                for(var k:animator.getAsJsonArray("keyframes")) {
                    var key=k.getAsJsonObject();String channel=key.get("channel").getAsString();
                    double time=key.get("time").getAsDouble();
                    assertTrue(Double.isFinite(time)&&time>=0&&time<=length);
                    var point=key.getAsJsonArray("data_points").get(0).getAsJsonObject();
                    for(String axis:List.of("x","y","z"))assertTrue(Double.isFinite(point.get(axis).getAsDouble()));
                    if(time==0)first.put(channel,point);
                    if(time==length)last.put(channel,point);
                    if(channel.equals("scale"))for(String axis:List.of("x","y","z"))assertEquals(1,point.get(axis).getAsDouble());
                    if(channel.equals("position")) {
                        assertEquals("player_root",name);
                        assertEquals(0,point.get("x").getAsDouble());assertEquals(0,point.get("z").getAsDouble());
                    }
                }
                assertEquals(first,last,"Continuous loop seam "+clip.get("name")+"/"+name);
            }
            assertEquals(16,names.size());
            assertTrue(names.containsAll(Set.of("player_root","pc_chest","pra_right_arm","pla_left_arm",
                    "pri_right_item","pli_left_item","prl_right_leg","pll_left_leg")));
        }
    }
    @Test void sourceArtPreservesAllPriorRigFieldsAndTwentyNineAnimations() throws Exception {
        var before=json("art/blockbench/animations/guardian_sword_w53.bbmodel");
        var after=json("art/blockbench/animations/guardian_sword_w55.bbmodel");
        for(String key:before.keySet())if(!Set.of("name","model_identifier","animations").contains(key))
            assertEquals(before.get(key),after.get(key),key);
        assertEquals(33,after.getAsJsonArray("animations").size());
        for(int i=0;i<29;i++)assertEquals(before.getAsJsonArray("animations").get(i),after.getAsJsonArray("animations").get(i));
        assertNotEquals(before.get("name"),after.get("name"));
    }
    @Test void newInstallerKeepsTemplateAndOldVersionUnchanged() throws Exception {
        var template=JsonParser.parseString("{\"groups\":[],\"elements\":[{\"name\":\"artist_skin\"}],\"animations\":[{\"name\":\"artist_idle\"}]}").getAsJsonObject();
        var names=new HashSet<String>();
        for(var c:clips())for(var a:c.getAsJsonObject().getAsJsonObject("animators").asMap().values()) {
            String name=a.getAsJsonObject().get("name").getAsString();
            if(names.add(name)) {
                var group=new JsonObject();group.addProperty("name",name);group.addProperty("uuid",UUID.randomUUID().toString());
                template.getAsJsonArray("groups").add(group);
            }
        }
        var before=template.deepCopy();var model=SwordStanceAssets.buildModel(template,clips());
        assertEquals(before,template);
        assertEquals(before.get("groups"),model.get("groups"));assertEquals(before.get("elements"),model.get("elements"));
        assertEquals(13,model.getAsJsonArray("animations").size());
        assertEquals("guardian_sword_w55",model.get("name").getAsString());
        assertEquals("guardian_sword_w53",SwordModelAssets.MODEL_NAME);
        assertNotEquals(HunterModelAssets.MODEL_NAME,SwordStanceAssets.MODEL_NAME);
        assertThrows(IllegalArgumentException.class,()->SwordStanceAssets.buildModel(template,new JsonArray()));
    }
}
