package kim.biryeong.destiny.fx;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;
final class BowTrailVisibilityW95Test {
    @Test void atEyeIsHidden() { assertTrue(BowTrailVisibility.hidesOwnerSample(0)); }
    @Test void innerSamplesAreHidden() { for(double d:new double[]{.35,.7,1.05}) assertTrue(BowTrailVisibility.hidesOwnerSample(d*d)); }
    @Test void boundaryIsKept() { assertFalse(BowTrailVisibility.hidesOwnerSample(1.25*1.25)); }
    @Test void nextLatticeSampleIsKept() { assertFalse(BowTrailVisibility.hidesOwnerSample(1.4*1.4)); }
    @Test void nearBoundaryUsesDeclaredStrictPolicy() { assertTrue(BowTrailVisibility.hidesOwnerSample(Math.nextDown(1.5625))); assertFalse(BowTrailVisibility.hidesOwnerSample(Math.nextUp(1.5625))); }
    @Test void negativeInvalidDistanceDoesNotHide() { assertFalse(BowTrailVisibility.hidesOwnerSample(-1)); }
    @Test void nonfiniteDoesNotHide() { for(double d:new double[]{Double.NaN,Double.POSITIVE_INFINITY,Double.NEGATIVE_INFINITY})assertFalse(BowTrailVisibility.hidesOwnerSample(d)); }
    @Test void radiusIsProvisionalVisualOnlyPolicy() { assertEquals(1.25,BowTrailVisibility.OWNER_RADIUS); }
}
