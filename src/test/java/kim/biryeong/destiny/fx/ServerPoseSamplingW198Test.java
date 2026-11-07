package kim.biryeong.destiny.fx;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class ServerPoseSamplingW198Test {
    @Test void revivalSmoothingDoesNotLeakIntoCombatAfterNestedScopeOrFailure() {
        assertEquals(1, ServerPoseSampling.smoothingTicks());
        assertThrows(IllegalStateException.class, () -> ServerPoseSampling.withSmoothing(2, () -> {
            ServerPoseSampling.run(false, () -> assertEquals(2, ServerPoseSampling.smoothingTicks()));
            ServerPoseSampling.withSmoothing(1, () -> assertEquals(1, ServerPoseSampling.smoothingTicks()));
            assertEquals(2, ServerPoseSampling.smoothingTicks());
            throw new IllegalStateException("test");
        }));
        assertEquals(1, ServerPoseSampling.smoothingTicks());
    }
    @Test void nestedPrimeRestoresSuppressedOuterFrameAndExceptionCannotLeakScope() {
        assertFalse(ServerPoseSampling.active());
        assertThrows(IllegalStateException.class, () -> ServerPoseSampling.run(false, () -> {
            assertTrue(ServerPoseSampling.active());
            assertFalse(ServerPoseSampling.publishing());
            ServerPoseSampling.run(() -> {
                assertTrue(ServerPoseSampling.active());
                assertTrue(ServerPoseSampling.publishing());
            });
            assertTrue(ServerPoseSampling.active());
            assertFalse(ServerPoseSampling.publishing());
            throw new IllegalStateException("test");
        }));
        assertFalse(ServerPoseSampling.active());
        assertFalse(ServerPoseSampling.publishing());
        ServerPoseSampling.run(() -> {
            assertTrue(ServerPoseSampling.publishing());
            ServerPoseSampling.run(false, () -> assertFalse(ServerPoseSampling.publishing()));
            assertTrue(ServerPoseSampling.publishing());
        });
        assertFalse(ServerPoseSampling.active());
    }
    @Test void superPrimeTickAndReadyLoopPolicyUsesTwoDisplayTicksOnly() {
        for (String clip : new String[] {"h15_super_arc_start", "h15_super_arc_attack", "h15_super_arc_dodge_left",
                "h15_super_arc", "h15_super_arc_move", "super_void", "h15_super_solar_end",
                "w229_titan_arc_start_air", "w229_titan_solar_idle", "w230_warlock_solar_move",
                "w230_hunter_spectral_blades_attack", "h15_revive_combat"}) {
            assertEquals(2, ServerPoseSampling.animationSmoothingTicks(clip), clip);
        }
        for (String clip : new String[] {"h15_intro_hunter", "h15_reload", "h15_roll_forward",
                "h15_dodge_marksman_left", "h15_class_dodge_right", "h15_sword_attack", "h15_grenade", "revive_combat"}) {
            assertEquals(1, ServerPoseSampling.animationSmoothingTicks(clip), clip);
        }
        assertEquals(1, ServerPoseSampling.animationSmoothingTicks(null));
    }
}
