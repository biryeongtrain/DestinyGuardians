package kim.biryeong.destiny.fx;
import com.google.gson.*;
import org.junit.jupiter.api.Test;
import java.util.*;
import static org.junit.jupiter.api.Assertions.*;

class TitanRunningW338Test {
    private JsonObject resource(String path) {
        try(var in=new java.io.InputStreamReader(Objects.requireNonNull(getClass().getResourceAsStream(path)),java.nio.charset.StandardCharsets.UTF_8)) {
            return JsonParser.parseReader(in).getAsJsonObject();
        } catch(java.io.IOException e){throw new AssertionError(e);}
    }
    @Test void r3AdmitsOnlyTwelveExplicitTitanRunClipsWithR3Provenance() {
        var valid=resource(SuperLocomotionW336.TITAN_RUNNING_RESOURCE);
        assertDoesNotThrow(()->SuperLocomotionW336.requireR3(valid,SuperLocomotionW336.TITAN_RUNNING_RESOURCE));
        for(String revision:List.of("R1","R2","")) {
            var copy=valid.deepCopy();if(revision.isEmpty())copy.remove("source_revision");else copy.addProperty("source_revision",revision);
            assertThrows(IllegalStateException.class,()->SuperLocomotionW336.requireR3(copy,SuperLocomotionW336.TITAN_RUNNING_RESOURCE));
        }
        assertThrows(IllegalStateException.class,()->SuperLocomotionW336.requireR3(valid,SuperLocomotionW336.CLASSES_RESOURCE));
        for(String field:List.of("source_revision","destiny_source_family","destiny_source_composed_action","destiny_source_period_seconds")) {
            var copy=valid.deepCopy();copy.getAsJsonArray("animations").get(0).getAsJsonObject().remove(field);
            assertThrows(IllegalStateException.class,()->SuperLocomotionW336.requireR3(copy,SuperLocomotionW336.TITAN_RUNNING_RESOURCE),field);
        }
        for(String foreign:List.of("w229_titan_arc_idle","w229_titan_arc_attack","w230_hunter_spectral_blades_move_forward","w230_titan_burning_maul_move_left")) {
            var copy=valid.deepCopy();copy.getAsJsonArray("animations").get(0).getAsJsonObject().addProperty("name",foreign);
            assertThrows(IllegalStateException.class,()->SuperLocomotionW336.requireR3(copy,SuperLocomotionW336.TITAN_RUNNING_RESOURCE),foreign);
        }
        var duplicate=valid.deepCopy();duplicate.getAsJsonArray("animations").set(1,duplicate.getAsJsonArray("animations").get(0).deepCopy());
        assertThrows(IllegalStateException.class,()->SuperLocomotionW336.requireR3(duplicate,SuperLocomotionW336.TITAN_RUNNING_RESOURCE));
        var fakeR2=valid.deepCopy();fakeR2.addProperty("source_revision","R2");
        assertThrows(IllegalStateException.class,()->SuperLocomotionW336.indexSources(Map.of(SuperLocomotionW336.CLASSES_RESOURCE,fakeR2)),"R3 payload cannot enter through the R2 path");
    }
    @Test void r3OrderedReplacementKeepsR2IdleAndRejectsOtherDuplicates() {
        var hunter=resource(SuperLocomotionW336.HUNTER_RESOURCE);var classes=resource(SuperLocomotionW336.CLASSES_RESOURCE);var running=resource(SuperLocomotionW336.TITAN_RUNNING_RESOURCE);
        // Deliberately insert R3 before R2; indexing must use the explicit resource order.
        var unordered=new LinkedHashMap<String,JsonObject>();unordered.put(SuperLocomotionW336.TITAN_RUNNING_RESOURCE,running);unordered.put(SuperLocomotionW336.CLASSES_RESOURCE,classes);unordered.put(SuperLocomotionW336.HUNTER_RESOURCE,hunter);
        var merged=SuperLocomotionW336.indexSources(unordered);
        assertEquals(hunter.getAsJsonArray("animations").size()+classes.getAsJsonArray("animations").size(),merged.size());
        for(var value:running.getAsJsonArray("animations")) {
            var clip=value.getAsJsonObject();assertEquals(clip,merged.get(clip.get("name").getAsString()));
        }
        for(var value:classes.getAsJsonArray("animations")) {
            var clip=value.getAsJsonObject();String name=clip.get("name").getAsString();
            if(!name.matches("w229_titan_(arc|solar|void)_move_(forward|backward|left|right)"))assertEquals(clip,merged.get(name),name);
        }
        var duplicate=classes.deepCopy();duplicate.getAsJsonArray("animations").add(duplicate.getAsJsonArray("animations").get(0).deepCopy());
        assertThrows(IllegalStateException.class,()->SuperLocomotionW336.indexSources(Map.of(SuperLocomotionW336.CLASSES_RESOURCE,duplicate)));
        var overlay=SuperLocomotionW336.overlay(new JsonArray(),"w2");
        for(var value:overlay) {var clip=value.getAsJsonObject();assertEquals(merged.get(clip.get("name").getAsString()),clip);}
    }
    @Test void r3RetainsSelectedSourcePeriodsAndUnarmedMapping() {
        var running=resource(SuperLocomotionW336.TITAN_RUNNING_RESOURCE);var names=new HashSet<String>();
        for(var value:running.getAsJsonArray("animations")) {
            var clip=value.getAsJsonObject();String name=clip.get("name").getAsString();assertTrue(names.add(name));
            boolean hammer=name.startsWith("w229_titan_solar");boolean forward=name.endsWith("forward");
            double period=hammer?(forward?16.0/30:17.0/30):20.0/30;
            if(!hammer&&forward)period=17.0/30;
            if(hammer&&name.endsWith("right"))period=18.0/30;
            assertEquals(period,clip.get("length").getAsDouble(),1e-9,name);
            assertEquals(period,SourceAnimationGrid.compile(clip).get("length").getAsDouble(),1e-9,name);
            assertEquals(hammer?"hammer_of_sol":"unarmed_fists_candidate",clip.get("destiny_source_family").getAsString());
            for(var animator:clip.getAsJsonObject("animators").asMap().values()) {
                var bone=animator.getAsJsonObject();if(!bone.get("name").getAsString().equals("player_root"))continue;
                for(var key:bone.getAsJsonArray("keyframes"))if(key.getAsJsonObject().get("channel").getAsString().equals("position")) {
                    var point=key.getAsJsonObject().getAsJsonArray("data_points").get(0).getAsJsonObject();assertEquals(0,point.get("x").getAsDouble());assertEquals(0,point.get("z").getAsDouble());
                }
            }
        }
        assertEquals(12,names.size());
    }

}
