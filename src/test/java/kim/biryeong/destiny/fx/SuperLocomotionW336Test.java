package kim.biryeong.destiny.fx;

import com.google.gson.*;
import org.junit.jupiter.api.Test;
import java.util.*;
import static org.junit.jupiter.api.Assertions.*;
import static kim.biryeong.destiny.fx.SuperLocomotionW336.Direction.*;

class SuperLocomotionW336Test {
    @Test void actualDisplacementIsRotatedIntoAllFourAimLocalDirections() {
        var m=new SuperLocomotionW336.Motion();
        assertEquals(FORWARD,m.sample(0,.08,0,1));
        assertEquals(BACKWARD,m.sample(0,-.08,0,2));
        assertEquals(LEFT,m.sample(.08,0,0,3));
        assertEquals(RIGHT,m.sample(-.08,0,0,4));
        assertEquals(FORWARD,m.sample(.08,0,-90,5));
        assertEquals(LEFT,m.sample(0,-.08,-90,6));
        assertEquals(RIGHT,m.sample(0,.08,-90,7));
        assertEquals(BACKWARD,m.sample(-.08,0,-90,8));
    }
    @Test void wallRestJitterDirectionHysteresisAndDuplicateTicksCannotRestartWalk() {
        var m=new SuperLocomotionW336.Motion();
        for(int i=0;i<10;i++)assertEquals(IDLE,m.sample(0,0,0,i),"Held input against a wall has no resolved displacement");
        assertEquals(FORWARD,m.sample(0,.08,0,10));
        assertEquals(FORWARD,m.sample(.081,.08,0,11),"Small diagonal boundary jitter preserves the prior direction");
        assertEquals(LEFT,m.sample(.11,.08,0,12));
        assertEquals(LEFT,m.sample(0,0,0,12),"A duplicate sample is not a second stopped frame");
        assertEquals(LEFT,m.sample(0,0,0,13));
        assertEquals(IDLE,m.sample(0,0,0,14),"Walk ends after two real stationary frames");
        assertEquals(IDLE,m.sample(.001,0,0,15));
        assertEquals(IDLE,m.sample(20,0,0,16),"Teleport is not a footstep");
        assertEquals(IDLE,new SuperLocomotionW336.Motion().sample(0,0,0,17),"New session has no previous actor hysteresis");
    }
    @Test void directionalAirAndMissingClipFallbackDoNotInventUnrelatedMotion() {
        String loop="w230_hunter_spectral_blades_idle",base="w230_hunter_spectral_blades";
        var clips=Set.of(loop,base+"_move_forward",base+"_move_left",base+"_move",base+"_air");
        assertEquals(base+"_move_left",SuperLocomotionW336.select(loop,LEFT,true,clips::contains));
        assertEquals(base+"_move",SuperLocomotionW336.select(loop,RIGHT,true,clips::contains));
        assertEquals(loop,SuperLocomotionW336.select(loop,IDLE,true,clips::contains));
        assertEquals(base+"_air",SuperLocomotionW336.select(loop,LEFT,false,clips::contains));
        assertEquals(loop,SuperLocomotionW336.select(loop,LEFT,false,Set.of(loop)::contains));
        String floating="w230_warlock_nova_warp",floatingIdle=floating+"_idle";
        var floatClips=Set.of(floatingIdle,floating+"_move",floating+"_air");
        assertEquals(floating+"_move",SuperLocomotionW336.select(floatingIdle,LEFT,false,true,floatClips::contains));
        assertEquals(floatingIdle,SuperLocomotionW336.select(floatingIdle,IDLE,false,true,floatClips::contains));
        assertEquals("h15_super_arc_move_backward",SuperLocomotionW336.select("super_arc",BACKWARD,true,
                Set.of("h15_super_arc","h15_super_arc_move_backward")::contains));
    }
    @Test void r2RevisionAndNamedSpectralFamilyRejectSupersededR1AndAccBindings() {
        var root=new JsonObject();root.addProperty("schema_version",1);root.add("animations",new JsonArray());
        assertThrows(IllegalStateException.class,()->SuperLocomotionW336.requireR2(root,"probe"));
        root.addProperty("source_revision","R1");assertThrows(IllegalStateException.class,()->SuperLocomotionW336.requireR2(root,"probe"));
        root.addProperty("source_revision","R2");assertDoesNotThrow(()->SuperLocomotionW336.requireR2(root,"probe"));
        var clip=new JsonObject();clip.addProperty("name","w230_hunter_spectral_blades_idle");
        assertThrows(IllegalStateException.class,()->SuperLocomotionW336.requireFamily(clip));
        clip.addProperty("destiny_source_family","unresolved_ACC99940");assertThrows(IllegalStateException.class,()->SuperLocomotionW336.requireFamily(clip));
        clip.addProperty("destiny_source_family","spectral_blades");assertDoesNotThrow(()->SuperLocomotionW336.requireFamily(clip));
    }
    @Test void sourceLoopsLoadForBothRigsWithoutRetimingOrReplacingOneShots() {
        assertNotNull(getClass().getResource(SuperLocomotionW336.HUNTER_RESOURCE));
        assertNotNull(getClass().getResource(SuperLocomotionW336.CLASSES_RESOURCE));
        for(String resource:List.of(SuperLocomotionW336.HUNTER_RESOURCE,SuperLocomotionW336.CLASSES_RESOURCE))
            try(var in=new java.io.InputStreamReader(Objects.requireNonNull(getClass().getResourceAsStream(resource)),java.nio.charset.StandardCharsets.UTF_8)) {
                assertEquals("R2",JsonParser.parseReader(in).getAsJsonObject().get("source_revision").getAsString());
            } catch(java.io.IOException e){throw new AssertionError(e);}
        var original=new JsonArray();var attack=new JsonObject();attack.addProperty("name","h15_super_arc_attack");attack.addProperty("length",1.3);original.add(attack);
        String before=original.toString();var hunter=SuperLocomotionW336.overlay(original,"h15_");
        assertEquals(before,original.toString());assertEquals(attack,hunter.get(0));
        var hunterNames=new HashSet<String>();for(var value:hunter)hunterNames.add(value.getAsJsonObject().get("name").getAsString());
        assertTrue(hunterNames.contains("h15_super_arc"));
        for(String direction:List.of("forward","backward","left","right"))assertTrue(hunterNames.contains("h15_super_arc_move_"+direction));
        var classNames=new HashSet<String>();for(var value:SuperLocomotionW336.overlay(new JsonArray(),"w2"))classNames.add(value.getAsJsonObject().get("name").getAsString());
        for(String base:List.of("w230_hunter_spectral_blades","w229_titan_arc","w229_titan_solar","w229_titan_void","w230_titan_burning_maul","w229_warlock_solar")) {
            assertTrue(classNames.contains(base+"_idle"));
            for(String direction:List.of("forward","backward","left","right"))assertTrue(classNames.contains(base+"_move_"+direction));
        }
        for(String base:List.of("w229_warlock_arc","w230_warlock_nova_warp"))assertTrue(classNames.contains(base+"_move"));
        assertTrue(SuperLocomotionW336.hasFamily("super_arc"));assertTrue(SuperLocomotionW336.hasFamily("w230_hunter_spectral_blades_idle"));
        for(String base:List.of("w229_titan_arc","w229_titan_solar","w229_titan_void","w230_titan_burning_maul",
                "w229_warlock_arc","w229_warlock_solar","w230_warlock_nova_warp"))assertTrue(SuperLocomotionW336.hasFamily(base+"_idle"),base);
        assertTrue(SuperLocomotionW336.floating("w229_warlock_arc_idle"));
        assertTrue(SuperLocomotionW336.floating("w230_warlock_nova_warp_idle"));
        for(String prefix:List.of("h15_","w2"))for(var value:SuperLocomotionW336.overlay(new JsonArray(),prefix)) {
            var clip=value.getAsJsonObject();assertEquals("loop",clip.get("loop").getAsString());
            double length=clip.get("length").getAsDouble();assertTrue(length>0);
            if(clip.get("name").getAsString().equals("h15_super_arc")||clip.get("name").getAsString().endsWith("_idle"))
                assertEquals(length,SourceAnimationGrid.compile(clip).get("length").getAsDouble(),1e-9);
            SuperLocomotionW336.requireFamily(clip);
            assertFalse(clip.get("name").getAsString().contains("attack"));
        }
        assertTrue(HunterModelAssets.MODEL_NAME.contains(SuperLocomotionW336.revision(SuperLocomotionW336.HUNTER_RESOURCE)));
        assertTrue(ClassSuperModelAssets.MODEL_NAME.contains(SuperLocomotionW336.revision(SuperLocomotionW336.HUNTER_RESOURCE,SuperLocomotionW336.CLASSES_RESOURCE)));
    }
}
