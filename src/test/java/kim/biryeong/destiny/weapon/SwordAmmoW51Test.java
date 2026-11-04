package kim.biryeong.destiny.weapon;

import org.junit.jupiter.api.Test;
import java.util.Set;
import java.util.stream.Collectors;
import static org.junit.jupiter.api.Assertions.*;

/** Pure ammo/cadence safety and explicitly separated sourced versus authored sword rules. */
class SwordAmmoW51Test {
    private static WeaponCatalog.Entry entry(String id) { return WeaponCatalog.find(id).orElseThrow(); }
    private static WeaponProfile base() { return WeaponProfile.forEntry(entry("abide_the_return")); }
    @Test void fiveSwordsHaveOneFinitePoolAndAllFiveShapes() {
        var swords=WeaponCatalog.all().stream().filter(e->e.family().equals("sword")).toList();
        assertEquals(5,swords.size());
        assertEquals(Set.of(SwordProfile.Shape.values()),swords.stream().map(e->SwordProfile.of(e).shape()).collect(Collectors.toSet()));
        for(var e:swords) {
            var p=WeaponProfile.forEntry(e);
            assertEquals(0,p.reserve());assertFalse(p.infiniteReserve());
            assertEquals(WeaponProfile.Mode.MELEE,p.mode());
        }
    }
    @Test void vortexCurrentCostIsFourAndUnpoweredAllFramesCostOne() {
        assertEquals(4,SwordProfile.of(entry("falling_guillotine")).heavyCost(1));
        for(var e:WeaponCatalog.all())if(e.family().equals("sword")) {
            var s=SwordProfile.of(e);
            assertEquals(1,s.heavyCost(0));assertEquals(1,s.heavyCost(-1));
            assertTrue(s.heavyCost(1)>=2&&s.heavyCost(1)<=16);
        }
    }
    @Test void anyNonzeroEnergyHasFullPowerNotAnOldLinearCurve() {
        var s=SwordProfile.of(entry("abide_the_return"));
        for(double energy:new double[]{.00001,.1,.25,.5,1})assertEquals(1,s.power(energy));
        assertEquals(.35f,s.power(0)); // authored weak factor, not claimed original stat
    }
    @Test void chargedPaymentIsAtomicAndDoesNotSpendOnDuplicateOrInsufficientAmmo() {
        var p=base();var ammo=new WeaponMagazine(p,3,0);var c=new WeaponCycle();
        assertFalse(c.fire(100,p,ammo,4));assertEquals(3,ammo.total());
        assertTrue(c.fire(100,p,ammo,3));assertEquals(0,ammo.total());
        assertFalse(c.fire(100,p,ammo,1));assertEquals(0,ammo.total());
        assertFalse(c.fire(200,p,ammo,4));assertEquals(0,ammo.total());
    }
    @Test void rangedProfilesCannotSpendSwordMultiCostOrUseEmptySwordCadence() {
        for(String id:new String[]{"austringer","bad_omens","nezarec_s_whisper"}) {
            var p=WeaponProfile.forEntry(entry(id));var ammo=new WeaponMagazine(p,3,0);var c=new WeaponCycle();
            int loaded=ammo.rounds();long total=ammo.total();
            assertFalse(c.fire(10,p,ammo,3));assertFalse(c.emptyMelee(10,p));
            assertEquals(loaded,ammo.rounds());assertEquals(total,ammo.total());
        }
        var p=base();var ammo=new WeaponMagazine(p,3,0);var c=new WeaponCycle();
        for(int cost:new int[]{Integer.MIN_VALUE,-1,0,17,Integer.MAX_VALUE})assertFalse(c.fire(10,p,ammo,cost));
        assertEquals(3,ammo.total());
    }
    @Test void weakEmptySwingUsesTheSameOwnerCooldownEvenAcrossCancel() {
        var p=base();var c=new WeaponCycle();
        assertTrue(c.emptyMelee(100,p));c.cancelPending();
        var ammo=new WeaponMagazine(p,10,0);
        assertFalse(c.fire(101,p,ammo,4));assertEquals(10,ammo.total());
        assertTrue(c.fire(100+p.intervalTicks(),p,ammo,4));assertEquals(6,ammo.total());
    }
    @Test void swordPickupIsFiniteUsableAmmoAndNeverAnOrdinaryGunReload() {
        var p=base();var ammo=new WeaponMagazine(p,p.magazine()-2,0);
        assertEquals(2,ammo.addLoaded(20));assertEquals(p.magazine(),ammo.rounds());
        assertEquals(0,ammo.addLoaded(1));assertEquals(0,ammo.addLoaded(-1));assertEquals(0,ammo.reserve());
        var gun=WeaponProfile.forEntry(entry("beloved"));var ranged=new WeaponMagazine(gun,0,0);
        assertEquals(0,ranged.addLoaded(5));assertEquals(0,ranged.rounds());
        var primary=new WeaponMagazine(WeaponProfile.forEntry(entry("austringer")),0,0);
        assertEquals(0,primary.addLoaded(5));
    }
    @Test void legacyOverflowIsConservedAndCannotBeOverwrittenByPickup() {
        var p=base();var ammo=new WeaponMagazine(p,2,3,p.magazine()+7L);
        long total=ammo.total();assertEquals(p.magazine()+12L,total);
        ammo.reload();assertEquals(total,ammo.total());assertEquals(p.magazine(),ammo.rounds());
        assertEquals(0,ammo.reserve());assertEquals(12,ammo.overflow());assertEquals(0,ammo.addLoaded(4));
        assertTrue(ammo.consume(4));assertEquals(total-4,ammo.total());
        ammo.reload();assertEquals(total-4,ammo.total());assertEquals(8,ammo.overflow());
    }
    @Test void authoredHeavyProfilesAreBoundedAndCasterRemainsTraveling() {
        for(var e:WeaponCatalog.all())if(e.family().equals("sword")) {
            var p=WeaponProfile.forEntry(e);var s=SwordProfile.of(e);
            var heavy=s.attack(p,p.damage()*s.heavyMultiplier(),true);
            assertEquals(WeaponProfile.Mode.MELEE,heavy.mode());assertEquals(0,heavy.reserve());
            assertTrue(heavy.cadenceTicks()>=p.cadenceTicks());assertTrue(heavy.range()<=4);
        }
        var e=entry("temptation_s_hook");var projectile=SwordProfile.of(e).caster(WeaponProfile.forEntry(e),20);
        assertEquals(WeaponProfile.Mode.PROJECTILE,projectile.mode());assertTrue(projectile.speed()>0);
        assertTrue(projectile.range()<=96&&projectile.blastRadius()<=5);
        assertThrows(IllegalArgumentException.class,()->SwordProfile.of(entry("austringer")));
    }
}
