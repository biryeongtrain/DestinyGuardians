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
class ReloadW174ClawsOfTheWolfTest {
    static final Path A = Path.of(System.getProperty("w174.root", "."),"src/main/resources/assets/destiny");
    static final String KEY = "weapon_reload_w174_claws_of_the_wolf/claws_of_the_wolf";
    static JsonObject json(Path p) throws Exception {
        return JsonParser.parseString(Files.readString(p)).getAsJsonObject();
    }
    @Test void actual263ParserAcceptsAll86OwnedModels() throws Exception {
        try (var paths = Files.list(A.resolve("models/weapon_reload_w174_claws_of_the_wolf"))) {
            var all = paths.toList(); assertEquals(86, all.size());
            for (var path : all) assertNotNull(CuboidModel.fromStream(new StringReader(Files.readString(path))), path.toString());
        }
    }
    @Test void exactSourceElementsAndUvPartitionWithoutDuplication() throws Exception {
        var source = json(A.resolve("models/weapon_surface_w123/claws_of_the_wolf.json"));
        var body = json(A.resolve("models/"+KEY+"_body.json"));
        var moving = json(A.resolve("models/"+KEY+"_magazine.json"));
        assertEquals(126,body.getAsJsonArray("elements").size());
        assertEquals(2,moving.getAsJsonArray("elements").size());
        var names=new java.util.HashSet<String>();
        for(var element:body.getAsJsonArray("elements")) names.add(element.getAsJsonObject().get("name").getAsString());
        assertTrue(names.containsAll(java.util.Set.of("receiver_core","receiver_wrist","grip_core","stock_core","rear_action")));
        assertEquals("magazine_core",moving.getAsJsonArray("elements").get(0).getAsJsonObject().get("name").getAsString());
        for (var element : moving.getAsJsonArray("elements"))
            assertTrue(element.getAsJsonObject().get("name").getAsString().startsWith("magazine_"));
        int b=0,m=0;
        for(int i=0;i<128;i++) assertEquals(source.getAsJsonArray("elements").get(i),
            i>=111 && i<=112 ? moving.getAsJsonArray("elements").get(m++) : body.getAsJsonArray("elements").get(b++));
        assertEquals(128,body.getAsJsonArray("elements").size()+moving.getAsJsonArray("elements").size());
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
            var expected=json(A.resolve(grip.equals("native") ? "models/weapon_surface_w123/claws_of_the_wolf.json" : "models/weapon/pulse_rifle/claws_of_the_wolf_twohand.json")).get("display");
            for(int frame:new int[]{0,20}) for(String part:new String[]{"body","magazine"}) {
                var model=json(A.resolve("models/"+KEY+"_%02d_%s_%s.json".formatted(frame,part,grip)));
                assertEquals(expected,model.get("display")); assertFalse(model.has("elements"));
            }
        }
        for(String grip:new String[]{"native","twohand"}) {
            var body=json(A.resolve("models/"+KEY+"_09_body_"+grip+".json")).getAsJsonObject("display");
            var moving=json(A.resolve("models/"+KEY+"_09_magazine_"+grip+".json")).getAsJsonObject("display");
            for(String hand:new String[]{"firstperson_righthand","firstperson_lefthand"})
                { assertNotEquals(body.getAsJsonObject(hand).get("translation"),moving.getAsJsonObject(hand).get("translation"));
                  assertEquals(body.getAsJsonObject(hand).get("rotation"),moving.getAsJsonObject(hand).get("rotation")); }
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
        var canonical=json(A.resolve("items/weapon/claws_of_the_wolf.json"));
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
                    String part=j==0 ? "body" : "magazine";
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
            assertEquals(256,assembled); // two alternative grips, each 128 assembled elements
            assertTrue(assembled/2<=1000);
        }
    }

    static org.joml.Vector3f vector(com.google.gson.JsonArray a) {
        return new org.joml.Vector3f(a.get(0).getAsFloat(),a.get(1).getAsFloat(),a.get(2).getAsFloat());
    }
    static org.joml.Quaternionf rotation(JsonObject display) {
        var a=vector(display.getAsJsonArray("rotation"));
        return new org.joml.Quaternionf().rotationXYZ((float)Math.toRadians(a.x),(float)Math.toRadians(a.y),(float)Math.toRadians(a.z));
    }
    @Test void independentJomlPointsMatchEveryChildBothHandsAndGrips() throws Exception {
        var manifest=json(Path.of(System.getProperty("w174.root", "."),"art/weapons/w174/claws_of_the_wolf/manifest.json"));
        var keys=manifest.getAsJsonArray("keyframes");
        var pivot=vector(manifest.getAsJsonArray("gripPivot"));
        var anchor=vector(manifest.getAsJsonArray("magazineAnchor"));
        for(int i=0;i<=20;i++) {
            float p=i/20f;var angles=new org.joml.Vector3f();var shift=new org.joml.Vector3f();var offset=new org.joml.Vector3f();
            for(int k=0;k<keys.size()-1;k++) {
                var a=keys.get(k).getAsJsonArray();var b=keys.get(k+1).getAsJsonArray();
                if(p<=b.get(0).getAsFloat()) {
                    float t=(p-a.get(0).getAsFloat())/(b.get(0).getAsFloat()-a.get(0).getAsFloat());t=t*t*(3-2*t);
                    angles.set(vector(a.get(1).getAsJsonArray())).lerp(vector(b.get(1).getAsJsonArray()),t);
                    shift.set(vector(a.get(2).getAsJsonArray())).lerp(vector(b.get(2).getAsJsonArray()),t);
                    offset.set(vector(a.get(3).getAsJsonArray())).lerp(vector(b.get(3).getAsJsonArray()),t);break;
                }
            }
            var motion=new org.joml.Quaternionf().rotationXYZ((float)Math.toRadians(angles.x),(float)Math.toRadians(angles.y),(float)Math.toRadians(angles.z));
            for(String grip:new String[]{"native","twohand"}) for(String hand:new String[]{"firstperson_righthand","firstperson_lefthand"}) {
                var idle=json(A.resolve("models/weapon_surface_w123/claws_of_the_wolf.json")).getAsJsonObject("display").getAsJsonObject(hand);
                var accepted=grip.equals("native") ? idle : json(A.resolve("models/weapon/pulse_rifle/claws_of_the_wolf_twohand.json")).getAsJsonObject("display").getAsJsonObject(hand);
                float scale=vector(accepted.getAsJsonArray("scale")).x;
                var idleQ=rotation(idle);var gripQ=rotation(accepted);
                var carrier=new org.joml.Quaternionf(gripQ).mul(new org.joml.Quaternionf(idleQ).conjugate());
                var worldPivot=new org.joml.Vector3f(pivot).sub(8,8,8).mul(scale).rotate(gripQ).add(vector(accepted.getAsJsonArray("translation"))).add(new org.joml.Vector3f(shift).rotate(carrier));
                for(String part:new String[]{"body","magazine"}) {
                    var child=json(A.resolve("models/"+KEY+"_%02d_%s_%s.json".formatted(i,part,grip))).getAsJsonObject("display").getAsJsonObject(hand);
                    for(var point:new org.joml.Vector3f[]{pivot,anchor,new org.joml.Vector3f(7.1f,11.2f,-6.3f)}) {
                        var local=new org.joml.Vector3f(point).sub(pivot);
                        if(part.equals("magazine")) local.add(offset);
                        var expected=local.rotate(motion).mul(scale).rotate(gripQ).add(worldPivot);
                        var actual=new org.joml.Vector3f(point).sub(8,8,8).mul(scale).rotate(rotation(child)).add(vector(child.getAsJsonArray("translation")));
                        assertTrue(expected.distance(actual)<0.00005f,"frame "+i+" "+grip+" "+hand+" "+part+" expected="+expected+" actual="+actual);
                    }
                }
            }
        }
    }
    /** Direct bounded runner; avoids compiling unrelated game/dependency sources. */
    public static void main(String[] args) throws Exception {
        var test=new ReloadW174ClawsOfTheWolfTest();int passed=0;
        for(var method:ReloadW174ClawsOfTheWolfTest.class.getDeclaredMethods()) {
            if(method.isAnnotationPresent(Test.class)) {
                try { method.invoke(test);System.out.println("PASS "+method.getName());passed++; }
                catch(java.lang.reflect.InvocationTargetException e) {throw new AssertionError(method.getName(),e.getCause());}
            }
        }
        System.out.println(passed+"/"+passed+" standalone targeted methods passed; actual Minecraft 26.3 parser/codec + JOML; no native game execution");
    }
}
