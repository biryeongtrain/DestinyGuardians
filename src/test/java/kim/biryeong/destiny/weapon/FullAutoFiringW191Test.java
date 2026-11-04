package kim.biryeong.destiny.weapon;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

/** Accepted-shot timing/finite ammunition behavior, rather than a numeric-stat test. */
class FullAutoFiringW191Test {
    private static WeaponCatalog.Entry shotgun(){return WeaponCatalog.find("dust_rock_blues").orElseThrow();}
    @Test void discountedNewTriggerCannotRetimingAlreadyPaidShotOrSpendOnRejection(){
        var e=shotgun();var base=WeaponProfile.forEntry(e);var selected=FullAutoProfile.firingProfile(e,base);
        var cycle=new WeaponCycle();var ammo=new WeaponMagazine(base,2,0);
        assertTrue(cycle.fire(0,base,ammo));
        double accepted=cycle.firingDeadline();
        int beforeOriginal=(int)Math.ceil(accepted)-1;
        assertFalse(cycle.fire(beforeOriginal,selected,ammo));
        assertEquals(accepted,cycle.firingDeadline());assertEquals(1,ammo.rounds());
        assertTrue(cycle.fire((int)Math.ceil(accepted),selected,ammo));
        assertEquals(0,ammo.rounds());
        double paid=cycle.firingDeadline();
        assertFalse(cycle.fire(1000,selected,ammo));assertEquals(paid,cycle.firingDeadline());
        assertEquals(base,WeaponProfile.forEntry(e));
    }
    @Test void heldRepeatsPayOneFiniteShellPerAcceptedShotAndDuplicatePacketsCannotIncreaseIt(){
        var e=shotgun();var base=WeaponProfile.forEntry(e);var p=FullAutoProfile.firingProfile(e,base);
        var cycle=new WeaponCycle();var ammo=new WeaponMagazine(base,3,0);int accepted=0;
        for(int t=0;t<200;t++){
            if(cycle.fire(t,p,ammo))accepted++;
            for(int packet=0;packet<5;packet++)assertFalse(cycle.fire(t,p,ammo));
        }
        assertEquals(3,accepted);assertEquals(0,ammo.total());
        assertFalse(base.automatic());assertTrue(WeaponAutoFirePolicy.supportsAutomatic(e,true));
        assertFalse(WeaponAutoFirePolicy.supportsAutomatic(e,false));
    }
}
