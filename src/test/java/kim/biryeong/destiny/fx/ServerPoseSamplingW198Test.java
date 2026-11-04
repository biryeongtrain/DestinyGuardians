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
}
