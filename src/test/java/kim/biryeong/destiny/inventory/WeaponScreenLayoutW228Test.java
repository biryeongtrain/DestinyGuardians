package kim.biryeong.destiny.inventory;

import kim.biryeong.destiny.inventory.WeaponScreenView.Card;
import kim.biryeong.destiny.inventory.WeaponScreenView.FamilyOption;
import kim.biryeong.destiny.inventory.WeaponScreenView.PerkOption;
import kim.biryeong.destiny.weapon.WeaponSlot;
import org.junit.jupiter.api.Test;

import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

import static org.junit.jupiter.api.Assertions.*;

/** Pure W228 projection/geometry coverage; master runs this with the integrated controller tests. */
class WeaponScreenLayoutW228Test {
    private static final int[][] DIRECTIONS = {{-1, 0}, {1, 0}, {0, -1}, {0, 1}};
    private static final float[][] ORIGINAL_BOXES = {
            {240, 360, 156, 156}, {240, 540, 156, 156}, {240, 720, 156, 156},
            {540, 360, 156, 156}, {720, 360, 156, 156}, {900, 360, 156, 156},
            {540, 540, 156, 156}, {720, 540, 156, 156}, {900, 540, 156, 156},
            {540, 720, 156, 156}, {720, 720, 156, 156}, {900, 720, 156, 156},
            {540, 860, 156, 48}, {900, 860, 156, 48}, {1740, 112, 152, 52}
    };

    @Test void retainsEveryOriginalBoxAndPublishesTheFiveNewControls() {
        assertTrue(WeaponScreenLayout.NODE_COUNT >= 20);
        for (int node = 0; node < ORIGINAL_BOXES.length; node++)
            assertBox(node, ORIGINAL_BOXES[node]);
        assertEquals(15, WeaponScreenLayout.TEST_ARMORY);
        assertEquals(16, WeaponScreenLayout.DAMAGE_PERKS);
        assertEquals(17, WeaponScreenLayout.UTILITY_PERKS);
        assertEquals(18, WeaponScreenLayout.BACK_WEAPONS);
        assertEquals(19, WeaponScreenLayout.CONFIRM_LOADOUT);
        assertBox(WeaponScreenLayout.TEST_ARMORY, new float[]{1450, 112, 280, 52});
        assertBox(WeaponScreenLayout.DAMAGE_PERKS, new float[]{1280, 920, 280, 44});
        assertBox(WeaponScreenLayout.UTILITY_PERKS, new float[]{1600, 920, 280, 44});
        assertBox(WeaponScreenLayout.BACK_WEAPONS, new float[]{720, 925, 220, 44});
        assertBox(WeaponScreenLayout.CONFIRM_LOADOUT, new float[]{1440, 858, 560, 44});
    }

    @Test void backButtonHasNoHitAreaInWeaponModeIncludingPaintedEdges() {
        var back = WeaponScreenLayout.bounds(WeaponScreenLayout.BACK_WEAPONS);
        for (float dx : new float[]{-back.width() / 2, 0, back.width() / 2})
            for (float dy : new float[]{-back.height() / 2, 0, back.height() / 2}) {
                assertEquals(-1, WeaponScreenLayout.hit(back.x() + dx, back.y() + dy, false));
                assertEquals(WeaponScreenLayout.BACK_WEAPONS,
                        WeaponScreenLayout.hit(back.x() + dx, back.y() + dy, true));
            }
        assertFalse(WeaponScreenLayout.visible(WeaponScreenLayout.BACK_WEAPONS, false));
        assertTrue(WeaponScreenLayout.visible(WeaponScreenLayout.BACK_WEAPONS, true));
    }

    @Test void everyVisibleBoxUsesItsPaintedHitEdgesWithoutOverlapsInEitherMode() {
        for (boolean perkMode : new boolean[]{false, true})
            for (int node = 0; node < 20; node++) {
                if (!WeaponScreenLayout.visible(node, perkMode)) continue;
                var box = WeaponScreenLayout.bounds(node);
                for (float dx : new float[]{-box.width() / 2, 0, box.width() / 2})
                    for (float dy : new float[]{-box.height() / 2, 0, box.height() / 2})
                        assertEquals(node, WeaponScreenLayout.hit(box.x() + dx, box.y() + dy, perkMode));
                for (int other = node + 1; other < 20; other++) {
                    if (!WeaponScreenLayout.visible(other, perkMode)) continue;
                    var candidate = WeaponScreenLayout.bounds(other);
                    assertTrue(Math.abs(box.x() - candidate.x()) > (box.width() + candidate.width()) / 2
                            || Math.abs(box.y() - candidate.y()) > (box.height() + candidate.height()) / 2,
                            "overlapping nodes " + node + " and " + other);
                }
            }
    }

