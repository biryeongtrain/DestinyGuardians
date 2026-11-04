package kim.biryeong.destiny.campaign;

import org.junit.jupiter.api.Test;
import java.util.UUID;
import static org.junit.jupiter.api.Assertions.*;
import static kim.biryeong.destiny.campaign.GuardianRisesProgress.Stage.*;

class GuardianRisesProgressTest {
    @Test void combatRequiresSuccessfulSpawnSealAndUniqueDefeats() {
        var state = new GuardianRisesProgress(UUID.randomUUID(),
                new GuardianRisesProgress.Snapshot(DIVIDE_WALKER, false, false));
        var token = state.token();
        var walker = UUID.randomUUID();
        assertFalse(state.advance(token));
        assertTrue(state.registerEnemy(token, walker));
        assertFalse(state.registerEnemy(token, walker));
        assertTrue(state.sealEncounter(token));
        assertFalse(state.advance(token));
        assertTrue(state.enemyDefeated(token, walker));
        assertFalse(state.enemyDefeated(token, walker));
        assertTrue(state.advance(token));
        assertEquals(DOCK_13, state.stage());
        assertFalse(state.advance(token));
    }
    @Test void deathRejectsOldCallbacksAndKeepsMusicOnce() {
        var state = new GuardianRisesProgress(UUID.randomUUID());
        assertTrue(state.startMusicOnce());
        while (state.stage() != BREACH_FIGHT) assertTrue(state.advance(state.token()));
        var old = state.token();
        assertTrue(state.restartCheckpoint());
        assertEquals(ARM_YOURSELF, state.stage());
        assertFalse(state.sealEncounter(old));
        assertFalse(state.advance(old));
        var restored = new GuardianRisesProgress(UUID.randomUUID(), state.snapshot());
        assertEquals(ARM_YOURSELF, restored.stage());
        assertFalse(restored.startMusicOnce());
        assertFalse(restored.advance(state.token()));
    }
    @Test void completeOnlyAfterDepartureAndCannotRestartAccidentally() {
        var state = new GuardianRisesProgress(UUID.randomUUID());
        while (state.stage() != DEPARTURE) {
            state.sealEncounter(state.token());
            assertTrue(state.advance(state.token()));
        }
        assertFalse(state.snapshot().completed());
        assertTrue(state.advance(state.token()));
        assertTrue(state.snapshot().completed());
        assertFalse(state.advance(state.token()));
        assertFalse(state.restartCheckpoint());
        assertEquals(COMPLETE, new GuardianRisesProgress(UUID.randomUUID(), state.snapshot()).stage());
    }
    @Test void lostEnemyReplacementWorksAfterSealButNeverAddsSlots() {
        var state = new GuardianRisesProgress(UUID.randomUUID());
        assertTrue(state.forceStage(SHIP_DEFENSE));
        assertEquals(DOCK_13, state.checkpoint());
        var token = state.token();
        var a = UUID.randomUUID();
        var b = UUID.randomUUID();
        assertTrue(state.registerEnemy(token, a));
        assertTrue(state.sealEncounter(token));
        assertFalse(state.registerEnemy(token, b));
        assertFalse(state.replaceEnemy(token, b, UUID.randomUUID()), "unknown enemy cannot be replaced");
        assertTrue(state.replaceEnemy(token, a, b));
        assertEquals(1, state.enemiesRemaining());
        assertFalse(state.enemyDefeated(token, a));
        assertTrue(state.enemyDefeated(token, b));
        assertTrue(state.advance(token));
        assertEquals(DEPARTURE, state.stage());
    }
    @Test void forceStageResetsGenerationAndRejectsComplete() {
        var state = new GuardianRisesProgress(UUID.randomUUID());
        var old = state.token();
        assertTrue(state.forceStage(BREACH_FIGHT));
        assertEquals(ARM_YOURSELF, state.checkpoint());
        assertFalse(state.owns(old));
        assertFalse(state.forceStage(COMPLETE));
        assertTrue(state.forceStage(GATEWAY));
        assertEquals(GHOST_SCAN, state.checkpoint());
    }
}
