package kim.biryeong.destiny.hud;

import org.junit.jupiter.api.Test;

import java.util.ArrayList;
import java.util.Collections;
import java.util.EnumSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;

import static kim.biryeong.destiny.hud.WeaponPerkRows.Kind.*;
import static org.junit.jupiter.api.Assertions.*;

/** Pure projection/registry-reconciliation tests. No Minecraft bootstrap or native fidelity claim. */
class WeaponPerkRowsW155Test {
    private static final List<WeaponPerkRows.Kind> PRIORITY = List.of(
            MEMENTO_MORI, HONED_EDGE, KILL_CLIP, RAMPAGE, ONE_FOR_ALL, SURROUNDED,
            SWASHBUCKLER, OUTLAW, ARCHERS_TEMPO, NO_DISTRACTIONS, FEEDING_FRENZY);
    private static final String PREFIX = "destiny:hud_perk_";

    private static WeaponPerkRows.Snapshot snapshot(Set<WeaponPerkRows.Kind> active) {
        return new WeaponPerkRows.Snapshot(
                active.contains(KILL_CLIP) ? 99 : 0, active.contains(OUTLAW) ? 87 : 0,
                active.contains(RAMPAGE) ? 3 : 0, active.contains(RAMPAGE) ? 61 : 0,
                active.contains(ARCHERS_TEMPO) ? 43 : 0, active.contains(MEMENTO_MORI) ? 6 : 0,
                active.contains(HONED_EDGE) ? 4 : 0, active.contains(NO_DISTRACTIONS),
                active.contains(FEEDING_FRENZY) ? 5 : 0, active.contains(FEEDING_FRENZY) ? 101 : 0,
                active.contains(ONE_FOR_ALL) ? 199 : 0, active.contains(SURROUNDED),
                active.contains(SWASHBUCKLER) ? 5 : 0, active.contains(SWASHBUCKLER) ? 89 : 0);
    }

    private static List<WeaponPerkRows.Kind> kinds(List<WeaponPerkRows.Row> rows) {
        return rows.stream().map(WeaponPerkRows.Row::kind).toList();
    }

    private static WeaponPerkRows.Row only(WeaponPerkRows.Snapshot state) {
        var rows = WeaponPerkRows.project(state);
        assertEquals(1, rows.size());
        return rows.getFirst();
    }

    @Test void allElevenCandidatesAreCappedAtFourWithExoticThenDamagePriority() {
        var rows = WeaponPerkRows.project(snapshot(EnumSet.allOf(WeaponPerkRows.Kind.class)));
        assertEquals(List.of(MEMENTO_MORI, HONED_EDGE, KILL_CLIP, RAMPAGE), kinds(rows));
        assertEquals(List.of(778, 746, 714, 682), rows.stream().map(WeaponPerkRows.Row::y).toList());
        assertEquals(List.of(0, 1, 2, 3), rows.stream().map(WeaponPerkRows.Row::slot).toList());
        assertEquals(4, WeaponPerkRows.MAX_ROWS);
        assertThrows(UnsupportedOperationException.class, rows::clear);
    }

    @Test void all2048ActivationCombinationsHaveStableContiguousNonoverlappingPrioritySlots() {
        for (int mask = 0; mask < (1 << PRIORITY.size()); mask++) {
            var active = EnumSet.noneOf(WeaponPerkRows.Kind.class);
            for (int bit = 0; bit < PRIORITY.size(); bit++)
                if ((mask & (1 << bit)) != 0) active.add(PRIORITY.get(bit));
            var state = snapshot(active);
            var rows = WeaponPerkRows.project(state);
            var expected = PRIORITY.stream().filter(active::contains).limit(4).toList();
            assertEquals(expected, kinds(rows), "mask " + mask);
            assertEquals(rows, WeaponPerkRows.project(state));
            for (int slot = 0; slot < rows.size(); slot++) {
                assertEquals(slot, rows.get(slot).slot());
                assertEquals(778 - 32 * slot, rows.get(slot).y());
                if (slot > 0) assertTrue(rows.get(slot - 1).y() - rows.get(slot).y() > 24,
                        "Existing tallest label is 24 units; row spacing must not overlap");
            }
        }
    }

    @Test void everyFreedSlotPromotesTheNextStillActiveCandidateWithoutCachedState() {
        var active = EnumSet.allOf(WeaponPerkRows.Kind.class);
        for (int removed = 0; removed < PRIORITY.size(); removed++) {
            assertEquals(PRIORITY.subList(removed, Math.min(removed + 4, PRIORITY.size())),
                    kinds(WeaponPerkRows.project(snapshot(active))));
            active.remove(PRIORITY.get(removed));
        }
        assertTrue(WeaponPerkRows.project(snapshot(active)).isEmpty());
        // Interleave independent snapshots to catch any global/per-player stale projection cache.
        var original = snapshot(EnumSet.of(OUTLAW, FEEDING_FRENZY));
        var expected = WeaponPerkRows.project(original);
        WeaponPerkRows.project(snapshot(EnumSet.allOf(WeaponPerkRows.Kind.class)));
        WeaponPerkRows.project(snapshot(Set.of()));
        assertEquals(expected, WeaponPerkRows.project(original));
    }

