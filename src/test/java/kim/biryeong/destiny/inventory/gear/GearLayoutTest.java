package kim.biryeong.destiny.inventory.gear;

import kim.biryeong.destiny.inventory.HudPainter;
import kim.biryeong.destiny.inventory.gear.GearLayout.Stage;
import org.junit.jupiter.api.Test;

import java.util.Map;

import static org.junit.jupiter.api.Assertions.*;

class GearLayoutTest {
    @Test void slotsAndGridsStayOnCanvasWithoutOverlap() {
        for (var slot : GearSlot.values()) {
            var b = GearLayout.slot(slot);
            assertTrue(b.y() - b.height() / 2 > 150 && b.y() + b.height() / 2 < 990, slot.name());
            if (slot.weapon() == null) continue;
            for (int i = 0; i < 9; i++) {
                var c = GearLayout.storage(slot, i);
                assertTrue(c.y() - c.height() / 2 >= GearLayout.GRID_TOP && c.y() + c.height() / 2 <= GearLayout.GRID_BOTTOM);
                assertFalse(b.contains(c.x(), c.y()), "cell inside its slot");
                assertTrue(c.x() > b.x(), "left column opens to the right");
                assertTrue(GearLayout.region(slot).contains(c.x(), c.y()));
            }
        }
    }

    @Test void expandedGridIsHitAndNavigableFromItsSlot() {
        Map<Integer, kim.biryeong.destiny.inventory.WeaponScreenLayout.Box> nodes =
                GearLayout.nodes(Stage.GEAR, GearSlot.ENERGY, 9, 0, false);
        var cell = GearLayout.storage(GearSlot.ENERGY, 4);
        assertEquals(GearLayout.STORAGE + 4, GearLayout.hit(nodes, cell.x(), cell.y()));
        int right = GearLayout.navigate(nodes, GearSlot.ENERGY.ordinal(), 1, 0);
        assertEquals(GearLayout.STORAGE + 3, right, "nearest cell in the same row");
        assertFalse(GearLayout.nodes(Stage.GEAR, null, 0, 0, false).containsKey(GearLayout.STORAGE));
        assertFalse(GearLayout.nodes(Stage.GEAR, null, 0, 0, false).containsKey(GearLayout.ARMORY));
    }

    @Test void statsKeepTooltipOrderAndDropHiddenZeros() {
        var stats = GearItems.stats(Map.of("4043523819", 92, "4284893193", 120, "1480404414", 0, "2715839340", 90, "3555269338", 0));
        assertEquals(java.util.List.of("분당 발사 수", "충격", "반동 방향"), stats.stream().map(GearItems.Stat::name).toList());
        assertFalse(stats.getFirst().bar());
    }

    @Test void wrapKeepsWidthAndLineLimit() {
        var lines = HudPainter.wrap("사격 속도는 느리지만 위력은 상당합니다. 오래된 설계지만 여전히 믿을 만하죠.", 18, 200, 2);
        assertEquals(2, lines.size());
        for (var l : lines) assertTrue(HudPainter.width(l, 18) <= 200 + 1, l);
        assertTrue(lines.getLast().endsWith("…"));
    }
    @Test void activityExitHasSeparateConfirmationAndNoEquipmentActions() {
        var normal = GearLayout.nodes(Stage.GEAR, null, 0, 0, false, 0, false);
        assertFalse(normal.containsKey(GearLayout.LEAVE));
        var live = GearLayout.nodes(Stage.GEAR, GearSlot.ENERGY, 9, 0, true, 10, true);
        var leave = GearLayout.leave();
        assertEquals(GearLayout.LEAVE, GearLayout.hit(live, leave.x(), leave.y()));
        for (var e : live.entrySet()) if (e.getKey() != GearLayout.LEAVE)
            assertFalse(e.getValue().contains(leave.x(), leave.y()), "leave does not overlap another action");
        var confirm = GearLayout.nodes(Stage.ACTIVITY_EXIT, null, 0, 0, false, 0, true);
        assertEquals(java.util.Set.of(GearLayout.BACK, GearLayout.LEAVE_CONFIRM, GearLayout.CLOSE), confirm.keySet());
        assertEquals(-1, GearLayout.hit(confirm, leave.x(), leave.y()), "repeat click at entry cannot confirm");
        var cancel = GearLayout.exitCancel(); var accept = GearLayout.exitConfirm();
        assertEquals(GearLayout.BACK, GearLayout.hit(confirm, cancel.x(), cancel.y()));
        assertEquals(GearLayout.LEAVE_CONFIRM, GearLayout.hit(confirm, accept.x(), accept.y()));
        assertFalse(cancel.contains(accept.x(), accept.y()));
    }

}
