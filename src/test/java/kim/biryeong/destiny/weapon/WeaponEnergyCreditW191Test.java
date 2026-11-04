package kim.biryeong.destiny.weapon;

import org.junit.jupiter.api.Test;
import java.util.List;
import java.util.Map;
import static org.junit.jupiter.api.Assertions.*;

/** Tests the production credit helper's behavior; no copy of its calculation or numeric profile oracle. */
class WeaponEnergyCreditW191Test {
    private static WeaponEnergyCredit.Cooldown<String> ability(String slot, int full, int remaining) {
        return new WeaponEnergyCredit.Cooldown<>(slot, full, remaining);
    }
    @Test void splitUsesOnlyUnchargedSlotsAndTheirOwnFullAuthoredCooldowns() {
        var credits = WeaponEnergyCredit.cooldowns(List.of(
            ability("grenade", 1000, 1000), ability("melee", 200, 200), ability("class", 300, 0)), 8);
        assertEquals(Map.of("grenade", 960, "melee", 192), credits);
        assertFalse(credits.containsKey("class"));
        assertThrows(UnsupportedOperationException.class, () -> credits.put("class", 1));
    }
    @Test void fractionalSplitRoundsOnceAndSubsequentKillsStillUseFullCooldown() {
        var thirds = WeaponEnergyCredit.cooldowns(List.of(
            ability("grenade", 101, 100), ability("melee", 101, 100), ability("class", 101, 100)), 8);
        assertEquals(Map.of("grenade", 97, "melee", 97, "class", 97), thirds);
        var first = WeaponEnergyCredit.cooldowns(List.of(ability("grenade", 1000, 100)), 8);
        assertEquals(20, first.get("grenade"));
        var next = WeaponEnergyCredit.cooldowns(List.of(ability("grenade", 1000, first.get("grenade"))), 8);
        assertEquals(0, next.get("grenade"));
    }
    @Test void reachingReadyClampsWithoutRedistributingUnusedShareOrCountingInvalidDuration() {
        var credits = WeaponEnergyCredit.cooldowns(List.of(
            ability("grenade", 1000, 1000), ability("melee", 1000, 1),
            ability("class", 1000, 0), ability("invalid", 0, 200)), 8);
        assertEquals(Map.of("grenade", 960, "melee", 0), credits);
        // On the NEXT final blow only grenade is uncharged, so it receives the whole chunk.
        assertEquals(Map.of("grenade", 880), WeaponEnergyCredit.cooldowns(List.of(
            ability("grenade", 1000, 960), ability("melee", 1000, 0)), 8));
    }
    @Test void emptyOrInvalidCreditIsNoOpAndLargeCooldownCannotWrap() {
        assertTrue(WeaponEnergyCredit.cooldowns(List.of(), 8).isEmpty());
        assertTrue(WeaponEnergyCredit.cooldowns(List.of(ability("ready", 1000, 0)), 8).isEmpty());
        assertTrue(WeaponEnergyCredit.cooldowns(List.of(ability("negative", 1000, -1)), 8).isEmpty());
        assertTrue(WeaponEnergyCredit.cooldowns(List.of(ability("grenade", 1000, 1000)), 101).isEmpty());
        assertEquals(Map.of("long", 0), WeaponEnergyCredit.cooldowns(List.of(
            ability("long", Integer.MAX_VALUE, 1)), 8));
        assertThrows(IllegalArgumentException.class, () -> WeaponEnergyCredit.cooldowns(List.of(
            ability("grenade", 100, 100), ability("grenade", 100, 100)), 8));
    }
    @Test void superIsAdditiveAndClampedAndFullSuperIsUnchanged() {
        assertEquals(.31f, WeaponEnergyCredit.superEnergy(.3f, 1), .000001f);
        assertEquals(.315f, WeaponEnergyCredit.superEnergy(.3f, 1.5), .000001f);
        assertEquals(1f, WeaponEnergyCredit.superEnergy(.999f, 1));
        assertEquals(1f, WeaponEnergyCredit.superEnergy(1f, 1.5));
        assertEquals(.3f, WeaponEnergyCredit.superEnergy(.3f, Double.NaN));
    }
    @Test void corpseIdentityIsSharedAcrossPayloadCallbacksButIndependentAcrossEmissions() {
        record Corpse(int id) {}
        var directAndSplash = new WeaponEnergyCredit.Corpses<Corpse>();
        var corpse = new Corpse(1);
        var otherVictim = new Corpse(1); // Equal value, distinct actual object.
        assertFalse(directAndSplash.admit(null));
        assertTrue(directAndSplash.admit(corpse));
        assertFalse(directAndSplash.admit(corpse));
        assertTrue(directAndSplash.admit(otherVictim));
        assertTrue(new WeaponEnergyCredit.Corpses<Corpse>().admit(corpse));
    }
    @Test void noOpFinalBlowStillConsumesItsCorpseOpportunity() {
        var ledger = new WeaponEnergyCredit.Corpses<Object>();
        var corpse = new Object();
        assertTrue(ledger.admit(corpse));
        assertTrue(WeaponEnergyCredit.cooldowns(List.of(ability("grenade", 100, 0)), 8).isEmpty());
        // An ability subsequently going on cooldown cannot turn a duplicate splash callback into credit.
        assertFalse(ledger.admit(corpse));
    }
}
