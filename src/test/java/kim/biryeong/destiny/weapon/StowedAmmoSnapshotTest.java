package kim.biryeong.destiny.weapon;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class StowedAmmoSnapshotTest {
    private WeaponProfile profile(boolean infinite) {
        return new WeaponProfile(WeaponProfile.Mode.HITSCAN,1,3,10,infinite?0:20,30,40,0,1,1,0,0,0,0,false,infinite);
    }
    @Test void perkLoadedMagazineAboveBaseDoesNotThrowWhenStowed() {
        var p = profile(false);
        var loaded = new WeaponMagazine(p, 25, 0, 0, 25);
        assertEquals(25, loaded.rounds());
        var state = WeaponAmmoState.stowed("hand_cannon", loaded, p.magazine(), p.reloadTicks(), false);
        assertEquals(25, state.rounds());
        assertTrue(state.capacity() >= state.rounds());
    }
    @Test void ordinaryMagazineKeepsItsBaseCapacity() {
        var p = profile(true);
        var state = WeaponAmmoState.stowed("auto_rifle", new WeaponMagazine(p, 4, 0), p.magazine(), p.reloadTicks(), true);
        assertEquals(10, state.capacity());
        assertEquals(4, state.rounds());
        assertTrue(state.infiniteReserve());
    }
}
