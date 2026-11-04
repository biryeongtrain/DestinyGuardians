package kim.biryeong.destiny.strike.devils;

import kim.biryeong.destiny.activity.presentation.ObjectiveGuide.Mode;
import kim.biryeong.destiny.strike.devils.DevilsDirector.Phase;
import net.minecraft.core.BlockPos;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;

class DevilsGuideTest {
    @Test void clearPhasesLeadToExitsAndPathMarkersExist() {
        assertEquals("RY.OUT", DevilsGuide.step(Phase.RY_CLEAR)[0]);
        assertEquals("RF.G", DevilsGuide.step(Phase.RF_DEVICE)[0]);
        assertEquals(Mode.COMBAT, DevilsGuide.step(Phase.RY_APPROACH)[1]);
        assertNull(DevilsGuide.step(Phase.RF_DEFENSE1));
        assertNull(DevilsGuide.step(Phase.SP_DAMAGE1));
        DevilsGuide.PATHS.forEach((zone, ids) -> ids.forEach(id ->
                assertNotNull(DevilsMaps.anchor(zone, id, BlockPos.ZERO), zone + " " + id)));
    }
}
