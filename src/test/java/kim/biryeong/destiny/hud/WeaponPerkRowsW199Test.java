package kim.biryeong.destiny.hud;

import org.junit.jupiter.api.Test;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Set;
import static kim.biryeong.destiny.hud.WeaponPerkRows.Kind.*;
import static org.junit.jupiter.api.Assertions.*;

/** Actual observer projection boundaries; no combat writer, registry bootstrap or native claim. */
class WeaponPerkRowsW199Test {
    private static final Set<WeaponPerkRows.Kind> NEW = Set.of(
            KILLING_TALLY, WHIRLWIND_BLADE, EN_GARDE, ASSASSINS_BLADE, DYNAMIC_SWAY);

    private static WeaponPerkRows.Snapshot state(int tally, int whirlwind, int whirlwindTicks,
                                               int enGarde, int assassins, int sway) {
        return new WeaponPerkRows.Snapshot(0, 0, 0, 0, 0, 0, 0, false, 0, 0,
                0, false, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                tally, whirlwind, whirlwindTicks, enGarde, assassins, sway);
    }

    private static List<WeaponPerkRows.Kind> kinds(WeaponPerkRows.Snapshot snapshot) {
        return WeaponPerkRows.project(snapshot).stream().map(WeaponPerkRows.Row::kind).toList();
    }

    private static WeaponPerkRows.Snapshot isolated(WeaponPerkRows.Kind kind, int count, int ticks) {
        return switch (kind) {
            case KILLING_TALLY -> state(count, 0, 0, 0, 0, 0);
            case WHIRLWIND_BLADE -> state(0, count, ticks, 0, 0, 0);
            case EN_GARDE -> state(0, 0, 0, ticks, 0, 0);
            case ASSASSINS_BLADE -> state(0, 0, 0, 0, ticks, 0);
            case DYNAMIC_SWAY -> state(0, 0, 0, 0, 0, count);
            default -> throw new IllegalArgumentException();
        };
    }

    @Test void stableDamagePriorityFourRowsAndPromotionPreserveEveryOldKindOrder() {
        assertEquals(List.of(MEMENTO_MORI, HONED_EDGE, KILL_CLIP, MULTIKILL_CLIP, RAMPAGE,
                ONE_FOR_ALL, SURROUNDED, SWASHBUCKLER, OUTLAW, ARCHERS_TEMPO, NO_DISTRACTIONS,
                RAPID_HIT, FEEDING_FRENZY, PERPETUAL_MOTION, TAP_THE_TRIGGER, FRENZY,
                ADRENALINE_JUNKIE, FOCUSED_FURY, STATS_FOR_ALL, HEATING_UP, THREAT_DETECTOR, SURPLUS),
                Arrays.stream(WeaponPerkRows.Kind.values()).filter(k -> k.ordinal() < BOX_BREATHING.ordinal() && !NEW.contains(k)).toList());
        var crowded = state(3, 10, 70, 30, 100, 10);
        var rows = WeaponPerkRows.project(crowded);
        assertEquals(List.of(KILLING_TALLY, WHIRLWIND_BLADE, EN_GARDE, ASSASSINS_BLADE), kinds(crowded));
        assertEquals(List.of(778, 746, 714, 682), rows.stream().map(WeaponPerkRows.Row::y).toList());
        assertEquals(List.of(0, 1, 2, 3), rows.stream().map(WeaponPerkRows.Row::slot).toList());
        assertEquals(List.of(WHIRLWIND_BLADE, EN_GARDE, ASSASSINS_BLADE, DYNAMIC_SWAY),
                kinds(state(0, 10, 70, 30, 100, 10)));
        var mixed = new WeaponPerkRows.Snapshot(40, 80, 0, 0, 0, 6, 4, false, 0, 0,
                0, false, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                3, 10, 70, 30, 100, 10);
        assertEquals(List.of(MEMENTO_MORI, HONED_EDGE, KILL_CLIP, KILLING_TALLY), kinds(mixed));
        assertEquals(rows, WeaponPerkRows.project(crowded));
        assertThrows(UnsupportedOperationException.class, rows::clear);
    }

    @Test void actualCountBoundsRejectCorruptionAndTenUsesTwoExistingDigitNodes() {
        for (var kind : List.of(KILLING_TALLY, WHIRLWIND_BLADE, DYNAMIC_SWAY)) {
            int max = kind == KILLING_TALLY ? 3 : 10;
            for (int count : new int[]{1, max}) {
                var row = WeaponPerkRows.project(isolated(kind, count, 70)).getFirst();
                assertEquals(kind, row.kind());
                assertEquals(count, row.displayCount());
                assertEquals("perk_" + kind.name().toLowerCase(java.util.Locale.ROOT) + "_w199", row.label());
                assertEquals(count == 10, row.nodeIds().contains(kind.nodeId("count_tens")));
                assertEquals(kind == WHIRLWIND_BLADE, row.kind().layout.timed());
            }
            for (int count : new int[]{Integer.MIN_VALUE, -1, 0, max + 1, Integer.MAX_VALUE})
                assertTrue(WeaponPerkRows.project(isolated(kind, count, 70)).isEmpty(), kind + " count " + count);
        }
    }

