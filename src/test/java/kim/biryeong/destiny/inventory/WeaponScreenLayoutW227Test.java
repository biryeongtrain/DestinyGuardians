package kim.biryeong.destiny.inventory;

import org.junit.jupiter.api.Test;

import java.util.ArrayDeque;
import java.util.HashSet;
import java.util.Set;

import static org.junit.jupiter.api.Assertions.*;

/** Pure reference-canvas and focus tests: no server, registry, game bootstrap, or client required. */
class WeaponScreenLayoutW227Test {
    private static final int[][] DIRECTIONS = {{-1, 0}, {1, 0}, {0, -1}, {0, 1}};
    private static final float[][] CENTRES = {
            {240, 360}, {240, 540}, {240, 720},
            {540, 360}, {720, 360}, {900, 360},
            {540, 540}, {720, 540}, {900, 540},
            {540, 720}, {720, 720}, {900, 720},
            {540, 860}, {900, 860}, {1740, 112},
            {1450, 112}, {1280, 920}, {1600, 920}, {720, 925}, {1440, 858}
    };

    @Test void publishedRenderBoxesMapToTheirOwnHitTargets() {
        assertTrue(WeaponScreenLayout.NODE_COUNT >= CENTRES.length);
        for (int node = 0; node < CENTRES.length; node++) {
            // Renderer uses these exact bounds for bases, all four frame edges, and focus.
            var box = WeaponScreenLayout.bounds(node);
            assertEquals(CENTRES[node][0], box.x(), "native cursor X for " + node);
            assertEquals(CENTRES[node][1], box.y(), "native cursor Y for " + node);
            assertEquals(node, WeaponScreenLayout.hit(box.x(), box.y(), true));
            assertTrue(box.x() - box.width() / 2 >= 0);
            assertTrue(box.x() + box.width() / 2 <= 1920);
            assertTrue(box.y() - box.height() / 2 >= 0);
            assertTrue(box.y() + box.height() / 2 <= 1080);
            if (node < 12) {
                assertEquals(156f, box.width());
                assertEquals(box.width(), box.height(), "equipment icons are squares");
            }
        }
    }

    @Test void paintedEdgesAndCornersAreInclusiveButImmediatelyOutsideMisses() {
        for (int node = 0; node < CENTRES.length; node++) {
            var b = WeaponScreenLayout.bounds(node);
            float left = b.x() - b.width() / 2, right = b.x() + b.width() / 2;
            float top = b.y() - b.height() / 2, bottom = b.y() + b.height() / 2;
            float[][] edges = {{left, b.y()}, {right, b.y()}, {b.x(), top}, {b.x(), bottom},
                    {left, top}, {right, top}, {left, bottom}, {right, bottom}};
            for (float[] point : edges) assertEquals(node, WeaponScreenLayout.hit(point[0], point[1], true));
            assertEquals(-1, WeaponScreenLayout.hit(Math.nextDown(left), b.y(), true));
            assertEquals(-1, WeaponScreenLayout.hit(Math.nextUp(right), b.y(), true));
            assertEquals(-1, WeaponScreenLayout.hit(b.x(), Math.nextDown(top), true));
            assertEquals(-1, WeaponScreenLayout.hit(b.x(), Math.nextUp(bottom), true));
        }
    }

    @Test void backgroundGapsAndOffCanvasPointerAreNotControls() {
        float[][] misses = {{0, 0}, {1920, 1080}, {960, 0}, {400, 540}, {630, 360},
                {720, 860}, {1440, 540}, {-1, 360}, {1921, 360}, {540, -1}, {540, 1081}};
        for (float[] point : misses) assertEquals(-1, WeaponScreenLayout.hit(point[0], point[1], true));
        for (float invalid : new float[]{Float.NaN, Float.POSITIVE_INFINITY, Float.NEGATIVE_INFINITY}) {
            assertEquals(-1, WeaponScreenLayout.hit(invalid, 360));
            assertEquals(-1, WeaponScreenLayout.hit(240, invalid));
            assertEquals(-1, WeaponScreenLayout.hit(invalid, invalid));
        }
    }

