package kim.biryeong.destiny.weapon;

import org.junit.jupiter.api.Test;
import java.util.ArrayList;
import static org.junit.jupiter.api.Assertions.*;

class WeaponCycleW46Test {
    private static WeaponProfile profile(double cadence, int burst, double spacing, boolean shared, boolean shell) {
        return new WeaponProfile(WeaponProfile.Mode.HITSCAN, 1, (int)Math.ceil(cadence), 100, 100,
                10, 48, 0, burst, 1, 0, 0, 0, 0, true, false,cadence,spacing,shared,shell);
    }
    @Test void fractional900RpmDoesNotFallBackTo600AndDuplicateCallsCannotIncreaseIt() {
        var p=profile(4.0/3,1,1,false,false);var c=new WeaponCycle();var a=new WeaponMagazine(p,100,0);
        var times=new ArrayList<Integer>();
        for(int t=0;t<40;t++) {
            if(c.fire(t,p,a))times.add(t);
            for(int duplicate=0;duplicate<20;duplicate++)assertFalse(c.fire(t,p,a));
        }
        assertEquals(30,times.size());assertEquals(70,a.rounds());
        assertTrue(times.contains(2)&&times.contains(3)&&times.contains(4),times.toString());
    }
    @Test void twelveHundredRpmFitsOneRoundPerTickWithoutPacketRateDependence() {
        var p=profile(1,1,1,false,false);var c=new WeaponCycle();var a=new WeaponMagazine(p,100,0);
        for(int t=100;t<120;t++){assertTrue(c.fire(t,p,a));assertFalse(c.fire(t,p,a));}
        assertEquals(80,a.rounds());
    }
    @Test void idleAndLagNeverAccumulateAFreeCatchUpBurstAndSwapKeepsDeadline() {
        var p=profile(4.0/3,1,1,false,false);var c=new WeaponCycle();var a=new WeaponMagazine(p,100,0);
        assertTrue(c.fire(0,p,a));assertTrue(c.fire(100,p,a));
        c.cancelPending();assertFalse(c.fire(100,p,a));assertFalse(c.fire(101,p,a));
        assertTrue(c.fire(102,p,a));assertEquals(97,a.rounds());
    }
    @Test void sharedBurstUsesOneRoundEvenForTheLastMagazineUnitAndCancellationNeverRefundsIt() {
        var p=profile(12,3,10.0/3,true,false);var c=new WeaponCycle();var a=new WeaponMagazine(p,1,0);
        assertTrue(c.fire(0,p,a));assertEquals(0,a.rounds());
        assertFalse(c.burst(3,a));assertTrue(c.burst(4,a));assertEquals(1,c.burstIndex());
        assertTrue(c.burst(7,a));assertEquals(2,c.burstIndex());assertFalse(c.burst(8,a));
        assertEquals(0,a.rounds());
        a=new WeaponMagazine(p,2,0);assertTrue(c.fire(20,p,a));c.cancelPending();
        assertFalse(c.burst(100,a));assertEquals(1,a.rounds());assertFalse(c.fire(21,p,a));
    }
    @Test void perBulletPulseStopsAtLastRoundAndCannotReloadMidBurst() {
        var p=profile(10,4,4.0/3,false,false);var c=new WeaponCycle();var a=new WeaponMagazine(p,2,5);
        assertTrue(c.fire(0,p,a));assertFalse(c.startReload(1,p,a));
        assertTrue(c.burst(2,a));assertEquals(0,a.rounds());assertFalse(c.burst(3,a));
    }
    @Test void subTickFusionBoltsDrainInBoundedTickGroupsWithoutSpendingMoreAmmo() {
        var p=profile(16,9,2.0/3,true,false);var c=new WeaponCycle();var a=new WeaponMagazine(p,2,0);
        assertTrue(c.fire(0,p,a));int bolts=1,maxDue=0;
        for(int t=0;t<=6;t++){
            int due=0;while(due<9&&c.burst(t,a)){due++;bolts++;}
            maxDue=Math.max(maxDue,due);
        }
        assertEquals(9,bolts);assertEquals(2,maxDue);assertEquals(1,a.rounds());
    }
    @Test void shellReloadPersistsEachInsertAndNewShotInterruptsWithoutCreatingOrLosingReserve() {
        var p=profile(10,1,1,false,true);var c=new WeaponCycle();var a=new WeaponMagazine(p,0,3);
        assertTrue(c.startReload(0,p,a));assertFalse(c.interruptReloadForShot(1,a));
        assertFalse(c.finishReload(9,a));assertTrue(c.finishReload(10,a));
        assertEquals(1,a.rounds());assertEquals(2,a.reserve());assertTrue(c.reloading());
        assertEquals(10,c.reloadRemaining(10));assertTrue(c.interruptReloadForShot(11,a));
        assertTrue(c.fire(11,p,a));assertEquals(0,a.rounds());assertEquals(2,a.reserve());
        assertFalse(c.finishReload(999,a));
        assertTrue(c.startReload(1000,p,a));assertTrue(c.finishReload(1010,a));
        assertTrue(c.finishReload(1020,a));assertFalse(c.reloading());assertEquals(2,a.rounds());assertEquals(0,a.reserve());
    }
    @Test void cancelledInsertNeverTransfersLaterAndClockJumpTransfersOnlyOneShell() {
        var p=profile(10,1,1,false,true);var c=new WeaponCycle();var a=new WeaponMagazine(p,0,3);
        assertTrue(c.startReload(0,p,a));assertTrue(c.finishReload(100,a));
        assertEquals(1,a.rounds());assertEquals(2,a.reserve());assertEquals(10,c.reloadRemaining(100));
        c.cancelPending();assertFalse(c.finishReload(10000,a));assertEquals(1,a.rounds());assertEquals(2,a.reserve());
    }
    @Test void unsafeFractionalTimingIsRejected() {
        assertThrows(IllegalArgumentException.class,()->profile(Double.NaN,1,1,false,false));
        assertThrows(IllegalArgumentException.class,()->profile(.5,1,1,false,false));
        assertThrows(IllegalArgumentException.class,()->profile(10,9,3,true,false));
        assertThrows(IllegalArgumentException.class,()->profile(10,2,-1,true,false));
    }
}
