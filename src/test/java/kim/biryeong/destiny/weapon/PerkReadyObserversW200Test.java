package kim.biryeong.destiny.weapon;

import org.junit.jupiter.api.Test;
import java.lang.reflect.Field;
import java.util.LinkedHashMap;
import java.util.Map;
import static org.junit.jupiter.api.Assertions.*;

/** Passive HUD polling cannot create, consume or invalidate an accepted ADS cycle. */
class PerkReadyObserversW200Test {
    private static Map<String, Object> state(BoxBreathingCycle cycle) throws IllegalAccessException {
        var state = new LinkedHashMap<String, Object>();
        for (Field field : BoxBreathingCycle.class.getDeclaredFields()) {
            if (java.lang.reflect.Modifier.isStatic(field.getModifiers())) continue;
            field.setAccessible(true);
            state.put(field.getName(), field.get(cycle));
        }
        return state;
    }
    @Test void unboundAndArmedQueriesCannotWriteTheCycleEvenOnFutureOrRollbackReads() throws Exception {
        var cycle = new BoxBreathingCycle();
        var empty = state(cycle);
        assertFalse(cycle.ready(Long.MAX_VALUE));
        assertEquals(empty, state(cycle));
        cycle.update(100, true, true);
        var armed = state(cycle);
        for (int i = 0; i < 20; i++) {
            assertTrue(cycle.ready(100 + BoxBreathingCycle.PROC_TICKS));
            assertFalse(cycle.ready(99));
            assertTrue(cycle.ready(Long.MAX_VALUE));
        }
        assertEquals(armed, state(cycle));
        var accepted = cycle.capture(100 + BoxBreathingCycle.PROC_TICKS, 1, true);
        assertTrue(cycle.boosted(100 + BoxBreathingCycle.PROC_TICKS, accepted));
    }
    @Test void pollingAfterPaidLastRoundOrExplicitReleaseCannotRearmOrRevokePaidToken() throws Exception {
        var cycle = new BoxBreathingCycle();
        cycle.update(100, true, true);
        long shot = 100 + BoxBreathingCycle.PROC_TICKS;
        var paid = cycle.capture(shot, 1, true);
        var consumed = state(cycle);
        for (int i = 0; i < 20; i++) assertFalse(cycle.ready(shot + i));
        assertEquals(consumed, state(cycle));
        assertTrue(cycle.boosted(shot + 20, paid));
        cycle.released(shot + 20);
        var released = state(cycle);
        assertFalse(cycle.ready(Long.MAX_VALUE));
        assertEquals(released, state(cycle));
        assertFalse(cycle.boosted(shot + 20, paid));
    }
}
