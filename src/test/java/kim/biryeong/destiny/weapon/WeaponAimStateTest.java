package kim.biryeong.destiny.weapon;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class WeaponAimStateTest {
    @Test void transitionIsTimedReversibleAndDuplicateTicksDoNotAdvance() {
        var s=new WeaponAimState();
        s.tick(1,true,5,.04f);s.tick(1,true,5,.04f);assertEquals(.2,s.progress(),.0001);
        for(int i=2;i<=5;i++)s.tick(i,true,5,.04f);
        assertEquals(1,s.progress());s.tick(6,false,5,.04f);assertEquals(.8,s.progress(),.0001);
        for(int i=7;i<20;i++)s.tick(i,false,5,.04f);assertEquals(0,s.progress());
    }
    @Test void bloomBoundsRecoversAndResetDoesNotMoveCamera() {
        var s=new WeaponAimState();
        for(int i=0;i<100;i++)s.shot(.2f);assertEquals(1,s.bloom());assertEquals(100,s.shots());
        s.shot(Float.NaN);assertEquals(1,s.bloom());
        for(int i=0;i<30;i++)s.tick(i,false,5,.04f);assertEquals(0,s.bloom());
        s.reset();assertEquals(0,s.shots());
    }
    @Test void zoomUsesPerspectiveGeometryNotFovDivision() {
        assertEquals(70,WeaponAimState.zoomFov(70,1),.001);
        assertEquals(38.5907,WeaponAimState.zoomFov(70,2),.001);
        assertTrue(WeaponAimState.zoomFov(70,4.5f)<20);
        assertThrows(IllegalArgumentException.class,()->WeaponAimState.zoomFov(70,Float.NaN));
    }
    @Test void sustainedFireBuildsBloomBeforeDelayedRecovery() {
        var s=new WeaponAimState();s.tick(0,false,5,.04f);s.shot(.1f);
        for(int i=1;i<=3;i++)s.tick(i,false,5,.04f);
        assertEquals(.1,s.bloom(),.0001);s.shot(.1f);
        assertEquals(.2,s.bloom(),.0001);
        for(int i=4;i<=6;i++)s.tick(i,false,5,.04f);assertEquals(.2,s.bloom(),.0001);
        s.tick(7,false,5,.04f);assertEquals(.16,s.bloom(),.0001);
    }
}
