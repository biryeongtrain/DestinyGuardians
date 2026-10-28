package kim.biryeong.destiny.inventory;

/**
 * One source of geometry for the renderer and controller. Coordinates are reference pixels on the
 * CENTER-aligned 1920 x 1080 DisplayHud canvas: (960, 540) is screen centre, +Y points down.
 * Boxes store their CENTRES, never their upper-left corners. Page numbers do not affect geometry.
 */
public final class WeaponScreenLayout {
    public static final int NODE_COUNT = 15;
    public static final int PREVIOUS = 12;
    public static final int NEXT = 13;
    public static final int CLOSE = 14;

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
            new Box(1740, 112, 152, 52)
    };

    private WeaponScreenLayout() { }

    public static Box bounds(int node) {
        if (node < 0 || node >= NODE_COUNT) throw new IllegalArgumentException("Unknown equipment node: " + node);
        return BOXES[node];
    }

    /** Returns -1 for the noninteractive canvas, including nonfinite pointer input. */
    public static int hit(float x, float y) {
        for (int node = 0; node < NODE_COUNT; node++) if (BOXES[node].contains(x, y)) return node;
        return -1;
    }

    /**
     * Directional nearest neighbour in the requested half-plane. Perpendicular distance is weighted
     * so rows/columns remain predictable; ties use the stable node order. Screen edges clamp.
     * Invalid focus recovers to node zero before looking at any bounds (pointer focus may be -1).
     * Diagonal input resolves to its dominant axis, with horizontal winning an exact tie.
     */
    public static int navigate(int current, int dx, int dy) {
        int start = current >= 0 && current < NODE_COUNT ? current : 0;
        if (dx == 0 && dy == 0) return start;
        boolean horizontal = Math.abs((long) dx) >= Math.abs((long) dy);
        int direction = Integer.signum(horizontal ? dx : dy);
        Box origin = BOXES[start];
        int best = start;
        double score = Double.POSITIVE_INFINITY;
        for (int node = 0; node < NODE_COUNT; node++) {
            if (node == start) continue;
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