    @Test void hiddenBackIsNeitherANavigationCandidateNorARecoveredFocus() {
        for (int current = -1; current <= WeaponScreenLayout.NODE_COUNT; current++) {
            for (int[] direction : DIRECTIONS) {
                int next = WeaponScreenLayout.navigate(current, direction[0], direction[1], false);
                assertTrue(WeaponScreenLayout.visible(next, false));
                assertNotEquals(WeaponScreenLayout.BACK_WEAPONS, next);
            }
            assertNotEquals(WeaponScreenLayout.BACK_WEAPONS, WeaponScreenLayout.navigate(current, 0, 0, false));
        }
        assertEquals(0, WeaponScreenLayout.navigate(WeaponScreenLayout.BACK_WEAPONS, 0, 0, false));
        for (int[] direction : DIRECTIONS)
            assertEquals(WeaponScreenLayout.navigate(0, direction[0], direction[1], false),
                    WeaponScreenLayout.navigate(WeaponScreenLayout.BACK_WEAPONS, direction[0], direction[1], false));
        assertEquals(WeaponScreenLayout.BACK_WEAPONS,
                WeaponScreenLayout.navigate(WeaponScreenLayout.PREVIOUS, 0, 1, true));
        assertNotEquals(WeaponScreenLayout.BACK_WEAPONS,
                WeaponScreenLayout.navigate(WeaponScreenLayout.PREVIOUS, 0, 1, false));
    }

    @Test void allVisibleControlsAreReachableFromEveryVisibleStartingPoint() {
        for (boolean perkMode : new boolean[]{false, true})
            for (int start = 0; start < 20; start++) {
                if (!WeaponScreenLayout.visible(start, perkMode)) continue;
                Set<Integer> visited = new HashSet<>();
                ArrayDeque<Integer> pending = new ArrayDeque<>();
                visited.add(start);
                pending.add(start);
                while (!pending.isEmpty()) {
                    int current = pending.removeFirst();
                    for (int[] direction : DIRECTIONS) {
                        int next = WeaponScreenLayout.navigate(current, direction[0], direction[1], perkMode);
                        assertTrue(WeaponScreenLayout.visible(next, perkMode));
                        if (visited.add(next)) pending.addLast(next);
                    }
                }
                assertEquals(perkMode ? 20 : 18, visited.size(),
                        "unreachable controls from " + start + " in perkMode=" + perkMode);
            }
    }

    @Test void legacyOverloadsUseAllNodesWhileExplicitModesRejectNonfinitePointers() {
        for (int node = 0; node < 20; node++) {
            var box = WeaponScreenLayout.bounds(node);
            assertEquals(node, WeaponScreenLayout.hit(box.x(), box.y()));
            for (int[] direction : DIRECTIONS)
                assertEquals(WeaponScreenLayout.navigate(node, direction[0], direction[1], true),
                        WeaponScreenLayout.navigate(node, direction[0], direction[1]));
        }
        for (boolean perkMode : new boolean[]{false, true}) {
            for (float invalid : new float[]{Float.NaN, Float.POSITIVE_INFINITY, Float.NEGATIVE_INFINITY}) {
                assertEquals(-1, WeaponScreenLayout.hit(invalid, 925, perkMode));
                assertEquals(-1, WeaponScreenLayout.hit(720, invalid, perkMode));
            }
            assertEquals(0, WeaponScreenLayout.navigate(Integer.MIN_VALUE, 0, 0, perkMode));
            for (int node = 0; node < 20; node++)
                assertTrue(WeaponScreenLayout.visible(WeaponScreenLayout.navigate(node,
                        Integer.MIN_VALUE, Integer.MAX_VALUE, perkMode), perkMode));
        }
    }