    @Test void observedTimerBoundsAndLastTickExpiryNeverInventActiveRows() {
        var timed = List.of(WHIRLWIND_BLADE, EN_GARDE, ASSASSINS_BLADE);
        int[] maxima = {70, 30, 100};
        for (int i = 0; i < timed.size(); i++) {
            var kind = timed.get(i);
            for (int ticks : new int[]{1, 20, 21, maxima[i]}) {
                var row = WeaponPerkRows.project(isolated(kind, 1, ticks)).getFirst();
                assertEquals(ticks, row.ticks());
                assertEquals((ticks + 19) / 20, row.seconds());
            }
            for (int ticks : new int[]{Integer.MIN_VALUE, -1, 0, maxima[i] + 1, Integer.MAX_VALUE})
                assertTrue(WeaponPerkRows.project(isolated(kind, 1, ticks)).isEmpty(), kind + " ticks " + ticks);
        }
        assertTrue(WeaponPerkRows.project(state(0, 0, 0, 0, 0, 0)).isEmpty());
        assertTrue(WeaponPerkRows.project(state(0, 0, 70, 0, 0, 0)).isEmpty());
        assertTrue(WeaponPerkRows.project(state(0, 10, 0, 0, 0, 0)).isEmpty());
        assertEquals(List.of(WHIRLWIND_BLADE, EN_GARDE, ASSASSINS_BLADE, DYNAMIC_SWAY),
                kinds(state(0, 1, 1, 1, 1, 10)));
        assertEquals(List.of(DYNAMIC_SWAY), kinds(state(0, 0, 0, 0, 0, 10)));
        // An Assassin's Blade aggregate is sufficient on its own, including while source is stowed.
        assertEquals(List.of(ASSASSINS_BLADE), kinds(state(0, 0, 0, 0, 1, 0)));
    }

    @Test void cleanupRemovesPreemptedExpiredUnknownAndOptionalTensNodes() {
        var all = new ArrayList<String>();
        for (var kind : WeaponPerkRows.Kind.values()) all.addAll(kind.nodeIds());
        all.add(WeaponPerkRows.PREFIX + "unknown_old_timer");
        all.add("destiny:hud_ammo_label");
        var visible = WeaponPerkRows.project(state(3, 10, 70, 30, 100, 10));
        var retained = visible.stream().flatMap(row -> row.nodeIds().stream()).toList();
        assertEquals(all.stream().filter(id -> id.startsWith(WeaponPerkRows.PREFIX) && !retained.contains(id)).sorted().toList(),
                WeaponPerkRows.nodesToRemove(visible, all));
        assertTrue(WeaponPerkRows.nodesToRemove(visible, all).contains(DYNAMIC_SWAY.nodeId("count_tens")));
        var previous = WeaponPerkRows.project(state(0, 10, 70, 0, 0, 10)).stream()
                .flatMap(row -> row.nodeIds().stream()).toList();
        for (int count : new int[]{1, 9}) {
            var single = WeaponPerkRows.project(state(0, count, 69, 0, 0, count));
            var removed = WeaponPerkRows.nodesToRemove(single, previous);
            assertEquals(List.of(DYNAMIC_SWAY.nodeId("count_tens"), WHIRLWIND_BLADE.nodeId("count_tens")),
                    removed, "ten to " + count);
            // Apply the same removal list used against DisplayHud's real registry.
            var remaining = new ArrayList<>(previous);
            remaining.removeAll(removed);
            assertEquals(single.stream().flatMap(row -> row.nodeIds().stream()).toList(), remaining);
            assertTrue(WeaponPerkRows.nodesToRemove(single, remaining).isEmpty());
            // Expanding back to ten retains both digit nodes; a later collapse removes them again.
            var ten = WeaponPerkRows.project(state(0, 10, 70, 0, 0, 10));
            assertTrue(WeaponPerkRows.nodesToRemove(ten, previous).isEmpty());
            assertEquals(2, ten.stream().flatMap(row -> row.nodeIds().stream())
                    .filter(id -> id.endsWith("count_tens")).count());
        }
        assertEquals(previous.stream().sorted().toList(), WeaponPerkRows.nodesToRemove(List.of(), previous));
        assertEquals(all.stream().filter(id -> id.startsWith(WeaponPerkRows.PREFIX)).sorted().toList(),
                WeaponPerkRows.nodesToRemove(List.of(), all));
    }

    @Test void w183AndEarlierConstructorsPreserveFieldsWithoutInferringNewPerks() {
        var old = new WeaponPerkRows.Snapshot(1, 2, 3, 4, 5, 6, 4, true, 5, 10,
                11, true, 5, 14, 3, 16, 5, 18, 2, 12, 144, 5, 90, 220, 200, 2, 110, 2, 3);
        var explicit = new WeaponPerkRows.Snapshot(1, 2, 3, 4, 5, 6, 4, true, 5, 10,
                11, true, 5, 14, 3, 16, 5, 18, 2, 12, 144, 5, 90, 220, 200, 2, 110, 2, 3,
                0, 0, 0, 0, 0, 0);
        assertEquals(explicit, old);
        assertEquals(3, old.surplusCharges());
        assertEquals(2, old.threatDetectorStacks());
        assertEquals(110, old.heatingUpTicks());
        assertEquals(List.of(MEMENTO_MORI, HONED_EDGE, KILL_CLIP, MULTIKILL_CLIP), kinds(old));
        var legacy = new WeaponPerkRows.Snapshot(1, 2, 3, 4, 5, 6, 4, true, 5, 10, 11, true, 5, 14);
        assertEquals(0, legacy.killingTallyStacks());
        assertEquals(0, legacy.whirlwindBladeStacks());
        assertEquals(0, legacy.whirlwindBladeTicks());
        assertEquals(0, legacy.enGardeTicks());
        assertEquals(0, legacy.assassinsBladeTicks());
        assertEquals(0, legacy.dynamicSwayStacks());
        assertEquals(14, legacy.swashbucklerTicks());
    }
}
