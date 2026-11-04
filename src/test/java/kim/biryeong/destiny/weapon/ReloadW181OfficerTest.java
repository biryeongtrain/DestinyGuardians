package kim.biryeong.destiny.weapon;

import com.google.gson.*;
import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.serialization.JsonOps;
import net.minecraft.client.color.item.ItemTintSources;
import net.minecraft.client.renderer.item.ItemModels;
import net.minecraft.client.resources.model.cuboid.CuboidModel;
import net.minecraft.world.item.ItemDisplayContext;
import org.joml.Quaternionf;
import org.joml.Vector3f;
import org.junit.jupiter.api.Test;
import java.io.StringReader;
import java.nio.file.*;
import java.util.*;
import static org.junit.jupiter.api.Assertions.*;

/** Standalone actual 26.3 asset parser/codec/transform acceptance. No runtime reload claim. */
class ReloadW181OfficerTest {
    static final Path ROOT=Path.of(System.getProperty("w181.root","."));
    static final Path A=ROOT.resolve("src/main/resources/assets/destiny");
    static final String KEY="weapon_reload_w181_seventh_seraph_officer_revolver/seventh_seraph_officer_revolver";
    static final String[] PARTS={"body","magazine"};
    static final String[] GRIPS={"native","twohand"};
    static JsonObject json(Path path) throws Exception {return JsonParser.parseString(Files.readString(path)).getAsJsonObject();}
    static CuboidModel parse(Path path) throws Exception {return CuboidModel.fromStream(new StringReader(Files.readString(path)));}
    static Path child(int i,String part,String grip) {return A.resolve("models/"+KEY+"_%02d_%s_%s.json".formatted(i,part,grip));}
    static Vector3f vector(JsonArray a) {return new Vector3f(a.get(0).getAsFloat(),a.get(1).getAsFloat(),a.get(2).getAsFloat());}
    static Quaternionf rotation(JsonObject d) {var a=vector(d.getAsJsonArray("rotation"));return degrees(a);}
    static Quaternionf degrees(Vector3f a) {return new Quaternionf().rotationXYZ((float)Math.toRadians(a.x),(float)Math.toRadians(a.y),(float)Math.toRadians(a.z));}
    @Test void representative263CuboidParserAcceptsParentsAndUnclampedChildren() throws Exception {
        int parsed=0;
        for(String part:PARTS) {assertNotNull(parse(A.resolve("models/"+KEY+"_"+part+".json")));parsed++;}
        for(int i:new int[]{0,7,13,20}) for(String part:PARTS) for(String grip:GRIPS) {
            var path=child(i,part,grip);var model=parse(path);parsed++;
            var display=json(path).getAsJsonObject("display");
            for(var ctx:new ItemDisplayContext[]{ItemDisplayContext.FIRST_PERSON_LEFT_HAND,ItemDisplayContext.FIRST_PERSON_RIGHT_HAND}) {
                var d=display.getAsJsonObject(ctx.getSerializedName());var t=model.transforms().getTransform(ctx);
                assertTrue(vector(d.getAsJsonArray("translation")).div(16).distance(t.translation())<1e-6f,"translation clamp "+path);
                assertTrue(vector(d.getAsJsonArray("scale")).distance(t.scale())<1e-6f,"scale clamp "+path);
            }
        }
        assertEquals(18,parsed);
    }
    @Test void canonical121ElementsUvPaintReconstructedWithWholeCylinder() throws Exception {
        var source=json(A.resolve("models/weapon_surface_w123/seventh_seraph_officer_revolver.json"));
        var manifest=json(ROOT.resolve("art/weapons/w181/seventh_seraph_officer_revolver/manifest.json"));
        var original=source.getAsJsonArray("elements");assertEquals(121,original.size());
        var rebuilt=new TreeMap<Integer,JsonElement>();int total=0;
        for(var part:PARTS) {
            var model=json(A.resolve("models/"+KEY+"_"+part+".json"));
            for(var entry:source.entrySet()) if(!entry.getKey().equals("elements")) assertEquals(entry.getValue(),model.get(entry.getKey()));
            var es=model.getAsJsonArray("elements");assertEquals(part.equals("body")?111:10,es.size());total+=es.size();
            var indices=manifest.getAsJsonObject("partitionIndices").getAsJsonArray(part);
            assertEquals(es.size(),indices.size());
            for(int i=0;i<es.size();i++) assertNull(rebuilt.put(indices.get(i).getAsInt(),es.get(i)),"duplicate canonical element");
        }
        assertEquals(121,total);assertTrue(total<=1000);assertEquals(121,rebuilt.size());
        for(int i=0;i<121;i++) assertEquals(original.get(i),rebuilt.get(i),"canonical element "+i);
        var cell=json(A.resolve("models/"+KEY+"_magazine.json")).getAsJsonArray("elements");
        String[] names={"rear_chamber","chamber_bevel_-1","chamber_bevel_1","chamber_underside",
            "chamber_brass_side_-1","chamber_brass_bevel_-1","chamber_brass_side_1",
            "chamber_brass_bevel_1","chamber_brass_top","chamber_brass_bottom"};
        assertEquals(10,cell.size());
        for(int i=0;i<10;i++) assertEquals(names[i],cell.get(i).getAsJsonObject().get("name").getAsString());
        var body=json(A.resolve("models/"+KEY+"_body.json")).getAsJsonArray("elements");
        var fixed=new HashSet<String>();for(var element:body)fixed.add(element.getAsJsonObject().get("name").getAsString());
        assertTrue(fixed.containsAll(Set.of("rear_frame","chamber_bottom_rail","shroud_main","top_rail","sight_base","grip_core")));
        assertFalse(fixed.contains("rear_chamber"));
    }

