package kim.biryeong.destiny.weapon;

import org.junit.jupiter.api.Test;
import java.util.Map;
import static org.junit.jupiter.api.Assertions.*;

/** Historical endpoints are distinct from the explicitly authored Minecraft interpolation/angle. */
class WeaponFlinchStateTest {
    // Frozen pre-W327 roster assertions retain their original counts; new identities have separate coverage.
    private static final float EPS = 1e-6f;

    @Test void twentyElapsedAdsTicksNotTwentyReadsEarnTheBaseTrait() {
        var s = new WeaponFlinchState();
        assertEquals(20, WeaponFlinchState.PROC_TICKS);
        assertEquals(.35f, WeaponFlinchState.NO_DISTRACTIONS_RESISTANCE);
        s.tick(100, true);
        for (int i = 0; i < 100; i++) { s.tick(100, true); assertFalse(s.active()); }
        s.tick(119, true); assertFalse(s.active()); s.tick(120, true); assertTrue(s.active());
        s.tick(121, true); assertTrue(s.active());
    }
    @Test void paidPreProcShotRequiresFreshQuietIntervalButEarnedFiringRetainsBuff() {
        var s = new WeaponFlinchState(); s.tick(0, true); s.tick(10, true); s.shot(10);
        s.tick(29, true); assertFalse(s.active()); s.tick(30, true); assertTrue(s.active());
        s.shot(30); s.shot(31); s.tick(31, true); assertTrue(s.active());
        s.tick(31, false); assertFalse(s.active());
    }
    @Test void thresholdEvaluatedBeforeShotAndSameTickAdsReleaseCannotBeHidden() {
        var s = new WeaponFlinchState(); s.tick(50, true); s.tick(70, true); s.shot(70); assertTrue(s.active());
        s.tick(70, false); s.tick(70, true); assertFalse(s.active());
        s.tick(89, true); assertFalse(s.active()); s.tick(90, true); assertTrue(s.active());
    }
    @Test void resetBackwardClockAndHipShotsCannotInheritOldWindup() {
        var s = new WeaponFlinchState(); s.shot(0); s.tick(100, false); s.tick(200, true);
        s.tick(220, true); assertTrue(s.active()); s.tick(10, true); assertFalse(s.active());
        s.tick(29, true); assertFalse(s.active()); s.tick(30, true); assertTrue(s.active());
        s.reset(); s.reset(); assertFalse(s.active()); s.shot(1000); s.tick(1000, true); assertFalse(s.active());
    }
    @Test void authoredAngleUsesActualLossAdsAndLocalStabilityInterpolationExactly() {
        // At stability56 and sniper endpoint .10: local resistance .045, not a sourced exact D2 stat conversion.
        float local = (.20f + 1.80f * .4f) * 1.35f;
        assertEquals(local * .955f, WeaponFlinchState.magnitude(4, 20, 56, .10f, 1, false), EPS);
        assertEquals(local * .955f * .65f, WeaponFlinchState.magnitude(4, 20, 56, .10f, 1, true), EPS);
        assertEquals(.92f, WeaponFlinchState.magnitude(4, 20, 20, .25f, 0, false), EPS);
        assertEquals(.92f * 1.0625f, WeaponFlinchState.magnitude(4, 20, 0, .25f, 0, false), EPS);
    }
    @Test void noDistractionsMultipliesRemainingFlinchRatherThanAddingResistance() {
        for (float endpoint : new float[]{.10f,.15f,.20f,.25f}) for (float stability : new float[]{0,20,56,100}) {
            float plain = WeaponFlinchState.magnitude(4,20,stability,endpoint,1,false);
            float buff = WeaponFlinchState.magnitude(4,20,stability,endpoint,1,true);
            assertEquals(plain * .65f, buff, EPS); assertTrue(buff > 0 && buff < plain);
        }
    }
    @Test void nonfiniteOrNonpositiveDamageInputsFailClosedAndFiniteInputsStayBounded() {
        for (float bad : new float[]{Float.NaN,Float.POSITIVE_INFINITY,Float.NEGATIVE_INFINITY}) {
            assertEquals(0,WeaponFlinchState.magnitude(bad,20,56,.1f,1,false));
            assertEquals(0,WeaponFlinchState.magnitude(4,bad,56,.1f,1,false));
            assertEquals(0,WeaponFlinchState.magnitude(4,20,bad,.1f,1,false));
            assertEquals(0,WeaponFlinchState.magnitude(4,20,56,bad,1,false));
            assertEquals(0,WeaponFlinchState.magnitude(4,20,56,.1f,bad,false));
        }
        for (float n : new float[]{-1,0}) {
            assertEquals(0,WeaponFlinchState.magnitude(n,20,56,.1f,1,false));
            assertEquals(0,WeaponFlinchState.magnitude(4,n,56,.1f,1,false));
        }
        for (float loss : new float[]{Float.MIN_VALUE,1,20,Float.MAX_VALUE})
            for (float stability : new float[]{-100,0,20,100,1000}) for (float ads : new float[]{-10,0,1,10}) {
                float n=WeaponFlinchState.magnitude(loss,20,stability,.25f,ads,false);
                assertTrue(Float.isFinite(n) && n >= 0 && n <= 3.375f);
            }
        assertEquals(WeaponFlinchState.magnitude(20,20,100,1,1,false),
                WeaponFlinchState.magnitude(Float.MAX_VALUE,20,100,2,2,false));
    }
    @Test void historicalFamilyEndpointsCoverAllRangedWeaponsWithoutInventingGlaiveOrSwordRows() {
        var expected=Map.ofEntries(
                Map.entry("auto_rifle",.25f),Map.entry("submachine_gun",.25f),Map.entry("bow",.25f),
                Map.entry("pulse_rifle",.20f),Map.entry("scout_rifle",.20f),Map.entry("sidearm",.20f),Map.entry("machine_gun",.20f),
                Map.entry("hand_cannon",.15f),Map.entry("trace_rifle",.15f),Map.entry("fusion_rifle",.10f),
                Map.entry("shotgun",.10f),Map.entry("sniper_rifle",.10f),Map.entry("grenade_launcher",.10f),
                Map.entry("heavy_grenade_launcher",.10f),Map.entry("linear_fusion_rifle",.10f),Map.entry("rocket_launcher",.10f));
        int ranged=0,excluded=0;
        for(var e:WeaponCatalog.all().stream().filter(e -> !LegendaryWeapons.contains(e.id()) && !WeaponExotics.expanded(e)).toList()) {
            float endpoint=expected.getOrDefault(e.family(),0f);
            assertEquals(endpoint,WeaponFlinchProfile.maxResistance(e),e.id());
            if(WeaponAimProfile.supports(e)) {assertTrue(endpoint>0,e.id());ranged++;}
            else {assertEquals(0,endpoint,e.id());excluded++;}
        }
        assertEquals(65,WeaponCatalog.all().stream().filter(e -> !LegendaryWeapons.contains(e.id()) && !WeaponExotics.expanded(e)).toList().size()); assertEquals(59,ranged); assertEquals(6,excluded);
        assertEquals(0,WeaponFlinchProfile.maxResistance(null));
        var source=WeaponCatalog.find("izanagis_burden").orElseThrow();
        var unknown=new WeaponCatalog.Entry("w85_unknown","w85_unknown","unknown",source.name(),source.source_frame_label(),source.item_model());
        assertEquals(0,WeaponFlinchProfile.maxResistance(unknown));
    }
    @Test void effectiveMeasurementCountsHpAndAbsorptionButRejectsNoLossOrHealing() {
        var m=new WeaponDamageMeasurement();
        m.begin(24); assertEquals(4,m.finish(20)); // shield-only loss and HP loss share the same total contract
        m.begin(20); assertEquals(4,m.finish(16));
        m.begin(20); assertEquals(0,m.finish(20));
        m.begin(16); assertEquals(0,m.finish(20));
    }
    @Test void nestedLossIsAttributedOnceToItsExclusiveOwner() {
        var m=new WeaponDamageMeasurement();
        m.begin(30); m.begin(28); assertEquals(5,m.finish(23)); assertEquals(5,m.finish(20));
        m.begin(20); m.begin(20); assertEquals(4,m.finish(16)); assertEquals(0,m.finish(16));
    }
    @Test void nestedHealingRetainsSignedChildDeltaAndThreeLevelsConserveLoss() {
        var m=new WeaponDamageMeasurement();
        m.begin(20); m.begin(15); assertEquals(0,m.finish(18)); assertEquals(7,m.finish(16));
        m.begin(30); m.begin(28); m.begin(25);
        assertEquals(2,m.finish(23)); assertEquals(4,m.finish(22)); assertEquals(4,m.finish(20));
    }
    @Test void independentMeasurementStacksAndNonfiniteFramesCannotLeakIntoNextHit() {
        var a=new WeaponDamageMeasurement(); var b=new WeaponDamageMeasurement();
        a.begin(20); b.begin(40); assertEquals(3,b.finish(37)); assertEquals(2,a.finish(18));
        for(float n:new float[]{Float.NaN,Float.POSITIVE_INFINITY,Float.NEGATIVE_INFINITY}) {
            a.begin(n); assertEquals(0,a.finish(10)); a.begin(20); assertEquals(0,a.finish(n));
            a.begin(20); assertEquals(1,a.finish(19));
        }
    }
}
