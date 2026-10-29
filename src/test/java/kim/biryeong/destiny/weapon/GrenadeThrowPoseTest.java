package kim.biryeong.destiny.weapon;

import org.joml.Vector3f;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class GrenadeThrowPoseTest {
    @Test void transitionPreservesEndpointsAndArmWidthWithoutMatrixShear() {
        for(boolean slim:new boolean[]{false,true})for(int segment=0;segment<4;segment++) {
            var from=GrenadeThrowPose.arm(segment,0,slim,false);
            var to=GrenadeThrowPose.arm(segment,.7f,slim,false);
            for(float t:new float[]{.2f,.5f,.8f}) {
                var blended=GrenadeThrowPose.blendArm(from,to,t,slim);
                var expected=new Vector3f(0,-.5f,0).mulPosition(from).lerp(new Vector3f(0,-.5f,0).mulPosition(to),t);
                assertTrue(expected.distance(new Vector3f(0,-.5f,0).mulPosition(blended))<1e-5);
                var x=blended.getColumn(0,new Vector3f());var y=blended.getColumn(1,new Vector3f());
                assertEquals(slim?.225:.3,x.length(),1e-5);
                assertEquals(0,x.dot(y),1e-5);
            }
        }
    }
    @Test void nativeHeadNegativeYAxisKeepsBothElbowsAndThrowingWristConnected() {
        for (boolean mirror : new boolean[]{false,true}) for (boolean slim : new boolean[]{false,true}) {
            for (int frame=0;frame<=60;frame++) {
                float progress=frame/60f;
                for (int side=0;side<2;side++) {
                    var upperEnd=new Vector3f(0,-.5f,0).mulPosition(GrenadeThrowPose.arm(side+2,progress,slim,mirror));
                    var lowerStart=new Vector3f().mulPosition(GrenadeThrowPose.arm(side,progress,slim,mirror));
                    assertTrue(upperEnd.distance(lowerStart)<1e-5f,"Elbow gap at "+frame);
                }
                int throwingSide=mirror?0:1;
                var wrist=new Vector3f(0,-.5f,0).mulPosition(GrenadeThrowPose.arm(throwingSide,progress,slim,mirror));
                var propCenter=new Vector3f().mulPosition(GrenadeThrowPose.prop(progress,mirror));
                assertTrue(wrist.distance(propCenter)<1e-5f,"Prop misses wrist at "+frame);
                assertTrue(Float.isFinite(wrist.x+wrist.y+wrist.z));
                assertTrue(wrist.z<-.2f,"Throw must remain in front of the camera");
            }
        }
    }
}