    @Test void oldElevenArgumentViewConstructorHasImmutableW228Defaults() {
        var view = new WeaponScreenView("수호자", WeaponSlot.KINETIC, List.of(), List.of(), null,
                0, 1, 0, 240, 360, "");
        assertFalse(view.testArmory());
        assertFalse(view.perkMode());
        assertEquals("", view.perkGroup());
        assertEquals("", view.selectedDamage());
        assertEquals("", view.selectedUtility());
        assertTrue(view.perks().isEmpty());
        assertEquals("LOADOUT", view.stage());
        assertTrue(view.families().isEmpty());
        assertEquals("", view.selectedFamily());
        assertNull(view.perkTarget());
        assertThrows(UnsupportedOperationException.class, () -> view.perks().add(option()));
    }

    @Test void projectionCopiesListsAndKeepsOriginalKoreanDescriptionAndDisabledReason() {
        var actual = card(0, "austringer", WeaponSlot.KINETIC, true);
        var equipped = new ArrayList<>(List.of(actual));
        var choices = new ArrayList<>(List.of(card(-1, "preview", WeaponSlot.KINETIC, false)));
        var perks = new ArrayList<>(List.of(option()));
        var families = new ArrayList<>(List.of(new FamilyOption("hand_cannon", "핸드 캐논", 6)));
        var view = new WeaponScreenView("수호자", WeaponSlot.KINETIC, equipped, choices, choices.getFirst(),
                0, 1, 3, 540, 360, "", true, "DAMAGE", perks, "살상 탄창", "무법자",
                "PERKS", families, "hand_cannon");
        equipped.clear();
        choices.clear();
        perks.clear();
        families.clear();
        assertEquals(1, view.equipped().size());
        assertEquals(-1, view.choices().getFirst().inventoryIndex());
        assertEquals("원작 설명\n다음 문장", view.perks().getFirst().description());
        assertEquals("유틸리티 퍽과 같은 소켓을 사용합니다", view.perks().getFirst().reason());
        assertTrue(view.perks().getFirst().selected());
        assertFalse(view.perks().getFirst().enabled());
        assertEquals("살상 탄창", view.selectedDamage());
        assertEquals("무법자", view.selectedUtility());
        assertTrue(view.testArmory());
        assertTrue(view.perkMode());
        assertEquals("hand_cannon", view.selectedFamily());
        assertEquals(new FamilyOption("hand_cannon", "핸드 캐논", 6), view.families().getFirst());
        assertThrows(UnsupportedOperationException.class, () -> view.equipped().clear());
        assertThrows(UnsupportedOperationException.class, () -> view.choices().clear());
        assertThrows(UnsupportedOperationException.class, () -> view.perks().clear());
        assertThrows(UnsupportedOperationException.class, () -> view.families().clear());
    }

    @Test void priorSixteenArgumentConstructorDefaultsToLoadoutAndKeepsEquippedLookup() {
        var kinetic = card(0, "austringer", WeaponSlot.KINETIC, true);
        var energy = card(1, "ammit_ar2", WeaponSlot.ENERGY, true);
        var preview = card(-1, "preview", WeaponSlot.ENERGY, false);
        var ownedHover = card(12, "other_owned", WeaponSlot.ENERGY, false);
        for (String group : new String[]{"", "DAMAGE", "UTILITY"})
            for (Card inspected : List.of(preview, ownedHover)) {
                var view = new WeaponScreenView("수호자", WeaponSlot.ENERGY, List.of(kinetic, energy),
                        List.of(inspected), inspected, 0, 1, 3, 540, 360, "", true, group,
                        List.of(), "", "");
                assertSame(energy, view.perkTarget());
                assertNotSame(inspected, view.perkTarget());
                assertEquals("LOADOUT", view.stage());
                assertFalse(view.perkMode());
            }
        var missing = new WeaponScreenView("수호자", WeaponSlot.POWER, List.of(kinetic, energy),
                List.of(preview), preview, 0, 1, 3, 540, 360, "", true, "DAMAGE", List.of(), "", "");
        assertNull(missing.perkTarget());
        var virtualEquipped = new WeaponScreenView("수호자", WeaponSlot.ENERGY, List.of(preview),
                List.of(), preview, 0, 1, 3, 540, 360, "", true, "UTILITY", List.of(), "", "");
        assertNull(virtualEquipped.perkTarget());
    }

