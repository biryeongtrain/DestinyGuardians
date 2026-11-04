package kim.biryeong.destiny.weapon;

import org.junit.jupiter.api.Test;
import java.util.Map;
import static org.junit.jupiter.api.Assertions.*;

class PerkBatchDW323Test {
    private static final PerkBatchDCycle.Config C = PerkBatchDCycle.Config.profile();
    private static PerkBatchDCycle.Guard sword(boolean counter, boolean flash, boolean valiant) {
        return new PerkBatchDCycle.Guard(counter, flash, valiant, false, false);
    }
    private static final PerkBatchDCycle.Guard GLAIVE = new PerkBatchDCycle.Guard(false, false, false, true, true);

    @Test void profileCarriesDdcBaseValuesAndEveryOfficialSocket() {
        assertEquals(10, C.counterWindow()); assertEquals(40, C.counterTicks()); assertEquals(1.5f, C.counterMultiplier());
        assertEquals(50, C.flashCooldown()); assertEquals(20, C.valiantTicks()); assertEquals(80, C.tiltTicks());
        assertEquals(80, C.unstoppableTicks()); assertEquals(1.2f, C.unstoppableMultiplier());
        assertEquals(140, C.moaX1Ticks()); assertEquals(1.15f, C.moaX1()); assertEquals(80, C.moaX2Ticks()); assertEquals(1.25f, C.moaX2());
        assertEquals(200, PerkBatchDProfile.ticks(PerkBatchDProfile.TURNABOUT, "durationTicks"));
        assertEquals(50, PerkBatchDProfile.value(PerkBatchDProfile.TURNABOUT, "overshieldHp"));
        assertEquals(1.8, PerkBatchDProfile.value(PerkBatchDProfile.VALIANT_CHARGE, "lungeScale"));
        var counts = Map.of(PerkBatchDProfile.TURNABOUT, 7, PerkBatchDProfile.COUNTERATTACK, 3, PerkBatchDProfile.FLASH_COUNTER, 3,
                PerkBatchDProfile.TILTING, 1, PerkBatchDProfile.VALIANT_CHARGE, 1, PerkBatchDProfile.DUELISTS_TRANCE, 1,
                PerkBatchDProfile.COLD_STEEL, 1, PerkBatchDProfile.UNSTOPPABLE_FORCE, 1, PerkBatchDProfile.MASTER_OF_ARMS, 1);
        counts.forEach((id, n) -> assertEquals(n, PerkBatchDProfile.rolls(id).size(), id));
        assertTrue(WeaponPerks.ids().containsAll(PerkBatchDProfile.IDS));
        assertEquals("the_recluse", PerkBatchDProfile.rolls(PerkBatchDProfile.MASTER_OF_ARMS).getFirst().id());
        assertEquals(3371413057L, PerkBatchDProfile.rolls(PerkBatchDProfile.COLD_STEEL).getFirst().hash());
    }

    @Test void counterattackOnlyWithinHalfSecondOfRaisingGuardAndOnlyForThatSword() {
        var c = new PerkBatchDCycle(C); var blade = new Object(); var other = new Object();
        c.guard(100, blade, true);
        assertFalse(c.blocked(111, blade, sword(true, false, false)));
        assertEquals(1f, c.counterMultiplier(111, blade)); // 11 ticks after raising: too late
        c.guard(112, blade, false); c.guard(113, blade, true);
        c.blocked(123, blade, sword(true, false, false));
        assertEquals(1.5f, c.counterMultiplier(123, blade));
        assertEquals(1f, c.counterMultiplier(123, other));
        assertEquals(1.5f, c.counterMultiplier(162, blade));
        assertEquals(1f, c.counterMultiplier(163, blade));
        c.blocked(130, blade, sword(true, false, false)); // still within window: refreshes
        c.changed(blade);
        assertEquals(1f, c.counterMultiplier(131, blade));
    }

    @Test void flashCounterHasCooldownAndStaleTicksCannotRetrigger() {
        var c = new PerkBatchDCycle(C); var blade = new Object();
        c.guard(0, blade, true);
        assertTrue(c.blocked(5, blade, sword(false, true, false)));
        assertFalse(c.blocked(54, blade, sword(false, true, false)));
        assertFalse(c.blocked(3, blade, sword(false, true, false))); // backward tick ignored
        assertTrue(c.blocked(55, blade, sword(false, true, false)));
        assertFalse(c.blocked(56, blade, sword(true, false, true)));
    }

    @Test void valiantChargeIsConsumedByTheNextSwingWithinOneSecond() {
        var c = new PerkBatchDCycle(C); var blade = new Object();
        c.blocked(10, blade, sword(false, false, true));
        assertFalse(c.consumeValiant(11, new Object()));
        assertTrue(c.consumeValiant(29, blade));
        assertFalse(c.consumeValiant(29, blade));
        c.blocked(40, blade, sword(false, false, true));
        assertFalse(c.consumeValiant(60, blade)); // expired at 40 + 20
    }

    @Test void glaiveShieldBuffsTiltingEndsOnLoweringUnstoppableKeepsTimer() {
        var c = new PerkBatchDCycle(C); var glaive = new Object();
        c.guard(0, glaive, true);
        c.blocked(2, glaive, GLAIVE);
        assertTrue(c.tilting(3, glaive));
        assertEquals(1.2f, c.unstoppableMultiplier(3, glaive));
        c.guard(4, glaive, false);
        assertFalse(c.tilting(4, glaive));
        assertEquals(1.2f, c.unstoppableMultiplier(81, glaive));
        assertEquals(1f, c.unstoppableMultiplier(82, glaive));
        c.guard(90, glaive, true);
        assertFalse(c.tilting(90, glaive)); // re-raising does not revive without a new block
    }

    @Test void duelistsTranceLastsUntilStow() {
        var c = new PerkBatchDCycle(C); var blade = new Object();
        c.swordKill(blade);
        c.guard(1, blade, false);
        assertTrue(c.trance(blade));
        c.guard(500, blade, true);
        assertTrue(c.trance(blade));
        c.guard(501, new Object(), false);
        assertFalse(c.trance(blade));
    }

    @Test void masterOfArmsStacksRefreshesAndFallsBackToX1() {
        var c = new PerkBatchDCycle(C);
        assertEquals(1f, c.moaMultiplier(0));
        c.weaponKill(0);
        assertEquals(1.15f, c.moaMultiplier(1));
        c.weaponKill(10);
        assertEquals(1.25f, c.moaMultiplier(11));
        assertEquals(1.25f, c.moaMultiplier(89));
        assertEquals(1.15f, c.moaMultiplier(90)); // x2 expired, x1 (10 + 140) still running
        assertEquals(1f, c.moaMultiplier(150));
        c.weaponKill(200);
        assertEquals(1.15f, c.moaMultiplier(201)); // fresh x1 after full expiry
        assertTrue(new PerkBatchDCycle(C).idle(0));
        assertFalse(c.idle(201));
    }

    @Test void swordRestoreNeverExceedsCapacity() {
        var s = new SwordCycle();
        s.bind(SwordCycle.CAPACITY - 10, 0);
        s.restore(1000);
        assertEquals(SwordCycle.CAPACITY, s.energy());
        s.restore(-5);
        assertEquals(SwordCycle.CAPACITY, s.energy());
    }
}
