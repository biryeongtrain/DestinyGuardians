package kim.biryeong.destiny.weapon;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

/** Authored geometry invariants; no claim these Minecraft angles/ranges match measured Destiny curves. */
class SwordArcW52Test {
    private static boolean light(double x,double y,double z) {
        return SwordArc.inside(1,0,x,y,z,SwordArc.LIGHT_RANGE,SwordArc.LIGHT_COS,SwordArc.LIGHT_HEIGHT);
    }
    private static boolean lunge(double x,double y,double z) {
        return SwordArc.inside(1,0,x,y,z,SwordArc.LUNGE_RANGE,SwordArc.LUNGE_COS,SwordArc.LUNGE_HEIGHT);
    }
    @Test void lightAdmitsBothSideEnemiesButExcludesRearAndNinetyDegrees() {
        assertTrue(light(2,0,1.5));assertTrue(light(2,0,-1.5));
        assertFalse(light(-1,0,0));assertFalse(light(0,0,2));assertFalse(light(0,0,-2));
    }
    @Test void lightRangeAndHeightBoundariesAreInclusiveWithoutUnlimitedReach() {
        assertTrue(light(3.5,1.5,0));assertTrue(light(3.5,-1.5,0));
        assertFalse(light(3.5001,0,0));assertFalse(light(2,1.5001,0));assertFalse(light(2,-1.5001,0));
    }
    @Test void halfArcBoundaryIsConsistentOnEitherSide() {
        for(double sign:new double[]{-1,1}) {
            double a=Math.toRadians(65);
            assertTrue(light(2*Math.cos(a),0,sign*2*Math.sin(a)));
            a=Math.toRadians(65.01);
            assertFalse(light(2*Math.cos(a),0,sign*2*Math.sin(a)));
        }
    }
    @Test void lungeAcquisitionIsNarrowerThanTheSlashCone() {
        double a=Math.toRadians(50),x=3*Math.cos(a),z=3*Math.sin(a);
        assertTrue(light(x,0,z));assertFalse(lunge(x,0,z));
        a=Math.toRadians(30);assertTrue(lunge(4*Math.cos(a),0,4*Math.sin(a)));
        assertFalse(lunge(-2,0,0));
    }
    @Test void lungeAcquisitionCannotExceedReachPlusAuthoredMovement() {
        assertEquals(SwordArc.LIGHT_RANGE+SwordArc.LUNGE_MAX,SwordArc.LUNGE_RANGE,1e-10);
        assertTrue(lunge(5.3,1.25,0));assertFalse(lunge(5.3001,0,0));assertFalse(lunge(3,1.2501,0));
    }
    @Test void contactAtTheSameHorizontalPointHasNoUndefinedAngle() {
        assertTrue(light(0,0,0));assertTrue(light(0,1,0));assertFalse(light(0,2,0));
        assertFalse(SwordArc.inside(0,0,0,0,0,3,.5,1));
    }
    @Test void directionNormalizationDoesNotChangeSelection() {
        assertEquals(light(2,0,1),SwordArc.inside(100,0,2,0,1,3.5,SwordArc.LIGHT_COS,1.5));
        assertTrue(SwordArc.inside(0,-1,0,0,-3,3.5,SwordArc.LIGHT_COS,1.5));
        assertFalse(SwordArc.inside(0,-1,0,0,3,3.5,SwordArc.LIGHT_COS,1.5));
    }
    @Test void nonfiniteAndUnsafeParametersAlwaysFailClosed() {
        for(double bad:new double[]{Double.NaN,Double.POSITIVE_INFINITY,Double.NEGATIVE_INFINITY}) {
            assertFalse(SwordArc.inside(bad,0,2,0,0,3.5,.5,1.5));
            assertFalse(SwordArc.inside(1,bad,2,0,0,3.5,.5,1.5));
            assertFalse(SwordArc.inside(1,0,bad,0,0,3.5,.5,1.5));
            assertFalse(SwordArc.inside(1,0,2,bad,0,3.5,.5,1.5));
            assertFalse(SwordArc.inside(1,0,2,0,bad,3.5,.5,1.5));
            assertFalse(SwordArc.inside(1,0,2,0,0,bad,.5,1.5));
            assertFalse(SwordArc.inside(1,0,2,0,0,3.5,bad,1.5));
            assertFalse(SwordArc.inside(1,0,2,0,0,3.5,.5,bad));
        }
        assertFalse(light(Double.MAX_VALUE,0,Double.MAX_VALUE));
        assertFalse(SwordArc.inside(1,0,2,0,0,9,.5,1));
        assertFalse(SwordArc.inside(1,0,2,0,0,3,-.1,1));
        assertFalse(SwordArc.inside(1,0,2,0,0,3,.5,-1));
    }
    @Test void lungeStopAndMaximumDisplacementAreBounded() {
        for(double d:new double[]{-1,0,.4,1.1})assertEquals(0,SwordArc.lungeDistance(d));
        assertEquals(.9,SwordArc.lungeDistance(2),1e-10);
        assertEquals(1.8,SwordArc.lungeDistance(3),1e-10);
        for(double d:new double[]{5.3,100,Double.MAX_VALUE})assertEquals(1.8,SwordArc.lungeDistance(d));
        for(double d:new double[]{Double.NaN,Double.POSITIVE_INFINITY,Double.NEGATIVE_INFINITY})
            assertEquals(0,SwordArc.lungeDistance(d));
        assertTrue(SwordArc.MAX_HITS<=SwordArc.MAX_CANDIDATES&&SwordArc.MAX_CANDIDATES<=64);
    }
    @Test void mirroredEnemiesAndRotatedForwardVectorsHaveTheSamePolicy() {
        for(int angle=0;angle<=180;angle++) {
            double a=Math.toRadians(angle),x=3*Math.cos(a),z=3*Math.sin(a);
            assertEquals(light(x,0,z),light(x,0,-z));
            assertEquals(light(x,0,z),SwordArc.inside(0,1,-z,0,x,3.5,SwordArc.LIGHT_COS,1.5));
        }
    }
}
