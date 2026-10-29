package kim.biryeong.destiny.compat.pack;

import com.google.gson.JsonParser;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class ProfileArmAssetsTest {
    @Test void removesPixelMeshesWithoutChangingWeaponTransformOrSelector() {
        var input=JsonParser.parseString("""
          {"type":"minecraft:range_dispatch","property":"minecraft:custom_model_data","index":1,
           "fallback":{"type":"minecraft:composite","models":[
             {"type":"minecraft:model","model":"destiny:body","transformation":[1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1]},
             {"type":"minecraft:model","model":"destiny:skin_arm_w204/poses/right_classic_test","tints":[{"type":"minecraft:constant","value":16711680}]}]},
           "entries":[{"threshold":0.5,"model":{"type":"minecraft:model","model":"destiny:skin_arm_w204/poses/left_classic_test"}}]}
          """).getAsJsonObject();
        var before=input.deepCopy();var result=ProfileArmAssets.gunOnly(input);
        assertEquals(before,input,"pack converter must not mutate source graph");
        assertEquals("destiny:body",result.getAsJsonObject("fallback").get("model").getAsString());
        assertEquals(before.getAsJsonObject("fallback").getAsJsonArray("models").get(0).getAsJsonObject().get("transformation"),result.getAsJsonObject("fallback").get("transformation"));
        assertEquals(0.5,result.getAsJsonArray("entries").get(0).getAsJsonObject().get("threshold").getAsDouble());
        assertEquals("minecraft:empty",result.getAsJsonArray("entries").get(0).getAsJsonObject().getAsJsonObject("model").get("type").getAsString());
        assertFalse(result.toString().contains("skin_arm_w204"));assertFalse(result.toString().contains("tints"));
    }
    @Test void gunProjectionPreservesExactOutputAndDetachesEveryMutableContainer() {
        var input=JsonParser.parseString("""
          {"type":"minecraft:composite","transformation":{"translation":[1,2,3]},"models":[
            {"type":"minecraft:condition","property":"minecraft:custom_model_data","index":8,
             "on_true":{"type":"minecraft:composite","transformation":[2,3],"models":[
               {"type":"minecraft:model","model":"destiny:body","tints":[{"type":"minecraft:constant","value":123}],"transformation":{"scale":[1,2,1]}},
               {"type":"minecraft:model","model":"destiny:skin_arm_w204/poses/right"}]},
             "on_false":{"type":"minecraft:composite","transformation":[4,5],"models":[
               {"type":"minecraft:model","model":"destiny:skin_arm_w204/poses/left"}]},
             "opaque":{"fallback":{"type":"minecraft:model","model":"destiny:skin_arm_w204/keep"}}},
            {"type":"minecraft:range_dispatch","property":"minecraft:custom_model_data","index":1,"scale":0.5,
             "entries":[{"threshold":-0.0,"opaque":{"samples":[1,2]},"model":{"type":"minecraft:model","model":"destiny:skin_arm_w204/poses/upper"}},
                        {"model":{"type":"minecraft:model","model":"destiny:magazine"},"threshold":0.0}],
             "fallback":{"type":"minecraft:empty","opaque":[{"value":7}]}},
            {"type":"minecraft:select","property":"minecraft:display_context",
             "cases":[{"when":["firstperson_righthand","firstperson_lefthand"],"model":{"type":"minecraft:composite","transformation":[6,7],"models":[
               {"type":"minecraft:model","model":"destiny:body"},{"type":"minecraft:empty"},
               {"type":"minecraft:model","model":"destiny:body"}]},"opaque":{"model":["keep"]}}],
             "fallback":{"type":"minecraft:model","model":"destiny:skin_arm_w204/poses/right"}},
            {"type":"custom:opaque","models":[{"type":"minecraft:model","model":"destiny:skin_arm_w204/keep"}],
             "model":{"payload":[1,null]},"transformation":{"rotation":[0,90,0]}}
          ],"opaque":{"cases":[{"model":"keep"}],"nullable":null}}
          """).getAsJsonObject();
        var expected=JsonParser.parseString("""
          {"type":"minecraft:composite","transformation":{"translation":[1,2,3]},"models":[
            {"type":"minecraft:condition","property":"minecraft:custom_model_data","index":8,
             "on_true":{"type":"minecraft:model","model":"destiny:body","tints":[{"type":"minecraft:constant","value":123}],"transformation":{"scale":[1,2,1]}},
             "on_false":{"type":"minecraft:empty"},
             "opaque":{"fallback":{"type":"minecraft:model","model":"destiny:skin_arm_w204/keep"}}},
            {"type":"minecraft:range_dispatch","property":"minecraft:custom_model_data","index":1,"scale":0.5,
             "entries":[{"threshold":-0.0,"opaque":{"samples":[1,2]},"model":{"type":"minecraft:empty"}},
                        {"model":{"type":"minecraft:model","model":"destiny:magazine"},"threshold":0.0}],
             "fallback":{"type":"minecraft:empty","opaque":[{"value":7}]}},
            {"type":"minecraft:select","property":"minecraft:display_context",
             "cases":[{"when":["firstperson_righthand","firstperson_lefthand"],"model":{"type":"minecraft:composite","transformation":[6,7],"models":[
               {"type":"minecraft:model","model":"destiny:body"},
               {"type":"minecraft:model","model":"destiny:body"}]},"opaque":{"model":["keep"]}}],
             "fallback":{"type":"minecraft:empty"}},
            {"type":"custom:opaque","models":[{"type":"minecraft:model","model":"destiny:skin_arm_w204/keep"}],
             "model":{"payload":[1,null]},"transformation":{"rotation":[0,90,0]}}
          ],"opaque":{"cases":[{"model":"keep"}],"nullable":null}}
          """).getAsJsonObject();
        String before=input.toString();
        var result=ProfileArmAssets.gunOnly(input);
        assertEquals(expected,result);
        assertEquals(expected.toString(),result.toString(),"field order and numeric spelling must also stay unchanged");
        assertEquals(before,input.toString(),"projection must not mutate the input");
        // Preserve even the existing zero/single-child composite collapse with transformation metadata.
        // Mutate ALL result containers, including opaque metadata, to detect any source aliases.
        mutateContainers(result);
        assertEquals(before,input.toString(),"projected children and opaque metadata must be fully detached");
    }

    private static void mutateContainers(com.google.gson.JsonElement value) {
        if(value.isJsonObject()) {
            var object=value.getAsJsonObject();
            object.entrySet().forEach(entry->mutateContainers(entry.getValue()));
            object.addProperty("test_mutation",true);
        } else if(value.isJsonArray()) {
            var array=value.getAsJsonArray();
            array.forEach(ProfileArmAssetsTest::mutateContainers);
            array.add("test_mutation");
        }
    }

    @Test void nativeSpecialUsesExplicitLocalOriginCompensation() {
        var n=JsonParser.parseString(ProfileArmAssets.ITEM_JSON).getAsJsonObject().getAsJsonObject("model");
        var t=com.mojang.math.Transformation.EXTENDED_CODEC.parse(com.mojang.serialization.JsonOps.INSTANCE,n.get("transformation")).getOrThrow();
        var p=t.getMatrix().transformPosition(new org.joml.Vector3f(-.5f,-.5f,-.5f));
        assertEquals(0,p.length(),.000001f);assertEquals("minecraft:player_head",n.getAsJsonObject("model").get("type").getAsString());
    }
}
