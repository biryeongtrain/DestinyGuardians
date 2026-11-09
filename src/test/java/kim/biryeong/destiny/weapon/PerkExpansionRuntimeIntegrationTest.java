package kim.biryeong.destiny.weapon;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

/** Real WeaponCycle/WeaponMagazine plus the same facade transfer used by runtime.
 * No ServerPlayer mock and no claim of server/client damage-event validation. */
class PerkExpansionRuntimeIntegrationTest {
    private static WeaponProfile fusion() {
        return new WeaponProfile(WeaponProfile.Mode.HITSCAN,1,20,6,30,20,40,10,7,1,0,0,0,0,
                false,false,20,1,true,false);
    }
    @Test void finalCartridgeCannotResetRewindUntilAllSevenSharedBoltsResolve() {
        var profile=fusion(); var runtime=new WeaponCycle(); var ammo=new WeaponMagazine(profile,2,10);
        var perk=new PerkExpansionCombatCycle(0);
        // First cartridge misses: it counts towards the expenditure threshold, never hit credit.
        assertTrue(runtime.fire(0,profile,ammo));
        for(int i=0;i<7;i++) {
            if(i>0)assertTrue(runtime.burst(i,ammo));
            var token=perk.paid(i,i==0,i==0,false); assertTrue(perk.resolved(token,i));
        }
        assertEquals(1,ammo.rounds());
        assertTrue(runtime.fire(20,profile,ammo));
        for(int bolt=0;bolt<7;bolt++) {
            int tick=20+bolt;
            if(bolt>0)assertTrue(runtime.burst(tick,ammo));
            var token=perk.paid(tick,bolt==0,bolt==0,false);
            assertTrue(perk.hit(token,tick,false,false,true));
            assertFalse(perk.hit(token,tick,false,false,true),"pellet duplicates cannot count twice");
            assertTrue(perk.resolved(token,tick));
            int moved=PerkExpansionCombat.transferRewind(perk,tick,6,ammo,false,runtime.bursting());
            assertEquals(bolt==6?5:0,moved,"No early generation reset may discard later bolts");
            assertEquals(bolt==6?5:0,ammo.rounds());
        }
        assertEquals(5,ammo.reserve()); assertEquals(10,ammo.total());
        assertEquals(0,PerkExpansionCombat.transferRewind(perk,26,6,ammo,false,false),"duplicate tick cannot refund twice");
    }
    @Test void completedReloadInvalidatesOldProjectileMagazineCredit() {
        var perk=new PerkExpansionCombatCycle(0); var ammo=new WeaponMagazine(fusion(),0,10);
        var old1=perk.paid(0,true,true,false); var old2=perk.paid(1,true,true,false);
        assertEquals(6,ammo.reload()); perk.resetMagazine();
        assertTrue(ammo.consume(6));
        assertTrue(perk.hit(old1,2,false,false,true)); assertTrue(perk.resolved(old1,2));
        assertTrue(perk.hit(old2,2,false,false,true)); assertTrue(perk.resolved(old2,2));
        assertEquals(0,PerkExpansionCombat.transferRewind(perk,2,6,ammo,false,false));
        assertEquals(4,ammo.total(),"old in-flight hits cannot refund a newer magazine");
    }
    @Test void duplicateRuntimeUpdatesCannotAccelerateReconstructionOrLoseFundedOverflow() {
        var p=fusion(); var cycle=new PerkExpansionCombatCycle(0); var ammo=new WeaponMagazine(p,6,10);
        assertEquals(0,cycle.reconstruction(119,6,ammo.rounds(),false));
        assertEquals(2,PerkExpansionCombatCycle.fund(ammo,6,cycle.reconstruction(120,6,ammo.rounds(),false)));
        assertEquals(0,PerkExpansionCombatCycle.fund(ammo,6,cycle.reconstruction(120,6,ammo.rounds(),false)));
        var restored=new WeaponMagazine(p,ammo.rounds(),ammo.reserve(),ammo.overflow(),ammo.loadedLimit());
        assertEquals(8,restored.rounds()); assertEquals(16,restored.total());
        assertEquals(0,restored.reload(),"ordinary reload never grows an overflow magazine");
        assertEquals(0,cycle.reconstruction(240,6,restored.rounds(),true),"active reload blocks reconstruction");
        assertEquals(2,PerkExpansionCombatCycle.fund(restored,6,cycle.reconstruction(240,6,restored.rounds(),false)));
        assertEquals(16,restored.total());
    }
    @Test void dualLoaderUsesActualCycleInsertsAndCancellationNeverSpendsFutureShells() {
        var base=new WeaponProfile(WeaponProfile.Mode.HITSCAN,1,10,6,20,10,20,0,1,1,0,0,0,0,
                false,false,10,0,false,true);
        var plan=PerkExpansionCombat.dualLoader(new WeaponReloadPolicy.Plan(10,10,1));
        var profile=PerkExpansionCombat.reloadProfile(base,plan); var ammo=new WeaponMagazine(profile,0,5); var runtime=new WeaponCycle();
        assertTrue(runtime.startReload(0,profile,ammo,plan,10));
        assertFalse(runtime.finishReload(9,ammo)); assertTrue(runtime.finishReload(10,ammo));
        assertEquals(2,ammo.rounds()); assertEquals(3,ammo.reserve());
        runtime.cancelPending(); assertFalse(runtime.finishReload(100,ammo));
        assertEquals(5,ammo.total()); assertEquals(2,ammo.rounds());
    }
}
