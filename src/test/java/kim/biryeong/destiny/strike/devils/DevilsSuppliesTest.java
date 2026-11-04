package kim.biryeong.destiny.strike.devils;
import kim.biryeong.destiny.weapon.WeaponAmmoType;
import org.junit.jupiter.api.Test;
import java.util.*;
import static org.junit.jupiter.api.Assertions.*;
class DevilsSuppliesTest {
 final UUID a=UUID.randomUUID(),b=UUID.randomUUID();
 final DevilsPlan.Zone zone=DevilsPlan.Zone.RF;
 DevilsSupplies.Stock stock(String token,int rounds,int reserve){return new DevilsSupplies.Stock(token,"shotgun|rollA",WeaponAmmoType.SPECIAL,rounds,reserve,0,5,25);}
 @Test void reserveOnlyFirstUseAndImmutableRetryBaseline(){
  var l=new DevilsSupplies.Ledger(List.of(a));l.entry(a,zone,List.of(stock("one",2,0)),Set.of());
  var first=l.use(a,zone,List.of(stock("one",2,0)),Set.of()).orElseThrow().get("one");
  assertEquals(new DevilsSupplies.Grant(0,13),first);
  assertTrue(l.use(a,zone,List.of(stock("one",2,0)),Set.of()).isEmpty());
  l.entry(a,zone,List.of(stock("one",5,25)),Set.of());
  assertEquals(new DevilsSupplies.Grant(0,15),l.reset(a,zone,List.of(stock("one",0,0)),Set.of()).get("one"));
  assertEquals(new DevilsSupplies.Grant(0,0),l.reset(a,zone,List.of(stock("one",5,20)),Set.of()).get("one"));
 }
 @Test void reloadCannotDuplicateBaselineAmmo(){
  var l=new DevilsSupplies.Ledger(List.of(a));l.entry(a,zone,List.of(stock("one",0,10)),Set.of());
  assertEquals(new DevilsSupplies.Grant(0,0),l.reset(a,zone,List.of(stock("one",5,5)),Set.of()).get("one"));
 }
 @Test void sameCatalogSwapAndPerkEditAreNotOriginalWeapon(){
  var l=new DevilsSupplies.Ledger(List.of(a));l.entry(a,zone,List.of(stock("one",5,20)),Set.of());
  assertTrue(l.reset(a,zone,List.of(stock("two",0,0)),Set.of()).isEmpty());
  var changed=new DevilsSupplies.Stock("one","shotgun|rollB",WeaponAmmoType.SPECIAL,0,0,0,5,25);
  assertTrue(l.reset(a,zone,List.of(changed),Set.of()).isEmpty());
 }
 @Test void tradeAndDuplicateTokenCannotCreateAnotherEntitlement(){
  var l=new DevilsSupplies.Ledger(List.of(a,b));l.entry(a,zone,List.of(stock("one",5,20)),Set.of());
  l.entry(b,zone,List.of(stock("one",0,0)),Set.of());
  assertTrue(l.use(b,zone,List.of(stock("one",0,0)),Set.of()).orElseThrow().isEmpty());
  assertTrue(l.reset(a,zone,List.of(stock("one",0,0)),Set.of("one")).isEmpty());
  assertTrue(l.reset(a,zone,List.of(stock("one",0,0)),Set.of()).isEmpty());
 }
 @Test void newPlayerAndClosedSessionDenied(){
  var l=new DevilsSupplies.Ledger(List.of(a));l.entry(b,zone,List.of(stock("one",1,1)),Set.of());
  assertFalse(l.available(b,zone));l.entry(a,zone,List.of(stock("one",1,1)),Set.of());l.close();
  assertTrue(l.reset(a,zone,List.of(stock("one",0,0)),Set.of()).isEmpty());assertFalse(l.available(a,zone));
 }
 @Test void heavyQuarterAndSwordNoReserveGrant(){
  var l=new DevilsSupplies.Ledger(List.of(a));
  var heavy=new DevilsSupplies.Stock("h","rocket",WeaponAmmoType.HEAVY,0,0,0,1,6);
  var sword=new DevilsSupplies.Stock("s","sword",WeaponAmmoType.HEAVY,2,0,0,30,0);
  l.entry(a,zone,List.of(heavy,sword),Set.of());var result=l.use(a,zone,List.of(heavy,sword),Set.of()).orElseThrow();
  assertEquals(new DevilsSupplies.Grant(0,2),result.get("h"));assertEquals(new DevilsSupplies.Grant(0,0),result.get("s"));
 }
 @Test void capacityReductionAndLegacyOverflowCannotMint(){
  var l=new DevilsSupplies.Ledger(List.of(a));l.entry(a,zone,List.of(stock("one",5,25)),Set.of());
  var reduced=new DevilsSupplies.Stock("one","shotgun|rollA",WeaponAmmoType.SPECIAL,0,0,0,2,4);
  assertEquals(new DevilsSupplies.Grant(2,4),l.reset(a,zone,List.of(reduced),Set.of()).get("one"));
  var legacy=new DevilsSupplies.Stock("one","shotgun|rollA",WeaponAmmoType.SPECIAL,0,0,100,5,25);
  assertEquals(new DevilsSupplies.Grant(0,0),l.reset(a,zone,List.of(legacy),Set.of()).get("one"));
 }
 @Test void zoneRightsIndependentButReentryIsNotNewRight(){
  var l=new DevilsSupplies.Ledger(List.of(a));l.entry(a,zone,List.of(stock("one",1,0)),Set.of());l.use(a,zone,List.of(stock("one",1,0)),Set.of());
  l.entry(a,zone,List.of(stock("one",1,0)),Set.of());assertFalse(l.available(a,zone));
  l.entry(a,DevilsPlan.Zone.BL,List.of(stock("one",1,0)),Set.of());assertTrue(l.available(a,DevilsPlan.Zone.BL));
 }
 @Test void saturatedLegacyDebtCannotCreatePhantomBaseline(){
  var l=new DevilsSupplies.Ledger(List.of(a));
  var saturated=new DevilsSupplies.Stock("one","shotgun|rollA",WeaponAmmoType.SPECIAL,0,0,Long.MAX_VALUE,5,25);
  l.entry(a,zone,List.of(saturated),Set.of());
  assertEquals(new DevilsSupplies.Grant(0,0),l.use(a,zone,List.of(saturated),Set.of()).orElseThrow().get("one"));
 }
}
