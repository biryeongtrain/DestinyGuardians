package kim.biryeong.destiny.fx;

import com.google.gson.*;
import java.util.*;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class SuperMotionOverlaysW332Test {
    @Test void fullSourceAndExplicitStaticHoldAreLoadedWithoutRetimingGameplay() {
        SuperMotionOverlaysW332.require();
        var hunter=SuperMotionOverlaysW332.overlay(new JsonArray(),"h15_");
        assertEquals(2,hunter.size());
        for(var value:hunter) {
            var clip=value.getAsJsonObject();assertEquals(1.3,clip.get("length").getAsDouble(),1e-9);
            assertEquals(1.3,clip.get("destiny_source_duration_seconds").getAsDouble(),1e-9);
        }
        var classes=SuperMotionOverlaysW332.overlay(new JsonArray(),"w230_");
        var hold=find(classes,"w230_warlock_nova_warp_charge_idle");
        assertEquals(0,hold.get("destiny_source_duration_seconds").getAsDouble());
        assertTrue(hold.get("destiny_static_source_hold").getAsBoolean());assertEquals(2,hold.get("length").getAsDouble());
        assertEquals(1.2666666666666666,find(classes,"w230_warlock_nova_warp_charge_exit").get("length").getAsDouble(),1e-9);
        assertEquals(7,ShadowshotTiming.RELEASE_TICKS,"Full visual source does not move the gameplay release cue");
    }
    @Test void splitOverlaysPreserveUnrelatedClipsAndInputOwnership() {
        var input=new JsonArray();var old=new JsonObject();old.addProperty("name","unrelated_existing");input.add(old);
        String before=input.toString();var hunter=SuperMotionOverlaysW332.overlay(input,"h15_");
        assertEquals(before,input.toString());assertEquals(3,hunter.size());assertEquals(old,hunter.get(0));
        assertTrue(hunter.asList().stream().noneMatch(x->x.getAsJsonObject().get("name").getAsString().startsWith("w230_")));
        hunter.get(1).getAsJsonObject().addProperty("length",.1);
        assertEquals(1.3,SuperMotionOverlaysW332.overlay(new JsonArray(),"h15_").get(0).getAsJsonObject().get("length").getAsDouble(),1e-9);
    }
    @Test void modelRevisionsAndClassIndexIncludeTheNewSourcePayload() {
        assertTrue(HunterModelAssets.MODEL_NAME.contains(SuperMotionOverlaysW332.revision()));
        assertTrue(ClassSuperModelAssets.MODEL_NAME.contains(SuperMotionOverlaysW332.revision()));
        assertTrue(ClassSuperModelAssets.hasClip("w230_warlock_nova_warp_charge_idle"));
        assertTrue(ClassSuperModelAssets.hasClip("w229_warlock_solar_start_air"));
        assertEquals(32,ClassSuperModelAssets.durationTicks("warlock/solar_super","start_air",0));
        assertEquals(40,ClassSuperModelAssets.durationTicks("warlock/nova_warp","charge_idle",0));
        assertEquals(29,SuperMotionOverlaysW332.playbackTicks("w230_warlock_nova_warp_charge_exit",0));
        assertEquals(1,SuperMotionOverlaysW332.entryBlendTicks("h15_super_void_attack"));
        assertEquals(2,SuperMotionOverlaysW332.exitBlendTicks("h15_super_void_attack_air"));
    }
    @Test void allNewCurvesCompileToTheOwnedGridWithFullSourceEndpoints() {
        for(String prefix:List.of("h15_","w2"))for(var value:SuperMotionOverlaysW332.overlay(new JsonArray(),prefix)) {
            var source=value.getAsJsonObject();var compiled=SourceAnimationGrid.compile(source);
            assertEquals(source.get("length"),compiled.get("length"));assertEquals(40,compiled.get("destiny_quaternion_baked_hz").getAsInt());
            for(var bone:compiled.getAsJsonObject("animators").entrySet())for(var k:bone.getValue().getAsJsonObject().getAsJsonArray("keyframes")) {
                var key=k.getAsJsonObject();assertTrue(key.get("time").getAsDouble()<=source.get("length").getAsDouble()+1e-9);
                assertFalse(key.has("destiny_quaternion"));
            }
        }
        assertEquals(29,MeleeSuperAnimationTiming.durationTicks("h15_super_arc_attack_heavy",0));
        assertEquals(21,MeleeSuperAnimationTiming.durationTicks("h15_super_arc_attack_heavy_air",0));
        assertEquals(7,MeleeSuperAnimationTiming.contactTicks("h15_super_arc_attack_heavy",0));
        assertEquals(7,MeleeSuperAnimationTiming.contactTicks("h15_super_arc_attack_heavy_air",0));
    }
    private static JsonObject find(JsonArray clips,String name) {
        return clips.asList().stream().map(JsonElement::getAsJsonObject).filter(c->name.equals(c.get("name").getAsString())).findFirst().orElseThrow();
    }
}
