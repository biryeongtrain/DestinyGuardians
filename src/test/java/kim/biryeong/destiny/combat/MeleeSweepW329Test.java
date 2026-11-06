package kim.biryeong.destiny.combat;

import kim.biryeong.destiny.weapon.SwordArc;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class MeleeSweepW329Test {
    @Test void yawSweepCoversBothSidesButCannotReachBehindOrAboveItsBound() {
        assertTrue(MeleeSweep.inside(1,0,2,0,1.5,3.5,.3,1.8));
        assertTrue(MeleeSweep.inside(1,0,2,0,-1.5,3.5,.3,1.8));
        assertFalse(MeleeSweep.inside(1,0,-.1,0,0,3.5,.3,1.8));
        assertFalse(MeleeSweep.inside(1,0,3.51,0,0,3.5,.3,1.8));
        assertFalse(MeleeSweep.inside(1,0,1,1.81,0,3.5,.3,1.8));
    }
    @Test void explicitSpinMayHitBehindButStillHasFiniteRangeAndHeight() {
        assertTrue(MeleeSweep.inside(1,0,-2,0,0,3,-1,1.8));
        assertFalse(MeleeSweep.inside(1,0,-3.1,0,0,3,-1,1.8));
        assertFalse(MeleeSweep.inside(1,0,-2,2,0,3,-1,1.8));
    }
    @Test void malformedSweepFailsClosedAndGroundAirTuningIsExplicit() {
        for(double bad:new double[]{Double.NaN,Double.POSITIVE_INFINITY,Double.NEGATIVE_INFINITY}) {
            assertFalse(MeleeSweep.inside(1,0,bad,0,0,3,.3,1.8));
            assertFalse(MeleeSweep.inside(1,0,1,0,0,bad,.3,1.8));
        }
        assertFalse(MeleeSweep.inside(0,0,1,0,0,3,.3,1.8));
        assertFalse(MeleeSweep.inside(1,0,1,0,0,9,.3,1.8));
        assertEquals(2,SwordArc.attackStep(true));
        assertEquals(5,SwordArc.attackStep(false));
    }
}
