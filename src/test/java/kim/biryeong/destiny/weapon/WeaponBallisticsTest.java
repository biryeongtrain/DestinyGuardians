package kim.biryeong.destiny.weapon;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class WeaponBallisticsTest {
    private static WeaponCatalog.Entry entry(String id) { return WeaponCatalog.find(id).orElseThrow(); }
    @Test void all63EntriesHaveValidatedProfilesAndMonotonicHipFireCurves() {
        WeaponCatalogTest.assertExpandedCatalog();
        for (var e : WeaponCatalog.all()) {
            var p = WeaponBallistics.of(e); double previous = 1;
            for (int distance = 0; distance <= 96; distance++) {
                double next = p.falloff(distance);
                assertTrue(next > 0 && next <= previous, e.id()); previous = next;
            }
        }
    }
    @Test void officialPerItemRangeStatEvaluatesPinnedCommunityCurve() {
        var p = WeaponBallistics.of(entry("austringer"));
        assertEquals(46, WeaponCharacteristics.of(entry("austringer")).stats().get("1240592695"));
        assertEquals(20.14, p.start(), 1e-8); assertEquals(30.38, p.end(), 1e-8);
        assertEquals(.33, p.floor());
    }
    @Test void curveIsContinuousLinearAndFlooredInsteadOfHardCutoff() {
        var p = new WeaponBallistics.Profile(20, 40, .4, 2);
        assertEquals(1, p.falloff(20)); assertEquals(.7, p.falloff(30), 1e-8);
        assertEquals(.4, p.falloff(40)); assertEquals(.4, p.falloff(96));
        assertEquals(14, p.damage(10, 30, true), 1e-6);
        assertEquals(7, p.damage(10, 30, false), 1e-6);
    }
    @Test void critEncodingIsDecodedNotRawStatOrUniversalDouble() {
        assertEquals(1.5, WeaponBallistics.of(entry("austringer")).precision());
        assertEquals(89 / 51.0 + 1.5, WeaponBallistics.of(entry("beloved")).precision(), 1e-8);
        assertEquals(1, WeaponBallistics.of(entry("erentil_fr4")).precision());
        assertEquals(1, WeaponBallistics.of(entry("nezarec_s_whisper")).precision());
        assertEquals(1, WeaponBallistics.of(entry("bad_omens")).precision());
    }
    @Test void pvePelletFloorDiffersFromSlugFloor() {
        assertEquals(.4, WeaponBallistics.of(entry("dust_rock_blues")).floor());
        assertEquals(.001, WeaponBallistics.of(entry("first_in_last_out")).floor());
        assertTrue(WeaponBallistics.of(entry("first_in_last_out")).precision() > 1.5);
    }
    @Test void distantSniperAndBowDoNotFallOffInsideSafetyBound() {
        for (String id : new String[]{"beloved", "biting_winds", "line_in_the_sand"})
            assertEquals(1, WeaponBallistics.of(entry(id)).falloff(96));
    }
    @Test void traceRemainsBoundedAndMeleeExplosionReachIsUnchanged() {
        for (var e : WeaponCatalog.all()) {
            var p = WeaponProfile.forEntry(e);
            double range = WeaponBallistics.traceRange(p);
            assertTrue(range > 0 && range <= 96);
            assertEquals(p.mode() == WeaponProfile.Mode.MELEE || p.blastRadius() > 0 ? p.range() : 96, range);
        }
    }
    @Test void invalidCurvesAndNonfiniteDamageAreRejectedSafely() {
        assertThrows(IllegalArgumentException.class, () -> new WeaponBallistics.Profile(20, 20, .5, 2));
        assertThrows(IllegalArgumentException.class, () -> new WeaponBallistics.Profile(0, 20, 0, 2));
        assertThrows(IllegalArgumentException.class, () -> new WeaponBallistics.Profile(0, 20, .5, Double.NaN));
        var p = new WeaponBallistics.Profile(20, 40, .4, 2);
        assertEquals(0, p.damage(Float.NaN, 20, true));
        assertEquals(0, p.damage(5, Double.NaN, true));
        assertEquals(0, p.damage(5, Double.POSITIVE_INFINITY, true));
    }
}
