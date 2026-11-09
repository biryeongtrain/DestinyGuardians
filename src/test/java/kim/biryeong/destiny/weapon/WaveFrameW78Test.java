package kim.biryeong.destiny.weapon;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class WaveFrameW78Test {
    // Frozen pre-W327 roster assertions retain their original counts; new identities have separate coverage.
    private static boolean hit(double fx,double fz,double minX,double minY,double minZ,double maxX,double maxY,double maxZ) {
        return WaveFrameProfile.intersects(fx,fz,0,1,0,fx*2,1,fz*2,2,1.5,minX,minY,minZ,maxX,maxY,maxZ);
    }
    @Test void waveAndCompressedAreExactTwoSupportedEntries() {
        assertEquals(2,WaveFrameProfile.all().stream().filter(p -> !LegendaryWeapons.contains(p.id())).count());
        for(var entry:WeaponCatalog.all().stream().filter(e -> !LegendaryWeapons.contains(e.id())).toList())assertEquals(entry.id().equals("deafening_whisper")||entry.id().equals("dimensional_hypotrochoid"),WaveFrameProfile.of(entry).isPresent(),entry.id());
        for(var p:WaveFrameProfile.all()) {
            var entry=WeaponCatalog.find(p.id()).orElseThrow();
            assertEquals(WeaponCharacteristics.of(entry).bungieHash(),p.hash());
            assertTrue(p.intrinsicHash()>0);assertTrue(p.length()>3);assertTrue(p.width()>0);
        }
    }
    @Test void orientedStripHitsForwardButNotRadialRearAndSides() {
        assertTrue(hit(1,0,1,1,.1,1.6,2.8,.7));
        assertFalse(hit(1,0,-2,1,0,-1,2.8,.6));
        assertFalse(hit(1,0,1,1,1.01,1.6,2.8,1.61));
        assertFalse(hit(1,0,3,1,0,3.6,2.8,.6));
    }
    @Test void heightUsesActualAabbIntersectionNotFeetOnlyOrInfiniteCylinder() {
        assertTrue(hit(1,0,1,2.49,0,1.6,4,.6));
        assertFalse(hit(1,0,1,2.501,0,1.6,4,.6));
        assertFalse(hit(1,0,1,-2,0,1.6,.99,.6));
        assertTrue(hit(1,0,1,-.1,0,1.6,1.01,.6));
    }
    @Test void diagonalRectangleRejectsAxisAlignedBoundingCorner() {
        double d=Math.sqrt(.5);
        assertTrue(hit(d,d,.8,1,.8,1.1,2.8,1.1));
        // Inside the broad AABB but outside the actual diagonal strip's perpendicular axis.
        assertFalse(hit(d,d,-.65,1,1.8,-.5,2.8,1.95));
        assertTrue(hit(-d,-d,-1.1,1,-1.1,-.8,2.8,-.8));
    }
    @Test void allWorldAndOrientedSeparatingAxesAreUsed() {
        double d=Math.sqrt(.5);
        // Beyond the tip's forward plane although each x/z overlaps the broad box.
        assertFalse(hit(d,d,1.8,1,1.8,1.9,2.8,1.9));
        // Entity AABB overlaps the strip even if its center is outside lateral bounds.
        assertTrue(hit(1,0,.8,1,.95,1.4,2.8,1.55));
    }
    @Test void invalidGeometryIsRejectedWithoutNaNAdmission() {
        assertFalse(hit(Double.NaN,0,0,1,0,1,2,1));
        assertFalse(hit(2,0,0,1,0,1,2,1));
        assertFalse(hit(1,0,2,1,0,1,2,1));
        assertFalse(hit(1,0,0,Double.POSITIVE_INFINITY,0,1,2,1));
    }
    @Test void invalidProfilesCannotExpandCostOrTerrainWithoutBounds() {
        assertThrows(IllegalArgumentException.class,()->new WaveFrameProfile.Profile("x",1,1,Double.NaN,2,1,1.5,.6,1,.2f,1));
        assertThrows(IllegalArgumentException.class,()->new WaveFrameProfile.Profile("x",1,1,15,2,0,1.5,.6,1,.2f,1));
        assertThrows(IllegalArgumentException.class,()->new WaveFrameProfile.Profile("x",1,1,15,2,1,1.5,2,1,.2f,1));
    }
}
