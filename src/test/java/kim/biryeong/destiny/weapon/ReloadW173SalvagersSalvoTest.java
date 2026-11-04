package kim.biryeong.destiny.weapon;

import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import com.mojang.serialization.JsonOps;
import net.minecraft.client.color.item.ItemTintSources;
import net.minecraft.client.renderer.item.ItemModels;
import net.minecraft.client.resources.model.cuboid.CuboidModel;
import org.junit.jupiter.api.Test;
import org.joml.Matrix3d;
import org.joml.Vector3d;
import java.io.StringReader;
import java.nio.file.*;
import static org.junit.jupiter.api.Assertions.*;

/** Real 26.3 asset codecs. Master owns route 18, GameTests and native grip QA. */
class ReloadW173SalvagersSalvoTest {
    static final Path A=Path.of("src/main/resources/assets/destiny");
    static final String KEY="weapon_reload_w173_salvager_s_salvo/salvager_s_salvo";
    static final String[] PARTS={"body","barrel","round"};
    static final String[] HANDS={"firstperson_righthand","firstperson_lefthand"};
    static JsonObject json(Path path) throws Exception {return JsonParser.parseString(Files.readString(path)).getAsJsonObject();}
    static JsonObject child(int i,String part,String grip) throws Exception {return json(A.resolve("models/"+KEY+"_%02d_%s_%s.json".formatted(i,part,grip)));}
    static boolean barrel(int i) {return i<32 || i>=36&&i<58 || i>=73&&i<76 || i>=85;}
    static Vector3d vector(JsonObject t,String key) {var a=t.getAsJsonArray(key);return new Vector3d(a.get(0).getAsDouble(),a.get(1).getAsDouble(),a.get(2).getAsDouble());}
    static Matrix3d rotation(JsonObject t) {var a=vector(t,"rotation").mul(Math.PI/180);return new Matrix3d().rotationXYZ(a.x,a.y,a.z);}
    static Vector3d point(JsonObject t,Vector3d p) {return rotation(t).transform(new Vector3d(p).sub(8,8,8).mul(vector(t,"scale"))).add(vector(t,"translation"));}
    @Test void real263CuboidParserAcceptsAll129Models() throws Exception {
        try(var paths=Files.list(A.resolve("models/weapon_reload_w173_salvager_s_salvo"))) {
            var models=paths.toList();assertEquals(129,models.size());
            for(var p:models) assertNotNull(CuboidModel.fromStream(new StringReader(Files.readString(p))),p.toString());
        }
    }
    @Test void fixedReceiverFaceAndGripArePartitionedWithoutChangingUvOrGeometry() throws Exception {
        var source=json(A.resolve("models/weapon_surface_w123/salvager_s_salvo.json"));
        var body=json(A.resolve("models/"+KEY+"_body.json"));var moving=json(A.resolve("models/"+KEY+"_barrel.json"));
        var round=json(A.resolve("models/"+KEY+"_round.json"));
        assertEquals(28,body.getAsJsonArray("elements").size());assertEquals(73,moving.getAsJsonArray("elements").size());assertEquals(6,round.getAsJsonArray("elements").size());
        int b=0,m=0;
        for(int i=0;i<101;i++) assertEquals(source.getAsJsonArray("elements").get(i),barrel(i)?moving.getAsJsonArray("elements").get(m++):body.getAsJsonArray("elements").get(b++));
        var fixed=new java.util.HashSet<String>();for(var e:body.getAsJsonArray("elements"))fixed.add(e.getAsJsonObject().get("name").getAsString());
        assertTrue(fixed.containsAll(java.util.Set.of("receiver_core","grip_main","trigger","guard_floor","stock_wood","breech_plug_0","breech_plug_3")));
        for(var p:new JsonObject[]{body,moving,round})assertEquals(source.get("textures"),p.get("textures"));
        for(var e:round.getAsJsonArray("elements"))assertTrue(e.getAsJsonObject().get("name").getAsString().startsWith("cosmetic_round_"));
        assertTrue(28+73+6<=1000);
    }
    @Test void exactHipEndpointsAndNoNonFpTransformChanges() throws Exception {
        for(String grip:new String[]{"native","twohand"}) {
            var expected=json(A.resolve(grip.equals("native")?"models/weapon_surface_w123/salvager_s_salvo.json":"models/weapon/grenade_launcher/salvager_s_salvo_twohand.json")).getAsJsonObject("display");
            for(int i=0;i<21;i++)for(String part:PARTS) {
                var c=child(i,part,grip);assertFalse(c.has("elements"));var d=c.getAsJsonObject("display");
                if(i==0||i==20)assertEquals(expected,d);
                for(var entry:expected.entrySet())if(!entry.getKey().startsWith("firstperson_"))assertEquals(entry.getValue(),d.get(entry.getKey()));
                for(String hand:HANDS)assertEquals(expected.getAsJsonObject(hand).get("scale"),d.getAsJsonObject(hand).get("scale"));
            }
        }
    }
    @Test void realJomlChildDisplaysKeepHingeCoincidentAndRoundAlongOpenedBore() throws Exception {
        var q=new Vector3d(8,10.91,4.14);
        for(String grip:new String[]{"native","twohand"})for(String hand:HANDS)for(int i:new int[]{3,6,9,13,15,18}) {
            var b=child(i,"body",grip).getAsJsonObject("display").getAsJsonObject(hand);
            var h=child(i,"barrel",grip).getAsJsonObject("display").getAsJsonObject(hand);
            assertTrue(point(b,q).distance(point(h,q))<1e-8,"hinge detached "+i+grip+hand);
        }
        // Sample 13 seats the round in the open fore-end before it vanishes.
        for(String grip:new String[]{"native","twohand"})for(String hand:HANDS) {
            var h=child(13,"barrel",grip).getAsJsonObject("display").getAsJsonObject(hand);
            assertEquals(h,child(13,"round",grip).getAsJsonObject("display").getAsJsonObject(hand));
            assertNotEquals(child(6,"body",grip).getAsJsonObject("display").getAsJsonObject(hand).get("rotation"),child(6,"barrel",grip).getAsJsonObject("display").getAsJsonObject(hand).get("rotation"));
        }
    }
    @Test void real263ItemCodecAcceptsHiddenRoundAndExactCanonicalFallback() throws Exception {
        net.minecraft.SharedConstants.tryDetectVersion();net.minecraft.server.Bootstrap.bootStrap();
        ItemModels.bootstrap();ItemTintSources.bootstrap();
        net.minecraft.client.renderer.item.properties.select.SelectItemModelProperties.bootstrap();
        net.minecraft.client.renderer.item.properties.conditional.ConditionalItemModelProperties.bootstrap();
        net.minecraft.client.renderer.item.properties.numeric.RangeSelectItemModelProperties.bootstrap();
        var wrapper=json(A.resolve("items/"+KEY+".json"));var graph=wrapper.getAsJsonObject("model");
        var decoded=ItemModels.CODEC.parse(JsonOps.INSTANCE,graph);assertTrue(decoded.error().isEmpty(),decoded.error().toString());
        var canonical=json(A.resolve("items/weapon/salvager_s_salvo.json"));
        assertEquals(canonical.get("hand_animation_on_swap"),wrapper.get("hand_animation_on_swap"));assertEquals(canonical.get("model"),graph.get("fallback"));
        var context=graph.getAsJsonArray("cases").get(0).getAsJsonObject();
        assertEquals(JsonParser.parseString("[\"firstperson_righthand\",\"firstperson_lefthand\"]"),context.get("when"));
        var range=context.getAsJsonObject("model");assertEquals(1,range.get("index").getAsInt());assertEquals(canonical.get("model"),range.get("fallback"));
        var entries=range.getAsJsonArray("entries");assertEquals(21,entries.size());
        for(int i=0;i<21;i++) {
            var e=entries.get(i).getAsJsonObject();assertEquals(i/20.,e.get("threshold").getAsDouble(),1e-9);var cond=e.getAsJsonObject("model");assertEquals(0,cond.get("index").getAsInt());
            boolean visible=i>=9&&i<=13;
            for(String branch:new String[]{"on_true","on_false"}) {
                var models=cond.getAsJsonObject(branch).getAsJsonArray("models");assertEquals(visible?3:2,models.size());String grip=branch.equals("on_true")?"twohand":"native";
                for(int j=0;j<models.size();j++) {
                    assertEquals("destiny:"+KEY+"_%02d_%s_%s".formatted(i,PARTS[j],grip),models.get(j).getAsJsonObject().get("model").getAsString());
                    assertEquals("destiny:"+KEY+"_"+PARTS[j],child(i,PARTS[j],grip).get("parent").getAsString());
                }
            }
        }
    }
}
