package kim.biryeong.destiny.weapon;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class WeaponEconomyW40Test {
    private WeaponCharacteristics.Entry metadata(String id) { return WeaponCharacteristics.of(WeaponCatalog.find(id).orElseThrow()); }
    @Test void all63HaveIndependentOfficialSlotAmmoAndDamageDefinitions() {
        WeaponCatalogTest.assertExpandedCatalog();
        for(var e:WeaponCatalogTest.beforeW350Entries()) {
            var m=WeaponCharacteristics.of(e);var p=WeaponProfile.forEntry(e);
            assertEquals(e.id(),m.id());assertTrue(m.bungieHash()>0);
            assertEquals(java.util.Set.of("ace_of_spades","izanagis_burden").contains(e.id()),m.exotic(),e.id());
            assertEquals(m.ammo()==WeaponAmmoType.PRIMARY,p.infiniteReserve());
            assertEquals(m.ammo()==WeaponAmmoType.HEAVY,m.slot()==WeaponSlot.POWER);
            assertNotNull(m.stats());
        }
        assertEquals(WeaponSlot.KINETIC,metadata("austringer").slot());
        assertEquals(WeaponAmmoType.PRIMARY,metadata("austringer").ammo());
        assertEquals(WeaponSlot.ENERGY,metadata("ammit_ar2").slot());
        assertEquals(WeaponAmmoType.PRIMARY,metadata("ammit_ar2").ammo());
        assertEquals(WeaponSlot.KINETIC,metadata("bite_of_the_fox").slot());
        assertEquals(WeaponAmmoType.SPECIAL,metadata("bite_of_the_fox").ammo());
        assertEquals(WeaponSlot.ENERGY,metadata("beloved").slot());
        assertEquals(WeaponAmmoType.SPECIAL,metadata("beloved").ammo());
        assertEquals(WeaponCharacteristics.Damage.ARC,metadata("nezarec_s_whisper").damage());
        assertEquals(WeaponCharacteristics.Damage.STASIS,metadata("dimensional_hypotrochoid").damage());
    }
    @Test void everyPrimaryHasFiniteMagazineButRepeatedInfiniteReserveReloads() {
        int checked=0;
        for(var e:WeaponCatalog.all()) {
            var p=WeaponProfile.forEntry(e);if(!p.infiniteReserve())continue;checked++;
            var ammo=new WeaponMagazine(p,0,Integer.MAX_VALUE);
            assertEquals(0,ammo.rounds());assertEquals(0,ammo.reserve());
            for(int reload=0;reload<5;reload++) {
                assertTrue(ammo.canReload());assertEquals(p.magazine(),ammo.reload());
                assertFalse(ammo.canReload());
                for(int i=0;i<p.magazine();i++)assertTrue(ammo.consume());
                assertFalse(ammo.consume());assertEquals(0,ammo.reserve());
            }
        }
        assertTrue(checked>20);
    }
    @Test void primaryReloadStillUsesServerDeadlineAndCanBeCancelled() {
        var p=WeaponProfile.forEntry(WeaponCatalog.find("austringer").orElseThrow());
        var ammo=new WeaponMagazine(p,0,0);var cycle=new WeaponCycle();
        assertTrue(cycle.startReload(5,p,ammo));
        assertFalse(cycle.finishReload(5+p.reloadTicks()-1,ammo));assertEquals(0,ammo.rounds());
        cycle.cancelPending();assertFalse(cycle.finishReload(200,ammo));assertEquals(0,ammo.rounds());
        assertTrue(cycle.startReload(201,p,ammo));
        assertTrue(cycle.finishReload(201+p.reloadTicks(),ammo));assertEquals(p.magazine(),ammo.rounds());
        assertEquals(0,ammo.reserve());assertFalse(cycle.finishReload(999,ammo));
    }
    @Test void finiteSpecialCannotReloadWithoutReserveAndNeverOverfills() {
        var p=WeaponProfile.forEntry(WeaponCatalog.find("beloved").orElseThrow());
        var empty=new WeaponMagazine(p,0,0);assertFalse(empty.canReload());assertEquals(0,empty.reload());
        var limited=new WeaponMagazine(p,3,2);assertEquals(1,limited.reload());
        assertEquals(4,limited.rounds());assertEquals(1,limited.reserve());
    }
}
