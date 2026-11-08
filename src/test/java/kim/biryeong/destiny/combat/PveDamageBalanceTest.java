package kim.biryeong.destiny.combat;

import kim.biryeong.destiny.weapon.AmmoGeneration.Kind;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertEquals;

class PveDamageBalanceTest {
    @Test void requestedPveDamageMultipliers() {
        assertEquals(15f, PveDamageBalance.scale(10, Kind.PRIMARY, false));
        assertEquals(40f, PveDamageBalance.scale(10, Kind.SPECIAL, false));
        assertEquals(60f, PveDamageBalance.scale(10, Kind.HEAVY, false));
        assertEquals(30f, PveDamageBalance.scale(10, Kind.ABILITY, false));
        assertEquals(100f, PveDamageBalance.scale(10, Kind.SUPER, false));
    }

    @Test void pvpAndOtherDamageKindsRemainUnchanged() {
        for (Kind kind : Kind.values())
            assertEquals(10f, PveDamageBalance.scale(10, kind, true));
        for (Kind kind : new Kind[]{Kind.GLAIVE_MELEE})
            assertEquals(10f, PveDamageBalance.scale(10, kind, false));
    }
}
