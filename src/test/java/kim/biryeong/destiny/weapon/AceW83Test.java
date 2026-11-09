package kim.biryeong.destiny.weapon;

import com.google.gson.JsonParser;
import org.junit.jupiter.api.Test;
import java.nio.file.Files;
import java.nio.file.Path;
import static org.junit.jupiter.api.Assertions.*;

class AceW83Test {
    @Test void canonicalFirstExoticAddsToEveryProfileWithoutReclassifyingOriginal63() {
        WeaponCatalogTest.assertExpandedCatalog();
        assertEquals(65,WeaponCatalog.all().stream().filter(e -> !LegendaryWeapons.contains(e.id())).count());
        assertEquals(2,WeaponCatalog.all().stream().filter(e->WeaponCharacteristics.of(e).exotic()).count());
        var ace=WeaponCatalog.find("ace_of_spades").orElseThrow();
        assertTrue(WeaponExotics.ace(ace));
        assertEquals(1,WeaponCatalog.all().stream().filter(WeaponExotics::ace).count());
        assertEquals(63,WeaponCatalog.all().stream().filter(e->!WeaponCharacteristics.of(e).exotic() && !LegendaryWeapons.contains(e.id())).count());
        var c=WeaponCharacteristics.of(ace);
        assertEquals(347366834L,c.bungieHash()); assertEquals(WeaponAmmoType.PRIMARY,c.ammo());
        assertEquals(WeaponSlot.KINETIC,c.slot()); assertEquals(WeaponCharacteristics.Damage.KINETIC,c.damage());
        assertEquals(85,c.stats().get("1240592695")); assertEquals(50,c.stats().get("155624089"));
        assertEquals(50,c.stats().get("943549884"));
        var p=WeaponProfile.forEntry(ace);
        assertEquals(13,p.magazine()); assertEquals(140,WeaponTiming.of(ace).rpm().orElseThrow());
        assertEquals(1200d/140,p.cadenceTicks(),1e-10); assertEquals(55,p.reloadTicks());
        assertTrue(p.infiniteReserve()); assertFalse(p.automatic());
        assertEquals(5,WeaponAimProfile.of(ace).transitionTicks());
        assertTrue(WeaponHandlingProfile.of(ace).supported());
        assertEquals(.75,WeaponAimMovementProfile.scalar(ace));
        assertEquals(WeaponModels.Grip.NATIVE,WeaponModels.defaultGrip(ace));
        assertEquals(.71,ReloadCreditProfile.find(ace).orElseThrow().fraction());
        assertEquals(39,WeaponAce.fireflyReloadTicks(ace));
        assertTrue(WeaponPerks.rolls().stream().noneMatch(r->r.id().equals(ace.id())));
    }
    @Test void unknownOrSpoofedEntryDoesNotBecomeAce() {
        assertFalse(WeaponExotics.ace(null));
        assertFalse(WeaponExotics.ace(new WeaponCatalog.Entry("ace_of_spades","hand_cannon","adaptive","Ace of Spades","Memento Mori","destiny:weapon/ace_of_spades")));
        assertThrows(IllegalArgumentException.class,()->WeaponAce.fireflyReloadTicks(WeaponCatalog.find("austringer").orElseThrow()));
    }
    @Test void sixEmissionsThenBaseAndNoRepeatedReloadCredit() {
        var c=new AceCycle();c.killed(10,false);assertTrue(c.reloaded(20));assertEquals(6,c.rounds());
        for(int i=5;i>=0;i--){assertTrue(c.shot());assertEquals(i,c.rounds());}
        assertFalse(c.shot());assertFalse(c.reloaded(30));assertEquals(0,c.rounds());
    }
    @Test void fullCompletionWindowIncludes72ButNot73OrEarlierTime() {
        var exact=new AceCycle();exact.killed(100,false);assertTrue(exact.reloaded(172));
        var late=new AceCycle();late.killed(100,false);assertFalse(late.reloaded(173));
        var past=new AceCycle();past.killed(100,false);assertFalse(past.reloaded(99));assertFalse(past.reloaded(-1));
        assertEquals(0,late.rounds());assertEquals(0,past.rounds());
    }
    @Test void stowClearsLoadedRoundsButKeepsPendingKillAndFirefly() {
        var c=new AceCycle();c.killed(10,true);c.stowed();assertTrue(c.killEligible(20));
        assertEquals(110,c.fireflyRemaining(20));assertTrue(c.reloaded(20));assertEquals(6,c.rounds());
        c.killed(21,true);c.stowed();assertEquals(0,c.rounds());assertEquals(119,c.fireflyRemaining(22));
        assertTrue(c.reloaded(22));assertEquals(6,c.rounds());
    }
    @Test void normalReloadWithoutFreshKillPreservesRemainingRoundsAsExplicitLocalPolicy() {
        var c=new AceCycle();c.killed(0,false);assertTrue(c.reloaded(1));assertTrue(c.shot());
        assertFalse(c.reloaded(2));assertEquals(5,c.rounds());
    }
    @Test void freshQualifyingReloadReplacesRatherThanAddsAsExplicitLocalPolicy() {
        var c=new AceCycle();c.killed(0,false);c.reloaded(1);c.shot();c.shot();c.killed(3,false);
        assertTrue(c.reloaded(4));assertEquals(6,c.rounds());
    }
    @Test void fireflyNeedsPrecisionAndExpiresAt120WithSafeMonotonicReads() {
        var c=new AceCycle();c.killed(10,false);assertEquals(0,c.fireflyRemaining(10));
        c.killed(20,true);assertEquals(0,c.fireflyRemaining(19));assertEquals(120,c.fireflyRemaining(20));
        assertEquals(1,c.fireflyRemaining(139));assertEquals(0,c.fireflyRemaining(140));
        c.killed(30,false);assertEquals(110,c.fireflyRemaining(30));
        c.killed(40,true);assertEquals(120,c.fireflyRemaining(40));
    }
    @Test void longTickBoundsDoNotOverflowOrMintCredit() {
        var c=new AceCycle();assertThrows(IllegalArgumentException.class,()->c.killed(-1,true));
        assertFalse(c.reloaded(Long.MAX_VALUE));assertFalse(c.killEligible(Long.MAX_VALUE));
        c.killed(Long.MAX_VALUE-72,true);assertTrue(c.reloaded(Long.MAX_VALUE));
        assertEquals(48,c.fireflyRemaining(Long.MAX_VALUE));
    }
    @Test void fireflySourcedCoreAndEndpointWithExplicitLocalHpInterpolation() {
        assertEquals(15,WeaponFirefly.damageAt(0));assertEquals(15,WeaponFirefly.damageAt(3.75));
        assertEquals(9,WeaponFirefly.damageAt(5.625),1e-6);assertEquals(3,WeaponFirefly.damageAt(7.5),1e-6);
        for(double d:new double[]{-1,7.500001,Double.NaN,Double.POSITIVE_INFINITY})assertEquals(0,WeaponFirefly.damageAt(d));
        assertEquals(128,WeaponFirefly.MAX_TARGETS);
    }
    @Test void officialWeaponAndFixedPlugsAreNotRandomLegendarySocketChoices() throws Exception {
        var p=JsonParser.parseString(Files.readString(Path.of("art/weapons/w83/data/bungie-ace.json"))).getAsJsonObject();
        assertEquals("Ace of Spades",p.getAsJsonObject("displayProperties").get("name").getAsString());
        var sockets=p.getAsJsonObject("sockets").getAsJsonArray("socketEntries");
        assertEquals(647617635L,sockets.get(0).getAsJsonObject().get("singleInitialItemHash").getAsLong());
        assertEquals(1561789734L,sockets.get(3).getAsJsonObject().get("singleInitialItemHash").getAsLong());
        assertEquals(1498917124L,sockets.get(10).getAsJsonObject().get("singleInitialItemHash").getAsLong());
        assertEquals(75,p.getAsJsonObject("stats").getAsJsonObject("stats").getAsJsonObject("1240592695").get("value").getAsInt());
    }
}
