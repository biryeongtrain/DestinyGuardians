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
    @Test void nativeSpecialUsesExplicitLocalOriginCompensation() {
        var n=JsonParser.parseString(ProfileArmAssets.ITEM_JSON).getAsJsonObject().getAsJsonObject("model");
        var t=com.mojang.math.Transformation.EXTENDED_CODEC.parse(com.mojang.serialization.JsonOps.INSTANCE,n.get("transformation")).getOrThrow();
        var p=t.getMatrix().transformPosition(new org.joml.Vector3f(-.5f,-.5f,-.5f));
        assertEquals(0,p.length(),.000001f);assertEquals("minecraft:player_head",n.getAsJsonObject("model").get("type").getAsString());
    }
}
