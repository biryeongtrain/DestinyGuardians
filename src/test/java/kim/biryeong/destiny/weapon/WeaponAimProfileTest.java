package kim.biryeong.destiny.weapon;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class WeaponAimProfileTest {
    // Frozen pre-W327 roster assertions retain their original counts; new identities have separate coverage.
    @Test void all63ProfilesHaveSafeAndExplicitSupportedState() {
        WeaponCatalogTest.assertExpandedCatalog();
        assertEquals(57,WeaponCatalogTest.originalW30Entries().stream().filter(WeaponAimProfile::supports).count());
        int supported=0;
        for(var e:WeaponCatalog.all().stream().filter(e -> !LegendaryWeapons.contains(e.id())).toList()) {
            var p=WeaponAimProfile.of(e);
            assertTrue(p.transitionTicks()>=2&&p.transitionTicks()<=20);
            if(WeaponAimProfile.supports(e)) {
                supported++;assertTrue(p.kick()>=.1&&p.kick()<=2);
                assertTrue(p.zoom()>=1&&p.zoom()<=6);assertEquals(.04f,p.recoveryPerTick());
            } else {assertEquals(1,p.zoom());assertEquals(0,p.kick());assertEquals(1,p.falloffScalar());}
        }assertEquals(59,supported);
    }
    @Test void visualZoomAndFalloffScalarAreIndependent() {
        var p=WeaponAimProfile.of(WeaponCatalog.find("austringer").orElseThrow());
        assertEquals(1.4f,p.zoom());assertEquals(1.5f,p.falloffScalar());
        assertEquals(6,p.transitionTicks());assertEquals(59,p.stability());assertEquals(95,p.recoilDirection());
    }
    @Test void unsafeProfilesAreRejected() {
        assertThrows(IllegalArgumentException.class,()->new WeaponAimProfile(1,1,1,50,50,1,.1f,.04f));
        assertThrows(IllegalArgumentException.class,()->new WeaponAimProfile(5,Float.NaN,1,50,50,1,.1f,.04f));
        assertThrows(IllegalArgumentException.class,()->new WeaponAimProfile(5,1,1,101,50,1,.1f,.04f));
    }
}
