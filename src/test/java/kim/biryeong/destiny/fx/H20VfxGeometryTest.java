package kim.biryeong.destiny.fx;

import org.junit.jupiter.api.Test;

import java.util.List;

import static org.junit.jupiter.api.Assertions.*;

class H20VfxGeometryTest {
    private static void bounded(List<H20VfxGeometry.Point> points, int maximum) {
        assertTrue(points.size() <= maximum);
        for (var p : points) {
            assertTrue(Double.isFinite(p.right()) && Double.isFinite(p.up()) && Double.isFinite(p.forward()));
            assertTrue(Math.abs(p.right()) < 1 && Math.abs(p.up()) < 1 && Math.abs(p.forward()) < 1);
        }
    }

    @Test void progressRejectsNonfiniteAndClampsOvershoot() {
        assertEquals(0, H20VfxGeometry.progress(Double.NaN));
        assertEquals(0, H20VfxGeometry.progress(Double.POSITIVE_INFINITY));
        assertEquals(0, H20VfxGeometry.progress(-1));
        assertEquals(1, H20VfxGeometry.progress(2));
        assertEquals(.5, H20VfxGeometry.progress(.5));
    }

    @Test void materializeGrowsPairedEdgesRatherThanFillingACloud() {
        assertEquals(2, H20VfxGeometry.bow(0, 0, true).size());
        assertEquals(10, H20VfxGeometry.bow(8, 0, true).size());
        for (int age = 0; age < 12; age++) for (var p : H20VfxGeometry.bow(age, 0, true)) {
            assertTrue(Math.abs(p.up()) >= .18, "Empty nock/face lane between limb edges");
            assertTrue(Math.abs(p.right()) <= .04, "Narrow edge, not a broad billboard");
        }
    }

    @Test void chargingMotesConvergeAndNockMovesBack() {
        var early = H20VfxGeometry.bow(4, .1, false);
        var late = H20VfxGeometry.bow(4, 1, false);
        assertEquals(10, late.size());
        assertTrue(Math.abs(late.get(3).up()) < Math.abs(early.get(3).up()));
        assertTrue(late.get(3).forward() < early.get(3).forward());
        bounded(late, 10);
    }

    @Test void allStagesAreSmallAndHaveFiniteDeterministicPointBudgets() {
        for (int age = 0; age <= 420; age++) {
            bounded(H20VfxGeometry.bow(age, .8, true), 14);
            bounded(H20VfxGeometry.staff(age), 8);
            bounded(H20VfxGeometry.gun(age), 6);
            // Runtime release only spans ages 0..6.
            bounded(H20VfxGeometry.release(age % 7), 8);
            bounded(H20VfxGeometry.anchor(age, 200 - age), 12);
        }
    }

    @Test void releaseIsSplitOutsideCentralAimLane() {
        var initial = H20VfxGeometry.release(0);
        var finalFrame = H20VfxGeometry.release(6);
        assertEquals(8, initial.size());
        for (var p : finalFrame) assertTrue(Math.abs(p.right()) >= .15);
        assertTrue(finalFrame.getFirst().right() < initial.getFirst().right());
    }

    @Test void anchorEnvelopeGrowsThenRetractsWithinSubBlockRadius() {
        var start = H20VfxGeometry.anchor(0, 160).get(2);
        var held = H20VfxGeometry.anchor(6, 154).get(2);
        var ending = H20VfxGeometry.anchor(159, 1).get(2);
        double initialRadius = Math.hypot(start.right(), start.forward());
        double fullRadius = Math.hypot(held.right(), held.forward());
        assertEquals(.74, fullRadius, 1e-9);
        assertTrue(initialRadius < fullRadius);
        assertTrue(Math.hypot(ending.right(), ending.forward()) < initialRadius);
    }
}
