package kim.biryeong.destiny.crucible;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;
import static kim.biryeong.destiny.crucible.CrucibleAmmoRules.*;

class CrucibleAmmoRulesTest {
    @Test void startingAndPickupDistinguishSniperAndTrace() {
        assertEquals(29, starting("trace_rifle"));
        assertEquals(1, starting("sniper_rifle"));
        assertEquals(2, brick("sniper_rifle"));
        assertEquals(1, specialPayout("sniper_rifle", true));
        assertEquals(2, specialPayout("sniper_rifle", false));
        assertEquals(22, heavyBrick("machine_gun"));
        assertEquals(2, starting("glaive"));
        for (String family : new String[]{"fusion_rifle", "shotgun", "grenade_launcher"})
            assertEquals(1, starting(family));
    }
    @Test void deathRetentionNeverRefillsAndCapsAllAmmoIncludingOverflow() {
        assertEquals(0, retained(0, 1));
        assertEquals(1, retained(1, 1));
        assertEquals(3, retained(8, 1));
        assertEquals(87, retained(Long.MAX_VALUE, 29));
        assertEquals(0, retained(30, 0));
        for (long total = 0; total < 100; total++) {
            long kept = retained(total, 2);
            assertTrue(kept <= total && kept <= 6);
            assertEquals(kept, retained(kept, 2));
        }
    }
    @Test void doubleSpecialUsesExplicitIntegerPolicyAndReducedRetention() {
        assertEquals(14, split(29, 2));
        assertEquals(1, split(2, 2));
        assertEquals(1, split(1, 2)); // Documented indivisibility exception.
        assertEquals(0, split(2, 0));
        assertEquals(42, retained(99, split(29, 2)));
    }
    @Test void latestRelativeReductionsAreAppliedToConfigurableLocalBase() {
        Config c = new Config(.8, .4, 1200, 200, 24, true);
        assertEquals(.8, gain(c, Credit.PRIMARY, false), 1e-12);
        assertEquals(.4, gain(c, Credit.ABILITY, true), 1e-12);
        for (Credit kind : new Credit[]{Credit.SPECIAL, Credit.HEAVY}) {
            assertEquals(.536, gain(c, kind, false), 1e-12);
            assertEquals(.268, gain(c, kind, true), 1e-12);
        }
        assertEquals(.536, gain(c, Credit.SUPER, false), 1e-12);
        assertEquals(.4, gain(c, Credit.SUPER, true), 1e-12);
        assertEquals(.64, gain(c, Credit.GLAIVE_MELEE, false), 1e-12);
        assertEquals(.32, gain(c, Credit.GLAIVE_MELEE, true), 1e-12);
    }
    @Test void crateWavesUsePlayingClockWithExactThirtySecondBoundary() {
        Config c = Config.localDefaults();
        assertEquals(-1, crateWave(0, c));
        assertEquals(-1, crateWave(599, c));
        assertEquals(0, crateWave(600, c));
        assertEquals(0, crateWave(1799, c));
        assertEquals(1, crateWave(1800, c));
        assertEquals(2, crateWave(3000, c));
        assertEquals(1200, BRICK_TICKS);
        assertEquals(1800, HEAVY_FIRST_TICKS);
        assertEquals(2400, HEAVY_REPEAT_TICKS);
    }
    @Test void invalidOrUnboundedLocalSettingsAreRejected() {
        assertThrows(IllegalArgumentException.class, () -> new Config(Double.NaN, .1, 1200, 200, 24, true));
        assertThrows(IllegalArgumentException.class, () -> new Config(.2, Double.POSITIVE_INFINITY, 1200, 200, 24, true));
        assertThrows(IllegalArgumentException.class, () -> new Config(.2, -.1, 1200, 200, 24, true));
        assertThrows(IllegalArgumentException.class, () -> new Config(.2, .1, 0, 200, 24, true));
        assertThrows(IllegalArgumentException.class, () -> new Config(.2, .1, 1200, 200, 10000, true));
    }
}
