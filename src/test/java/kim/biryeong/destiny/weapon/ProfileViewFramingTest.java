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
}
