package kim.biryeong.destiny.weapon;

import com.google.gson.*;
import com.mojang.serialization.JsonOps;
import net.minecraft.client.color.item.ItemTintSources;
import net.minecraft.client.renderer.item.ItemModels;
import net.minecraft.client.resources.model.cuboid.CuboidModel;
import org.junit.jupiter.api.Test;
import org.joml.Vector3f;
import org.joml.Quaternionf;
import java.io.StringReader;
import java.nio.file.*;
import static org.junit.jupiter.api.Assertions.*;

/** Standalone Java25 actual26.3 asset parser/codec + independent JOML checks.
 * Runtime admission, server GT and native presentation are master-owned. */
class InsertW179MindbenderTest {
    static final Path ROOT=Path.of(System.getProperty("w179.root","."));
    static final Path A=ROOT.resolve("src/main/resources/assets/destiny");
    static final String KEY="weapon_insert_w179_mindbender_s_ambition_adept/mindbender_s_ambition_adept";
    static final String[] PHASES={"initial","loop","return"};
    static final String[] PARTS={"body","shell"}, GRIPS={"native","twohand"};
    static final String[] HANDS={"firstperson_righthand","firstperson_lefthand"};
    static JsonObject json(Path path) throws Exception {return JsonParser.parseString(Files.readString(path)).getAsJsonObject();}
    static JsonObject child(String phase,int i,String part,String grip) throws Exception {
        return json(A.resolve("models/"+KEY+"_%s_%02d_%s_%s.json".formatted(phase,i,part,grip)));
    }
    static JsonObject source() throws Exception {return json(A.resolve("models/weapon_surface_w123/mindbender_s_ambition_adept.json"));}
    static JsonObject accepted(String grip) throws Exception {
        return grip.equals("native")?source().getAsJsonObject("display"):
            json(A.resolve("models/weapon/shotgun/mindbender_s_ambition_adept_twohand.json")).getAsJsonObject("display");
    }
    @Test void representative263ParserAcceptsParentsAndPhaseHandGripChildrenAndRejectsMalformedControl() throws Exception {
        for (String part:PARTS) {
            assertNotNull(CuboidModel.fromStream(new StringReader(Files.readString(A.resolve("models/"+KEY+"_"+part+".json")))));
            for (String phase:PHASES) for (String grip:GRIPS) for (int frame:new int[]{0,11,20}) {
                var model=child(phase,frame,part,grip);
                assertNotNull(CuboidModel.fromStream(new StringReader(model.toString())));
            }
        }
        assertThrows(Exception.class,()->CuboidModel.fromStream(new StringReader("{\"elements\":[{\"from\":[1,2],\"to\":[3,4,5],\"faces\":{}}]}")));
    }
    @Test void canonicalBodyAndUvsExactAndConnectedHiddenShellBudget() throws Exception {
        var canonical=json(kim.biryeong.destiny.testfixtures.PreW251Assets.path("src/main/resources/assets/destiny/models/weapon_surface_w123/mindbender_s_ambition_adept.json"));var body=json(A.resolve("models/"+KEY+"_body.json"));var shell=json(A.resolve("models/"+KEY+"_shell.json"));
        assertEquals(canonical,body);assertEquals(104,body.getAsJsonArray("elements").size());
        assertEquals(12,shell.getAsJsonArray("elements").size());assertEquals(canonical.get("textures"),shell.get("textures"));
        assertTrue(104+12<=1000);
        for(var e:shell.getAsJsonArray("elements")) {
            var el=e.getAsJsonObject();var from=vector(el.getAsJsonArray("from"));var to=vector(el.getAsJsonArray("to"));
            assertTrue(to.x>from.x && to.y>from.y && to.z>from.z);
        }
        for(var texture:canonical.getAsJsonObject("textures").entrySet()) {
            String id=texture.getValue().getAsString();assertTrue(Files.isRegularFile(A.resolve("textures/"+id.substring("destiny:".length())+".png")));
        }
    }
    @Test void bothHandsGripsExactHipAndHeldSeamsWithHiddenShell() throws Exception {
        for(String grip:GRIPS) {
            assertEquals(accepted(grip),child("initial",0,"body",grip).get("display"));
            assertEquals(accepted(grip),child("return",20,"body",grip).get("display"));
            var held=child("initial",20,"body",grip).get("display");
            assertEquals(held,child("loop",0,"body",grip).get("display"));
            assertEquals(held,child("loop",20,"body",grip).get("display"));
            assertEquals(held,child("return",0,"body",grip).get("display"));
            assertNotEquals(accepted(grip),held);
            String[] phases={"initial","initial","loop","loop","return","return"};int[] frames={0,20,0,20,0,20};
            for(int j=0;j<frames.length;j++) for(String hand:HANDS)
                assertEquals(new Vector3f(),vector(child(phases[j],frames[j],"shell",grip).getAsJsonObject("display").getAsJsonObject(hand).getAsJsonArray("scale")));
        }
    }
    @Test void real263ItemCodecAcceptsPhasedFpGraphWithExactCanonicalFallback() throws Exception {
        net.minecraft.SharedConstants.tryDetectVersion();net.minecraft.server.Bootstrap.bootStrap();
        ItemModels.bootstrap();ItemTintSources.bootstrap();
        net.minecraft.client.renderer.item.properties.select.SelectItemModelProperties.bootstrap();
        net.minecraft.client.renderer.item.properties.conditional.ConditionalItemModelProperties.bootstrap();
        net.minecraft.client.renderer.item.properties.numeric.RangeSelectItemModelProperties.bootstrap();
        var canonical=json(A.resolve("items/weapon/mindbender_s_ambition_adept.json"));var wrapper=json(A.resolve("items/"+KEY+".json"));var graph=wrapper.getAsJsonObject("model");
        var result=ItemModels.CODEC.parse(JsonOps.INSTANCE,graph);assertTrue(result.error().isEmpty(),result.error().toString());
        assertTrue(ItemModels.CODEC.parse(JsonOps.INSTANCE,JsonParser.parseString("{\"type\":\"destiny:invalid_w179_control\"}")).error().isPresent());
        assertEquals(canonical.get("model"),graph.get("fallback"));assertEquals(canonical.get("hand_animation_on_swap"),wrapper.get("hand_animation_on_swap"));
        var context=graph.getAsJsonArray("cases").get(0).getAsJsonObject();assertEquals(JsonParser.parseString("[\"firstperson_righthand\",\"firstperson_lefthand\"]"),context.get("when"));
        var modes=context.getAsJsonObject("model");
        for(var c:modes.getAsJsonArray("cases"))assertEquals(canonical.get("model"),c.getAsJsonObject().get("model"));
        var range=modes.getAsJsonObject("fallback");assertEquals(4,range.get("index").getAsInt());assertEquals(canonical.get("model"),range.get("fallback"));
        var entries=range.getAsJsonArray("entries");assertEquals(63,entries.size());
        for(int phase=0;phase<3;phase++) for(int i=0;i<=20;i++) {
            var entry=entries.get(phase*21+i).getAsJsonObject();assertEquals(phase*2+i/20.,entry.get("threshold").getAsDouble(),1e-9);
            var condition=entry.getAsJsonObject("model");assertEquals(0,condition.get("index").getAsInt());
            for(String branch:new String[]{"on_true","on_false"}) {
                String grip=branch.equals("on_true")?"twohand":"native";var composite=condition.getAsJsonObject(branch);assertEquals("minecraft:composite",composite.get("type").getAsString());
                var models=composite.getAsJsonArray("models");assertEquals(2,models.size());
                for(int part=0;part<2;part++) {
                    String id="destiny:"+KEY+"_%s_%02d_%s_%s".formatted(PHASES[phase],i,PARTS[part],grip);
                    assertEquals(id,models.get(part).getAsJsonObject().get("model").getAsString());
                    assertEquals("destiny:"+KEY+"_"+PARTS[part],child(PHASES[phase],i,PARTS[part],grip).get("parent").getAsString());
                }
            }
        }
    }
    static Vector3f vector(JsonArray a) {return new Vector3f(a.get(0).getAsFloat(),a.get(1).getAsFloat(),a.get(2).getAsFloat());}
    static Quaternionf rotation(JsonObject d) {
        var a=vector(d.getAsJsonArray("rotation"));return new Quaternionf().rotationXYZ((float)Math.toRadians(a.x),(float)Math.toRadians(a.y),(float)Math.toRadians(a.z));
    }
    @Test void independentJomlGripAnchorAndFarPointForEveryPhaseHandGrip() throws Exception {
        var manifest=json(ROOT.resolve("art/weapons/w179/mindbender_s_ambition_adept/manifest.json"));
        var pivot=vector(manifest.getAsJsonArray("gripPivot"));var anchor=vector(manifest.getAsJsonArray("shellAnchor"));int points=0;
        for(String phase:PHASES) for(int i:new int[]{0,3,8,11,16,20}) {
            float p=i/20f;var angles=new Vector3f();var shift=new Vector3f();var offset=new Vector3f();
            var keys=manifest.getAsJsonObject("keyframes").getAsJsonArray(phase);
            for(int k=0;k<keys.size()-1;k++) {
                var a=keys.get(k).getAsJsonArray();var b=keys.get(k+1).getAsJsonArray();
                if(p<=b.get(0).getAsFloat()) {
                    float t=(p-a.get(0).getAsFloat())/(b.get(0).getAsFloat()-a.get(0).getAsFloat());t=t*t*(3-2*t);
                    angles.set(vector(a.get(1).getAsJsonArray())).lerp(vector(b.get(1).getAsJsonArray()),t);
                    shift.set(vector(a.get(2).getAsJsonArray())).lerp(vector(b.get(2).getAsJsonArray()),t);
                    offset.set(vector(a.get(3).getAsJsonArray())).lerp(vector(b.get(3).getAsJsonArray()),t);break;
                }
            }
            var motion=new Quaternionf().rotationXYZ((float)Math.toRadians(angles.x),(float)Math.toRadians(angles.y),(float)Math.toRadians(angles.z));
            for(String grip:GRIPS) for(String hand:HANDS) {
                var idle=accepted("native").getAsJsonObject(hand);var base=accepted(grip).getAsJsonObject(hand);
                var idleQ=rotation(idle);var gripQ=rotation(base);float scale=vector(base.getAsJsonArray("scale")).x;
                var carrier=new Quaternionf(gripQ).mul(new Quaternionf(idleQ).conjugate());
                var worldPivot=new Vector3f(pivot).sub(8,8,8).mul(scale).rotate(gripQ).add(vector(base.getAsJsonArray("translation"))).add(new Vector3f(shift).rotate(carrier));
                for(String part:PARTS) {
                    var d=child(phase,i,part,grip).getAsJsonObject("display").getAsJsonObject(hand);
                    boolean hidden=vector(d.getAsJsonArray("scale")).lengthSquared()==0;
                    var queries=part.equals("shell") && hidden?new Vector3f[]{anchor}:new Vector3f[]{pivot,anchor,new Vector3f(7.1f,11.2f,-6.3f)};
                    for(var point:queries) {
                        var local=new Vector3f(point).sub(pivot);if(part.equals("shell"))local.add(offset);
                        var expected=local.rotate(motion).mul(scale).rotate(gripQ).add(worldPivot);
                        var actual=new Vector3f(point).sub(8,8,8).mul(vector(d.getAsJsonArray("scale"))).rotate(rotation(d)).add(vector(d.getAsJsonArray("translation")));
                        assertTrue(expected.distance(actual)<.00006f,phase+" "+i+" "+part+" "+grip+" "+hand+" expected="+expected+" actual="+actual);points++;
                    }
                }
            }
        }
        System.out.println("JOML representative transformed point assertions: "+points);
    }
    public static void main(String[] args) throws Exception {
        var test=new InsertW179MindbenderTest();int passed=0;
        for(var method:InsertW179MindbenderTest.class.getDeclaredMethods()) if(method.isAnnotationPresent(Test.class)) {
            try {method.invoke(test);System.out.println("PASS "+method.getName());passed++;}
            catch(java.lang.reflect.InvocationTargetException e){throw new AssertionError(method.getName(),e.getCause());}
        }
        System.out.println(passed+"/"+passed+" targeted methods passed; actual Minecraft26.3 Cuboid parser/item codec + JOML; no game/server execution");
    }
}
