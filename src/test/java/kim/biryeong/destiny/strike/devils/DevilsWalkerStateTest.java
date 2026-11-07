package kim.biryeong.destiny.strike.devils;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;
import static kim.biryeong.destiny.strike.devils.DevilsWalkerState.*;

class DevilsWalkerStateTest {
    @Test void sixLegsRemainIndependentAndOnlyOldestReturnsWhenAllSpent() {
        var boss = new DevilsWalkerState();
        boss.hit(Region.REAR_RIGHT, MAX_LEG * .25, null);
        for (Region leg : Region.values()) {
            if (!leg.leg()) continue;
            assertTrue(boss.hit(leg, 100, null).legBroken());
            for (int t = 0; t < STAGGER_TICKS + EXPOSED_TICKS + RECOVER_TICKS; t++) boss.tick();
            if (leg != Region.REAR_RIGHT) assertEquals(MAX_LEG * .75, boss.leg(Region.REAR_RIGHT));
        }
        assertEquals(Phase.ARMORED, boss.phase());
        assertEquals(MAX_LEG, boss.leg(Region.FRONT_LEFT));
        for (Region leg : Region.values()) if (leg.leg() && leg != Region.FRONT_LEFT) assertEquals(0, boss.leg(leg));
        assertEquals(MAX_CORE, boss.core());
    }
    @Test void exposureAndArmorUseSeparatePoolsWithoutDuplicateBalance() {
        var boss = new DevilsWalkerState();
        assertEquals(10, boss.hit(Region.HULL, 100, "a").applied());
        assertEquals(MAX_CORE - 10, boss.core());
        assertEquals(0, boss.hit(Region.FRONT_LEFT, 100, "a").applied());
        boss.tick();
        assertTrue(boss.hit(Region.FRONT_LEFT, 100, "a").legBroken());
        assertEquals(0, boss.hit(Region.CORE, 100, "b").applied());
        for (int t = 0; t < STAGGER_TICKS; t++) boss.tick();
        assertEquals(Phase.EXPOSED, boss.phase());
        assertEquals(100, boss.hit(Region.CORE, 100, "b").applied());
        assertEquals(MAX_CORE - 110, boss.core());
        assertTrue(boss.hit(Region.CORE, 2000, "c").killed());
        assertEquals(0, boss.core());
        assertFalse(boss.hit(Region.CORE, 2000, "d").killed());
    }
    @Test void exposureEndsAfterTwelveSecondsAndInvalidDamageNeverPoisonsPools() {
        var boss = new DevilsWalkerState();
        for (double damage : new double[]{Double.NaN, Double.POSITIVE_INFINITY, -1, 0})
            assertEquals(0, boss.hit(Region.HULL, damage, null).applied());
        boss.hit(Region.FRONT_RIGHT, 100, null);
        for (int t = 0; t < STAGGER_TICKS; t++) boss.tick();
        for (int t = 0; t < EXPOSED_TICKS - 1; t++) boss.tick();
        assertEquals(Phase.EXPOSED, boss.phase());
        boss.tick();
        assertEquals(Phase.RECOVER, boss.phase());
    }
}
