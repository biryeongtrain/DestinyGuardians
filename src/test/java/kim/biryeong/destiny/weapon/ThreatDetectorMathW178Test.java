package kim.biryeong.destiny.weapon;

import org.junit.jupiter.api.Test;
import java.util.*;
import static org.junit.jupiter.api.Assertions.*;

/** Frozen raw-curve oracle values generated only after reproducing W46/W58/W44 baselines.
 * Tests execute the real production methods; they never copy a timing implementation.
 */
class ThreatDetectorMathW178Test {
    private static final List<String> TIERS=List.of(
        "seventh_seraph_officer_revolver 0 8 9 6 52",
        "seventh_seraph_officer_revolver 1 6 7 5 46",
        "seventh_seraph_officer_revolver 2 3 4 4 37",
        "cold_denial 0 10 10 9 44",
        "cold_denial 1 8 7 8 37",
        "cold_denial 2 4 4 6 27",
        "claws_of_the_wolf 0 10 10 9 47",
        "claws_of_the_wolf 1 8 7 8 40",
        "claws_of_the_wolf 2 4 4 6 28",
        "bug_out_bag 0 8 7 6 38",
        "bug_out_bag 1 6 5 5 33",
        "bug_out_bag 2 4 4 4 27",
        "dead_man_walking_xx7463 0 6 7 5 36",
        "dead_man_walking_xx7463 1 5 6 4 32",
        "dead_man_walking_xx7463 2 3 4 3 24",
        "high_albedo 0 6 7 5 36",
        "high_albedo 1 5 6 4 33",
        "high_albedo 2 3 4 3 25",
        "brass_attacks 0 7 8 6 37",
        "brass_attacks 1 5 6 5 33",
        "brass_attacks 2 3 4 3 25",
        "mindbender_s_ambition_adept 0 9 10 8 16",
        "mindbender_s_ambition_adept 1 7 7 7 14",
        "mindbender_s_ambition_adept 2 4 4 5 10",
        "dust_rock_blues 0 9 10 8 16",
        "dust_rock_blues 1 7 7 7 13",
        "dust_rock_blues 2 4 4 5 10",
        "parcel_of_stardust_fell_to_earth 0 7 7 6 14",
        "parcel_of_stardust_fell_to_earth 1 5 5 5 12",
        "parcel_of_stardust_fell_to_earth 2 4 4 5 10",
        "dream_breaker 0 10 8 8 46",
        "dream_breaker 1 8 6 7 41",
        "dream_breaker 2 6 3 5 31",
        "line_in_the_sand 0 10 8 8 49",
        "line_in_the_sand 1 8 6 7 44",
        "line_in_the_sand 2 6 3 5 33",
        "deafening_whisper 0 8 7 8 42",
        "deafening_whisper 1 6 5 7 38",
        "deafening_whisper 2 5 5 7 37",
        "edge_transit 0 9 8 9 66",
        "edge_transit 1 7 6 8 60",
        "edge_transit 2 5 5 7 49",
        "dimensional_hypotrochoid 0 9 8 9 65",
        "dimensional_hypotrochoid 1 7 6 8 59",
        "dimensional_hypotrochoid 2 5 5 7 48",
        "bellowing_giant 0 10 9 9 64",
        "bellowing_giant 1 7 6 8 59",
        "bellowing_giant 2 5 4 7 53",
        "hammerhead 0 8 8 8 91",
        "hammerhead 1 6 6 8 85",
        "hammerhead 2 5 5 7 80");
    private static final List<String> PAIRS=List.of(
        "seventh_seraph_officer_revolver feeding_frenzy 1 1 25 26 0.90000000000000002 0.97499999999999998 false 6 7 5 43",
        "seventh_seraph_officer_revolver feeding_frenzy 1 2 25 68 0.90000000000000002 0.90000000000000002 false 6 7 5 33",
        "seventh_seraph_officer_revolver feeding_frenzy 1 3 25 78 0.90000000000000002 0.87 false 6 7 5 32",
        "seventh_seraph_officer_revolver feeding_frenzy 1 4 25 93 0.90000000000000002 0.83999999999999997 false 6 7 5 31",
        "seventh_seraph_officer_revolver feeding_frenzy 1 5 25 118 0.90000000000000002 0.80000000000000004 false 6 7 5 30",
        "seventh_seraph_officer_revolver feeding_frenzy 2 1 100 68 0.81000000000000005 0.97499999999999998 false 3 4 4 36",
        "seventh_seraph_officer_revolver feeding_frenzy 2 2 100 110 0.81000000000000005 0.90000000000000002 false 3 4 4 33",
        "seventh_seraph_officer_revolver feeding_frenzy 2 3 100 120 0.81000000000000005 0.87 false 3 4 4 32",
        "seventh_seraph_officer_revolver feeding_frenzy 2 4 100 135 0.81000000000000005 0.83999999999999997 false 3 4 4 31",
        "seventh_seraph_officer_revolver feeding_frenzy 2 5 100 160 0.81000000000000005 0.80000000000000004 false 3 4 4 30",
        "high_albedo snapshot 1 1 25 18 0.90000000000000002 1 true 5 6 2 33",
        "high_albedo snapshot 2 1 100 60 0.81000000000000005 1 true 3 4 2 25",
        "brass_attacks frenzy 1 1 125 118 0.90000000000000002 1 false 3 5 3 23",
        "brass_attacks frenzy 2 1 200 160 0.81000000000000005 1 false 3 4 3 23",
        "dust_rock_blues snapshot 1 1 25 18 0.90000000000000002 1 true 7 7 6 13",
        "dust_rock_blues snapshot 2 1 100 60 0.81000000000000005 1 true 4 4 4 10",
        "parcel_of_stardust_fell_to_earth outlaw 1 1 25 88 0.90000000000000002 0.90000000000000002 false 5 5 5 9",
        "parcel_of_stardust_fell_to_earth outlaw 2 1 100 130 0.81000000000000005 0.90000000000000002 false 4 4 5 9",
        "dream_breaker frenzy 1 1 125 118 0.90000000000000002 1 false 7 3 5 30",
        "dream_breaker frenzy 2 1 200 160 0.81000000000000005 1 false 6 3 5 30");
    private static WeaponCatalog.Entry e(String id){return WeaponCatalog.find(id).orElseThrow();}
    @Test void sourcedValuesAndNoInvalidTierSaturation() {
        assertEquals(15,ThreatDetectorProfile.radius());
        for(int i=0;i<3;i++) {
            assertEquals(new int[]{0,15,40}[i],ThreatDetectorProfile.stabilityBonus(i));
            assertEquals(new int[]{0,25,100}[i],ThreatDetectorProfile.handlingBonus(i));
            assertEquals(new int[]{0,18,60}[i],ThreatDetectorProfile.reloadBonus(i));
            assertEquals(new double[]{1,.9,.81}[i],ThreatDetectorProfile.handlingScalar(i));
        }
        for(int bad:new int[]{Integer.MIN_VALUE,-1,3,Integer.MAX_VALUE}) {
            assertThrows(IllegalArgumentException.class,()->ThreatDetectorProfile.stabilityBonus(bad));
            assertThrows(IllegalArgumentException.class,()->ThreatDetectorProfile.handlingBonus(bad));
            assertThrows(IllegalArgumentException.class,()->ThreatDetectorProfile.reloadBonus(bad));
            assertThrows(IllegalArgumentException.class,()->ThreatDetectorProfile.handlingScalar(bad));
        }
    }
    @Test void finiteInclusiveThreeDimensionalFootpointRadius() {
        assertTrue(ThreatDetectorProfile.withinRadius(0,0,0));
        for(double sign:new double[]{-1,1}) {
            assertTrue(ThreatDetectorProfile.withinRadius(sign*15,0,0));
            assertTrue(ThreatDetectorProfile.withinRadius(0,sign*15,0));
            assertTrue(ThreatDetectorProfile.withinRadius(0,0,sign*15));
            assertTrue(ThreatDetectorProfile.withinRadius(sign*9,sign*12,0));
            assertFalse(ThreatDetectorProfile.withinRadius(sign*Math.nextUp(15.0),0,0));
        }
        assertFalse(ThreatDetectorProfile.withinRadius(15,0.000001,0));
        assertFalse(ThreatDetectorProfile.withinRadius(15,15,0));
        for(double bad:new double[]{Double.NaN,Double.POSITIVE_INFINITY,Double.NEGATIVE_INFINITY,Double.MAX_VALUE}) {
            assertFalse(ThreatDetectorProfile.withinRadius(bad,0,0));
            assertFalse(ThreatDetectorProfile.withinRadius(0,bad,0));
            assertFalse(ThreatDetectorProfile.withinRadius(0,0,bad));
        }
    }
    @Test void everyWeaponAndTierMatchesFrozenRawOracle() {
        assertEquals(51,TIERS.size());
        for(String row:TIERS) {
            var v=row.split(" ");var entry=e(v[0]);int tier=Integer.parseInt(v[1]);
            int h=ThreatDetectorProfile.handlingBonus(tier),r=ThreatDetectorProfile.reloadBonus(tier);
            assertEquals(Integer.parseInt(v[2]),ThreatDetectorProfile.handlingTicks(entry,h,ThreatDetectorProfile.handlingScalar(tier),true),row);
            assertEquals(Integer.parseInt(v[3]),ThreatDetectorProfile.handlingTicks(entry,h,ThreatDetectorProfile.handlingScalar(tier),false),row);
            assertEquals(Integer.parseInt(v[4]),ThreatDetectorProfile.adsTicks(entry,h,false),row);
            assertEquals(Integer.parseInt(v[5]),ThreatDetectorProfile.reloadTicks(entry,r,1),row);
        }
    }
    @Test void finiteCompanionMatrixIncludesAllFeedingTiersAndScalarProducts() {
        assertEquals(20,PAIRS.size());
        for(String row:PAIRS) {
            var v=row.split(" ");var entry=e(v[0]);
            int tier=Integer.parseInt(v[2]),companion=Integer.parseInt(v[3]);
            int h=Integer.parseInt(v[4]),r=Integer.parseInt(v[5]);
            double hs=Double.parseDouble(v[6]),rs=Double.parseDouble(v[7]);
            boolean snapshot=Boolean.parseBoolean(v[8]);
            assertEquals(Integer.parseInt(v[9]),ThreatDetectorProfile.handlingTicks(entry,h,hs,true),row);
            assertEquals(Integer.parseInt(v[10]),ThreatDetectorProfile.handlingTicks(entry,h,hs,false),row);
            assertEquals(Integer.parseInt(v[11]),ThreatDetectorProfile.adsTicks(entry,h,snapshot),row);
            assertEquals(Integer.parseInt(v[12]),ThreatDetectorProfile.reloadTicks(entry,r,rs),row);
            if(v[1].equals("feeding_frenzy")) {
                var actual=FeedingFrenzyProfile.reload(entry,companion);
                int bonus=actual.effectiveReloadStat()-actual.baseReloadStat();
                assertEquals(rs,FeedingFrenzyProfile.durationMultiplier(companion));
                assertEquals(Integer.parseInt(v[12]),ThreatDetectorProfile.reloadTicks(entry,ThreatDetectorProfile.reloadBonus(tier)+bonus,rs));
            }
            if(v[1].equals("frenzy")) {
                assertEquals(ThreatDetectorProfile.handlingBonus(tier)+FrenzyProfile.handlingBonus(),h);
                assertEquals(ThreatDetectorProfile.reloadBonus(tier)+FrenzyProfile.reloadBonus(),r);
            }
            if(v[1].equals("outlaw")) assertEquals(ThreatDetectorProfile.reloadBonus(tier)+OutlawProfile.perk().reloadBonus(),r);
        }
    }
    @Test void capsWideAdditionAndSingleRoundingAvoidRoundedBaseScaling() {
        assertEquals(100,ThreatDetectorProfile.effectiveStat(99,Integer.MAX_VALUE));
        assertEquals(0,ThreatDetectorProfile.effectiveStat(99,Integer.MIN_VALUE));
        assertEquals(100,ThreatDetectorProfile.effectiveStat(99,1));
        boolean differs=false;
        for(var roll:ThreatDetectorProfile.rolls()) {
            var entry=e(roll.id());
            assertEquals(ThreatDetectorProfile.reloadTicks(entry,100,1),ThreatDetectorProfile.reloadTicks(entry,Integer.MAX_VALUE,1));
            assertEquals(ThreatDetectorProfile.handlingTicks(entry,100,.81,true),ThreatDetectorProfile.handlingTicks(entry,Integer.MAX_VALUE,.81,true));
            assertEquals(ThreatDetectorProfile.adsTicks(entry,100,false),ThreatDetectorProfile.adsTicks(entry,Integer.MAX_VALUE,false));
            int roundedThenScaled=(int)Math.ceil(ThreatDetectorProfile.handlingTicks(entry,25,1,true)*.9);
            differs|=roundedThenScaled!=ThreatDetectorProfile.handlingTicks(entry,25,.9,true);
        }
        assertTrue(differs,"At least one real source curve detects scaling after rounding");
    }
    @Test void snapshotOnlyOnEntryAndNoThreatScalarOnAds() {
        for(String id:List.of("dust_rock_blues","high_albedo")) {
            var entry=e(id);
            assertTrue(ThreatDetectorProfile.adsTicks(entry,25,true)<ThreatDetectorProfile.adsTicks(entry,25,false));
        }
        assertThrows(IllegalArgumentException.class,()->ThreatDetectorProfile.adsTicks(e("dream_breaker"),25,true));
        // High Albedo at100 Handling: raw ADS still uses ordinary2 tick floor, Snapshot entry1.
        assertEquals(3,ThreatDetectorProfile.adsTicks(e("high_albedo"),100,false));
        assertEquals(2,ThreatDetectorProfile.adsTicks(e("high_albedo"),100,true));
    }
    @Test void scalarDomainsRejectNonfiniteAndPreserveOneTickUnderflow() {
        var entry=e("dream_breaker");
        for(double bad:new double[]{Double.NaN,Double.POSITIVE_INFINITY,Double.NEGATIVE_INFINITY,0,-1,1.0001}) {
            assertThrows(IllegalArgumentException.class,()->ThreatDetectorProfile.handlingTicks(entry,25,bad,true));
            assertThrows(IllegalArgumentException.class,()->ThreatDetectorProfile.reloadTicks(entry,18,bad));
        }
        assertEquals(1,ThreatDetectorProfile.reloadTicks(entry,60,Double.MIN_VALUE));
        assertEquals(1,ThreatDetectorProfile.handlingTicks(entry,100,Double.MIN_VALUE,false));
    }
    @Test void acceptedPlansPreserveWholeAndShellTopologyWithDistinctFirstDelay() {
        var whole=e("dream_breaker");var base=new WeaponReloadPolicy.Plan(46,46,0);
        var accepted=ThreatDetectorProfile.reloadPlan(whole,18,1,0,1,base);
        assertEquals(new WeaponReloadPolicy.Plan(ThreatDetectorProfile.reloadTicks(whole,18,1),ThreatDetectorProfile.reloadTicks(whole,18,1),0),accepted);
        var shell=e("parcel_of_stardust_fell_to_earth");var ordinary=new WeaponReloadPolicy.Plan(14,14,1);
        var plan=ThreatDetectorProfile.reloadPlan(shell,60,1,0,1,ordinary);
        assertEquals(1,plan.roundsPerInsert());assertEquals(plan.firstTicks(),plan.intervalTicks());
        // Distinct phase plan already includes Outlaw. Scale by new total/prior unrounded seconds.
        var prior=new WeaponReloadPolicy.Plan(20,13,1);
        var adjusted=ThreatDetectorProfile.reloadPlan(shell,130,.9,70,.9,prior);
        // Both sums cap100; no second Outlaw scaling and neither phase is collapsed.
        assertEquals(prior,adjusted);
        var distinct=ThreatDetectorProfile.reloadPlan(shell,18,1,0,1,new WeaponReloadPolicy.Plan(20,13,1));
        assertNotEquals(distinct.firstTicks(),distinct.intervalTicks());assertEquals(1,distinct.roundsPerInsert());
        ThreatDetectorProfile.reloadPlan(whole,60,1,0,1,base);
        assertEquals(new WeaponReloadPolicy.Plan(46,46,0),base);
        assertEquals(new WeaponReloadPolicy.Plan(ThreatDetectorProfile.reloadTicks(whole,18,1),ThreatDetectorProfile.reloadTicks(whole,18,1),0),accepted);
    }
}
