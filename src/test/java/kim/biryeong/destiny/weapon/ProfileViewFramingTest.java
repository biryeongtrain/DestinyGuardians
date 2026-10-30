package kim.biryeong.destiny.weapon;

import org.junit.jupiter.api.Test;
import org.joml.Vector3f;
import static org.junit.jupiter.api.Assertions.*;

class ProfileViewFramingTest {
    @Test void chargedCrossbowCompensationIsAppliedBeforeEveryModelPose() {
        var right=ProfileWeaponView.handMatrix(false,true,1);
        var left=ProfileWeaponView.handMatrix(true,true,1);
        assertEquals(.56f-.641864f,right.m30(),1e-6f);
        assertEquals(-right.m30(),left.m30(),1e-6f);
        var forward=right.transformDirection(new Vector3f(0,0,-1));
        assertEquals(-(float)Math.sin(Math.toRadians(10)),forward.x,1e-6f);
        assertEquals(-(float)Math.cos(Math.toRadians(10)),forward.z,1e-6f);
        assertTrue(right.equals(ProfileWeaponView.handMatrix(false,true,0),1e-6f));
    }
    @Test void oneHandHipMovesInwardAndAdsKeepsItsCalibratedSightLine() {
        assertEquals(.44f,ProfileWeaponView.handX(false,false,0),1e-6f);
        assertEquals(.56f,ProfileWeaponView.handX(false,false,1),1e-6f);
        for(int i=0;i<=20;i++)assertEquals(-ProfileWeaponView.handX(false,false,i/20f),ProfileWeaponView.handX(true,false,i/20f));
    }
    private static com.google.gson.JsonObject arm(String id){
        return com.google.gson.JsonParser.parseString("{\"type\":\"minecraft:model\",\"model\":\"destiny:skin_arm_w204/poses/"+id+"\"}").getAsJsonObject();
    }
    private static com.google.gson.JsonObject grip(com.google.gson.JsonObject two,com.google.gson.JsonObject nat){
        var o=new com.google.gson.JsonObject();o.addProperty("type","minecraft:condition");o.addProperty("property","minecraft:custom_model_data");
        o.addProperty("index",0);o.add("on_true",two);o.add("on_false",nat);return ProfileArmGraph.armsOnly(o);
    }
    /** W278: reload banks that bake the native grip into both branches must not get the inverse carrier. */
    @Test void carrierOnlyForRoutesWithDistinctTwoHandPoses() {
        var data=new net.minecraft.world.item.component.CustomModelData(java.util.List.of(),java.util.List.of(true),java.util.List.of(),java.util.List.of());
        var distinct=grip(arm("right_classic_a"),arm("right_classic_b"));
        var shared=grip(arm("right_classic_a"),arm("right_classic_a"));
        assertTrue(ProfileWeaponView.carrierCompensated(distinct,data,false,false,ProfileArmGraph.select(distinct,data,false,false)));
        assertFalse(ProfileWeaponView.carrierCompensated(shared,data,false,false,ProfileArmGraph.select(shared,data,false,false)));
        var native_=ProfileWeaponView.handMatrix(false,true,false,0);
        assertEquals(ProfileWeaponView.handX(false,true,0),native_.m30(),1e-6f);
        assertEquals(0,native_.m20(),1e-6f);
    }
}