    @Test void gridIsRowMajorAndNavigationPreservesRowsAndColumns() {
        for (int row = 0; row < 3; row++) for (int col = 0; col < 3; col++) {
            int node = 3 + row * 3 + col;
            var b = WeaponScreenLayout.bounds(node);
            assertEquals(540f + 180 * col, b.x());
            assertEquals(360f + 180 * row, b.y());
            if (col > 0) assertEquals(node - 1, WeaponScreenLayout.navigate(node, -1, 0, true));
            if (col < 2) assertEquals(node + 1, WeaponScreenLayout.navigate(node, 1, 0, true));
            if (row > 0) assertEquals(node - 3, WeaponScreenLayout.navigate(node, 0, -1, true));
            if (row < 2) assertEquals(node + 3, WeaponScreenLayout.navigate(node, 0, 1, true));
        }
        for (int slot = 0; slot < 3; slot++) {
            assertEquals(3 + 3 * slot, WeaponScreenLayout.navigate(slot, 1, 0, true));
            assertEquals(slot, WeaponScreenLayout.navigate(3 + 3 * slot, -1, 0, true));
        }
    }

    @Test void everyControlIsReachableFromEveryOtherControlWithoutAFocusTrap() {
        // Includes empty candidate cells and disabled page endpoints: neither traps keyboard focus.
        for (int start = 0; start < CENTRES.length; start++) {
            Set<Integer> visited = new HashSet<>();
            ArrayDeque<Integer> queue = new ArrayDeque<>();
            visited.add(start);
            queue.add(start);
            while (!queue.isEmpty()) {
                int current = queue.remove();
                for (int[] direction : DIRECTIONS) {
                    int next = WeaponScreenLayout.navigate(current, direction[0], direction[1], true);
                    assertTrue(next >= 0 && next < WeaponScreenLayout.NODE_COUNT);
                    if (visited.add(next)) queue.add(next);
                }
            }
            assertEquals(CENTRES.length, visited.size(), "unreachable from " + start + ": " + visited);
        }
    }

    @Test void navigationIsDeterministicAndClampsAtOuterBoundaries() {
        assertEquals(0, WeaponScreenLayout.navigate(0, -1, 0, true));
        assertEquals(WeaponScreenLayout.CLOSE, WeaponScreenLayout.navigate(WeaponScreenLayout.CLOSE, 0, -1, true));
        assertEquals(WeaponScreenLayout.CLOSE, WeaponScreenLayout.navigate(WeaponScreenLayout.CLOSE, 1, 0, true));
        assertEquals(WeaponScreenLayout.PREVIOUS, WeaponScreenLayout.navigate(9, 0, 1, true));
        assertEquals(WeaponScreenLayout.NEXT, WeaponScreenLayout.navigate(11, 0, 1, true));
        assertEquals(0, WeaponScreenLayout.navigate(-1, 0, 0, true));
        assertEquals(0, WeaponScreenLayout.navigate(Integer.MIN_VALUE, 0, 0, true));
        assertEquals(3, WeaponScreenLayout.navigate(999, 1, 0, true));
        for (int node = 0; node < CENTRES.length; node++) {
            assertEquals(node, WeaponScreenLayout.navigate(node, 0, 0, true));
            for (int[] direction : DIRECTIONS) {
                int next = WeaponScreenLayout.navigate(node, direction[0], direction[1], true);
                for (int i = 0; i < 4; i++) assertEquals(next, WeaponScreenLayout.navigate(node, direction[0], direction[1], true));
            }
            assertEquals(WeaponScreenLayout.navigate(node, 1, 0, true), WeaponScreenLayout.navigate(node, 1, 1, true));
            assertEquals(WeaponScreenLayout.navigate(node, 0, -1, true), WeaponScreenLayout.navigate(node, 1, -2, true));
            assertEquals(WeaponScreenLayout.navigate(node, -1, 0, true),
                    WeaponScreenLayout.navigate(node, Integer.MIN_VALUE, Integer.MAX_VALUE, true));
        }
        assertThrows(IllegalArgumentException.class, () -> WeaponScreenLayout.bounds(-1));
        assertThrows(IllegalArgumentException.class, () -> WeaponScreenLayout.bounds(WeaponScreenLayout.NODE_COUNT));
    }

    @Test void boxesRejectNonfiniteOrDegenerateRenderGeometry() {
        assertThrows(IllegalArgumentException.class, () -> new WeaponScreenLayout.Box(Float.NaN, 0, 10, 10));
        assertThrows(IllegalArgumentException.class, () -> new WeaponScreenLayout.Box(0, Float.POSITIVE_INFINITY, 10, 10));
        assertThrows(IllegalArgumentException.class, () -> new WeaponScreenLayout.Box(0, 0, Float.NaN, 10));
        assertThrows(IllegalArgumentException.class, () -> new WeaponScreenLayout.Box(0, 0, 10, Float.NEGATIVE_INFINITY));
        assertThrows(IllegalArgumentException.class, () -> new WeaponScreenLayout.Box(0, 0, 0, 10));
        assertThrows(IllegalArgumentException.class, () -> new WeaponScreenLayout.Box(0, 0, 10, -1));
    }
}
