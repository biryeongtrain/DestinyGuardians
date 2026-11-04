package kim.biryeong.destiny.weapon;

import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import com.mojang.serialization.JsonOps;
import net.minecraft.client.color.item.ItemTintSources;
import net.minecraft.client.renderer.item.ItemModels;
import net.minecraft.client.resources.model.cuboid.CuboidModel;
import org.junit.jupiter.api.Test;
import java.io.StringReader;
import java.nio.file.*;
import static org.junit.jupiter.api.Assertions.*;

/** Asset acceptance only. Runtime routing and native visual QA belong to master. */
class ReloadW168BygonesTest {
    static final Path A = Path.of("src/main/resources/assets/destiny");
    static final String KEY = "weapon_reload_w168_bygones/bygones";
    static JsonObject json(Path p) throws Exception {
        return JsonParser.parseString(Files.readString(p)).getAsJsonObject();
    }
    @Test void actual263ParserAcceptsAll86OwnedModels() throws Exception {
        try (var paths = Files.list(A.resolve("models/weapon_reload_w168_bygones"))) {
            var all = paths.toList(); assertEquals(86, all.size());
            for (var path : all) assertNotNull(CuboidModel.fromStream(new StringReader(Files.readString(path))), path.toString());
        }
    }
    @Test void exactSourceElementsAndUvPartitionWithoutDuplication() throws Exception {
        var source = json(A.resolve("models/weapon_surface_w123/bygones.json"));
        var body = json(A.resolve("models/"+KEY+"_body.json"));
        var moving = json(A.resolve("models/"+KEY+"_moving.json"));
        assertEquals(124,body.getAsJsonArray("elements").size());
        assertEquals(5,moving.getAsJsonArray("elements").size());
        var fixed = java.util.Set.of("receiver_keel","stock_belly_join","stock_toe");
        var bodyNames = new java.util.HashSet<String>();
        for (var element : body.getAsJsonArray("elements")) bodyNames.add(element.getAsJsonObject().get("name").getAsString());
        assertTrue(bodyNames.containsAll(fixed));
        for (var element : moving.getAsJsonArray("elements"))
            assertFalse(fixed.contains(element.getAsJsonObject().get("name").getAsString()));
        int b=0,m=0;
        for(int i=0;i<129;i++) assertEquals(source.getAsJsonArray("elements").get(i),
            i>=106 && i<=110 ? moving.getAsJsonArray("elements").get(m++) : body.getAsJsonArray("elements").get(b++));
        assertEquals(source.get("textures"),body.get("textures"));
        assertEquals(source.get("textures"),moving.get("textures"));
        for (var entry : source.getAsJsonObject("textures").entrySet()) {
            String id=entry.getValue().getAsString();
            assertTrue(Files.isRegularFile(A.resolve("textures/"+id.substring("destiny:".length())+".png")),id);
        }
    }
    @Test void eachAssembledSampleUsesOnly129SourceSolidsAndPreservesNonFp() throws Exception {
        int count = json(A.resolve("models/"+KEY+"_body.json")).getAsJsonArray("elements").size()
                  + json(A.resolve("models/"+KEY+"_moving.json")).getAsJsonArray("elements").size();
        assertEquals(129,count); assertTrue(count<=1000);
        for (String grip : new String[]{"native","twohand"}) {
            var source = json(A.resolve(grip.equals("native") ? "models/weapon_surface_w123/bygones.json" : "models/weapon/pulse_rifle/bygones_twohand.json")).getAsJsonObject("display");
            for (int i=0;i<21;i++) for (String part : new String[]{"body","moving"}) {
                var child=json(A.resolve("models/"+KEY+"_%02d_%s_%s.json".formatted(i,part,grip)));
                assertFalse(child.has("elements"));
                for(var entry:source.entrySet()) if (!entry.getKey().startsWith("firstperson_"))
                    assertEquals(entry.getValue(),child.getAsJsonObject("display").get(entry.getKey()));
            }
        }
    }
    @Test void endpointsAreExactHipForBothPartsAndGrips() throws Exception {
        for(String grip:new String[]{"native","twohand"}) {
            var expected=json(A.resolve(grip.equals("native") ? "models/weapon_surface_w123/bygones.json" : "models/weapon/pulse_rifle/bygones_twohand.json")).get("display");
            for(int frame:new int[]{0,20}) for(String part:new String[]{"body","moving"}) {
                var model=json(A.resolve("models/"+KEY+"_%02d_%s_%s.json".formatted(frame,part,grip)));
                assertEquals(expected,model.get("display")); assertFalse(model.has("elements"));
            }
        }
        for(String grip:new String[]{"native","twohand"}) {
            var body=json(A.resolve("models/"+KEY+"_09_body_"+grip+".json")).getAsJsonObject("display");
            var moving=json(A.resolve("models/"+KEY+"_09_moving_"+grip+".json")).getAsJsonObject("display");
            for(String hand:new String[]{"firstperson_righthand","firstperson_lefthand"})
                assertNotEquals(body.getAsJsonObject(hand).get("translation"),moving.getAsJsonObject(hand).get("translation"));
        }
    }
    @Test void actual263CodecAcceptsFpOnlyGraphAndExactCanonicalFallbacks() throws Exception {
        net.minecraft.SharedConstants.tryDetectVersion(); net.minecraft.server.Bootstrap.bootStrap();
        ItemModels.bootstrap(); ItemTintSources.bootstrap();
        net.minecraft.client.renderer.item.properties.select.SelectItemModelProperties.bootstrap();
        net.minecraft.client.renderer.item.properties.conditional.ConditionalItemModelProperties.bootstrap();
        net.minecraft.client.renderer.item.properties.numeric.RangeSelectItemModelProperties.bootstrap();
        var wrapper=json(A.resolve("items/"+KEY+".json"));
        var graph=wrapper.getAsJsonObject("model");
        var result=ItemModels.CODEC.parse(JsonOps.INSTANCE,graph);
        assertTrue(result.error().isEmpty(),result.error().toString());
        var canonical=json(A.resolve("items/weapon/bygones.json"));
        assertEquals(canonical.get("hand_animation_on_swap"),wrapper.get("hand_animation_on_swap"));
        assertEquals(canonical.get("model"),graph.get("fallback"));
        var context=graph.getAsJsonArray("cases").get(0).getAsJsonObject();
        assertEquals(JsonParser.parseString("[\"firstperson_righthand\",\"firstperson_lefthand\"]"),context.get("when"));
        var range=context.getAsJsonObject("model");
        assertEquals(1,range.get("index").getAsInt()); assertEquals(canonical.get("model"),range.get("fallback"));
        var entries=range.getAsJsonArray("entries"); assertEquals(21,entries.size());
        for(int i=0;i<21;i++) {
            var entry=entries.get(i).getAsJsonObject();assertEquals(i/20.,entry.get("threshold").getAsDouble(),1e-9);
            var condition=entry.getAsJsonObject("model"); assertEquals(0,condition.get("index").getAsInt());
            for(String branch:new String[]{"on_true","on_false"}) {
                var models=condition.getAsJsonObject(branch).getAsJsonArray("models"); assertEquals(2,models.size());
                String grip=branch.equals("on_true") ? "twohand" : "native";
                for(int j=0;j<2;j++) {
                    String part=j==0 ? "body" : "moving";
                    String id=models.get(j).getAsJsonObject().get("model").getAsString();
                    assertEquals("destiny:"+KEY+"_%02d_%s_%s".formatted(i,part,grip),id);
                    Path child=A.resolve("models/"+id.substring("destiny:".length())+".json");
                    assertNotNull(CuboidModel.fromStream(new StringReader(Files.readString(child))),child.toString());
                    assertEquals("destiny:"+KEY+"_"+part,json(child).get("parent").getAsString());
                    Path parent=A.resolve("models/"+KEY+"_"+part+".json");
                    assertNotNull(CuboidModel.fromStream(new StringReader(Files.readString(parent))),parent.toString());
                }
            }
        }
    }
}
