package kim.biryeong.destiny.inventory.gear;

import kim.biryeong.destiny.inventory.WeaponScreenLayout.Box;

import java.util.LinkedHashMap;
import java.util.Map;

/**
 * Geometry of the gear screen on the 1920 x 1080 CENTER canvas (box centres, +Y down). Pure: the renderer,
 * pointer hit test and keyboard navigation all read the same boxes for the same state.
 */
public final class GearLayout {
    public static final int SLOT_COUNT = 10, STORAGE = 10, STORAGE_COUNT = 9, CLOSE = 19, ARMORY = 20,
            FIELD = 21, FIELD_COUNT = 7, BACK = 28,
            ENGRAM = 29, ENGRAM_COUNT = 10, NODE_COUNT = 39;
    public static final float SLOT = 120, CELL = 104, STEP = 116;
    static final float LEFT_X = 300, RIGHT_X = 1620, TOP_Y = 280, ROW = 140;
    /** Vertical band in which a storage grid may sit. */
    static final float GRID_TOP = 200, GRID_BOTTOM = 940;

    public enum Stage { GEAR, DETAIL, SUBCLASS, OPTIONS }

    private GearLayout() { }

    public static Box slot(GearSlot slot) {
        int row = slot.ordinal() % 5;
        return new Box(slot.left() ? LEFT_X : RIGHT_X, TOP_Y + row * ROW, SLOT, SLOT);
    }

    /** Storage cell {@code index} (0..8, row-major) beside an expanded slot; mirrors for the right column. */
    public static Box storage(GearSlot slot, int index) {
        Box s = slot(slot);
        int col = index % 3, row = index / 3;
        float first = slot.left() ? s.x() + SLOT / 2 + 20 + CELL / 2 : s.x() - SLOT / 2 - 20 - CELL / 2;
        float x = first + (slot.left() ? 1 : -1) * col * STEP;
        float centre = Math.clamp(s.y(), GRID_TOP + STEP + CELL / 2, GRID_BOTTOM - STEP - CELL / 2);
        return new Box(x, centre + (row - 1) * STEP, CELL, CELL);
    }

    /** Slot plus its open grid, padded: the pointer may cross the gap without collapsing the grid. */
    public static Box region(GearSlot slot) {
        Box s = slot(slot), a = storage(slot, 0), b = storage(slot, 8);
        float left = Math.min(s.x() - s.width() / 2, Math.min(a.x(), b.x()) - CELL / 2) - 12;
        float right = Math.max(s.x() + s.width() / 2, Math.max(a.x(), b.x()) + CELL / 2) + 12;
        float top = Math.min(s.y() - SLOT / 2, a.y() - CELL / 2) - 12, bottom = Math.max(s.y() + SLOT / 2, b.y() + CELL / 2) + 12;
        return new Box((left + right) / 2, (top + bottom) / 2, right - left, bottom - top);
    }

    /** Subclass screen: ability fields down the left, option grid in the centre. */
    public static Box field(int index) { return new Box(330, 250 + index * 104, 380, 92); }
    public static Box option(int index) { return new Box(760 + (index % 3) * 200, 330 + (index / 3) * 200, 184, 184); }

    /** Held engram {@code index} (0..9): Destiny's engram row, top right of the character screen. */
    public static Box engram(int index) { return new Box(1150 + index * 58, 92, 50, 50); }

    public static Box close() { return new Box(1760, 1022, 200, 48); }
    public static Box armory() { return new Box(1530, 1022, 220, 48); }
    public static Box back() { return new Box(160, 1022, 200, 48); }

    /** Every visible interactive node for a state, in stable order. */
    public static Map<Integer, Box> nodes(Stage stage, GearSlot expanded, int storageCount, int optionCount, boolean armory) {
        return nodes(stage, expanded, storageCount, optionCount, armory, 0);
    }

    public static Map<Integer, Box> nodes(Stage stage, GearSlot expanded, int storageCount, int optionCount, boolean armory, int engrams) {
        var out = new LinkedHashMap<Integer, Box>();
        switch (stage) {
            case GEAR -> {
                for (var slot : GearSlot.values()) out.put(slot.ordinal(), slot(slot));
                if (expanded != null && expanded.weapon() != null)
                    for (int i = 0; i < Math.min(STORAGE_COUNT, storageCount); i++) out.put(STORAGE + i, storage(expanded, i));
                if (armory) out.put(ARMORY, armory());
                for (int i = 0; i < Math.min(ENGRAM_COUNT, engrams); i++) out.put(ENGRAM + i, engram(i));
            }
            case DETAIL -> out.put(BACK, back());
            case SUBCLASS -> { for (int i = 0; i < FIELD_COUNT; i++) out.put(FIELD + i, field(i)); out.put(BACK, back()); }
            case OPTIONS -> {
                for (int i = 0; i < FIELD_COUNT; i++) out.put(FIELD + i, field(i));
                for (int i = 0; i < Math.min(STORAGE_COUNT, optionCount); i++) out.put(STORAGE + i, option(i));
                out.put(BACK, back());
            }
        }
        out.put(CLOSE, close());
        return out;
    }

    public static int hit(Map<Integer, Box> nodes, float x, float y) {
        for (var e : nodes.entrySet()) if (e.getValue().contains(x, y)) return e.getKey();
        return -1;
    }

    /** Directional nearest neighbour (perpendicular distance weighted), dominant axis wins. */
    public static int navigate(Map<Integer, Box> nodes, int current, int dx, int dy) {
        if (nodes.isEmpty()) return -1;
        int start = nodes.containsKey(current) ? current : nodes.keySet().iterator().next();
        if (dx == 0 && dy == 0) return start;
        boolean horizontal = Math.abs(dx) >= Math.abs(dy);
        int direction = Integer.signum(horizontal ? dx : dy);
        Box origin = nodes.get(start);
        int best = start; double score = Double.POSITIVE_INFINITY;
        for (var e : nodes.entrySet()) {
            if (e.getKey() == start) continue;
            Box c = e.getValue();
            double forward = (horizontal ? c.x() - origin.x() : c.y() - origin.y()) * direction;
            if (forward <= 0) continue;
            double side = horizontal ? c.y() - origin.y() : c.x() - origin.x();
            double d = forward * forward + 8 * side * side;
            if (d < score) { score = d; best = e.getKey(); }
        }
        return best;
    }
}
