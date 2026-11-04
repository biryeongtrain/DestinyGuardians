package kim.biryeong.destiny.weapon;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class WeaponAmmoStateTest {
    private WeaponAmmoState state(int rounds, int remaining) {
        return new WeaponAmmoState("hand_cannon", rounds, 70, 10, remaining, 36, false);
    }
    @Test void reloadProgressUsesActualRemainingTicksWithoutChangingAmmo() {
        var s = state(2,18);
        assertTrue(s.reloading()); assertEquals(.5f,s.reloadProgress()); assertEquals(2,s.rounds());
        assertEquals(0,state(2,36).reloadProgress());
        assertFalse(state(2,0).reloading()); assertEquals(0,state(2,0).reloadProgress());
    }
    @Test void lowAmmoIncludesZeroAndBoundaryNotHealthyMagazine() {
        assertTrue(state(0,0).low()); assertTrue(state(2,0).low()); assertFalse(state(3,0).low());
        assertTrue(new WeaponAmmoState("sniper_rifle",1,20,4,0,48,false).low());
    }
    @Test void rejectsImpossibleSnapshots() {
        assertThrows(IllegalArgumentException.class,()->state(-1,0));
        assertThrows(IllegalArgumentException.class,()->state(11,0));
        assertThrows(IllegalArgumentException.class,()->state(1,37));
        assertThrows(IllegalArgumentException.class,()->new WeaponAmmoState("x",0,-1,10,0,1,false));
        assertThrows(IllegalArgumentException.class,()->new WeaponAmmoState(null,0,0,1,0,1,false));
    }
}