    @Test void zeroNegativeAndInconsistentStackTimerInputsDoNotOccupySlots() {
        assertTrue(WeaponPerkRows.project(snapshot(Set.of())).isEmpty());
        assertTrue(WeaponPerkRows.project(new WeaponPerkRows.Snapshot(
                -1, -20, -1, 40, Integer.MIN_VALUE, -1, 1, false, 0, 40,
                -1, false, 3, 0)).isEmpty());
        assertTrue(WeaponPerkRows.project(new WeaponPerkRows.Snapshot(
                0, 0, 3, -1, 0, 0, -1, false, 5, -1,
                0, false, 0, 40)).isEmpty());
        assertThrows(NullPointerException.class, () -> WeaponPerkRows.project(null));
        // Invalid damage/stack inputs must not prevent the following utility row from promotion.
        var row = only(new WeaponPerkRows.Snapshot(0, 1, 0, 40, 0, 0, 1,
                false, 0, 40, 0, false, 0, 40));
        assertEquals(OUTLAW, row.kind());
        assertEquals(778, row.y());
    }

    @Test void timerCeilingKeepsLiveLastTickAndDoesNotOverflow() {
        int[] ticks = {1, 19, 20, 21, 39, 40, 41, 199, Integer.MAX_VALUE};
        int[] seconds = {1, 1, 1, 2, 2, 2, 3, 10, 107374183};
        for (int i = 0; i < ticks.length; i++) {
            var row = only(new WeaponPerkRows.Snapshot(ticks[i], 0, 0, 0, 0, 0, 0,
                    false, 0, 0, 0, false, 0, 0));
            assertEquals(ticks[i], row.ticks());
            assertEquals(seconds[i], row.seconds());
        }
    }

    @Test void countsAndRampageNextDecayKeepTheirActualRuntimeMeaning() {
        for (int rounds : new int[]{1, 5, 6, 7}) {
            var mori = only(new WeaponPerkRows.Snapshot(0, 0, 0, 0, 0, rounds, 0,
                    false, 0, 0, 0, false, 0, 0));
            assertEquals(rounds, mori.count());
            assertEquals(Math.min(6, rounds), mori.displayCount());
            assertEquals(0, mori.ticks());
            assertFalse(mori.kind().layout.timed());
            assertEquals("perk_memento_mori_w83", mori.label());
        }
        for (int charge = 2; charge <= 4; charge++) {
            var honed = only(new WeaponPerkRows.Snapshot(0, 0, 0, 0, 0, 0, charge,
                    false, 0, 0, 0, false, 0, 0));
            assertEquals(charge, honed.displayCount());
            assertFalse(honed.kind().layout.timed());
        }
        for (int stacks = 1; stacks <= 3; stacks++) {
            var rampage = only(new WeaponPerkRows.Snapshot(0, 0, stacks, 21, 0, 0, 0,
                    false, 0, 0, 0, false, 0, 0));
            assertEquals(stacks, rampage.count());
            assertEquals(21, rampage.ticks());
            assertEquals(2, rampage.seconds());
            assertEquals("perk_rampage_w66_x" + stacks, rampage.label());
        }
        var stacked = WeaponPerkRows.project(snapshot(EnumSet.of(SWASHBUCKLER, FEEDING_FRENZY)));
        assertEquals(List.of(5, 5), stacked.stream().map(WeaponPerkRows.Row::displayCount).toList());
        assertEquals(List.of(89, 101), stacked.stream().map(WeaponPerkRows.Row::ticks).toList());
        assertEquals(List.of(5, 6), stacked.stream().map(WeaponPerkRows.Row::seconds).toList());
        assertEquals(List.of("perk_swashbuckler_w110", "perk_feeding_frenzy_w108"),
                stacked.stream().map(WeaponPerkRows.Row::label).toList());
    }

