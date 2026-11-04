package kim.biryeong.destiny.weapon;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class RapidHitCycleW169Test {
    @Test void fiveConfirmedHitsCapAndRefreshWithoutReadMutation() {
        var c=new RapidHitCycle();
        for(int i=1;i<=5;i++) {
            assertTrue(c.confirmed(i*10,true,1));
            assertEquals(i,c.stacks(i*10));assertEquals(40,c.remaining(i*10));
        }
        assertEquals(5,c.stacks(89));assertEquals(1,c.remaining(89));
        assertTrue(c.confirmed(89,true,1));assertEquals(5,c.stacks(89));
        for(int i=0;i<100;i++)assertEquals(1,c.remaining(128));
        assertEquals(0,c.stacks(129));assertEquals(0,c.remaining(129));
        assertTrue(c.confirmed(129,true,1));assertEquals(1,c.stacks(129));
    }
    @Test void ordinaryBodyMissRejectedAndNonfiniteDamageNeverExtendWindow() {
        var c=new RapidHitCycle();c.confirmed(20,true,1);
        assertFalse(c.confirmed(30,false,8));
        for(float actual:new float[]{0,-1,Float.NaN,Float.POSITIVE_INFINITY,Float.NEGATIVE_INFINITY})
            assertFalse(c.confirmed(40,true,actual));
        assertEquals(1,c.stacks(59));assertEquals(1,c.remaining(59));assertEquals(0,c.stacks(60));
    }
    @Test void backwardsAndOverflowClocksFailClosedWithoutWipingActualChain() {
        var c=new RapidHitCycle();assertFalse(c.confirmed(-1,true,1));
        assertFalse(c.confirmed(Long.MAX_VALUE,true,1));assertEquals(0,c.stacks(Long.MAX_VALUE));
        c.confirmed(100,true,1);assertFalse(c.confirmed(99,true,1));assertEquals(0,c.stacks(99));
        assertEquals(1,c.stacks(100));assertEquals(40,c.remaining(100));
        c.clear();assertEquals(0,c.stacks(101));assertTrue(c.confirmed(101,true,1));assertEquals(1,c.stacks(101));
    }
    @Test void sameTickIndependentDamageTransactionsCanEachAddOneNotMoreThanFive() {
        var c=new RapidHitCycle();
        for(int i=1;i<=10;i++){c.confirmed(0,true,1);assertEquals(Math.min(5,i),c.stacks(0));}
        assertEquals(0,c.stacks(40));
    }
    @Test void stabilityUsesExistingLocalCurveAndCapsStatNotAClaimOfExactDestinyRecoil() {
        for(var e:WeaponCatalog.all()) {
            if(!WeaponAimProfile.supports(e))continue;
            var b=WeaponAimProfile.of(e);
            assertEquals(b.kick(),RapidHitStability.kick(b,0));
            assertEquals(b.bloomPerShot(),RapidHitStability.bloom(b,0));
            float kick=b.kick(),bloom=b.bloomPerShot();
            for(int bonus:new int[]{2,12,14,18,25}) {
                assertEquals(Math.min(100,b.stability()+bonus),RapidHitStability.effective(b.stability(),bonus));
                float k=RapidHitStability.kick(b,bonus),v=RapidHitStability.bloom(b,bonus);
                assertTrue(Float.isFinite(k)&&k>=.1f&&k<=kick+1e-6,e.id());
                assertTrue(Float.isFinite(v)&&v>=.02f-1e-6&&v<=bloom+1e-6,e.id());
                kick=k;bloom=v;
            }
        }
    }
    @Test void stabilityInputsAreBoundedAndBaseAimProfilesStayImmutable() {
        assertThrows(IllegalArgumentException.class,()->RapidHitStability.effective(Float.NaN,25));
        assertThrows(IllegalArgumentException.class,()->RapidHitStability.effective(101,25));
        assertThrows(IllegalArgumentException.class,()->RapidHitStability.effective(50,-1));
        var e=WeaponCatalog.find("duke_mk_44").orElseThrow();var b=WeaponAimProfile.of(e);
        RapidHitStability.kick(b,25);assertSame(b,WeaponAimProfile.of(e));
    }
    @Test void liveBowStabilityOnlyExtendsExistingInformationalWindowNotDraw() {
        for(var e:WeaponCatalog.family("bow")) {
            int base=WeaponBowWindow.windowTicks(e);
            var no=WeaponBowWindow.state(e,12,12,0);
            assertEquals(base,no.windowTicks());
            for(int bonus:new int[]{2,12,14,18,25}) {
                int stat=WeaponCharacteristics.of(e).stats().get("155624089");
                int expected=(WeaponBowWindow.windowMicros(e.frame(),Math.min(100,stat+bonus))+49_999)/50_000;
                assertEquals(WeaponBowWindow.Phase.DRAWING,WeaponBowWindow.state(e,12,11,bonus).phase());
                var boosted=WeaponBowWindow.state(e,12,12+expected-1,bonus);
                assertEquals(expected,boosted.windowTicks());assertTrue(expected>=base);
                assertEquals(WeaponBowWindow.Phase.PERFECT,boosted.phase());
                assertEquals(WeaponBowWindow.Phase.LATE,WeaponBowWindow.state(e,12,12+expected,bonus).phase());
            }
        }
    }
    @Test void onlyDistinctApostateOutlawPairAddsStatAndMultipliesScalarsBeforeSingleCeil() {
        var entry=WeaponCatalog.find("apostate").orElseThrow();
        double[] scalars={.99,.96,.95,.945,.92};int[] expected={40,38,38,38,37};
        for(int i=1;i<=5;i++){
            var plan=RapidHitProfile.reloadWithOutlaw(entry,i);
            int ticks=(int)Math.ceil((6.74498e-05*100*100-.0231542*100+3.8384)*.9*scalars[i-1]*20);
            assertEquals(expected[i-1],ticks);assertEquals(ticks,plan.firstTicks());
            assertEquals(ticks,plan.intervalTicks());assertEquals(100,plan.effectiveReloadStat());
            assertTrue(ticks<=OutlawProfile.reload(entry).firstTicks());
        }
        for(var roll:RapidHitProfile.rolls())if(!roll.id().equals("apostate"))
            assertThrows(IllegalArgumentException.class,()->RapidHitProfile.reloadWithOutlaw(WeaponCatalog.find(roll.id()).orElseThrow(),5));
    }
}
