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
class ReloadW168AustringerTest {
    static final Path A = Path.of("src/main/resources/assets/destiny");
    static final String KEY = "weapon_reload_w168_austringer/austringer";
    static JsonObject json(Path p) throws Exception {
        return JsonParser.parseString(Files.readString(p)).getAsJsonObject();
    }
    @Test void actual263ParserAcceptsAll86OwnedModels() throws Exception {
        try (var paths = Files.list(A.resolve("models/weapon_reload_w168_austringer"))) {
            var all = paths.toList(); assertEquals(86, all.size());
            for (var path : all) assertNotNull(CuboidModel.fromStream(new StringReader(Files.readString(path))), path.toString());
        }
    }
    @Test void exactSourceElementsAndUvPartitionWithoutDuplication() throws Exception {
        var source = json(A.resolve("models/weapon_surface_w123/austringer.json"));
        var body = json(A.resolve("models/"+KEY+"_body.json"));
        var moving = json(A.resolve("models/"+KEY+"_moving.json"));
        assertEquals(114,body.getAsJsonArray("elements").size());
        assertEquals(12,moving.getAsJsonArray("elements").size());
        assertEquals("Cylinder_lower_frame",body.getAsJsonArray("elements").get(32).getAsJsonObject().get("name").getAsString());
        for (var element : moving.getAsJsonArray("elements"))
            assertNotEquals("Cylinder_lower_frame",element.getAsJsonObject().get("name").getAsString());
        int b=0,m=0;
        for(int i=0;i<126;i++) assertEquals(source.getAsJsonArray("elements").get(i),
            i>=32 && i<=43 ? moving.getAsJsonArray("elements").get(m++) : body.getAsJsonArray("elements").get(b++));
        assertEquals(126,body.getAsJsonArray("elements").size()+moving.getAsJsonArray("elements").size());
        assertTrue(body.getAsJsonArray("elements").size()+moving.getAsJsonArray("elements").size()<=1000);
        assertEquals(source.get("textures"),body.get("textures"));
        assertEquals(source.get("textures"),moving.get("textures"));
        for (var entry : source.getAsJsonObject("textures").entrySet()) {
            String id=entry.getValue().getAsString();
            assertTrue(Files.isRegularFile(A.resolve("textures/"+id.substring("destiny:".length())+".png")),id);
        }
    }
    @Test void endpointsAreExactHipForBothPartsAndGrips() throws Exception {
        for(String grip:new String[]{"native","twohand"}) {
            var expected=json(A.resolve(grip.equals("native") ? "models/weapon_surface_w123/austringer.json" : "models/weapon/hand_cannon/austringer_twohand.json")).get("display");
            for(int frame:new int[]{0,20}) for(String part:new String[]{"body","moving"}) {
                var model=json(A.resolve("models/"+KEY+"_%02d_%s_%s.json".formatted(frame,part,grip)));
                assertEquals(expected,model.get("display")); assertFalse(model.has("elements"));
            }
        }
        for(String grip:new String[]{"native","twohand"}) {
            var body=json(A.resolve("models/"+KEY+"_09_body_"+grip+".json")).getAsJsonObject("display");
            var moving=json(A.resolve("models/"+KEY+"_09_moving_"+grip+".json")).getAsJsonObject("display");
            for(String hand:new String[]{"firstperson_righthand","firstperson_lefthand"})
                { assertNotEquals(body.getAsJsonObject(hand).get("translation"),moving.getAsJsonObject(hand).get("translation"));
                  assertNotEquals(body.getAsJsonObject(hand).get("rotation"),moving.getAsJsonObject(hand).get("rotation")); }
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
        var canonical=json(A.resolve("items/weapon/austringer.json"));
        assertEquals(canonical.get("hand_animation_on_swap"),wrapper.get("hand_animation_on_swap"));
        assertEquals(canonical.get("model"),graph.get("fallback"));
        var context=graph.getAsJsonArray("cases").get(0).getAsJsonObject();
        assertEquals(JsonParser.parseString("[\"firstperson_righthand\",\"firstperson_lefthand\"]"),context.get("when"));
        var range=context.getAsJsonObject("model");
        assertEquals(1,range.get("index").getAsInt()); assertEquals(canonical.get("model"),range.get("fallback"));
        var entries=range.getAsJsonArray("entries"); assertEquals(21,entries.size());
        for(int i=0;i<21;i++) {
            int assembled=0;
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
                    assembled+=json(parent).getAsJsonArray("elements").size();
                }
            }
            assertEquals(252,assembled); // two alternative grips, each 126 assembled elements
            assertTrue(assembled/2<=1000);
        }
    }
}
