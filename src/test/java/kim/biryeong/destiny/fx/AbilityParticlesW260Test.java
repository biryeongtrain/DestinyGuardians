package kim.biryeong.destiny.fx;

import net.minecraft.core.particles.DustColorTransitionOptions;
import net.minecraft.core.particles.DustParticleOptions;
import net.minecraft.core.particles.ParticleOptions;
import net.minecraft.core.particles.ParticleTypes;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;

import java.util.List;

import static org.junit.jupiter.api.Assertions.*;

/** Native particle-option tests only; team routing, network range and rendering need master QA. */
class AbilityParticlesW260Test {
    @BeforeAll static void bootstrap() {
        net.minecraft.SharedConstants.tryDetectVersion();
        net.minecraft.server.Bootstrap.bootStrap();
    }

    @Test void nonEnemySelectionRetainsExactTypeColorAndObjectForEveryUsedAccent() {
        for (ParticleOptions original : List.of(
                new DustParticleOptions(0x4567AB, .65f),
                new DustColorTransitionOptions(0x123456, 0xABCDEF, 1.4f),
                ParticleTypes.ELECTRIC_SPARK, ParticleTypes.FLAME, ParticleTypes.PORTAL,
                ParticleTypes.CRIT, ParticleTypes.LAVA, ParticleTypes.LARGE_SMOKE)) {
            assertSame(original, AbilityParticles.variant(original, false));
        }
    }

    @Test void enemyDustIsRedButRetainsAuthoredScaleWithoutMutatingOriginal() {
        for (float size : new float[] {.3f, .4f, .65f, .8f, 1.2f, 1.6f, 2f}) {
            var original = new DustParticleOptions(0x4567AB, size);
            var before = original.getColor();
            var enemy = assertInstanceOf(DustParticleOptions.class, AbilityParticles.variant(original, true));
            assertNotSame(original, enemy);
            assertEquals(size, enemy.getScale());
            assertEquals(new DustParticleOptions(AbilityParticles.ENEMY_COLOR, size).getColor(), enemy.getColor());
            assertEquals(before, original.getColor());
            assertSame(original, AbilityParticles.variant(original, false));
        }
    }

    @Test void enemyTransitionRemainsRedAtBothEndsAndKeepsScale() {
        var original = new DustColorTransitionOptions(0x123456, 0xABCDEF, 1.4f);
        var from = original.getFromColor(); var to = original.getToColor();
        var enemy = assertInstanceOf(DustColorTransitionOptions.class, AbilityParticles.variant(original, true));
        var red = new DustParticleOptions(AbilityParticles.ENEMY_COLOR, 1.4f).getColor();
        assertEquals(red, enemy.getFromColor()); assertEquals(red, enemy.getToColor());
        assertEquals(original.getScale(), enemy.getScale());
        assertEquals(from, original.getFromColor()); assertEquals(to, original.getToColor());
    }

    @Test void untintableAccentsUseRedDustOnlyForEnemySelection() {
        for (ParticleOptions original : List.of(ParticleTypes.ELECTRIC_SPARK, ParticleTypes.FLAME,
                ParticleTypes.PORTAL, ParticleTypes.CRIT, ParticleTypes.LAVA, ParticleTypes.LARGE_SMOKE)) {
            var enemy = assertInstanceOf(DustParticleOptions.class, AbilityParticles.variant(original, true));
            assertEquals(new DustParticleOptions(AbilityParticles.ENEMY_COLOR, 1).getColor(), enemy.getColor());
            assertEquals(1, enemy.getScale());
            assertSame(original, AbilityParticles.variant(original, false));
        }
    }

    @Test void selectionHasNoStickyTeamStateAcrossAudienceChanges() {
        var original = new DustParticleOptions(0x44BBFF, .8f);
        ParticleOptions firstEnemy = AbilityParticles.variant(original, true);
        assertSame(original, AbilityParticles.variant(original, false));
        ParticleOptions secondEnemy = AbilityParticles.variant(original, true);
        assertEquals(((DustParticleOptions) firstEnemy).getColor(), ((DustParticleOptions) secondEnemy).getColor());
        assertEquals(new DustParticleOptions(0x44BBFF, .8f).getColor(), original.getColor());
    }
}
