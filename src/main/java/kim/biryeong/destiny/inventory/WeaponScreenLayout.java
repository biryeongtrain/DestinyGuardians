package kim.biryeong.destiny.inventory;

/**
 * One source of geometry for the renderer and controller. Coordinates are reference pixels on the
 * CENTER-aligned 1920 x 1080 DisplayHud canvas: (960, 540) is screen centre, +Y points down.
 * Boxes store their CENTRES, never their upper-left corners. Page numbers do not affect geometry.
 */
public final class WeaponScreenLayout {
    public static final int NODE_COUNT = 29;
    public static final int PREVIOUS = 12;
    public static final int NEXT = 13;
    public static final int CLOSE = 14;
    public static final int TEST_ARMORY = 15;
    public static final int DAMAGE_PERKS = 16;
    public static final int UTILITY_PERKS = 17;
    public static final int BACK_WEAPONS = 18;
    public static final int CONFIRM_LOADOUT = 19;
    public static final int CHARACTER_TAB = 20;
    public static final int LOADOUT_TAB = 21;
    public static final int CLASS = 22;
    public static final int SUBCLASS = 23;
    public static final int GRENADE = 24;
    public static final int MELEE = 25;
    public static final int CLASS_ABILITY = 26;
    public static final int SUPER = 27;
    public static final int BACK_CHARACTER = 28;

    public record Box(float x, float y, float width, float height) {
        public Box {
            if (!Float.isFinite(x) || !Float.isFinite(y) || !Float.isFinite(width)
                    || !Float.isFinite(height) || width <= 0 || height <= 0)
                throw new IllegalArgumentException("A screen box must be finite and have positive dimensions");
        }

        /** All four painted edges are clickable; the layout leaves gaps between controls. */
        public boolean contains(float px, float py) {
            return Float.isFinite(px) && Float.isFinite(py)
                    && px >= x - width / 2 && px <= x + width / 2
                    && py >= y - height / 2 && py <= y + height / 2;
        }
    }

    private static final Box[] BOXES = {
            new Box(240, 360, 156, 156),
            new Box(240, 540, 156, 156),
            new Box(240, 720, 156, 156),
            new Box(540, 360, 156, 156), new Box(720, 360, 156, 156), new Box(900, 360, 156, 156),
            new Box(540, 540, 156, 156), new Box(720, 540, 156, 156), new Box(900, 540, 156, 156),
            new Box(540, 720, 156, 156), new Box(720, 720, 156, 156), new Box(900, 720, 156, 156),
            new Box(540, 860, 156, 48), new Box(900, 860, 156, 48),
            new Box(1740, 112, 152, 52),
            new Box(1450, 112, 280, 52),
            new Box(1280, 920, 280, 44), new Box(1600, 920, 280, 44),
            new Box(720, 925, 220, 44),
            new Box(1440, 858, 560, 44),
            new Box(890, 112, 186, 52), new Box(1130, 112, 186, 52),
            new Box(330, 360, 340, 156), new Box(800, 360, 340, 156),
            new Box(330, 540, 340, 156), new Box(800, 540, 340, 156),
            new Box(330, 720, 340, 156), new Box(800, 720, 340, 156),
            new Box(720, 925, 220, 44)
    };

    private WeaponScreenLayout() { }

    public static Box bounds(int node) {
        if (node < 0 || node >= NODE_COUNT) throw new IllegalArgumentException("Unknown equipment node: " + node);
        return BOXES[node];
    }

    /** Legacy weapon geometry (0..19); live callers supply a stage to include character controls. */
    public static int hit(float x, float y) {
        return hit(x, y, true);
    }

    /** Compatibility geometry: false excludes the back and confirmation buttons. */
    public static int hit(float x, float y, boolean perkMode) {
        for (int node = 0; node < NODE_COUNT; node++)
            if (visible(node, perkMode) && BOXES[node].contains(x, y)) return node;
        return -1;
    }

    public static boolean visible(int node, boolean perkMode) {
        return node >= 0 && node <= CONFIRM_LOADOUT
                && (perkMode || (node != BACK_WEAPONS && node != CONFIRM_LOADOUT));
    }

    /** Live wizard geometry. A missing/unknown stage safely exposes only the loadout controls. */
    public static boolean visible(int node, String stage) {
        if (node < 0 || node >= NODE_COUNT) return false;
        if (node == CHARACTER_TAB || node == LOADOUT_TAB || node == CLOSE) return true;
        if ("CHARACTER".equals(stage)) return node >= CLASS && node <= SUPER;
        if ("CHARACTER_OPTIONS".equals(stage))
            return (node >= 3 && node <= NEXT) || node == BACK_CHARACTER;
        if (node < 3 || node == CLOSE) return true;
        return switch (stage == null ? "LOADOUT" : stage) {
            case "FAMILY", "WEAPON" -> (node >= 3 && node <= NEXT) || node == BACK_WEAPONS;
            case "PERKS" -> (node >= 3 && node <= NEXT) || node == DAMAGE_PERKS
                    || node == UTILITY_PERKS || node == BACK_WEAPONS || node == CONFIRM_LOADOUT;
            default -> node == TEST_ARMORY;
        };
    }

    public static int hit(float x, float y, String stage) {
        for (int node = 0; node < NODE_COUNT; node++)
            if (visible(node, stage) && BOXES[node].contains(x, y)) return node;
        return -1;
    }

    /**
     * Directional nearest neighbour in the requested half-plane. Perpendicular distance is weighted
     * so rows/columns remain predictable; ties use the stable node order. Screen edges clamp.
     * Invalid focus recovers to node zero before looking at any bounds (pointer focus may be -1).
     * Diagonal input resolves to its dominant axis, with horizontal winning an exact tie.
     */
    public static int navigate(int current, int dx, int dy) {
        return navigate(current, dx, dy, true);
    }

    /** Hidden focus recovers just like invalid focus; hidden nodes cannot be navigation candidates. */
    public static int navigate(int current, int dx, int dy, boolean perkMode) {
        return navigateVisible(current, dx, dy, node -> visible(node, perkMode));
    }

    public static int navigate(int current, int dx, int dy, String stage) {
        return navigateVisible(current, dx, dy, node -> visible(node, stage));
    }

    /** Stage-specific recovery is also shared by controller refresh and the rendered cursor. */
    public static int fallback(String stage) {
        return "CHARACTER".equals(stage) ? CLASS : "CHARACTER_OPTIONS".equals(stage) ? 3 : 0;
    }

    private static int navigateVisible(int current, int dx, int dy, java.util.function.IntPredicate visible) {
        int start = current;
        if (!visible.test(start)) {
            // Content comes before tabs/close even when those controls have a lower node number.
            start = visible.test(CLASS) ? CLASS : visible.test(0) ? 0 : visible.test(3) ? 3 : CLOSE;
        }
        if (dx == 0 && dy == 0) return start;
        boolean horizontal = Math.abs((long) dx) >= Math.abs((long) dy);
        int direction = Integer.signum(horizontal ? dx : dy);
        Box origin = BOXES[start];
        int best = start;
        double score = Double.POSITIVE_INFINITY;
        for (int node = 0; node < NODE_COUNT; node++) {
            if (node == start || !visible.test(node)) continue;
            Box candidate = BOXES[node];
            double forward = (horizontal ? candidate.x - origin.x : candidate.y - origin.y) * direction;
            if (forward <= 0) continue;
            double perpendicular = horizontal ? candidate.y - origin.y : candidate.x - origin.x;
            double distance = forward * forward + 8 * perpendicular * perpendicular;
            if (distance < score) { score = distance; best = node; }
        }
        return best;
    }
}