    @Test void bothGripsAndHandsHaveExactCanonicalEndpointsAndNonFpDisplays() throws Exception {
        for(var grip:GRIPS) {
            var accepted=json(A.resolve(grip.equals("native")?"models/weapon_surface_w123/seventh_seraph_officer_revolver.json":"models/weapon/hand_cannon/seventh_seraph_officer_revolver_twohand.json")).getAsJsonObject("display");
            for(int i=0;i<21;i++) for(var part:PARTS) {
                var c=json(child(i,part,grip));assertEquals(Set.of("parent","display"),c.keySet());
                assertEquals("destiny:"+KEY+"_"+part,c.get("parent").getAsString());var d=c.getAsJsonObject("display");
                for(var context:accepted.entrySet()) {
                    assertEquals(context.getValue().getAsJsonObject().get("scale"),d.getAsJsonObject(context.getKey()).get("scale"));
                    if(i==0||i==20||!context.getKey().startsWith("firstperson")) assertEquals(context.getValue(),d.get(context.getKey()));
                }
            }
        }
    }
    @Test void actual263ItemModelsCodecAndExplicitAdsInspectGuard() throws Exception {
        net.minecraft.SharedConstants.tryDetectVersion();net.minecraft.server.Bootstrap.bootStrap();
        ItemModels.bootstrap();ItemTintSources.bootstrap();
        net.minecraft.client.renderer.item.properties.select.SelectItemModelProperties.bootstrap();
        net.minecraft.client.renderer.item.properties.conditional.ConditionalItemModelProperties.bootstrap();
        net.minecraft.client.renderer.item.properties.numeric.RangeSelectItemModelProperties.bootstrap();
        var wrapper=json(A.resolve("items/"+KEY+".json"));var graph=wrapper.getAsJsonObject("model");
        var result=ItemModels.CODEC.parse(JsonOps.INSTANCE,graph);assertTrue(result.error().isEmpty(),result.error().toString());
        var canonical=json(A.resolve("items/weapon/seventh_seraph_officer_revolver.json"));var accepted=canonical.getAsJsonObject("model");
        assertEquals(canonical.get("hand_animation_on_swap"),wrapper.get("hand_animation_on_swap"));
        assertEquals(accepted,graph.get("fallback"));assertEquals("minecraft:display_context",graph.get("property").getAsString());
        var context=graph.getAsJsonArray("cases").get(0).getAsJsonObject();
        assertEquals(JsonParser.parseString("[\"firstperson_righthand\",\"firstperson_lefthand\"]"),context.get("when"));
        var guard=context.getAsJsonObject("model");assertEquals(accepted.get("cases"),guard.get("cases"));
        assertEquals("minecraft:custom_model_data",guard.get("property").getAsString());assertEquals(0,guard.get("index").getAsInt());
        var range=guard.getAsJsonObject("fallback");assertEquals(1,range.get("index").getAsInt());assertEquals(accepted,range.get("fallback"));
        var entries=range.getAsJsonArray("entries");assertEquals(21,entries.size());
        for(int i=0;i<21;i++) {
            var entry=entries.get(i).getAsJsonObject();assertEquals(i/20.,entry.get("threshold").getAsDouble(),1e-9);
            var condition=entry.getAsJsonObject("model");assertEquals(0,condition.get("index").getAsInt());
            for(String branch:new String[]{"on_true","on_false"}) {
                String grip=branch.equals("on_true")?"twohand":"native";
                var models=condition.getAsJsonObject(branch).getAsJsonArray("models");assertEquals(2,models.size());
                for(int j=0;j<2;j++) {
                    assertEquals("destiny:"+KEY+"_%02d_%s_%s".formatted(i,PARTS[j],grip),models.get(j).getAsJsonObject().get("model").getAsString());
                    assertTrue(Files.isRegularFile(child(i,PARTS[j],grip)));
                }
            }
        }
    }
    @Test void representativeParsedItemTransformsAndJomlAgreeIncludingLeftMirror() throws Exception {
        var manifest=json(ROOT.resolve("art/weapons/w181/seventh_seraph_officer_revolver/manifest.json"));var keys=manifest.getAsJsonArray("keyframes");
        var pivot=vector(manifest.getAsJsonArray("gripPivot"));var hinge=vector(manifest.getAsJsonArray("cylinderHinge"));int points=0;
        for(int i:new int[]{0,2,7,13,15,20}) {
            float p=i/20f;var angles=new Vector3f();var shift=new Vector3f();var cylinder=new Vector3f();
            for(int k=0;k<keys.size()-1;k++) {
                var a=keys.get(k).getAsJsonArray();var b=keys.get(k+1).getAsJsonArray();
                if(p<=b.get(0).getAsFloat()) {
                    float t=(p-a.get(0).getAsFloat())/(b.get(0).getAsFloat()-a.get(0).getAsFloat());t=t*t*(3-2*t);
                    angles.set(vector(a.get(1).getAsJsonArray())).lerp(vector(b.get(1).getAsJsonArray()),t);
                    shift.set(vector(a.get(2).getAsJsonArray())).lerp(vector(b.get(2).getAsJsonArray()),t);
                    cylinder.set(vector(a.get(3).getAsJsonArray())).lerp(vector(b.get(3).getAsJsonArray()),t);break;
                }
            }
            var motion=degrees(angles);var cylinderQ=degrees(cylinder);
            for(String grip:GRIPS) for(var context:new ItemDisplayContext[]{ItemDisplayContext.FIRST_PERSON_LEFT_HAND,ItemDisplayContext.FIRST_PERSON_RIGHT_HAND}) {
                String hand=context.getSerializedName();boolean left=context.leftHand();
                var idle=json(A.resolve("models/weapon_surface_w123/seventh_seraph_officer_revolver.json")).getAsJsonObject("display").getAsJsonObject(hand);
                var accepted=grip.equals("native")?idle:json(A.resolve("models/weapon/hand_cannon/seventh_seraph_officer_revolver_twohand.json")).getAsJsonObject("display").getAsJsonObject(hand);
                float scale=vector(accepted.getAsJsonArray("scale")).x;var idleQ=rotation(idle);var gripQ=rotation(accepted);
                var carrier=new Quaternionf(gripQ).mul(new Quaternionf(idleQ).conjugate());
                var worldPivot=new Vector3f(pivot).sub(8,8,8).mul(scale).rotate(gripQ).add(vector(accepted.getAsJsonArray("translation"))).add(new Vector3f(shift).rotate(carrier));
                for(String part:PARTS) {
                    var parsed=parse(child(i,part,grip)).transforms().getTransform(context);
                    var pose=new PoseStack.Pose();parsed.apply(left,pose);
                    for(var point:new Vector3f[]{pivot,hinge,new Vector3f(7.1f,11.2f,4.2f),new Vector3f(8.9f,12.72f,7.29f)}) {
                        // Left-hand apply is F * authoredTransform * F, where F reflects X.
                        // Compute direct carrier/pivot geometry independently of emitted Euler/translation.
                        var local=new Vector3f(point);if(left)local.x=16-local.x;
                        if(part.equals("magazine"))local.sub(hinge).rotate(cylinderQ).add(hinge);
                        local.sub(pivot);
                        var expected=local.rotate(motion).mul(scale).rotate(gripQ).add(worldPivot).div(16);
                        if(left)expected.x=-expected.x;
                        var actual=pose.pose().transformPosition(new Vector3f(point).div(16));
                        assertTrue(expected.distance(actual)<0.000006f,"frame "+i+" "+grip+" "+hand+" "+part+" expected="+expected+" actual="+actual);
                        points++;
                    }
                }
            }
        }
        assertEquals(192,points);
    }
    /** Direct bounded runner avoids unrelated source/dependency compilation and all Gradle gates. */
    public static void main(String[] args) throws Exception {
        var test=new ReloadW181OfficerTest();int passed=0;
        var methods=Arrays.stream(ReloadW181OfficerTest.class.getDeclaredMethods()).filter(m->m.isAnnotationPresent(Test.class)).sorted(Comparator.comparing(java.lang.reflect.Method::getName)).toList();
        for(var method:methods) {
            try{method.invoke(test);System.out.println("PASS "+method.getName());passed++;}
            catch(java.lang.reflect.InvocationTargetException e){throw new AssertionError(method.getName(),e.getCause());}
        }
        System.out.println(passed+"/"+methods.size()+" targeted methods passed; representative 26.3 cuboid parser + ItemModels codec + 192 parsed ItemTransform/JOML points; no native execution");
    }
}
