package kim.biryeong.destiny.hud;

import org.junit.jupiter.api.Test;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Set;
import static kim.biryeong.destiny.hud.WeaponPerkRows.Kind.*;
import static org.junit.jupiter.api.Assertions.*;

/** New observer flags, compatibility and cleanup; no fabricated gameplay/timer fixture. */
class WeaponPerkRowsW200Test {
    private static WeaponPerkRows.Snapshot flags(boolean box, boolean pulse, boolean unrelenting) {
        return state(0, 0, 0, 0, box, pulse, unrelenting);
    }
    private static WeaponPerkRows.Snapshot state(int killClip, int outlaw, int mori, int sway,
                                                boolean box, boolean pulse, boolean unrelenting) {
        return new WeaponPerkRows.Snapshot(killClip, outlaw, 0, 0, 0, mori, 0, false, 0, 0,
                0, false, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                0, 0, 0, 0, 0, sway, box, pulse, unrelenting);
    }
    private static List<WeaponPerkRows.Kind> kinds(WeaponPerkRows.Snapshot state) {
        return WeaponPerkRows.project(state).stream().map(WeaponPerkRows.Row::kind).toList();
    }
    @Test void everyFlagCombinationProjectsOnlyObservedLabelsWithoutTimerOrCount() {
        var added = List.of(BOX_BREATHING, PULSE_MONITOR, UNRELENTING);
        for (int mask = 0; mask < 8; mask++) {
            var snapshot = flags((mask & 1) != 0, (mask & 2) != 0, (mask & 4) != 0);
            var expected = new ArrayList<WeaponPerkRows.Kind>();
            for (int bit = 0; bit < 3; bit++) if ((mask & (1 << bit)) != 0) expected.add(added.get(bit));
            assertEquals(expected, kinds(snapshot));
            var rows = WeaponPerkRows.project(snapshot);
            assertEquals(rows, WeaponPerkRows.project(snapshot));
            for (var row : rows) {
                assertEquals(WeaponPerkRows.Layout.FLAG, row.kind().layout);
                assertEquals(List.of(row.kind().nodeId("marker"), row.kind().nodeId("label")), row.nodeIds());
                assertEquals(0, row.ticks());
                assertEquals(0, row.count());
                assertEquals(0, row.seconds());
                assertEquals("perk_" + row.kind().name().toLowerCase(java.util.Locale.ROOT) + "_w200", row.label());
            }
        }
    }
    @Test void appendPreservesLegacyKindsAndFourRowPriorityWithPromotion() {
        var added = Set.of(BOX_BREATHING, PULSE_MONITOR, UNRELENTING);
        assertEquals(added, Set.copyOf(Arrays.stream(WeaponPerkRows.Kind.values()).skip(DYNAMIC_SWAY.ordinal() + 1).limit(3).toList()));
        assertEquals(List.of(MEMENTO_MORI, KILL_CLIP, OUTLAW, DYNAMIC_SWAY),
                kinds(state(20, 20, 1, 1, true, true, true)));
        assertEquals(List.of(KILL_CLIP, OUTLAW, DYNAMIC_SWAY, BOX_BREATHING),
                kinds(state(20, 20, 0, 1, true, true, true)));
        assertEquals(List.of(OUTLAW, DYNAMIC_SWAY, BOX_BREATHING, PULSE_MONITOR),
                kinds(state(0, 20, 0, 1, true, true, true)));
        assertEquals(List.of(DYNAMIC_SWAY, BOX_BREATHING, PULSE_MONITOR, UNRELENTING),
                kinds(state(0, 0, 0, 1, true, true, true)));
    }
    @Test void legacyConstructorPreservesAllW199FieldsAndDefaultsAllNewFlagsOff() {
        var old = new WeaponPerkRows.Snapshot(1, 2, 3, 4, 5, 6, 4, true, 5, 10,
                11, true, 5, 14, 3, 16, 5, 18, 2, 12, 144, 5, 90, 220, 200, 2, 110, 2, 3,
                3, 10, 70, 30, 100, 10);
        var explicit = new WeaponPerkRows.Snapshot(1, 2, 3, 4, 5, 6, 4, true, 5, 10,
                11, true, 5, 14, 3, 16, 5, 18, 2, 12, 144, 5, 90, 220, 200, 2, 110, 2, 3,
                3, 10, 70, 30, 100, 10, false, false, false);
        assertEquals(explicit, old);
        var early = new WeaponPerkRows.Snapshot(1, 2, 3, 4, 5, 6, 4, true, 5, 10, 11, true, 5, 14);
        assertFalse(early.boxBreathingReady());
        assertFalse(early.pulseMonitorActive());
        assertFalse(early.unrelentingActive());
    }
    @Test void cleanupPrunesExpiredPreemptedAndLegacyTimerNodesWithoutTouchingOtherHud() {
        var previous = WeaponPerkRows.project(flags(true, true, true)).stream()
                .flatMap(r -> r.nodeIds().stream()).toList();
        var existing = new ArrayList<>(previous);
        existing.add(BOX_BREATHING.nodeId("ones"));
        existing.add(PULSE_MONITOR.nodeId("minutes"));
        existing.add(UNRELENTING.nodeId("count"));
        existing.add("destiny:hud_ammo_label");
        existing.add("foreign:label");
        var rows = WeaponPerkRows.project(flags(false, true, true));
        assertEquals(List.of(BOX_BREATHING.nodeId("label"), BOX_BREATHING.nodeId("marker"),
                BOX_BREATHING.nodeId("ones"), PULSE_MONITOR.nodeId("minutes"), UNRELENTING.nodeId("count")),
                WeaponPerkRows.nodesToRemove(rows, existing));
        var crowded = WeaponPerkRows.project(state(20, 20, 1, 1, true, true, true));
        assertEquals(previous.stream().sorted().toList(), WeaponPerkRows.nodesToRemove(crowded, previous));
        assertEquals(existing.stream().filter(id -> id.startsWith(WeaponPerkRows.PREFIX)).sorted().toList(),
                WeaponPerkRows.nodesToRemove(List.of(), existing));
        var reconciled = new ArrayList<>(existing);
        reconciled.removeAll(WeaponPerkRows.nodesToRemove(rows, existing));
        assertTrue(WeaponPerkRows.nodesToRemove(rows, reconciled).isEmpty());
        assertTrue(reconciled.contains("destiny:hud_ammo_label"));
        assertTrue(reconciled.contains("foreign:label"));
    }
}
