package kim.biryeong.destiny.compat.pack;

import com.google.gson.*;
import com.mojang.math.Transformation;
import com.mojang.serialization.JsonOps;
import eu.pb4.polymer.resourcepack.api.PackResource;
import org.joml.Matrix4f;
import org.junit.jupiter.api.Test;
import java.util.*;
import static org.junit.jupiter.api.Assertions.*;

class SharedWeaponGeometryTest {
    private static JsonObject json(String s) { return JsonParser.parseString(s).getAsJsonObject(); }
    private static final JsonObject BASE=json("""
        {"elements":[],"textures":{"0":"destiny:test"},"display":{
        "firstperson_righthand":{"rotation":[12,31,-8],"translation":[1,2,3],"scale":[0.7,0.8,0.9]},
        "gui":{"rotation":[30,45,0],"scale":[0.8,0.8,0.8]}}}
        """);
    private static final JsonObject POSE=json("""
        {"parent":"destiny:weapon/base","display":{
        "firstperson_righthand":{"rotation":[-20,40,9],"translation":[2,4,-1],"scale":[1,0.8,0.5]},
        "firstperson_lefthand":{"rotation":[10,25,3],"translation":[-4,2,1]},
        "gui":{"rotation":[5,60,-10],"translation":[2,0,0]}}}
        """);
    private SharedWeaponGeometry sharing(JsonObject base, JsonObject pose) {
        return new SharedWeaponGeometry(Map.of("assets/destiny/models/weapon/base.json",PackResource.fromString(base.toString()),
                "assets/destiny/models/weapon/pose.json",PackResource.fromString(pose.toString())));
    }
    @Test void everyContextPreservesComposedTransformAndTintWithSharedGeometry() {
        var leaf=json("""
            {"type":"minecraft:model","model":"destiny:weapon/pose",
            "transformation":{"translation":[0.2,0.3,-0.1],"scale":[0.8,1.2,0.9],"left_rotation":[0,0,0,1],"right_rotation":[0,0,0,1]},
            "tints":[{"type":"minecraft:constant","value":123}]}
            """);
        var before=leaf.deepCopy();var result=sharing(BASE,POSE).rewrite(leaf);
        assertEquals(before,leaf);
        var original=Transformation.EXTENDED_CODEC.parse(JsonOps.INSTANCE,leaf.get("transformation")).getOrThrow().getMatrix();
        assertEquals(9,result.getAsJsonArray("cases").size());
        for (var raw:result.getAsJsonArray("cases")) {
            var entry=raw.getAsJsonObject();var context=entry.get("when").getAsString();var value=entry.getAsJsonObject("model");
            assertEquals("destiny:weapon/base",value.get("model").getAsString());
            assertEquals(leaf.get("tints"),value.get("tints"));
            var local=Transformation.EXTENDED_CODEC.parse(JsonOps.INSTANCE,value.get("transformation")).getOrThrow().getMatrix();
            var expected=SharedWeaponGeometry.matrix(List.of(POSE,BASE),context).mul(original);
            var actual=SharedWeaponGeometry.matrix(List.of(BASE),context).mul(local);
            assertTrue(expected.equals(actual,.00005f),context);
        }
        assertEquals(leaf.get("transformation"),result.getAsJsonObject("fallback").get("transformation"));
    }
    @Test void missingLeftUsesSameLevelRightBeforeParentLeft() {
        var child=json("{\"display\":{\"firstperson_righthand\":{\"translation\":[2,3,4]}}}");
        var parent=json("{\"display\":{\"firstperson_lefthand\":{\"translation\":[9,9,9]}}}");
        assertEquals(SharedArmGeometry.displayMatrix(child.getAsJsonObject("display").getAsJsonObject("firstperson_righthand"),true),
                SharedWeaponGeometry.matrix(List.of(child,parent),"firstperson_lefthand"));
    }
    @Test void textureOverridesSingularBasesAndAncestorTransformsStayUntouched() {
        var leaf=json("{\"type\":\"minecraft:model\",\"model\":\"destiny:weapon/pose\"}");
        var textured=POSE.deepCopy();textured.add("textures",json("{\"0\":\"destiny:other\"}"));
        assertEquals(leaf,sharing(BASE,textured).rewrite(leaf.deepCopy()));
        var singular=BASE.deepCopy();singular.getAsJsonObject("display").add("gui",json("{\"scale\":[0,0,0]}"));
        assertEquals(leaf,sharing(singular,POSE).rewrite(leaf.deepCopy()));
        var composite=json("{\"type\":\"minecraft:composite\",\"transformation\":{\"translation\":[1,2,3]},\"models\":[]}");
        composite.getAsJsonArray("models").add(leaf);
        assertEquals(composite,sharing(BASE,POSE).rewrite(composite.deepCopy()));
    }
}
