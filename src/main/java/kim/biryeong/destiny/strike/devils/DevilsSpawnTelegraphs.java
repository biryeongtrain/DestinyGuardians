package kim.biryeong.destiny.strike.devils;

import kim.biryeong.destiny.activity.reinforcement.SpawnWarnings;
import net.minecraft.world.phys.AABB;
import java.util.*;

/** Devils' Lair pad adapter; warning ownership and timing live in the shared activity layer. */
final class DevilsSpawnTelegraphs {
    private final SpawnWarnings<String, DevilsSpatial.Point, AABB> warnings = new SpawnWarnings<>();
    SpawnWarnings.Pending<DevilsSpatial.Point, AABB> get(long generation, String slot) {
        return warnings.get(generation, slot);
    }
    void begin(long generation, String slot, DevilsSpatial.Point point, AABB body, long tick, int lead) {
        warnings.begin(generation, slot, point, body, tick, lead);
    }
    List<AABB> reservations(String exceptSlot) { return warnings.reservations(exceptSlot); }
    void remove(String slot) { warnings.remove(slot); }
    List<String> retain(long generation, Set<String> slots) { return warnings.retain(generation, slots); }
    void clear() { warnings.clear(); }
}
