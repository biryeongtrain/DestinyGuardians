package kim.biryeong.destiny.world.template;

import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;
import org.junit.jupiter.api.Test;

import java.util.ArrayList;
import java.util.List;

import static org.junit.jupiter.api.Assertions.*;

class TemplateHazardsTest {
    @Test void feetUseInclusiveBlocksAndExcludeTheUpperFace() {
        var hazard = new TemplateHazards(List.of(new TemplateHazards.DeathRegion("pit", new AABB(10, 0, 20, 14, 32, 24))));
        assertTrue(hazard.deathAt(new Vec3(10, 0, 20)).isPresent());
        assertTrue(hazard.deathAt(new Vec3(13.99, 31.99, 23.99)).isPresent());
        assertTrue(hazard.deathAt(new Vec3(12, 32, 22)).isEmpty());
        assertTrue(hazard.deathAt(new Vec3(14, 20, 22)).isEmpty());
        assertTrue(hazard.deathAt(new Vec3(12, 200, 22)).isEmpty());
    }

    @Test void eachMapOwnsItsImmutableVolumes() {
        var definitions = new ArrayList<TemplateHazards.DeathRegion>();
        var first = new TemplateHazards(definitions);
        definitions.add(new TemplateHazards.DeathRegion("other map", new AABB(0, 0, 0, 10, 10, 10)));
        var second = new TemplateHazards(definitions);
        assertTrue(first.deathAt(new Vec3(1, 1, 1)).isEmpty());
        assertTrue(second.deathAt(new Vec3(1, 1, 1)).isPresent());
        assertThrows(UnsupportedOperationException.class, () -> second.deaths().clear());
    }
}
