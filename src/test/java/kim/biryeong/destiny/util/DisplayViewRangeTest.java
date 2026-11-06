package kim.biryeong.destiny.util;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class DisplayViewRangeTest {
    @Test void nearViewStaysBetweenMountedEyeAndUnobstructedThirdPersonAcrossVanillaSettings() {
        for(int client : new int[]{2,8,16,32}) for(int server : new int[]{4,10,32}) {
            float range=DisplayViewRange.nearCamera(.64f,client,server);
            double vanillaChunkScale=Math.max(1,Math.min(2.5,Math.min(client,server)/8.0));
            for(double entityScale:new double[]{.5,1,2,5}) {
                double radius=64*range*vanillaChunkScale*entityScale;
                assertEquals(.64*entityScale,radius,1e-6);
                assertTrue(radius>.30,"Mounted-eye margin at minimum setting");
                assertTrue(radius<4,"Unobstructed vanilla third-person camera is outside");
            }
        }
    }
    @Test void rejectsNonFiniteOrEmptyVisibilityRadius() {
        for(float radius:new float[]{0,-1,Float.NaN,Float.POSITIVE_INFINITY})
            assertThrows(IllegalArgumentException.class,()->DisplayViewRange.nearCamera(radius,16,10));
    }
}