    // Pin the pre-W155 node IDs independently of the production layout metadata.
    private static Map<WeaponPerkRows.Kind, List<String>> legacyNodes() {
        var result = new LinkedHashMap<WeaponPerkRows.Kind, List<String>>();
        String timer = "marker label minutes colon tens ones";
        String stacked = "marker label x count minutes colon tens ones";
        legacy(result, KILL_CLIP, "", timer);
        legacy(result, OUTLAW, "outlaw_", timer);
        legacy(result, RAMPAGE, "rampage_", timer);
        legacy(result, ARCHERS_TEMPO, "archers_tempo_", timer);
        legacy(result, MEMENTO_MORI, "memento_mori_", "marker label x count");
        legacy(result, HONED_EDGE, "honed_edge_", "marker label x count");
        legacy(result, NO_DISTRACTIONS, "no_distractions_", "marker label");
        legacy(result, FEEDING_FRENZY, "feeding_frenzy_", stacked);
        legacy(result, ONE_FOR_ALL, "one_for_all_", timer);
        legacy(result, SURROUNDED, "surrounded_", "marker label");
        legacy(result, SWASHBUCKLER, "swashbuckler_", stacked);
        return result;
    }

    private static void legacy(Map<WeaponPerkRows.Kind, List<String>> mapping,
                               WeaponPerkRows.Kind kind, String key, String suffixes) {
        mapping.put(kind, List.of(suffixes.split(" ")).stream().map(s -> PREFIX + key + s).toList());
    }

    @Test void cleanupMappingMatchesAll58LegacyNodesIncludingStacksAndTimerlessRows() {
        var legacy = legacyNodes();
        assertEquals(11, legacy.size());
        var all = legacy.values().stream().flatMap(List::stream).toList();
        assertEquals(58, all.size());
        assertEquals(58, Set.copyOf(all).size());
        legacy.forEach((kind, nodes) -> assertEquals(nodes, kind.nodeIds(), kind.toString()));
        assertEquals(all.stream().sorted().toList(), WeaponPerkRows.nodesToRemove(List.of(), all));
    }

    @Test void cleanupReconcilesLegacyElevenRowFeedForEveryActivationCombination() {
        var legacy = legacyNodes();
        var existing = new ArrayList<>(legacy.values().stream().flatMap(List::stream).toList());
        existing.add(PREFIX + "feeding_frenzy_old_timer");
        existing.add(PREFIX + "obsolete_label");
        existing.add("destiny:hud_ammo_label");
        existing.add("destiny:hud_perks_unrelated");
        for (int mask = 0; mask < (1 << PRIORITY.size()); mask++) {
            var active = EnumSet.noneOf(WeaponPerkRows.Kind.class);
            for (int bit = 0; bit < PRIORITY.size(); bit++)
                if ((mask & (1 << bit)) != 0) active.add(PRIORITY.get(bit));
            var rows = WeaponPerkRows.project(snapshot(active));
            var keep = PRIORITY.stream().filter(active::contains).limit(4)
                    .flatMap(k -> legacy.get(k).stream()).toList();
            var expected = existing.stream().filter(id -> id.startsWith(PREFIX) && !keep.contains(id))
                    .sorted().toList();
            assertEquals(expected, WeaponPerkRows.nodesToRemove(rows, existing), "mask " + mask);
        }
        Collections.reverse(existing);
        assertEquals(existing.stream().filter(id -> id.startsWith(PREFIX)).sorted().toList(),
                WeaponPerkRows.nodesToRemove(List.of(), existing), "Removal order is deterministic");
    }

    @Test void preemptionAndDeactivationRemoveEveryStackedAndTimerlessNodeThenPromote() {
        var legacy = legacyNodes();
        var utility = WeaponPerkRows.project(snapshot(EnumSet.of(
                SURROUNDED, SWASHBUCKLER, NO_DISTRACTIONS, FEEDING_FRENZY)));
        var oldNodes = utility.stream().flatMap(r -> legacy.get(r.kind()).stream()).toList();
        assertEquals(20, oldNodes.size());
        var crowded = WeaponPerkRows.project(snapshot(EnumSet.allOf(WeaponPerkRows.Kind.class)));
        assertEquals(oldNodes.stream().sorted().toList(), WeaponPerkRows.nodesToRemove(crowded, oldNodes));
        var promoted = WeaponPerkRows.project(snapshot(EnumSet.of(
                HONED_EDGE, KILL_CLIP, RAMPAGE, SWASHBUCKLER, FEEDING_FRENZY)));
        assertEquals(List.of(HONED_EDGE, KILL_CLIP, RAMPAGE, SWASHBUCKLER), kinds(promoted));
        assertEquals(682, promoted.getLast().y());
        var crowdedNodes = crowded.stream().flatMap(r -> legacy.get(r.kind()).stream()).toList();
        assertEquals(legacy.get(MEMENTO_MORI).stream().sorted().toList(),
                WeaponPerkRows.nodesToRemove(promoted, crowdedNodes));
        var promotedNodes = promoted.stream().flatMap(r -> legacy.get(r.kind()).stream()).toList();
        assertEquals(promotedNodes.stream().sorted().toList(),
                WeaponPerkRows.nodesToRemove(WeaponPerkRows.project(snapshot(Set.of())), promotedNodes));
    }
}
