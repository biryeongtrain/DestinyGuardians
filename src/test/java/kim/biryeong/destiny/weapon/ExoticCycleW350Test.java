package kim.biryeong.destiny.weapon;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

final class ExoticCycleW350Test {
    @Test void whiteNailNeedsThreeActualPrecisionHitsAndNeverCountsRejectedDamage() {
        var chain=new ExoticCycleW350.PrecisionChain();
        assertFalse(chain.confirmed(0,true,3));
        assertFalse(chain.confirmed(1,true,0));
        assertFalse(chain.confirmed(1,true,Float.NaN));
        assertFalse(chain.confirmed(25,true,4));
        assertTrue(chain.confirmed(50,true,1));
        assertEquals(0,chain.hits());
        assertFalse(chain.confirmed(50,true,1));
    }
    @Test void bodyMissStowGapAndClockRollbackCannotJoinPrecisionChains() {
        var c=new ExoticCycleW350.PrecisionChain();
        c.confirmed(0,true,1);c.confirmed(1,true,1);
        assertFalse(c.confirmed(2,false,1));assertEquals(0,c.hits());
        c.confirmed(3,true,1);c.confirmed(4,true,1);c.clear();
        assertFalse(c.confirmed(5,true,1));
        assertFalse(c.confirmed(56,true,1));assertEquals(1,c.hits());
        assertFalse(c.confirmed(55,true,1));assertEquals(1,c.hits());
    }
    private WeaponProfile finite() {
        return new WeaponProfile(WeaponProfile.Mode.HITSCAN,16,17,3,20,48,96,0,1,1,0,0,0,0,false,false);
    }
    @Test void currentWhiteNailCreatesOneAndTransfersAtMostTwoRealReserveCartridges() {
        var ammo=new WeaponMagazine(finite(),0,2);
        assertEquals(1,ammo.generateLoaded(1));assertEquals(2,ammo.reloadRounds(2));
        assertEquals(3,ammo.rounds());assertEquals(0,ammo.reserve());assertEquals(3,ammo.total());
        var empty=new WeaponMagazine(finite(),0,0);
        empty.generateLoaded(1);empty.reloadRounds(2);
        assertEquals(1,empty.rounds());assertEquals(0,empty.reserve());
        var partial=new WeaponMagazine(finite(),2,2);
        partial.generateLoaded(1);partial.reloadRounds(2);
        assertEquals(3,partial.rounds());assertEquals(2,partial.reserve());
    }
    @Test void remnantOverflowIsGeneratedExplicitlyCappedAndConservedAcrossProjection() {
        var profile=new WeaponProfile(WeaponProfile.Mode.HITSCAN,7,9,11,0,30,40,0,1,1,0,0,0,0,false,true);
        var ammo=new WeaponMagazine(profile,11,0);
        for(int i=0;i<20;i++)ammo.generateLoadedOverflow(4,40);
        assertEquals(40,ammo.rounds());assertEquals(40,ammo.loadedLimit());
        assertEquals(0,ammo.generateLoadedOverflow(4,40));
        var restored=new WeaponMagazine(profile,ammo.rounds(),ammo.reserve(),ammo.overflow(),ammo.loadedLimit());
        assertEquals(40,restored.rounds());
        assertEquals(0,ammo.generateLoadedOverflow(4,10));
    }
    @Test void soulDevourerPickupExtendsSevenSecondsToElevenAndSurvivesAnIdleRead() {
        long first=ExoticCycleW350.extendSoul(100,0);assertEquals(240,first);
        long second=ExoticCycleW350.extendSoul(120,first);assertEquals(340,second);
        assertEquals(500,ExoticCycleW350.extendSoul(360,second));
    }
    @Test void parasitismUsesSourcedPveCurveAndCapsUnknownPvpTiersAtLastKnownPoint() {
        assertEquals(1,ExoticCycleW350.parasitism(0,false));
        assertEquals(2.5f,ExoticCycleW350.parasitism(5,false),1e-6);
        assertEquals(4,ExoticCycleW350.parasitism(100,false),1e-6);
        assertEquals(4,ExoticCycleW350.parasitism(Integer.MAX_VALUE,false),1e-6);
        assertEquals(1.75f,ExoticCycleW350.parasitism(100,true),1e-6);
    }
    @Test void rapidHitNanitesRequireTwelveDistinctConfirmedReceiptsWithinLocalWindow() {
        var c=new ExoticCycleW350.RapidHits();
        for(int i=0;i<11;i++)assertFalse(c.confirmed(i));assertTrue(c.confirmed(11));
        assertFalse(c.confirmed(12));assertFalse(c.confirmed(40));
        for(int i=1;i<11;i++)assertFalse(c.confirmed(40+i));assertTrue(c.confirmed(51));
    }
    @Test void packHunterRequiresLivingSameLevelAlliesAndLegendaryRocketIdentity() {
        assertTrue(ExoticCycleW350.packEligible(true,true,false,true,true));
        assertFalse(ExoticCycleW350.packEligible(true,true,true,true,true));
        assertFalse(ExoticCycleW350.packEligible(false,true,false,true,true));
        assertFalse(ExoticCycleW350.packEligible(true,false,false,true,true));
        assertFalse(ExoticCycleW350.packEligible(true,true,false,false,true));
        assertFalse(ExoticCycleW350.packEligible(true,true,false,true,false));
    }
    @Test void mulliganOnlyRollsOnGeometryMissesAndDoesNotGuaranteeOrDuplicateAmmo() {
        for(int roll=0;roll<100;roll++)assertFalse(ExoticCycleW350.mulligan(true,roll));
        int wins=0;for(int roll=0;roll<100;roll++)if(ExoticCycleW350.mulligan(false,roll))wins++;
        assertEquals(20,wins);
    }
    @Test void scorchNeedsOneHundredStacksThenEnforcesReapplyCooldownAndDecay() {
        var scorch=new ExoticCycleW350.Scorch();
        for(int i=0;i<9;i++)assertFalse(scorch.add(0,10));
        assertEquals(90,scorch.stacks(0));assertTrue(scorch.add(0,10));
        assertEquals(0,scorch.stacks(0));assertFalse(scorch.add(31,10));
        assertEquals(0,scorch.stacks(31));assertFalse(scorch.add(32,10));
        assertEquals(10,scorch.stacks(32));assertTrue(scorch.pulse(42));assertFalse(scorch.pulse(43));
        assertEquals(10,scorch.stacks(78));assertEquals(5,scorch.stacks(82));assertTrue(scorch.expired(86));
    }

}
