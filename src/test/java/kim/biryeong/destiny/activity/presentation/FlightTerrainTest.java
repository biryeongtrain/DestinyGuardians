package kim.biryeong.destiny.activity.presentation;

import net.minecraft.world.phys.AABB;
import org.junit.jupiter.api.Test;
import java.util.HashSet;
import java.util.Set;
import static org.junit.jupiter.api.Assertions.*;
import static kim.biryeong.destiny.activity.presentation.FlightTerrain.Result.*;

class FlightTerrainTest {
    private static class Probe implements FlightTerrain.Probe {
        final Set<String> chunks=new HashSet<>();int collisions;boolean inside=true,blocked;
        String missing;
        public boolean inside(AABB b){return inside;}
        public boolean loaded(int x,int z){String key=x+":"+z;chunks.add(key);return !key.equals(missing);}
        public boolean collides(AABB b){collisions++;return blocked;}
    }
    @Test void neighboringChunkIsRequiredBeforeAnyShapeRead() {
        var probe=new Probe();probe.missing="1:0";
        assertEquals(UNLOADED,FlightTerrain.inspect(new AABB(14,10,2,15.5,12,4),probe));
        assertEquals(0,probe.collisions);
        assertTrue(probe.chunks.contains("1:0"));
    }
    @Test void negativeChunkCoordinatesAndExtendedShapesAreChecked() {
        var probe=new Probe();probe.blocked=true;
        assertEquals(BLOCKED,FlightTerrain.inspect(new AABB(-.5,10,-.5,.5,12,.5),probe));
        assertEquals(Set.of("-1:-1","-1:0","0:-1","0:0"),probe.chunks);
        assertEquals(1,probe.collisions);
    }
    @Test void enormousOrInvalidRoutesNeverReachWorldQueries() {
        var probe=new Probe();
        assertEquals(TOO_LARGE,FlightTerrain.inspect(new AABB(0,0,0,1000,1000,1000),probe));
        assertEquals(OUTSIDE,FlightTerrain.inspect(new AABB(Double.NaN,0,0,1,1,1),probe));
        assertTrue(probe.chunks.isEmpty());assertEquals(0,probe.collisions);
    }
    @Test void terrainChangesRequireFreshInspection() {
        var probe=new Probe();var b=new AABB(2,10,2,4,12,4);
        assertEquals(CLEAR,FlightTerrain.inspect(b,probe));
        probe.blocked=true;assertEquals(BLOCKED,FlightTerrain.inspect(b,probe));
        probe.inside=false;assertEquals(OUTSIDE,FlightTerrain.inspect(b,probe));
        assertEquals(2,probe.collisions);
    }
}
