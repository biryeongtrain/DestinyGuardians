package kim.biryeong.destiny.hud;

import org.junit.jupiter.api.Test;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Set;
import java.util.stream.Collectors;
import static kim.biryeong.destiny.hud.WeaponPerkRows.Kind.*;
import static org.junit.jupiter.api.Assertions.*;

/** Pure projection checks; gameplay durations and source ownership belong to runtime workers. */
class WeaponPerkRowsW202Test {
    private static WeaponPerkRows.Snapshot state(int head, int steady, int mori, int honed,
                                                int killClip, int outlaw, int feeding) {
        return new WeaponPerkRows.Snapshot(killClip, outlaw, 0, 0, 0, mori, honed, false, feeding, feeding,
                0, false, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                0, 0, 0, 0, 0, 0, false, false, false, head, steady);
    }

    private static WeaponPerkRows.Snapshot state(int head, int steady) {
        return state(head, steady, 0, 0, 0, 0, 0);
    }

    private static List<WeaponPerkRows.Kind> kinds(WeaponPerkRows.Snapshot state) {
        return WeaponPerkRows.project(state).stream().map(WeaponPerkRows.Row::kind).toList();
    }

    @Test void observedBoundsRejectCorruptExpiredAndAbsentWindows() {
        for (int ticks : new int[]{Integer.MIN_VALUE, -1, 0, 12, Integer.MAX_VALUE})
            assertFalse(kinds(state(ticks, 1)).contains(HEADSEEKER));
        for (int ticks : new int[]{Integer.MIN_VALUE, -1, 0, 171, Integer.MAX_VALUE})
            assertFalse(kinds(state(1, ticks)).contains(STEADY_HANDS));
        for (int ticks : new int[]{1, 10, 11}) {
            var row = WeaponPerkRows.project(state(ticks, 0)).getFirst();
            assertEquals(HEADSEEKER, row.kind());
            assertEquals(ticks, row.ticks());
            assertEquals("perk_headseeker_w202", row.label());
            assertEquals(WeaponPerkRows.Layout.FLAG, row.kind().layout);
            assertEquals(List.of(HEADSEEKER.nodeId("marker"), HEADSEEKER.nodeId("label")), row.nodeIds());
        }
        for (int ticks : new int[]{1, 20, 21, 130, 170}) {
            var row = WeaponPerkRows.project(state(0, ticks)).getFirst();
            assertEquals(STEADY_HANDS, row.kind());
            assertEquals(ticks, row.ticks());
            assertEquals((ticks + 19) / 20, row.seconds());
            assertEquals("perk_steady_hands_w202", row.label());
            assertEquals(WeaponPerkRows.Layout.TIMER, row.kind().layout);
            assertEquals(6, row.nodeIds().size());
        }
        assertTrue(WeaponPerkRows.project(state(0, 0)).isEmpty());
    }

    @Test void damagePrecedesReloadAndHiddenUtilityPromotesWithoutRestartingTimer() {
        var crowded = state(11, 130, 1, 2, 20, 20, 1);
        var rows = WeaponPerkRows.project(crowded);
        assertEquals(List.of(MEMENTO_MORI, HONED_EDGE, KILL_CLIP, HEADSEEKER), kinds(crowded));
        assertEquals(4, rows.size());
        assertEquals(List.of(778, 746, 714, 682), rows.stream().map(WeaponPerkRows.Row::y).toList());
        assertEquals(rows, WeaponPerkRows.project(crowded));
        assertEquals(List.of(HEADSEEKER, OUTLAW, FEEDING_FRENZY, STEADY_HANDS),
                kinds(state(1, 129, 0, 0, 0, 1, 1)));
        var promoted = WeaponPerkRows.project(state(0, 21, 0, 0, 0, 1, 1));
        assertEquals(List.of(OUTLAW, FEEDING_FRENZY, STEADY_HANDS), promoted.stream().map(WeaponPerkRows.Row::kind).toList());
        assertEquals(21, promoted.getLast().ticks());
        assertEquals(2, promoted.getLast().seconds());
    }

    @Test void legacyConstructorsAndEnumOrdinalsStayCompatible() throws Exception {
        assertEquals(32, Arrays.stream(WeaponPerkRows.Kind.values()).filter(k -> !k.label.endsWith("_w327")).count());
        assertEquals(29, UNRELENTING.ordinal());
        assertEquals(30, HEADSEEKER.ordinal());
        assertEquals(31, STEADY_HANDS.ordinal());
        assertEquals(Set.of(14, 16, 18, 19, 20, 21, 23, 24, 25, 27, 28, 29, 35, 38, 40),
                Arrays.stream(WeaponPerkRows.Snapshot.class.getDeclaredConstructors())
                        .map(c -> c.getParameterCount()).collect(Collectors.toSet()));
        // Exercise every legacy overload with distinct values and compare every preserved field.
        var components = WeaponPerkRows.Snapshot.class.getRecordComponents();
        for (var constructor : WeaponPerkRows.Snapshot.class.getDeclaredConstructors()) {
            if (constructor.getParameterCount() == 40) continue;
            var args = new Object[constructor.getParameterCount()];
            for (int i = 0; i < args.length; i++) {
                if (components[i].getType() == boolean.class) args[i] = true;
                else args[i] = i + 1;
            }
            var old = (WeaponPerkRows.Snapshot) constructor.newInstance(args);
            assertEquals(0, old.headseekerTicks());
            assertEquals(0, old.steadyHandsTicks());
            for (int i = 0; i < args.length; i++)
                assertEquals(args[i], components[i].getAccessor().invoke(old));
        }
    }

    @Test void cleanupRemovesExpiredPreemptedAndStaleFlagTimerNodes() {
        var previous = WeaponPerkRows.project(state(11, 170)).stream().flatMap(r -> r.nodeIds().stream()).toList();
        var existing = new ArrayList<>(previous);
        existing.add(HEADSEEKER.nodeId("minutes"));
        existing.add(STEADY_HANDS.nodeId("count"));
        existing.add("destiny:hud_ammo_label");
        var visible = WeaponPerkRows.project(state(1, 0));
        var expected = new ArrayList<>(STEADY_HANDS.nodeIds());
        expected.add(HEADSEEKER.nodeId("minutes"));
        expected.add(STEADY_HANDS.nodeId("count"));
        assertEquals(expected.stream().sorted().toList(), WeaponPerkRows.nodesToRemove(visible, existing));
        var crowded = WeaponPerkRows.project(state(1, 130, 1, 2, 1, 1, 1));
        assertEquals(STEADY_HANDS.nodeIds().stream().sorted().toList(), WeaponPerkRows.nodesToRemove(crowded, previous));
        existing.removeAll(WeaponPerkRows.nodesToRemove(visible, existing));
        assertTrue(existing.contains("destiny:hud_ammo_label"));
        assertTrue(WeaponPerkRows.nodesToRemove(visible, existing).isEmpty());
        assertEquals(HEADSEEKER.nodeIds().stream().sorted().toList(), WeaponPerkRows.nodesToRemove(List.of(), existing));
    }
}
