package kim.biryeong.destiny.weapon;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

/** Timer-only intrinsic recovery must not accidentally also refill an ordinary magazine. */
class IntrinsicReloadW84Test {
    private static WeaponProfile profile() {
        return WeaponProfile.forEntry(WeaponCatalog.find("beloved").orElseThrow());
    }
    @Test void fullMagazineCanRecoverWithoutAnySecondAmmoCredit() {
        var p=profile();var ammo=new WeaponMagazine(p,p.magazine(),p.reserve());
        var c=new WeaponCycle();long total=ammo.total();
        assertTrue(c.startExternalReload(10,60));assertFalse(c.ready(10));
        assertFalse(c.startExternalReload(11,60));assertEquals(60,c.reloadPhaseTicks());
        assertFalse(c.finishReload(69,ammo));assertTrue(c.reloading());
        assertFalse(c.finishReload(70,ammo));assertFalse(c.reloading());
        assertEquals(total,ammo.total());assertEquals(p.magazine(),ammo.rounds());
        assertTrue(c.ready(70));assertFalse(c.finishReload(71,ammo));
    }
    @Test void externalRecoveryNeverRefillsAnEmptyMagazineEvenWithPickups() {
        var p=profile();var ammo=new WeaponMagazine(p,0,1);var c=new WeaponCycle();
        assertTrue(c.startExternalReload(0,60));assertTrue(ammo.addReserve(1)>0);
        assertFalse(c.finishReload(60,ammo));assertEquals(0,ammo.rounds());assertEquals(2,ammo.total());
    }
    @Test void cancellationCannotCreditADeferredOrdinaryTransfer() {
        var p=profile();var ammo=new WeaponMagazine(p,1,p.reserve());var c=new WeaponCycle();
        assertTrue(c.startExternalReload(0,60));c.cancelPending();
        assertFalse(c.finishReload(100,ammo));assertEquals(1,ammo.rounds());
        assertTrue(c.startReload(101,p,ammo));assertTrue(c.finishReload(101+p.reloadTicks(),ammo));
        assertEquals(p.magazine(),ammo.rounds());
    }
    @Test void unsafeDeadlinesFailClosedAndFiringCadenceStillSurvivesCancellation() {
        var p=profile();var ammo=new WeaponMagazine(p,p.magazine(),0);var c=new WeaponCycle();
        assertThrows(IllegalArgumentException.class,()->c.startExternalReload(-1,1));
        assertThrows(IllegalArgumentException.class,()->c.startExternalReload(0,0));
        assertThrows(IllegalArgumentException.class,()->c.startExternalReload(0,1201));
        assertThrows(IllegalArgumentException.class,()->c.startExternalReload(Long.MAX_VALUE,1));
        assertTrue(c.fire(0,p,ammo));double deadline=c.firingDeadline();
        assertTrue(c.startExternalReload(0,1));c.cancelPending();
        assertEquals(deadline,c.firingDeadline());assertFalse(c.ready(0));
    }
}
