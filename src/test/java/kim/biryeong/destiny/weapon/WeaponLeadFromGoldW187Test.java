package kim.biryeong.destiny.weapon;

import java.nio.file.*;
import java.util.*;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

/** Production magazine tests plus explicit source boundaries. Real player grant is master actualGT. */
class WeaponLeadFromGoldW187Test {
    private static String runtime() throws Exception {
        return Files.readString(Path.of("src/main/java/kim/biryeong/destiny/weapon/WeaponLeadFromGold.java"));
    }
    private static WeaponProfile profile() { return WeaponProfile.forEntry(WeaponCatalog.find("hollow_words").orElseThrow()); }
    @Test void productionReserveTransactionReportsActualAcceptedAndNeverRefillsMagazine() {
        var p=profile(); var ammo=new WeaponMagazine(p,1,p.reserve()-2);
        assertEquals(2,ammo.addReserve(LeadFromGoldProfile.amount(WeaponCatalog.find("hollow_words").orElseThrow(),1)));
        assertEquals(1,ammo.rounds()); assertEquals(p.reserve(),ammo.reserve());
        long full=ammo.total(); assertEquals(0,ammo.addReserve(8)); assertEquals(full,ammo.total());
        var empty=new WeaponMagazine(p,0,0);
        assertEquals(4,empty.addReserve(LeadFromGoldProfile.amount(WeaponCatalog.find("hollow_words").orElseThrow(),2)));
        assertEquals(0,empty.rounds()); assertEquals(4,empty.reserve());
    }
    @Test void productionLegacyOverflowIsConservedAndCannotBeCountedAsNewGrant() {
        var p=profile(); var legacy=new WeaponMagazine(p,100,100,19);
        long total=legacy.total(), overflow=legacy.overflow();
        assertTrue(overflow>0); assertEquals(219,total);
        assertEquals(0,legacy.addReserve(8)); assertEquals(total,legacy.total()); assertEquals(overflow,legacy.overflow());
        var saturated=new WeaponMagazine(p,Long.MAX_VALUE,Long.MAX_VALUE,Long.MAX_VALUE);
        assertEquals(Long.MAX_VALUE,saturated.total()); assertEquals(0,saturated.addReserve(8));
        assertEquals(Long.MAX_VALUE,saturated.total());
    }
    @Test void nullOwnerIsInert() { assertEquals(0,WeaponLeadFromGold.grant(null)); }
    @Test void runtimeRequiresOwnerActualLoadoutCanonicalStackAndExactBaseRoll() throws Exception {
        String source=runtime();
        for(String guard:List.of("player == null","!player.isAlive()","player.isRemoved()","player.isSpectator()",
                "!WeaponLoadout.enabled(player)","WeaponLoadout.equipped(player)","stack.getCount() == 1",
                "player.getInventory().getItem(e.slot().hotbar()) == stack","WeaponLoadout.slot(player, stack, e.weapon()) == e.slot()",
                "e.characteristics().ammo() == WeaponAmmoType.SPECIAL","WeaponCatalog.find(e.weapon().id()).filter(e.weapon()::equals)",
                "new IdentityHashMap<>()","seen.add(stack)","LeadFromGoldProfile.supports(entry)",
                "WeaponPerks.selected(stack, LeadFromGoldProfile.ID)","filter(LeadFromGoldProfile.rolls()::contains)"))
            assertTrue(source.contains(guard),guard);
        assertTrue(source.indexOf("seen.add(stack)") < source.indexOf("WeaponPerks.selected("));
        assertTrue(source.contains("LeadFromGoldProfile.amount(entry, specials.size())"));
        String loadout=Files.readString(Path.of("src/main/java/kim/biryeong/destiny/weapon/WeaponLoadout.java"));
        assertTrue(loadout.contains("WeaponItems.entry(stack).filter(e->slot(p,stack,e)==slot)"));
        String items=Files.readString(Path.of("src/main/java/kim/biryeong/destiny/weapon/WeaponItems.java"));
        assertTrue(items.contains("if (!stack.is(WeaponCombatItem.INSTANCE)) return Optional.empty()"));
        assertTrue(items.contains("getBooleanOr(LIVE, false)"));
    }
    @Test void reserveOnlySaveFollowsActualGainAndMasterOwnsBroadcastAndEvent() throws Exception {
        String source=runtime();
        for(String required:List.of("ammo.addReserve(","if (gained > 0)","WeaponItems.save(stack, ammo)",
                "accepted += gained","if (accepted > 0) player.getInventory().setChanged()","return accepted"))
            assertTrue(source.contains(required),required);
        assertTrue(source.indexOf("if (gained > 0)") < source.indexOf("WeaponItems.save("));
        for(String forbidden:List.of("broadcastChanges(","getMainHandItem(","getOffhandItem(","getSelectedSlot(",
                "getAttachedOrCreate(","WeaponLoadout.canUse(","SESSIONS","static final Map", "tick(",
                "AbilityService", "Guardians.data(","reload(","reloadRounds(","generateLoaded(","addLoaded(",
                "AmmoEconomy.","METERS", "energy", "System.currentTimeMillis", "new Thread"))
            assertFalse(source.contains(forbidden),forbidden);
    }
}
