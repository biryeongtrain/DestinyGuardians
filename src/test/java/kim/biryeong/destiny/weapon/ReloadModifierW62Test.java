package kim.biryeong.destiny.weapon;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class ReloadModifierW62Test {
    private static WeaponProfile profile(boolean shell) {
        return new WeaponProfile(WeaponProfile.Mode.HITSCAN,3,10,10,20,40,48,0,1,1,0,0,0,0,false,false,
                10,0,false,shell,40,shell?1:0);
    }
    @Test void capturedWholeMagazineTimingChangesOnlyDeadlineAndStillPaysExactFiniteReserve() {
        var p=profile(false);var c=new WeaponCycle();var ammo=new WeaponMagazine(p,1,5);long total=ammo.total();
        assertTrue(c.startReload(100,p,ammo,new WeaponReloadPolicy.Plan(12,12,0)));
        assertEquals(12,c.reloadPhaseTicks());assertFalse(c.finishReload(111,ammo));
        assertEquals(1,ammo.rounds());assertEquals(5,ammo.reserve());assertTrue(c.finishReload(112,ammo));
        assertFalse(c.reloading());assertEquals(6,ammo.rounds());assertEquals(0,ammo.reserve());assertEquals(total,ammo.total());
        assertFalse(c.finishReload(112,ammo));
    }
    @Test void laterPlanCannotRetargetRunningAnimationOrChangeItsCompletion() {
        var p=profile(false);var c=new WeaponCycle();var ammo=new WeaponMagazine(p,1,20);
        assertTrue(c.startReload(10,p,ammo,new WeaponReloadPolicy.Plan(12,12,0)));
        assertFalse(c.startReload(15,p,ammo,new WeaponReloadPolicy.Plan(40,40,0)));
        assertEquals(12,c.reloadPhaseTicks());assertEquals(7,c.reloadRemaining(15));assertTrue(c.finishReload(22,ammo));
        assertTrue(ammo.consume());assertTrue(c.startReload(23,p,ammo));
        assertFalse(c.finishReload(62,ammo));assertTrue(c.finishReload(63,ammo));
    }
    @Test void acceleratedShellSnapshotUsesExactFirstAndFollowingDeadlinesWithoutCatchUpOrExtraCost() {
        var p=profile(true);var c=new WeaponCycle();var ammo=new WeaponMagazine(p,0,3);
        assertTrue(c.startReload(0,p,ammo,new WeaponReloadPolicy.Plan(9,6,1)));
        assertFalse(c.finishReload(8,ammo));assertTrue(c.finishReload(9,ammo));assertEquals(1,ammo.rounds());
        assertEquals(6,c.reloadPhaseTicks());assertFalse(c.finishReload(14,ammo));assertTrue(c.finishReload(15,ammo));
        assertEquals(2,ammo.rounds());assertEquals(1,ammo.reserve());
        assertTrue(c.finishReload(1000,ammo));assertEquals(3,ammo.rounds());assertFalse(c.reloading());assertEquals(0,ammo.reserve());
    }
    @Test void modifierCannotChangeGranularityBypassBurstOrResetTheFiringDeadline() {
        var p=profile(false);var c=new WeaponCycle();var ammo=new WeaponMagazine(p,1,20);
        assertThrows(IllegalArgumentException.class,()->c.startReload(0,p,ammo,new WeaponReloadPolicy.Plan(3,3,1)));
        assertTrue(c.fire(0,p,ammo));assertTrue(c.startReload(1,p,ammo,new WeaponReloadPolicy.Plan(2,2,0)));
        assertTrue(c.finishReload(3,ammo));assertFalse(c.fire(3,p,ammo));assertFalse(c.fire(9,p,ammo));assertTrue(c.fire(10,p,ammo));
        assertThrows(IllegalArgumentException.class,()->new WeaponReloadPolicy.Plan(0,2,0));
        var shell=profile(true);assertThrows(IllegalArgumentException.class,()->new WeaponCycle().startReload(0,shell,new WeaponMagazine(shell,0,2),new WeaponReloadPolicy.Plan(2,2,2)));
    }
}
