package kim.biryeong.destiny.weapon;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class WeaponBowDrawW49Test {
    private static WeaponProfile bow() { return WeaponProfile.forEntry(WeaponCatalog.find("biting_winds").orElseThrow()); }
    @Test void fullDrawPreservesExactExistingProfileAndOverdrawDoesNotInventExtraDamage() {
        var p=bow();assertSame(p,WeaponBowDraw.shot(p,p.chargeTicks()));
        assertSame(p,WeaponBowDraw.shot(p,Long.MAX_VALUE));
    }
    @Test void authoredEarlyDrawIsMonotonicallyWeakerSlowerAndMoreCurved() {
        var p=bow();double damage=0,speed=0,gravity=Double.MAX_VALUE;
        for(int t=0;t<=p.chargeTicks();t++) {
            var s=WeaponBowDraw.shot(p,t);
            assertTrue(s.damage()>damage&&s.damage()<=p.damage());
            assertTrue(s.speed()>speed&&s.speed()<=p.speed());
            assertTrue(s.gravity()<gravity&&s.gravity()>=p.gravity());
            damage=s.damage();speed=s.speed();gravity=s.gravity();
        }
        assertEquals(.35*p.damage(),WeaponBowDraw.shot(p,0).damage(),1e-5);
        assertEquals(.25*p.speed(),WeaponBowDraw.shot(p,0).speed(),1e-10);
    }
    @Test void partialDrawCannotChangeMagazineReserveTimingInputOrReloadPolicy() {
        var p=bow();var s=WeaponBowDraw.shot(p,1);
        assertEquals(p.magazine(),s.magazine());assertEquals(p.reserve(),s.reserve());
        assertEquals(p.infiniteReserve(),s.infiniteReserve());assertEquals(p.chargeTicks(),s.chargeTicks());
        assertEquals(p.cadenceTicks(),s.cadenceTicks());assertEquals(p.burst(),s.burst());
        assertEquals(p.firstReloadTicks(),s.firstReloadTicks());assertEquals(p.reloadTicks(),s.reloadTicks());
        assertEquals(p.roundsPerInsert(),s.roundsPerInsert());assertEquals(p.shellReload(),s.shellReload());
        assertEquals(p.automatic(),s.automatic());assertEquals(p.sharedBurstAmmo(),s.sharedBurstAmmo());
        assertEquals(p.range(),s.range());assertEquals(p.blastRadius(),s.blastRadius());
    }
    @Test void cancelledOrUnstartedDrawCannotBeTurnedIntoAnArrow() {
        assertThrows(IllegalArgumentException.class,()->WeaponBowDraw.shot(bow(),-1));
        var p=WeaponProfile.forEntry(WeaponCatalog.find("austringer").orElseThrow());
        assertThrows(IllegalArgumentException.class,()->WeaponBowDraw.shot(p,1));
        var c=new WeaponCycle();assertEquals(-1,c.chargeElapsed(100));
        assertTrue(c.startCharge(100));assertEquals(0,c.chargeElapsed(100));assertEquals(3,c.chargeElapsed(103));
        c.cancelCharge();assertEquals(-1,c.chargeElapsed(1000));
    }
    @Test void nockingHasNoChargeAndBufferedDrawOnlyStartsWhenNockActuallyFinishes() {
        var p=bow();var c=new WeaponCycle();var ammo=new WeaponMagazine(p,0,0);
        assertTrue(c.startReload(100,p,ammo));assertEquals(-1,c.chargeElapsed(105));
        assertFalse(c.startCharge(105));assertFalse(c.finishReload(100+p.firstReloadTicks()-1,ammo));
        int at=100+p.firstReloadTicks();assertTrue(c.finishReload(at,ammo));assertEquals(1,ammo.rounds());
        assertTrue(c.startCharge(at));assertEquals(0,c.chargeElapsed(at));
        var partial=WeaponBowDraw.shot(p,c.chargeElapsed(at+1));
        assertTrue(partial.damage()<p.damage());assertTrue(partial.speed()<p.speed());
    }
    @Test void sharedBurstKeepsReloadClosedUntilEveryAlreadyPaidBoltIsDrained() {
        var p=WeaponProfile.forEntry(WeaponCatalog.find("stormchaser").orElseThrow());
        var c=new WeaponCycle();var ammo=new WeaponMagazine(p,1,2);
        assertTrue(c.fire(100,p,ammo));assertTrue(c.bursting());assertEquals(0,ammo.rounds());
        assertFalse(c.startReload(100,p,ammo));
        while(c.burst(1000,ammo)) { }
        assertFalse(c.bursting());assertEquals(0,ammo.rounds());assertEquals(2,ammo.reserve());
        assertTrue(c.startReload(1000,p,ammo));assertFalse(c.finishReload(1000+p.firstReloadTicks()-1,ammo));
    }
}
