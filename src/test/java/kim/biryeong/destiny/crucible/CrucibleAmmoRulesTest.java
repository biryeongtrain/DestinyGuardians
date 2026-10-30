package kim.biryeong.destiny.crucible;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;
import static kim.biryeong.destiny.crucible.CrucibleAmmoRules.*;

class CrucibleAmmoRulesTest {
    @Test void initialRespawnAndBrickUseThirtyTraceAndTwoOtherSpecialPerWeapon() {
        for (String family : new String[]{"sniper_rifle", "fusion_rifle", "shotgun", "grenade_launcher", "glaive", "trace_rifle"}) {
            int expected = family.equals("trace_rifle") ? 30 : 2;
            assertEquals(expected, starting(family));
            assertEquals(expected, brick(family));
            assertEquals(expected, specialPayout(family, false));
        }
    }
    @Test void deathRetainsNothingIncludingLoadedReserveAndLegacyOverflow() {
        for (long total : new long[]{0, 1, 2, 30, 300, Long.MAX_VALUE}) {
            assertEquals(0, retained(total, 2));
            assertEquals(0, retained(total, 30));
        }
    }
    @Test void heavyPayoutAndItsExistingSplitRemainUnchanged() {
        assertEquals(22, heavyBrick("machine_gun"));
        assertEquals(8, heavyBrick("sword"));
        assertEquals(3, heavyBrick("heavy_grenade_launcher"));
        assertEquals(3, heavyBrick("linear_fusion_rifle"));
        assertEquals(1, heavyBrick("rocket_launcher"));
        assertEquals(11, split(22, 2));
        assertEquals(1, split(1, 2));
        assertEquals(0, split(2, 0));
    }
    @Test void legacyConfigurationCannotEnableSpecialMetersOrTimedCrates() {
        Config c = new Config(1, 1, 1, 200, 24, true);
        for (Credit kind : Credit.values()) {
            assertEquals(0, gain(c, kind, false));
            assertEquals(0, gain(c, kind, true));
        }
        for (int tick : new int[]{0, 599, 600, 1799, 1800, 3000, Integer.MAX_VALUE})
            assertEquals(-1, crateWave(tick, c));
        assertEquals(1200, BRICK_TICKS);
        assertEquals(1800, HEAVY_FIRST_TICKS);
        assertEquals(2400, HEAVY_REPEAT_TICKS);
    }
    @Test void koreanHelpDescribesPerLifeSharedPolicyWithoutOldRetentionOrMeterPromises() {
        for (String family : new String[]{"sniper_rifle", "trace_rifle"}) {
            String text = kim.biryeong.destiny.inventory.CrucibleAmmoHelpText.description(family, "SPECIAL");
            assertTrue(text.contains("시작·부활 " + starting(family) + "발"));
            assertTrue(text.contains("공용 탄약 " + brick(family) + "발"));
            assertTrue(text.contains("2개 장착해도 분할 없음"));
            assertTrue(text.contains("양 팀 참가자"));
            assertFalse(text.contains("부활 재지급 없음"));
            assertFalse(text.contains("발 보존"));
        }
        assertFalse(kim.biryeong.destiny.inventory.CrucibleAmmoHelpText.description("hand_cannon", "PRIMARY")
                .contains("게이지를 채웁니다"));
    }
    @Test void invalidOrUnboundedLocalSettingsAreRejected() {
        assertThrows(IllegalArgumentException.class, () -> new Config(Double.NaN, .1, 1200, 200, 24, true));
        assertThrows(IllegalArgumentException.class, () -> new Config(.2, Double.POSITIVE_INFINITY, 1200, 200, 24, true));
        assertThrows(IllegalArgumentException.class, () -> new Config(.2, -.1, 1200, 200, 24, true));
        assertThrows(IllegalArgumentException.class, () -> new Config(.2, .1, 0, 200, 24, true));
        assertThrows(IllegalArgumentException.class, () -> new Config(.2, .1, 1200, 200, 10000, true));
    }
}
