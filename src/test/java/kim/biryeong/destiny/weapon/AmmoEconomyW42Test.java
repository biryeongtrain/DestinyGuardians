package kim.biryeong.destiny.weapon;

import com.google.gson.JsonParser;
import com.mojang.serialization.JsonOps;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class AmmoEconomyW42Test {
    @Test void immutableMetersPreserveOverflowAndSpendOnlyOneActualBrick() {
        var old=new AmmoMeters(95000,90000);var next=old.add(12000,15000);
        assertEquals(95000,old.special());assertEquals(107000,next.special());
        assertEquals(7000,next.spend(WeaponAmmoType.SPECIAL).special());
        assertEquals(105000,next.spend(WeaponAmmoType.SPECIAL).heavy());
        assertEquals(old,old.spend(WeaponAmmoType.SPECIAL));
    }
    @Test void corruptOrExtremeProgressCannotWrapNegativeOrCreatePrimaryBricks() {
        var m=new AmmoMeters(-1,Integer.MAX_VALUE).add(Integer.MAX_VALUE,Integer.MAX_VALUE);
        assertEquals(AmmoMeters.MAX,m.special());assertEquals(AmmoMeters.MAX,m.heavy());
        assertFalse(m.owed(WeaponAmmoType.PRIMARY));assertEquals(m,m.spend(WeaponAmmoType.PRIMARY));
        assertEquals(1,m.fraction(WeaponAmmoType.HEAVY));assertEquals(0,m.fraction(WeaponAmmoType.PRIMARY));
    }
    @Test void persistenceCodecRoundtripsDebtWithoutSharingMutableState() {
        var m=new AmmoMeters(203000,7100);var json=AmmoMeters.CODEC.encodeStart(JsonOps.INSTANCE,m).getOrThrow();
        assertEquals(m,AmmoMeters.CODEC.parse(JsonOps.INSTANCE,json).getOrThrow());
        assertEquals(AmmoMeters.EMPTY,AmmoMeters.CODEC.parse(JsonOps.INSTANCE,JsonParser.parseString("{}")).getOrThrow());
        assertEquals(0,AmmoMeters.CODEC.parse(JsonOps.INSTANCE,JsonParser.parseString("{\"heavy\":-50}")).getOrThrow().heavy());
    }
    @Test void generationStatContributesAndAssistsNeverBecomeFullFinalBlows() {
        var low=new AmmoGeneration(AmmoGeneration.Kind.PRIMARY,0).gains(false);
        var high=new AmmoGeneration(AmmoGeneration.Kind.PRIMARY,100).gains(false);
        assertTrue(high.special()>low.special());assertTrue(high.heavy()>low.heavy());
        var assist=new AmmoGeneration(AmmoGeneration.Kind.PRIMARY,100).gains(true);
        assertEquals(high.special()/2,assist.special());assertEquals(high.heavy()/2,assist.heavy());
        assertEquals(100,new AmmoGeneration(AmmoGeneration.Kind.SPECIAL,Integer.MAX_VALUE).stat());
    }
    @Test void catalogUsesOfficialAmmoAndGenerationStatWithSwordException() {
        for(var e:WeaponCatalog.all()) {
            var source=AmmoGeneration.weapon(e);var meta=WeaponCharacteristics.of(e);
            assertEquals(meta.ammo().name(),source.kind().name());
            assertEquals(e.family().equals("sword")?0:Math.clamp(meta.stats().getOrDefault("1931675084",0),0,100),source.stat());
            assertEquals(meta.ammo()!=WeaponAmmoType.PRIMARY,AmmoGeneration.perBrick(e)>0);
        }
    }
    @Test void doubleSpecialHasReducedPerWeaponPayoutAndNoInvalidNegativeGrant() {
        assertEquals(2,AmmoGeneration.split(4,2));assertEquals(1,AmmoGeneration.split(3,2));
        assertEquals(0,AmmoGeneration.split(0,2));assertEquals(0,AmmoGeneration.split(4,0));
        assertEquals(1,AmmoGeneration.split(1,2));
    }
    private static WeaponProfile profile(boolean infinite) {
        return new WeaponProfile(WeaponProfile.Mode.HITSCAN,5,10,6,infinite?0:30,40,40,0,1,1,0,0,0,0,false,infinite);
    }
    @Test void pickupsOnlyFillReserveNeverMagazineAndAreCapacityBounded() {
        var ammo=new WeaponMagazine(profile(false),1,28);
        assertEquals(2,ammo.addReserve(Integer.MAX_VALUE));assertEquals(30,ammo.reserve());assertEquals(1,ammo.rounds());
        assertEquals(0,ammo.addReserve(5));assertEquals(0,ammo.addReserve(-4));
        assertEquals(5,ammo.reload());assertEquals(6,ammo.rounds());assertEquals(25,ammo.reserve());
    }
    @Test void infinitePrimaryNeverConsumesOrStoresBrickAmmunition() {
        var ammo=new WeaponMagazine(profile(true),0,999);
        assertEquals(0,ammo.addReserve(10));assertEquals(0,ammo.reserve());assertEquals(0,ammo.rounds());
        assertEquals(6,ammo.reload());
    }
}