    @Test void eachWizardStageHitsAndNavigatesOnlyItsVisibleControls() {
        Map<String, Set<Integer>> controls = Map.of(
                "LOADOUT", Set.of(0, 1, 2, 14, 15, 20, 21),
                "FAMILY", Set.of(0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 18, 20, 21),
                "WEAPON", Set.of(0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 18, 20, 21),
                "PERKS", Set.of(0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 16, 17, 18, 19, 20, 21));
        for (var stage : controls.entrySet()) {
            String name = stage.getKey();
            Set<Integer> expected = stage.getValue();
            for (int node = -1; node <= WeaponScreenLayout.NODE_COUNT; node++) {
                assertEquals(expected.contains(node), WeaponScreenLayout.visible(node, name));
                assertEquals(expected.contains(node) ? node : 0, WeaponScreenLayout.navigate(node, 0, 0, name));
                for (int[] direction : DIRECTIONS)
                    assertTrue(expected.contains(WeaponScreenLayout.navigate(node, direction[0], direction[1], name)));
                if (node < 0 || node >= WeaponScreenLayout.CLASS) continue; // Character fields reuse another stage's canvas.
                var box = WeaponScreenLayout.bounds(node);
                for (float dx : new float[]{-box.width() / 2, 0, box.width() / 2})
                    for (float dy : new float[]{-box.height() / 2, 0, box.height() / 2})
                        assertEquals(expected.contains(node) ? node : -1,
                                WeaponScreenLayout.hit(box.x() + dx, box.y() + dy, name));
            }
            for (int start : expected) {
                Set<Integer> visited = new HashSet<>(Set.of(start));
                ArrayDeque<Integer> pending = new ArrayDeque<>(Set.of(start));
                while (!pending.isEmpty()) {
                    int current = pending.removeFirst();
                    for (int[] direction : DIRECTIONS) {
                        int next = WeaponScreenLayout.navigate(current, direction[0], direction[1], name);
                        if (visited.add(next)) pending.addLast(next);
                    }
                }
                assertEquals(expected, visited, "unreachable controls in " + name + " from " + start);
            }
            assertEquals(-1, WeaponScreenLayout.hit(Float.NaN, 858, name));
            assertEquals(-1, WeaponScreenLayout.hit(1440, Float.POSITIVE_INFINITY, name));
        }
        assertTrue(WeaponScreenLayout.visible(15, (String) null));
        assertFalse(WeaponScreenLayout.visible(19, "unknown"));
    }

    @Test void onlyPerksStageTargetsDetachedDraftAndOtherStagesKeepActualLoadout() {
        var actual = card(1, "ammit_ar2", WeaponSlot.ENERGY, true);
        var draft = card(-1, "draft", WeaponSlot.ENERGY, false);
        for (String stage : List.of("LOADOUT", "FAMILY", "WEAPON", "PERKS")) {
            var view = new WeaponScreenView("수호자", WeaponSlot.ENERGY, List.of(actual), List.of(draft), draft,
                    0, 1, 3, 540, 360, "", true, "DAMAGE", List.of(option()), "살상 탄창", "무법자",
                    stage, List.of(new FamilyOption("auto_rifle", "자동 소총", 4)), "auto_rifle");
            assertEquals("PERKS".equals(stage), view.perkMode());
            assertSame("PERKS".equals(stage) ? draft : actual, view.perkTarget());
            assertSame(actual, view.equipped().getFirst());
            assertEquals(3, actual.rounds());
        }
        var noDraft = new WeaponScreenView("수호자", WeaponSlot.ENERGY, List.of(actual), List.of(), null,
                0, 1, 0, 240, 360, "", false, "UTILITY", List.of(), "", "", "PERKS", List.of(), "");
        assertNull(noDraft.perkTarget(), "PERKS must not fall back to a real equipped weapon");
    }

    private static void assertBox(int node, float[] expected) {
        var box = WeaponScreenLayout.bounds(node);
        assertArrayEquals(expected, new float[]{box.x(), box.y(), box.width(), box.height()}, "node " + node);
    }

    private static Card card(int inventoryIndex, String id, WeaponSlot slot, boolean equipped) {
        return new Card(inventoryIndex, id, id, "Hand Cannon", "Adaptive Frame", slot, "KINETIC", "PRIMARY",
                false, Map.of(), inventoryIndex < 0 ? 99 : 3, 12, equipped);
    }

    private static PerkOption option() {
        return new PerkOption("kill_clip", "살상 탄창", "원작 설명\n다음 문장", true, false,
                "유틸리티 퍽과 같은 소켓을 사용합니다");
    }
}
