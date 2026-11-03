package kim.biryeong.destiny.campaign.presentation;

import kim.biryeong.destiny.strike.devils.DevilsPlan;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class DevilsTransportSelectionTest {
    @Test void shipsServeOutdoorFallenReinforcementsOnly() {
        for (var pack : DevilsPlan.packs()) for (var slot : pack.slots()) {
            boolean expected = (slot.zone() == DevilsPlan.Zone.BL || slot.zone() == DevilsPlan.Zone.SP
                    || pack.id().equals("RY-approach-3"))
                    && switch (slot.kind()) { case DREG, VANDAL, MARAUDER, CAPTAIN -> true; default -> false; };
            assertEquals(expected, DevilsPresentation.deliveredBySkiff(slot), slot.id());
        }
        for (var special : DevilsPlan.specials()) assertFalse(DevilsPresentation.deliveredBySkiff(special));
    }
}
