package kim.biryeong.destiny.strike.devils;

import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;
import org.junit.jupiter.api.Test;
import java.util.Set;
import static org.junit.jupiter.api.Assertions.*;

class DevilsSpawnTelegraphsTest {
    private static DevilsSpatial.Point point(double x) { return new DevilsSpatial.Point("alternative", new Vec3(x,10,20),0,true); }
    private static AABB body(double x) { return new AABB(x-1,10,19,x+1,13,21); }
    @Test void lateSelectionAndRerouteRequireTheirOwnFullWarningInterval() {
        var gate = new DevilsSpawnTelegraphs();
        gate.begin(3,"shield",point(30),body(30),800,24);
        assertFalse(gate.get(3,"shield").ready(823));
        assertTrue(gate.get(3,"shield").ready(824));
        gate.remove("shield"); // selected point became obstructed at commit
        gate.begin(3,"shield",point(40),body(40),824,24);
        assertFalse(gate.get(3,"shield").ready(847));
        assertEquals(point(40),gate.get(3,"shield").point());
        assertTrue(gate.get(3,"shield").ready(848));
    }
    @Test void pendingFootprintsPersistButNeverBlockTheirOwnCommit() {
        var gate = new DevilsSpawnTelegraphs();
        gate.begin(1,"a",point(30),body(30),0,40);
        gate.begin(1,"b",point(40),body(40),1,40);
        assertEquals(java.util.List.of(body(40)),gate.reservations("a"));
        assertEquals(2,gate.reservations("new-slot").size());
        gate.remove("a");
        assertEquals(java.util.List.of(body(40)),gate.reservations("new-slot"));
    }
    @Test void retiredSlotsAndOldGenerationCannotActivateOrKeepReservations() {
        var gate = new DevilsSpawnTelegraphs();
        gate.begin(1,"a",point(30),body(30),0,24);
        gate.begin(1,"b",point(40),body(40),0,24);
        assertEquals(java.util.List.of("b"),gate.retain(1,Set.of("a")));
        assertNull(gate.get(1,"b"));
        assertNull(gate.get(2,"a"));
        assertEquals(java.util.List.of("a"),gate.retain(2,Set.of("a")));
        assertTrue(gate.reservations("none").isEmpty());
        gate.begin(2,"a",point(40),body(40),50,24);
        gate.clear(); assertNull(gate.get(2,"a"));
    }
}
